import hmac
import hashlib
import time
import logging
from functools import lru_cache
from typing import Optional, Dict, Any, Tuple
from urllib.parse import parse_qs, unquote
from flask import request, jsonify, g
from ...config.settings import settings
from ...persistence.database import database
from ...persistence.employee_repository_impl import EmployeeRepository
from ...persistence.group_repository_impl import GroupRepository

logger = logging.getLogger(__name__)


def get_exempt_paths():
    """Get list of exempt paths from settings"""
    base_paths = ['/health', '/api-docs', '/apispec.json', '/flasgger_static']
    if hasattr(settings, 'TELEGRAM_AUTH_EXEMPT_PATHS'):
        custom_paths = [p.strip() for p in settings.TELEGRAM_AUTH_EXEMPT_PATHS.split(',')]
        base_paths.extend(custom_paths)
    return base_paths

# Simple in-memory cache for user lookups (will be replaced with Redis in Phase 2)
_user_cache = {}
_cache_timestamps = {}

# Simple rate limiter (will be enhanced in Phase 3)
_rate_limit_tracker = {}


class TelegramAuthError(Exception):
    """Base exception for Telegram authentication errors"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def parse_init_data(init_data: str) -> Dict[str, Any]:
    """
    Parse Telegram initData query string into a dictionary

    Args:
        init_data: URL-encoded query string from Telegram Web App

    Returns:
        Dictionary with parsed values
    """
    try:
        # Parse query string
        parsed = parse_qs(init_data)

        # Convert to simple dict (parse_qs returns lists)
        result = {}
        for key, value in parsed.items():
            result[key] = value[0] if len(value) == 1 else value

        # Parse user JSON if present
        if 'user' in result:
            import json
            result['user'] = json.loads(unquote(result['user']))

        return result
    except Exception as e:
        logger.error(f"Failed to parse initData: {e}")
        raise TelegramAuthError("Invalid initData format", 401)


def verify_telegram_signature(init_data: str, bot_token: str) -> bool:
    """
    Verify HMAC-SHA256 signature of Telegram Web App initData

    Algorithm:
    1. Parse initData and extract hash
    2. Sort remaining parameters alphabetically
    3. Create data-check-string (key=value\\n format)
    4. Compute secret_key = HMAC-SHA256(bot_token, "WebAppData")
    5. Compute hash = HMAC-SHA256(secret_key, data-check-string)
    6. Compare with provided hash (constant-time comparison)

    Args:
        init_data: The initData string from Telegram
        bot_token: Bot token for signature verification

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Parse the query string
        parsed = parse_qs(init_data)

        # Extract hash
        if 'hash' not in parsed:
            logger.warning("No hash found in initData")
            return False

        received_hash = parsed['hash'][0]

        # Remove hash from data and sort remaining parameters
        data_check_dict = {k: v[0] for k, v in parsed.items() if k != 'hash'}
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data_check_dict.items()))

        # Compute secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()

        # Compute hash
        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hash, received_hash)

    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


def check_timestamp_freshness(auth_date: str, max_age: int) -> bool:
    """
    Check if the authentication timestamp is within acceptable range

    Args:
        auth_date: Unix timestamp as string
        max_age: Maximum age in seconds

    Returns:
        True if timestamp is fresh, False otherwise
    """
    try:
        auth_timestamp = int(auth_date)
        current_timestamp = int(time.time())
        age = current_timestamp - auth_timestamp

        if age > max_age:
            logger.warning(f"InitData expired: age={age}s, max_age={max_age}s")
            return False

        if age < -60:  # Allow 1 minute clock skew into future
            logger.warning(f"InitData timestamp in future: age={age}s")
            return False

        return True
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid auth_date format: {e}")
        return False


@lru_cache(maxsize=1000)
def get_employee_by_telegram_id_cached(telegram_id: str, cache_time: int):
    """
    Get employee from database with LRU cache

    Args:
        telegram_id: Telegram user ID
        cache_time: Current time rounded to cache TTL for cache invalidation

    Returns:
        Employee object or None
    """
    session = database.get_session()
    try:
        employee_repo = EmployeeRepository(session)
        employee = employee_repo.find_by_telegram_id(telegram_id)
        return employee
    finally:
        session.close()


@lru_cache(maxsize=500)
def get_group_by_chat_id_cached(chat_id: str, cache_time: int):
    """
    Get group from database with LRU cache

    Args:
        chat_id: Telegram chat ID
        cache_time: Current time rounded to cache TTL for cache invalidation

    Returns:
        Group object or None
    """
    session = database.get_session()
    try:
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(chat_id)
        return group
    finally:
        session.close()


