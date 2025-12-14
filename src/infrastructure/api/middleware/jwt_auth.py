"""
JWT authentication middleware for admin portal

This module provides JWT-based authentication for the admin portal,
separate from the Telegram authentication used by the miniapp.
"""

import logging
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from ...config.settings import settings
from ...persistence.mongodb_connection import mongodb

logger = logging.getLogger(__name__)


def get_jwt_exempt_paths():
    """
    Get list of paths exempt from JWT authentication

    Returns:
        list: List of path prefixes that don't require JWT auth
    """
    # Paths that don't require JWT authentication
    return [
        '/health',
        '/api-docs',
        '/apispec.json',
        '/flasgger_static',
        '/api/auth/login',  # Login endpoint itself
        '/api/auth/telegram-login',  # Telegram login for admin
        '/webhook/',  # OpnForm webhooks (use HMAC signature instead)
    ]


def jwt_required_admin(fn):
    """
    Decorator to require JWT authentication for admin endpoints

    This decorator:
    1. Verifies JWT token is present and valid
    2. Checks if user is an admin
    3. Loads admin user data into request context
    4. Returns 401 if authentication fails

    Usage:
        @app.route('/api/admin/dashboard')
        @jwt_required_admin
        def admin_dashboard():
            admin_user = g.current_admin
            return jsonify(...)

    Args:
        fn: The route function to protect

    Returns:
        Decorated function with JWT authentication
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Verify JWT token in request
            verify_jwt_in_request()

            # Get user identity from JWT
            current_user_id = get_jwt_identity()

            if not current_user_id:
                logger.warning("JWT token missing identity")
                return jsonify({"error": "Invalid authentication token"}), 401

            # Get JWT claims
            jwt_data = get_jwt()

            # Get admin user from MongoDB
            db = mongodb.get_database()
            admin_user = db.admin_users.find_one({"telegram_id": current_user_id})

            if not admin_user:
                logger.warning(f"Admin user not found: {current_user_id}")
                return jsonify({"error": "Admin user not found"}), 403

            # Check if user is active
            if admin_user.get('status') != 'active':
                logger.warning(f"Inactive admin user attempted access: {current_user_id}")
                return jsonify({"error": "Admin account is inactive"}), 403

            # Attach admin data to request context
            g.current_admin = admin_user
            g.jwt_data = jwt_data
            g.admin_telegram_id = current_user_id

            logger.info(f"Admin authenticated: {admin_user.get('username', current_user_id)}")

            # Call the actual route function
            return fn(*args, **kwargs)

        except ExpiredSignatureError:
            logger.warning("Expired JWT token")
            return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401

        except (NoAuthorizationError, InvalidHeaderError):
            logger.warning("Missing or invalid JWT token")
            return jsonify({"error": "Missing or invalid authentication token"}), 401

        except InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            return jsonify({"error": "Invalid authentication token"}), 401

        except Exception as e:
            logger.error(f"Unexpected error in JWT auth: {e}", exc_info=True)
            return jsonify({"error": "Authentication error"}), 500

    return wrapper


def optional_jwt_auth(fn):
    """
    Decorator to optionally load JWT authentication

    Similar to jwt_required_admin but doesn't fail if no token present.
    Useful for endpoints that work for both authenticated and unauthenticated users.

    Args:
        fn: The route function

    Returns:
        Decorated function with optional JWT authentication
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)

            current_user_id = get_jwt_identity()

            if current_user_id:
                db = mongodb.get_database()
                admin_user = db.admin_users.find_one({"telegram_id": current_user_id})

                if admin_user and admin_user.get('status') == 'active':
                    g.current_admin = admin_user
                    g.admin_telegram_id = current_user_id

        except Exception as e:
            logger.debug(f"Optional JWT auth failed (not critical): {e}")
            # Don't fail, just continue without authentication

        return fn(*args, **kwargs)

    return wrapper
