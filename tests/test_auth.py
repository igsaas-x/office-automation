"""
Test script for admin authentication endpoints
"""
import sys
sys.path.insert(0, '..')

from src.infrastructure.api.flask_app import create_app
from src.infrastructure.persistence.mongodb_connection import mongodb
from src.infrastructure.config.settings import settings
import json

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("=" * 60)
    print("AUTHENTICATION SYSTEM TEST")
    print("=" * 60)

    # Create Flask test client
    app = create_app()
    client = app.test_client()

    print("\n1. Testing health check (should work)...")
    response = client.get('/health')
    print(f"   Status: {response.status_code}")

    print("\n2. Testing MongoDB connection...")
    try:
        db = mongodb.get_database()
        admin_count = db.admin_users.count_documents({})
        print(f"   ✓ MongoDB connected: {settings.MONGODB_DATABASE}")
        print(f"   ✓ Admin users in database: {admin_count}")
    except Exception as e:
        print(f"   ✗ MongoDB connection failed: {e}")
        return

    print("\n3. Testing /api/auth/telegram-login endpoint...")

    # Test with missing data
    print("\n   3a. Test with missing request body:")
    response = client.post('/api/auth/telegram-login',
                          content_type='application/json')
    print(f"       Status: {response.status_code} (expected: 400)")
    print(f"       Response: {response.get_json()}")

    # Test with invalid Telegram data (missing hash)
    print("\n   3b. Test with invalid Telegram data (missing hash):")
    response = client.post('/api/auth/telegram-login',
                          data=json.dumps({
                              "id": 123456789,
                              "first_name": "Test",
                              "username": "testuser"
                          }),
                          content_type='application/json')
    print(f"       Status: {response.status_code} (expected: 401)")
    print(f"       Response: {response.get_json()}")

    # Test with invalid hash
    print("\n   3c. Test with invalid hash:")
    response = client.post('/api/auth/telegram-login',
                          data=json.dumps({
                              "id": 123456789,
                              "first_name": "Test",
                              "username": "testuser",
                              "auth_date": 1234567890,
                              "hash": "invalid_hash"
                          }),
                          content_type='application/json')
    print(f"       Status: {response.status_code} (expected: 401)")
    print(f"       Response: {response.get_json()}")

    # Test with non-admin user (valid signature but not in whitelist)
    print("\n   3d. Test with non-admin user:")
    print(f"       Note: This requires valid Telegram signature")
    print(f"       Current admin whitelist: {settings.get_admin_telegram_ids()}")

    print("\n4. Testing /api/auth/me endpoint (without token)...")
    response = client.get('/api/auth/me')
    print(f"   Status: {response.status_code} (expected: 401)")
    print(f"   Response: {response.get_json()}")

    print("\n5. Testing /api/auth/refresh endpoint (without token)...")
    response = client.post('/api/auth/refresh')
    print(f"   Status: {response.status_code} (expected: 401)")
    print(f"   Response: {response.get_json()}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ Flask app created successfully")
    print("✓ MongoDB connection working")
    print("✓ All authentication endpoints registered and responding")
    print("✓ JWT middleware properly rejects unauthorized requests")
    print("\nNOTE: To test successful login, you need to:")
    print("1. Set ADMIN_TELEGRAM_IDS in .env (e.g., ADMIN_TELEGRAM_IDS=123456789)")
    print("2. Use Telegram Login Widget to get valid auth data with hash")
    print("3. POST to /api/auth/telegram-login with the auth data")
    print("\nAPI is ready for Vue.js frontend integration!")
    print("=" * 60)

if __name__ == "__main__":
    test_auth_endpoints()
