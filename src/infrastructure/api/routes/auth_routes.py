"""
Authentication routes for admin portal

Provides endpoints for:
- Telegram Login Widget authentication
- JWT token generation and refresh
- Admin user management
"""

import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from ...config.settings import settings
from ...persistence.mongodb_connection import mongodb
from ..middleware.jwt_auth import jwt_required_admin

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def verify_telegram_login_widget(auth_data: dict, bot_token: str) -> bool:
    """
    Verify Telegram Login Widget authentication data

    https://core.telegram.org/widgets/login#checking-authorization

    Args:
        auth_data: Dictionary with Telegram auth data (id, first_name, last_name, username, photo_url, auth_date, hash)
        bot_token: Bot token for signature verification

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        check_hash = auth_data.get('hash')
        if not check_hash:
            logger.warning("No hash in Telegram auth data")
            return False

        # Create data-check-string from auth_data (excluding hash)
        data_check_arr = []
        for key in sorted(auth_data.keys()):
            if key != 'hash':
                data_check_arr.append(f"{key}={auth_data[key]}")

        data_check_string = '\n'.join(data_check_arr)

        # Compute secret key (SHA256 of bot token)
        secret_key = hashlib.sha256(bot_token.encode()).digest()

        # Compute HMAC-SHA256
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(computed_hash, check_hash)

    except Exception as e:
        logger.error(f"Error verifying Telegram login widget: {e}")
        return False


@auth_bp.route('/telegram-login', methods=['POST'])
def telegram_login():
    """
    Authenticate admin via Telegram Login Widget

    Endpoint: POST /api/auth/telegram-login

    Request body:
    {
        "id": 123456789,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "photo_url": "https://...",
        "auth_date": 1234567890,
        "hash": "abc123..."
    }

    Response:
    {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "user": {
            "id": "123456789",
            "first_name": "John",
            "username": "johndoe",
            "role": "admin"
        }
    }

    Returns:
        200: Login successful with JWT tokens
        401: Invalid Telegram authentication
        403: User is not an admin
    """
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Verify Telegram authentication
        bot_token = settings.CHECKIN_BOT_TOKEN
        if not verify_telegram_login_widget(data, bot_token):
            logger.warning(f"Invalid Telegram login attempt from {request.remote_addr}")
            return jsonify({"error": "Invalid Telegram authentication"}), 401

        # Extract user ID
        user_id = str(data.get('id'))
        if not user_id:
            return jsonify({"error": "Missing user ID"}), 400

        # Check if user is in admin whitelist
        admin_telegram_ids = settings.get_admin_telegram_ids()
        if not admin_telegram_ids or user_id not in admin_telegram_ids:
            logger.warning(f"Unauthorized login attempt from Telegram ID: {user_id}")
            return jsonify({
                "error": "Unauthorized. Admin access only.",
                "code": "NOT_ADMIN"
            }), 403

        # Get or create admin user in MongoDB
        db = mongodb.get_database()

        admin_user = db.admin_users.find_one({"telegram_id": user_id})

        if not admin_user:
            # Create new admin user
            logger.info(f"Creating new admin user: {user_id}")

            admin_user = {
                "telegram_id": user_id,
                "first_name": data.get('first_name'),
                "last_name": data.get('last_name'),
                "username": data.get('username'),
                "photo_url": data.get('photo_url'),
                "role": "admin",
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }

            db.admin_users.insert_one(admin_user)
        else:
            # Update existing admin user
            logger.info(f"Updating admin user: {user_id}")

            db.admin_users.update_one(
                {"telegram_id": user_id},
                {
                    "$set": {
                        "first_name": data.get('first_name'),
                        "last_name": data.get('last_name'),
                        "username": data.get('username'),
                        "photo_url": data.get('photo_url'),
                        "updated_at": datetime.utcnow(),
                        "last_login": datetime.utcnow()
                    }
                }
            )

        # Check if user is active
        if admin_user.get('status') != 'active':
            logger.warning(f"Inactive admin user login attempt: {user_id}")
            return jsonify({
                "error": "Your admin account is inactive. Contact system administrator.",
                "code": "INACTIVE_ACCOUNT"
            }), 403

        # Create JWT tokens
        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                "first_name": data.get('first_name'),
                "username": data.get('username'),
                "role": "admin"
            },
            expires_delta=timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRES)
        )

        refresh_token = create_refresh_token(
            identity=user_id,
            expires_delta=timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXPIRES)
        )

        logger.info(f"Admin login successful: {admin_user.get('username', user_id)}")

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user_id,
                "first_name": admin_user.get('first_name'),
                "last_name": admin_user.get('last_name'),
                "username": admin_user.get('username'),
                "photo_url": admin_user.get('photo_url'),
                "role": admin_user.get('role', 'admin')
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in telegram login: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token

    Endpoint: POST /api/auth/refresh

    Headers:
        Authorization: Bearer <refresh_token>

    Response:
    {
        "access_token": "eyJ..."
    }

    Returns:
        200: New access token generated
        401: Invalid or expired refresh token
    """
    try:
        identity = get_jwt_identity()

        # Verify user still exists and is active
        db = mongodb.get_database()
        admin_user = db.admin_users.find_one({"telegram_id": identity})

        if not admin_user or admin_user.get('status') != 'active':
            return jsonify({"error": "Invalid or inactive user"}), 401

        # Create new access token
        new_access_token = create_access_token(
            identity=identity,
            additional_claims={
                "first_name": admin_user.get('first_name'),
                "username": admin_user.get('username'),
                "role": admin_user.get('role', 'admin')
            },
            expires_delta=timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRES)
        )

        return jsonify({"access_token": new_access_token}), 200

    except Exception as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required_admin
def get_current_user():
    """
    Get current authenticated admin user

    Endpoint: GET /api/auth/me

    Headers:
        Authorization: Bearer <access_token>

    Response:
    {
        "id": "123456789",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "photo_url": "https://...",
        "role": "admin",
        "status": "active"
    }

    Returns:
        200: User information
        401: Invalid or expired token
    """
    from flask import g

    admin_user = g.current_admin

    return jsonify({
        "id": admin_user.get('telegram_id'),
        "first_name": admin_user.get('first_name'),
        "last_name": admin_user.get('last_name'),
        "username": admin_user.get('username'),
        "photo_url": admin_user.get('photo_url'),
        "role": admin_user.get('role', 'admin'),
        "status": admin_user.get('status', 'active'),
        "last_login": admin_user.get('last_login').isoformat() if admin_user.get('last_login') else None
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required_admin
def logout():
    """
    Logout current user

    Note: Since we're using stateless JWT, actual logout is handled client-side
    by deleting the tokens. This endpoint is here for consistency and can be
    extended to blacklist tokens if needed in the future.

    Endpoint: POST /api/auth/logout

    Headers:
        Authorization: Bearer <access_token>

    Response:
    {
        "message": "Logged out successfully"
    }

    Returns:
        200: Logout successful
    """
    from flask import g

    logger.info(f"Admin logout: {g.current_admin.get('username', g.admin_telegram_id)}")

    return jsonify({
        "message": "Logged out successfully"
    }), 200
