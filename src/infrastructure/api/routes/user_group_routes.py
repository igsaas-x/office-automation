from flask import Blueprint, jsonify, g
from ....infrastructure.persistence.database import database
from ....infrastructure.persistence.employee_group_repository_impl import EmployeeGroupRepository
from ....infrastructure.persistence.group_repository_impl import GroupRepository
from ....infrastructure.persistence.mongodb_connection import mongodb
from ....infrastructure.external.opnform_client import opnform_client
import logging

logger = logging.getLogger(__name__)

user_group_bp = Blueprint('user_groups', __name__)

def get_repositories():
    """Get repository instances with a new session"""
    session = database.get_session()
    return (
        EmployeeGroupRepository(session),
        GroupRepository(session),
        session
    )

@user_group_bp.route('/user/groups', methods=['GET'])
def get_user_groups():
    """
    Get groups that the authenticated user is enrolled in
    ---
    tags:
      - User - Groups
    parameters:
      - in: header
        name: X-Telegram-Init-Data
        type: string
        required: true
        description: Telegram Web App initData for authentication
    responses:
      200:
        description: List of groups user is enrolled in
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
                        example: "Engineering Team"
                      business_name:
                        type: string
                        example: "Tech Corp"
                      joined_at:
                        type: string
                        example: "2024-01-15T10:30:00"
                      has_form:
                        type: boolean
                        example: true
                      form_url:
                        type: string
                        example: "https://opnform.com/forms/employee-registration"
                      form_name:
                        type: string
                        example: "Employee Registration Form"
                total:
                  type: integer
                  example: 2
      401:
        description: Unauthorized - invalid Telegram authentication
      403:
        description: Forbidden - user not registered as employee
      500:
        description: Internal server error
    """
    try:
        # Get current user from Flask context (set by Telegram auth middleware)
        current_user = g.current_user

        # Get repositories
        employee_group_repo, group_repo, session = get_repositories()

        try:
            # Get all employee_group records for this employee
            employee_groups = employee_group_repo.find_by_employee_id(current_user.id)

            # Fetch full group details for each enrollment
            user_groups = []
            for eg in employee_groups:
                group = group_repo.find_by_id(eg.group_id)
                if group:
                    user_groups.append({
                        'employee_group': eg,
                        'group': group
                    })

            # Enrich with OpnForm data
            enriched_groups = _enrich_with_form_data(user_groups)

            return jsonify({
                'success': True,
                'data': {
                    'groups': enriched_groups,
                    'total': len(enriched_groups)
                }
            }), 200

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error getting user groups: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def _enrich_with_form_data(user_groups):
    """
    Enrich group data with OpnForm information

    Args:
        user_groups: List of dicts with 'employee_group' and 'group' objects

    Returns:
        List of dictionaries with group data + form information
    """
    if not user_groups:
        return []

    # Convert to dict format
    enriched = []
    for item in user_groups:
        eg = item['employee_group']
        group = item['group']

        group_data = {
            'id': group.id,
            'chat_id': group.chat_id,
            'name': group.name,
            'business_name': group.business_name,
            'joined_at': eg.joined_at.isoformat() if eg.joined_at else None,
            'has_form': False,
            'form_url': None,
            'form_name': None
        }
        enriched.append(group_data)

    try:
        # Get MongoDB database
        db_mongo = mongodb.get_database()

        # Collect all chat_ids for batch query
        chat_ids = [item['group'].chat_id for item in user_groups]

        # Batch query MongoDB for form configurations
        form_configs = list(db_mongo.form_configurations.find({
            'telegram_group_chat_id': {'$in': chat_ids},
            'is_active': True
        }))

        # Create lookup map: chat_id -> form_config
        form_config_map = {
            config['telegram_group_chat_id']: config
            for config in form_configs
        }

        # If we have any forms, fetch all forms from OpnForm to get slugs
        if form_configs:
            try:
                all_forms = opnform_client.get_forms()
                if all_forms:
                    # Create lookup map: form_id -> form_details
                    form_details_map = {
                        form['id']: form
                        for form in all_forms
                    }

                    # Enrich each group with form data
                    for group_data in enriched:
                        form_config = form_config_map.get(group_data['chat_id'])
                        if form_config:
                            opnform_form_id = form_config.get('opnform_form_id')
                            form_details = form_details_map.get(opnform_form_id)

                            if form_details and form_details.get('slug'):
                                group_data['has_form'] = True
                                group_data['form_url'] = f"https://opnform.com/forms/{form_details['slug']}"
                                group_data['form_name'] = form_config.get('form_name') or form_details.get('title')
                else:
                    # OpnForm API failed, but we can still indicate forms exist
                    logger.warning("Failed to fetch forms from OpnForm API")
                    for group_data in enriched:
                        form_config = form_config_map.get(group_data['chat_id'])
                        if form_config:
                            group_data['has_form'] = True
                            group_data['form_name'] = form_config.get('form_name')
                            # form_url remains None
            except Exception as e:
                logger.error(f"Error fetching OpnForm data: {e}", exc_info=True)
                # Continue with form configurations but no URLs
                for group_data in enriched:
                    form_config = form_config_map.get(group_data['chat_id'])
                    if form_config:
                        group_data['has_form'] = True
                        group_data['form_name'] = form_config.get('form_name')

    except Exception as e:
        logger.error(f"Error enriching groups with form data: {e}", exc_info=True)
        # Continue without form data - graceful degradation

    return enriched
