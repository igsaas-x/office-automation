"""
Webhook Routes

Handles incoming webhooks from OpnForm for form submissions.
Stores submissions in MongoDB linked to group configurations.
"""

from flask import Blueprint, request, jsonify
from ....infrastructure.persistence.mongodb_connection import mongodb
from bson import ObjectId
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')


@webhook_bp.route('/opnform/<form_config_id>', methods=['POST'])
def receive_opnform_submission(form_config_id):
    """
    Receive OpnForm submission webhook
    ---
    tags:
      - Webhooks
    parameters:
      - in: path
        name: form_config_id
        type: string
        required: true
        description: Form configuration ID (MongoDB ObjectId)
      - in: body
        name: body
        required: true
        schema:
          type: object
          description: OpnForm submission data
    responses:
      200:
        description: Submission received and stored
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                submission_id:
                  type: string
                  example: "67submission123"
                form_config_id:
                  type: string
                  example: "67abc123def456"
                status:
                  type: string
                  example: "received"
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
              example: "No submission data provided"
      404:
        description: Form configuration not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Form configuration not found"
    """
    try:
        # Validate form_config_id
        try:
            config_obj_id = ObjectId(form_config_id)
        except Exception:
            logger.error(f"Invalid form_config_id format: {form_config_id}")
            return jsonify({"success": False, "error": "Invalid form_config_id format"}), 400

        # Get submission data from request
        submission_data = request.get_json()

        if not submission_data:
            logger.error("No submission data provided")
            return jsonify({"success": False, "error": "No submission data provided"}), 400

        # Get form configuration from MongoDB
        db_mongo = mongodb.get_database()
        form_config = db_mongo.form_configurations.find_one({'_id': config_obj_id})

        if not form_config:
            logger.error(f"Form configuration not found: {form_config_id}")
            return jsonify({"success": False, "error": "Form configuration not found"}), 404

        if not form_config.get('is_active'):
            logger.warning(f"Form configuration is not active: {form_config_id}")
            return jsonify({"success": False, "error": "Form configuration is not active"}), 400

        # Extract submission ID from OpnForm data (if provided)
        opnform_submission_id = submission_data.get('id') or submission_data.get('submission_id')

        # Create submission record
        submission_record = {
            'form_config_id': config_obj_id,
            'opnform_submission_id': opnform_submission_id,
            'opnform_form_id': form_config.get('opnform_form_id'),
            'telegram_group_chat_id': form_config.get('telegram_group_chat_id'),
            'submission_data': submission_data,
            'processing_status': 'received',
            'created_at': datetime.utcnow(),
            'metadata': {
                'submitted_at': submission_data.get('submitted_at'),
                'webhook_received_at': datetime.utcnow().isoformat()
            }
        }

        # Store submission in MongoDB
        result = db_mongo.form_submissions.insert_one(submission_record)
        submission_id = str(result.inserted_id)

        logger.info(f"Stored submission {submission_id} for form_config {form_config_id}")

        return jsonify({
            "success": True,
            "data": {
                "submission_id": submission_id,
                "form_config_id": form_config_id,
                "status": "received"
            }
        }), 200

    except Exception as e:
        logger.error(f"Error receiving OpnForm submission: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@webhook_bp.route('/opnform/<form_config_id>/test', methods=['GET'])
def test_webhook(form_config_id):
    """
    Test webhook endpoint (for debugging)
    ---
    tags:
      - Webhooks
    parameters:
      - in: path
        name: form_config_id
        type: string
        required: true
        description: Form configuration ID
    responses:
      200:
        description: Webhook endpoint is active
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Webhook endpoint is active"
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
                is_active:
                  type: boolean
                  example: true
                telegram_group_chat_id:
                  type: string
                  example: "-1001234567890"
    """
    try:
        # Validate form_config_id
        try:
            config_obj_id = ObjectId(form_config_id)
        except Exception:
            return jsonify({"success": False, "error": "Invalid form_config_id format"}), 400

        # Check if form config exists
        db_mongo = mongodb.get_database()
        form_config = db_mongo.form_configurations.find_one({'_id': config_obj_id})

        if not form_config:
            return jsonify({"success": False, "error": "Form configuration not found"}), 404

        return jsonify({
            "success": True,
            "message": "Webhook endpoint is active",
            "data": {
                "form_config_id": form_config_id,
                "opnform_form_id": form_config.get('opnform_form_id'),
                "form_name": form_config.get('form_name'),
                "is_active": form_config.get('is_active'),
                "telegram_group_chat_id": form_config.get('telegram_group_chat_id')
            }
        }), 200

    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