def check_rate_limit(telegram_id: str) -> Tuple[bool, int]:
    """
    Simple rate limiter based on user ID

    Args:
        telegram_id: Telegram user ID

    Returns:
        Tuple of (is_allowed, retry_after_seconds)
    """
    current_time = int(time.time())
    rate_limit_window = settings.TELEGRAM_RATE_LIMIT_WINDOW
    window_start = current_time - rate_limit_window

    if telegram_id not in _rate_limit_tracker:
        _rate_limit_tracker[telegram_id] = []

    # Clean old requests outside the window
    _rate_limit_tracker[telegram_id] = [
        req_time for req_time in _rate_limit_tracker[telegram_id]
        if req_time > window_start
    ]

    # Check if limit exceeded
    request_count = len(_rate_limit_tracker[telegram_id])
    if request_count >= settings.TELEGRAM_RATE_LIMIT_PER_USER:
        oldest_request = min(_rate_limit_tracker[telegram_id])
        retry_after = rate_limit_window - (current_time - oldest_request)
        return False, max(1, retry_after)

    # Add current request
    _rate_limit_tracker[telegram_id].append(current_time)
    return True, 0


def validate_telegram_auth():
    """
    Flask before_request middleware to validate Telegram authentication

    This middleware:
    1. Checks if path is exempt from authentication
    2. Extracts and validates initData signature
    3. Checks timestamp freshness
    4. Verifies user exists in database
    5. Optionally validates group membership
    6. Enforces rate limiting
    7. Enriches request context with user data

    Returns:
        None if validation passes (request continues)
        Flask JSON response with error if validation fails
    """
    # Skip if authentication is disabled
    if not settings.TELEGRAM_AUTH_ENABLED:
        return None

    # Check if path is exempt
    exempt_paths = get_exempt_paths()
    if any(request.path.startswith(path) for path in exempt_paths):
        return None

    # Also exempt non-API paths
    if not request.path.startswith('/api/'):
        return None

    try:
        # Extract initData from request (try header first, then body)
        init_data = None

        # Try custom header
        if 'X-Telegram-Init-Data' in request.headers:
            init_data = request.headers.get('X-Telegram-Init-Data')
        # Try body (for POST/PUT requests)
        elif request.is_json and request.json:
            init_data = request.json.get('initData')
        # Try form data
        elif request.form:
            init_data = request.form.get('initData')

        if not init_data:
            logger.warning(f"Missing initData for {request.path} from {request.remote_addr}")
            if settings.TELEGRAM_AUTH_STRICT_MODE:
                return jsonify({"error": "Missing Telegram authentication"}), 401
            else:
                logger.info("Allowing request in non-strict mode")
                return None

        # Validate HMAC signature
        if not verify_telegram_signature(init_data, settings.CHECKIN_BOT_TOKEN):
            logger.warning(f"Invalid signature for {request.path} from {request.remote_addr}")
            if settings.TELEGRAM_AUTH_STRICT_MODE:
                return jsonify({"error": "Invalid Telegram authentication"}), 401
            else:
                logger.info("Allowing request in non-strict mode")
                return None

        # Parse initData
        parsed_data = parse_init_data(init_data)

        # Check timestamp freshness
        if 'auth_date' in parsed_data:
            if not check_timestamp_freshness(parsed_data['auth_date'], settings.TELEGRAM_INITDATA_MAX_AGE):
                logger.warning(f"Expired initData for {request.path}")
                if settings.TELEGRAM_AUTH_STRICT_MODE:
                    return jsonify({"error": "Authentication expired, please refresh"}), 401
                else:
                    logger.info("Allowing request in non-strict mode")
                    return None

        # Extract user ID
        if 'user' not in parsed_data or 'id' not in parsed_data['user']:
            logger.error("Missing user.id in initData")
            return jsonify({"error": "Invalid authentication data"}), 401

        telegram_user_id = str(parsed_data['user']['id'])

        # Check rate limit
        is_allowed, retry_after = check_rate_limit(telegram_user_id)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {telegram_user_id}")
            return jsonify({
                "error": "Rate limit exceeded",
                "retry_after": retry_after
            }), 429

        # Get current time rounded to cache TTL for cache invalidation
        cache_time = int(time.time() // settings.TELEGRAM_AUTH_CACHE_TTL)

        # Check if user exists in database
        employee = get_employee_by_telegram_id_cached(telegram_user_id, cache_time)

        if not employee:
            logger.warning(f"Unregistered user attempt: {telegram_user_id} for {request.path}")
            if settings.TELEGRAM_AUTH_STRICT_MODE:
                return jsonify({"error": "User not registered as employee"}), 403
            else:
                logger.info("Allowing request in non-strict mode")
                return None

        # Validate group if group_chat_id is provided in request
        group_chat_id = None
        if request.is_json and request.json:
            group_chat_id = request.json.get('group_chat_id')
        elif request.form:
            group_chat_id = request.form.get('group_chat_id')

        if group_chat_id:
            group = get_group_by_chat_id_cached(group_chat_id, cache_time)
            if not group:
                logger.warning(f"Invalid group_chat_id: {group_chat_id}")
                return jsonify({"error": "Group not found"}), 404
            g.current_group = group

        # Attach validated data to Flask request context
        g.current_user = employee
        g.telegram_data = parsed_data
        g.telegram_user_id = telegram_user_id

        logger.info(f"Authenticated user {employee.name} ({telegram_user_id}) for {request.path}")

        # Allow request to proceed
        return None

    except TelegramAuthError as e:
        logger.error(f"TelegramAuthError: {e.message}")
        return jsonify({"error": e.message}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in telegram auth middleware: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
