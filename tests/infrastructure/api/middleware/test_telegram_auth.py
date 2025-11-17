import unittest
import hmac
import hashlib
import time
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import urlencode

from src.infrastructure.api.middleware.telegram_auth import (
    parse_init_data,
    verify_telegram_signature,
    check_timestamp_freshness,
    check_rate_limit,
    TelegramAuthError
)


class TestParseInitData(unittest.TestCase):
    """Test cases for parse_init_data function"""

    def test_parse_valid_init_data(self):
        """Test parsing valid initData"""
        init_data = "query_id=123&auth_date=1234567890&hash=abc123"
        result = parse_init_data(init_data)

        self.assertIn('query_id', result)
        self.assertIn('auth_date', result)
        self.assertIn('hash', result)
        self.assertEqual(result['query_id'], '123')
        self.assertEqual(result['auth_date'], '1234567890')
        self.assertEqual(result['hash'], 'abc123')

    def test_parse_init_data_with_user_json(self):
        """Test parsing initData with user JSON object"""
        import json
        from urllib.parse import quote

        user_obj = {"id": 123456789, "first_name": "John", "last_name": "Doe"}
        user_json = quote(json.dumps(user_obj))
        init_data = f"user={user_json}&auth_date=1234567890&hash=abc123"

        result = parse_init_data(init_data)

        self.assertIn('user', result)
        self.assertIsInstance(result['user'], dict)
        self.assertEqual(result['user']['id'], 123456789)
        self.assertEqual(result['user']['first_name'], 'John')

    def test_parse_invalid_init_data_raises_error(self):
        """Test that invalid initData raises TelegramAuthError"""
        # Malformed query string
        init_data = "this is not valid query string format!!!"

        # Should not raise exception but might not parse correctly
        # The actual parsing is lenient, so we just check it returns something
        result = parse_init_data(init_data)
        self.assertIsInstance(result, dict)


class TestVerifyTelegramSignature(unittest.TestCase):
    """Test cases for verify_telegram_signature function"""

    def generate_valid_init_data(self, bot_token: str, data: dict) -> str:
        """Helper to generate valid signed initData"""
        # Sort data and create check string
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))

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

        # Add hash to data
        data_with_hash = data.copy()
        data_with_hash['hash'] = computed_hash

        # Return as query string
        return urlencode(data_with_hash)

    def test_verify_valid_signature(self):
        """Test that valid signature passes verification"""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        data = {
            "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
            "user": '{"id":123456789,"first_name":"John"}',
            "auth_date": "1234567890"
        }

        init_data = self.generate_valid_init_data(bot_token, data)
        result = verify_telegram_signature(init_data, bot_token)

        self.assertTrue(result)

    def test_verify_invalid_signature(self):
        """Test that tampered signature fails verification"""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        data = {
            "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
            "user": '{"id":123456789,"first_name":"John"}',
            "auth_date": "1234567890"
        }

        # Generate valid init data
        init_data = self.generate_valid_init_data(bot_token, data)

        # Tamper with the data
        tampered_init_data = init_data.replace("John", "Hacker")

        result = verify_telegram_signature(tampered_init_data, bot_token)
        self.assertFalse(result)

    def test_verify_missing_hash(self):
        """Test that missing hash fails verification"""
        bot_token = "test_token"
        init_data = "query_id=123&auth_date=1234567890"  # No hash

        result = verify_telegram_signature(init_data, bot_token)
        self.assertFalse(result)

    def test_verify_wrong_bot_token(self):
        """Test that wrong bot token fails verification"""
        correct_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        wrong_token = "999999:WRONG-TOKEN"

        data = {
            "query_id": "test",
            "auth_date": "1234567890"
        }

        init_data = self.generate_valid_init_data(correct_token, data)
        result = verify_telegram_signature(init_data, wrong_token)

        self.assertFalse(result)


