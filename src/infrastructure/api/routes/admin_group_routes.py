"""
Admin Group Routes

Read-only API endpoints for admin portal to view groups.
Queries MySQL groups table (no duplication with MongoDB).
"""

from flask import Blueprint, request, jsonify
from ....infrastructure.persistence.database import database
from ....infrastructure.persistence.group_repository_impl import GroupRepository
from ....infrastructure.persistence.mongodb_connection import mongodb
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

admin_group_bp = Blueprint('admin_groups', __name__, url_prefix='/api/admin/groups')


@admin_group_bp.route('', methods=['GET'])
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
