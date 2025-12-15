"""
Admin Group Routes

Read-only API endpoints for admin portal to view groups.
Queries MySQL groups table (no duplication with MongoDB).
"""

from flask import Blueprint, request, jsonify
from ....infrastructure.persistence.database import database
from ....infrastructure.persistence.group_repository_impl import GroupRepository
from ....infrastructure.persistence.mongodb_connection import mongodb
from ..middleware.jwt_auth import jwt_required_admin
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

admin_group_bp = Blueprint('admin_groups', __name__, url_prefix='/api/admin/groups')


@admin_group_bp.route('', methods=['GET'])
@jwt_required_admin
def list_all_groups():
    """
    List all groups from MySQL (admin view)
    ---
    tags:
      - Admin - Groups
    security:
      - Bearer: []
    parameters:
      - in: query
        name: search
        type: string
        description: Search by group name
      - in: query
        name: has_form
        type: boolean
        description: Filter by whether group has linked form
      - in: query
        name: limit
        type: integer
        default: 50
        description: Maximum number of results
      - in: query
        name: offset
        type: integer
        default: 0
        description: Number of results to skip
    responses:
      200:
        description: List of all groups
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                groups:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      chat_id:
                        type: string
                        example: "-1001234567890"
                      name:
                        type: string
                        example: "My Group"
                      created_at:
                        type: string
                        example: "2023-12-14T10:00:00"
                      has_form:
                        type: boolean
                        example: true
                      form_info:
                        type: object
                        properties:
                          form_config_id:
                            type: string
                            example: "67abc123def456"
                          form_name:
                            type: string
                            example: "Registration Form"
                          opnform_form_id:
                            type: string
                            example: "opnform-123"
                      submission_count:
                        type: integer
                        example: 42
                total:
                  type: integer
                  example: 100
                limit:
                  type: integer
                  example: 50
                offset:
                  type: integer
                  example: 0
      401:
        description: Unauthorized
    """
    try:
        session = database.get_session()
        group_repo = GroupRepository(session)

        # Get all groups from MySQL
        # Note: GroupRepository doesn't have find_all method, so we query directly
        from ...persistence.models import GroupModel
        query = session.query(GroupModel)

        # Search filter
        search = request.args.get('search')
        if search:
            query = query.filter(GroupModel.name.like(f'%{search}%'))

        # Get total count
        total = query.count()

        # Pagination
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        groups = query.order_by(GroupModel.created_at.desc()).offset(offset).limit(limit).all()

        # Convert to dict and add form info from MongoDB
        db_mongo = mongodb.get_database()
        result_groups = []

        for group in groups:
            group_data = {
                'id': group.id,
                'chat_id': group.chat_id,
                'name': group.name,
                'created_at': group.created_at.isoformat() if group.created_at else None,
                'has_form': False,
                'form_info': None,
                'submission_count': 0
            }

            # Check if group has linked form in MongoDB (by chat_id)
            form_config = db_mongo.form_configurations.find_one({
                'telegram_group_chat_id': group.chat_id,
                'is_active': True
            })

            if form_config:
                group_data['has_form'] = True
                group_data['form_info'] = {
                    'form_config_id': str(form_config['_id']),
                    'form_name': form_config.get('form_name'),
                    'opnform_form_id': form_config.get('opnform_form_id')
                }

                # Get submission count
                group_data['submission_count'] = db_mongo.form_submissions.count_documents({
                    'form_config_id': form_config['_id']
                })

            result_groups.append(group_data)

        session.close()

        # Filter by has_form if requested
        has_form_filter = request.args.get('has_form')
        if has_form_filter is not None:
            if has_form_filter.lower() == 'true':
                result_groups = [g for g in result_groups if g['has_form']]
            else:
                result_groups = [g for g in result_groups if not g['has_form']]

        return jsonify({
            "success": True,
            "data": {
                "groups": result_groups,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }), 200

    except Exception as e:
        logger.error(f"Error listing groups (admin): {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_group_bp.route('/<int:group_id>', methods=['GET'])
@jwt_required_admin
def get_group_details(group_id):
    """
    Get group details from MySQL (admin view)
    ---
    tags:
      - Admin - Groups
    security:
      - Bearer: []
    parameters:
      - in: path
        name: group_id
        type: integer
        required: true
        description: Group ID (MySQL)
    responses:
      200:
        description: Group details
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                chat_id:
                  type: string
                  example: "-1001234567890"
                name:
                  type: string
                  example: "My Group"
                created_at:
                  type: string
                  example: "2023-12-14T10:00:00"
                has_form:
                  type: boolean
                  example: true
                form_info:
                  type: object
                  properties:
                    form_config_id:
                      type: string
                      example: "67abc123def456"
                    form_name:
                      type: string
                      example: "Registration Form"
                    opnform_form_id:
                      type: string
                      example: "opnform-123"
                    is_active:
                      type: boolean
                      example: true
                submission_count:
                  type: integer
                  example: 42
                recent_submissions:
                  type: array
                  items:
                    type: object
                    properties:
                      _id:
                        type: string
                        example: "67submission123"
                      form_config_id:
                        type: string
                        example: "67abc123def456"
                      submission_data:
                        type: object
                      created_at:
                        type: string
                        example: "2023-12-14T10:00:00"
      404:
        description: Group not found
    """
    try:
        session = database.get_session()
        group_repo = GroupRepository(session)

        # Get group from MySQL
        group = group_repo.find_by_id(group_id)

        if not group:
            session.close()
            return jsonify({"success": False, "error": "Group not found"}), 404

        # Convert to dict
        group_data = {
            'id': group.id,
            'chat_id': group.chat_id,
            'name': group.name,
            'created_at': group.created_at.isoformat() if group.created_at else None,
            'has_form': False,
            'form_info': None,
            'submission_count': 0,
            'recent_submissions': []
        }

        # Check MongoDB for form link
        db_mongo = mongodb.get_database()
        form_config = db_mongo.form_configurations.find_one({
            'telegram_group_chat_id': group.chat_id,
            'is_active': True
        })

        if form_config:
            group_data['has_form'] = True
            group_data['form_info'] = {
                'form_config_id': str(form_config['_id']),
                'form_name': form_config.get('form_name'),
                'opnform_form_id': form_config.get('opnform_form_id'),
                'is_active': form_config.get('is_active')
            }

            # Get submission count
            group_data['submission_count'] = db_mongo.form_submissions.count_documents({
                'form_config_id': form_config['_id']
            })

            # Get recent submissions (last 10)
            recent_subs = list(db_mongo.form_submissions.find(
                {'form_config_id': form_config['_id']},
                sort=[('created_at', -1)],
                limit=10
            ))

            for sub in recent_subs:
                sub['_id'] = str(sub['_id'])
                if sub.get('form_config_id'):
                    sub['form_config_id'] = str(sub['form_config_id'])
                if sub.get('customer_id'):
                    sub['customer_id'] = str(sub['customer_id'])

            group_data['recent_submissions'] = recent_subs

        session.close()

        return jsonify({
            "success": True,
            "data": group_data
        }), 200

    except Exception as e:
        logger.error(f"Error getting group details (admin): {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_group_bp.route('/stats', methods=['GET'])
@jwt_required_admin
def get_group_stats():
    """
    Get group statistics (admin dashboard)
    ---
    tags:
      - Admin - Groups
    security:
      - Bearer: []
    responses:
      200:
        description: Group statistics
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                total_groups:
                  type: integer
                  example: 150
                groups_with_forms:
                  type: integer
                  example: 45
                groups_without_forms:
                  type: integer
                  example: 105
                total_submissions:
                  type: integer
                  example: 1234
                recent_groups_7d:
                  type: integer
                  example: 12
    """
    try:
        session = database.get_session()
        from ...persistence.models import GroupModel

        # Total groups in MySQL
        total_groups = session.query(GroupModel).count()

        # Get MongoDB stats
        db_mongo = mongodb.get_database()

        # Groups with forms linked (count distinct telegram_group_chat_id in form_configurations)
        groups_with_forms_cursor = db_mongo.form_configurations.aggregate([
            {'$match': {'is_active': True, 'telegram_group_chat_id': {'$ne': None}}},
            {'$group': {'_id': '$telegram_group_chat_id'}},
            {'$count': 'total'}
        ])
        groups_with_forms_result = list(groups_with_forms_cursor)
        groups_with_forms = groups_with_forms_result[0]['total'] if groups_with_forms_result else 0

        # Total submissions across all groups
        total_submissions = db_mongo.form_submissions.count_documents({})

        # Groups created in last 7 days
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_groups = session.query(GroupModel).filter(
            GroupModel.created_at >= seven_days_ago
        ).count()

        session.close()

        return jsonify({
            "success": True,
            "data": {
                "total_groups": total_groups,
                "groups_with_forms": groups_with_forms,
                "groups_without_forms": total_groups - groups_with_forms,
                "total_submissions": total_submissions,
                "recent_groups_7d": recent_groups
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting group stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_group_bp.route('/<int:group_id>/form', methods=['POST'])
@jwt_required_admin
def link_form_to_group(group_id):
    """
    Link OpnForm to a group
    ---
    tags:
      - Admin - Groups
    security:
      - Bearer: []
    parameters:
      - in: path
        name: group_id
        type: integer
        required: true
        description: Group ID (MySQL)
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - opnform_form_id
          properties:
            opnform_form_id:
              type: string
              description: OpnForm form ID
            form_name:
              type: string
              description: Optional form name
    responses:
      200:
        description: Form linked successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                form_config_id:
                  type: string
                  example: "67abc123def456"
                opnform_form_id:
                  type: string
                  example: "opnform-form-123"
                form_name:
                  type: string
                  example: "Registration Form"
                group_id:
                  type: integer
                  example: 1
                group_chat_id:
                  type: string
                  example: "-1001234567890"
      404:
        description: Group not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Group not found"
      400:
        description: Invalid request
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "opnform_form_id is required"
    """
    try:
        data = request.get_json()
        opnform_form_id = data.get('opnform_form_id')
        form_name = data.get('form_name', f'Form for Group {group_id}')

        if not opnform_form_id:
            return jsonify({"success": False, "error": "opnform_form_id is required"}), 400

        # Verify group exists in MySQL
        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_id(group_id)

        if not group:
            session.close()
            return jsonify({"success": False, "error": "Group not found"}), 404

        # Create or update form_configuration in MongoDB
        db_mongo = mongodb.get_database()

        # Check if form already exists for this group
        existing_config = db_mongo.form_configurations.find_one({
            'telegram_group_chat_id': group.chat_id
        })

        from datetime import datetime

        if existing_config:
            # Update existing configuration
            db_mongo.form_configurations.update_one(
                {'_id': existing_config['_id']},
                {
                    '$set': {
                        'opnform_form_id': opnform_form_id,
                        'form_name': form_name,
                        'is_active': True,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            form_config_id = str(existing_config['_id'])
        else:
            # Create new configuration
            form_config = {
                'telegram_group_chat_id': group.chat_id,
                'opnform_form_id': opnform_form_id,
                'form_name': form_name,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            result = db_mongo.form_configurations.insert_one(form_config)
            form_config_id = str(result.inserted_id)

        session.close()

        return jsonify({
            "success": True,
            "data": {
                "form_config_id": form_config_id,
                "opnform_form_id": opnform_form_id,
                "form_name": form_name,
                "group_id": group_id,
                "group_chat_id": group.chat_id
            }
        }), 200

    except Exception as e:
        logger.error(f"Error linking form to group: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_group_bp.route('/<int:group_id>/webhook', methods=['GET'])
@jwt_required_admin
def get_webhook_url(group_id):
    """
    Get webhook URL for receiving OpnForm submissions
    ---
    tags:
      - Admin - Groups
    security:
      - Bearer: []
    parameters:
      - in: path
        name: group_id
        type: integer
        required: true
        description: Group ID (MySQL)
    responses:
      200:
        description: Webhook URL
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                webhook_url:
                  type: string
                  example: "http://localhost:3000/api/webhooks/opnform/67abc123def456"
                form_config_id:
                  type: string
                  example: "67abc123def456"
                opnform_form_id:
                  type: string
                  example: "opnform-form-123"
                form_name:
                  type: string
                  example: "Registration Form"
      404:
        description: Group not found or no form linked
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "No form linked to this group"
    """
    try:
        # Verify group exists in MySQL
        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_id(group_id)

        if not group:
            session.close()
            return jsonify({"success": False, "error": "Group not found"}), 404

        # Get form configuration from MongoDB
        db_mongo = mongodb.get_database()
        form_config = db_mongo.form_configurations.find_one({
            'telegram_group_chat_id': group.chat_id,
            'is_active': True
        })

        if not form_config:
            session.close()
            return jsonify({"success": False, "error": "No form linked to this group"}), 404

        # Generate webhook URL
        from ...config.settings import settings
        base_url = settings.ADMIN_PORTAL_URL.rstrip('/')
        webhook_url = f"{base_url}/api/webhooks/opnform/{str(form_config['_id'])}"

        session.close()

        return jsonify({
            "success": True,
            "data": {
                "webhook_url": webhook_url,
                "form_config_id": str(form_config['_id']),
                "opnform_form_id": form_config.get('opnform_form_id'),
                "form_name": form_config.get('form_name')
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting webhook URL: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_group_bp.route('/<int:group_id>/submissions', methods=['GET'])
@jwt_required_admin
def get_group_submissions(group_id):
    """
    Get form submissions for a group
    ---
    tags:
      - Admin - Groups
    security:
      - Bearer: []
    parameters:
      - in: path
        name: group_id
        type: integer
        required: true
        description: Group ID (MySQL)
      - in: query
        name: limit
        type: integer
        default: 50
        description: Maximum number of results
      - in: query
        name: offset
        type: integer
        default: 0
        description: Number of results to skip
      - in: query
        name: start_date
        type: string
        format: date
        description: Filter submissions from this date (YYYY-MM-DD)
      - in: query
        name: end_date
        type: string
        format: date
        description: Filter submissions until this date (YYYY-MM-DD)
    responses:
      200:
        description: List of submissions
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                submissions:
                  type: array
                  items:
                    type: object
                    properties:
                      _id:
                        type: string
                        example: "67submission123"
                      form_config_id:
                        type: string
                        example: "67abc123def456"
                      opnform_submission_id:
                        type: string
                        example: "sub-123"
                      submission_data:
                        type: object
                        description: The actual form submission data from OpnForm
                      processing_status:
                        type: string
                        example: "received"
                      created_at:
                        type: string
                        example: "2023-12-14T10:00:00"
                total:
                  type: integer
                  example: 100
                limit:
                  type: integer
                  example: 50
                offset:
                  type: integer
                  example: 0
                group_id:
                  type: integer
                  example: 1
                group_name:
                  type: string
                  example: "My Group"
                form_name:
                  type: string
                  example: "Registration Form"
      404:
        description: Group not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Group not found"
    """
    try:
        # Verify group exists in MySQL
        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_id(group_id)

        if not group:
            session.close()
            return jsonify({"success": False, "error": "Group not found"}), 404

        # Get form configuration from MongoDB
        db_mongo = mongodb.get_database()
        form_config = db_mongo.form_configurations.find_one({
            'telegram_group_chat_id': group.chat_id,
            'is_active': True
        })

        if not form_config:
            session.close()
            return jsonify({
                "success": True,
                "data": {
                    "submissions": [],
                    "total": 0,
                    "message": "No form linked to this group"
                }
            }), 200

        # Build query filter
        query_filter = {'form_config_id': form_config['_id']}

        # Date filters
        from datetime import datetime
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date or end_date:
            query_filter['created_at'] = {}
            if start_date:
                query_filter['created_at']['$gte'] = datetime.fromisoformat(start_date)
            if end_date:
                # Add one day to include the end_date
                end_datetime = datetime.fromisoformat(end_date)
                from datetime import timedelta
                query_filter['created_at']['$lt'] = end_datetime + timedelta(days=1)

        # Get total count
        total = db_mongo.form_submissions.count_documents(query_filter)

        # Pagination
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Get submissions
        submissions = list(db_mongo.form_submissions.find(
            query_filter,
            sort=[('created_at', -1)],
            skip=offset,
            limit=limit
        ))

        # Convert ObjectId to string
        for sub in submissions:
            sub['_id'] = str(sub['_id'])
            if sub.get('form_config_id'):
                sub['form_config_id'] = str(sub['form_config_id'])
            if sub.get('created_at'):
                sub['created_at'] = sub['created_at'].isoformat()

        session.close()

        return jsonify({
            "success": True,
            "data": {
                "submissions": submissions,
                "total": total,
                "limit": limit,
                "offset": offset,
                "group_id": group_id,
                "group_name": group.name,
                "form_name": form_config.get('form_name')
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting group submissions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