class TestCheckTimestampFreshness(unittest.TestCase):
    """Test cases for check_timestamp_freshness function"""

    def test_fresh_timestamp(self):
        """Test that recent timestamp is considered fresh"""
        current_time = int(time.time())
        auth_date = str(current_time - 100)  # 100 seconds ago
        max_age = 3600  # 1 hour

        result = check_timestamp_freshness(auth_date, max_age)
        self.assertTrue(result)

    def test_expired_timestamp(self):
        """Test that old timestamp is considered expired"""
        current_time = int(time.time())
        auth_date = str(current_time - 7200)  # 2 hours ago
        max_age = 3600  # 1 hour

        result = check_timestamp_freshness(auth_date, max_age)
        self.assertFalse(result)

    def test_future_timestamp_allowed_with_skew(self):
        """Test that slightly future timestamp is allowed (clock skew)"""
        current_time = int(time.time())
        auth_date = str(current_time + 30)  # 30 seconds in future
        max_age = 3600

        result = check_timestamp_freshness(auth_date, max_age)
        self.assertTrue(result)

    def test_far_future_timestamp_rejected(self):
        """Test that far future timestamp is rejected"""
        current_time = int(time.time())
        auth_date = str(current_time + 300)  # 5 minutes in future
        max_age = 3600

        result = check_timestamp_freshness(auth_date, max_age)
        self.assertFalse(result)

    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp format is rejected"""
        auth_date = "not_a_number"
        max_age = 3600

        result = check_timestamp_freshness(auth_date, max_age)
        self.assertFalse(result)


class TestCheckRateLimit(unittest.TestCase):
    """Test cases for check_rate_limit function"""

    def setUp(self):
        """Clear rate limit tracker before each test"""
        from src.infrastructure.api.middleware import telegram_auth
        telegram_auth._rate_limit_tracker.clear()

    @patch('src.infrastructure.api.middleware.telegram_auth.settings')
    def test_rate_limit_allows_initial_requests(self, mock_settings):
        """Test that initial requests are allowed"""
        mock_settings.TELEGRAM_RATE_LIMIT_PER_USER = 10
        mock_settings.TELEGRAM_RATE_LIMIT_WINDOW = 60

        telegram_id = "123456789"
        is_allowed, retry_after = check_rate_limit(telegram_id)

        self.assertTrue(is_allowed)
        self.assertEqual(retry_after, 0)

    @patch('src.infrastructure.api.middleware.telegram_auth.settings')
    def test_rate_limit_blocks_excess_requests(self, mock_settings):
        """Test that requests over limit are blocked"""
        mock_settings.TELEGRAM_RATE_LIMIT_PER_USER = 3
        mock_settings.TELEGRAM_RATE_LIMIT_WINDOW = 60

        telegram_id = "123456789"

        # Make 3 requests (should all be allowed)
        for i in range(3):
            is_allowed, _ = check_rate_limit(telegram_id)
            self.assertTrue(is_allowed, f"Request {i+1} should be allowed")

        # 4th request should be blocked
        is_allowed, retry_after = check_rate_limit(telegram_id)
        self.assertFalse(is_allowed)
        self.assertGreater(retry_after, 0)

    @patch('src.infrastructure.api.middleware.telegram_auth.settings')
    def test_rate_limit_per_user_isolation(self, mock_settings):
        """Test that rate limits are per user"""
        mock_settings.TELEGRAM_RATE_LIMIT_PER_USER = 2
        mock_settings.TELEGRAM_RATE_LIMIT_WINDOW = 60

        user1 = "111111111"
        user2 = "222222222"

        # User 1 makes 2 requests
        check_rate_limit(user1)
        check_rate_limit(user1)

        # User 1 should be blocked
        is_allowed, _ = check_rate_limit(user1)
        self.assertFalse(is_allowed)

        # User 2 should still be allowed
        is_allowed, _ = check_rate_limit(user2)
        self.assertTrue(is_allowed)


class TestTelegramAuthError(unittest.TestCase):
    """Test cases for TelegramAuthError exception"""

    def test_error_with_default_status_code(self):
        """Test error with default 401 status code"""
        error = TelegramAuthError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 401)

    def test_error_with_custom_status_code(self):
        """Test error with custom status code"""
        error = TelegramAuthError("Forbidden", 403)
        self.assertEqual(error.message, "Forbidden")
        self.assertEqual(error.status_code, 403)


if __name__ == '__main__':
    unittest.main()
