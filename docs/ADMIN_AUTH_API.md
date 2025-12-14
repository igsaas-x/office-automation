# Admin Portal Authentication API

This document describes the authentication API endpoints for the Admin Portal.

## Overview

The admin portal uses JWT (JSON Web Token) authentication with Telegram Login Widget integration.

**Authentication Flow:**
1. Admin user clicks "Login with Telegram" on the frontend (Vue.js)
2. Telegram Login Widget returns user data with HMAC signature
3. Frontend sends this data to `/api/auth/telegram-login`
4. Backend verifies the signature and checks admin whitelist
5. Backend returns JWT access token and refresh token
6. Frontend stores tokens and uses access token for subsequent requests
7. When access token expires, use refresh token to get a new one

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://rootUsername:rootPassword@localhost:27017/
MONGODB_DATABASE=office_automation_forms

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-use-random-string
JWT_ACCESS_TOKEN_EXPIRES=28800  # 8 hours in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days in seconds

# Admin Portal Configuration
ADMIN_TELEGRAM_IDS=123456789,987654321  # Comma-separated list of admin Telegram IDs
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## API Endpoints

### 1. Login with Telegram

Authenticate admin user using Telegram Login Widget data.

**Endpoint:** `POST /api/auth/telegram-login`

**Request Body:**
```json
{
  "id": 123456789,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "photo_url": "https://...",
  "auth_date": 1234567890,
  "hash": "abc123..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": "123456789",
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "photo_url": "https://...",
    "role": "admin"
  }
}
```

**Error Responses:**
- `400`: Request body is required
- `401`: Invalid Telegram authentication (signature verification failed)
- `403`: User is not in admin whitelist or account is inactive
- `500`: Internal server error

---

### 2. Refresh Access Token

Get a new access token using a refresh token.

**Endpoint:** `POST /api/auth/refresh`

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Success Response (200):**
```json
{
  "access_token": "eyJ..."
}
```

**Error Responses:**
- `401`: Invalid or expired refresh token, or user is inactive
- `500`: Internal server error

---

### 3. Get Current User

Get information about the currently authenticated admin user.

**Endpoint:** `GET /api/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "id": "123456789",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "photo_url": "https://...",
  "role": "admin",
  "status": "active",
  "last_login": "2024-12-13T10:30:00"
}
```

**Error Responses:**
- `401`: Missing or invalid access token, or token expired
- `403`: Admin user not found or inactive
- `500`: Internal server error

---

### 4. Logout

Logout the current user (client-side token deletion).

**Endpoint:** `POST /api/auth/logout`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

**Note:** Since we use stateless JWT, actual logout is handled client-side by deleting the tokens. This endpoint is here for consistency and logging purposes.

---

## Using Protected Endpoints

To access protected admin endpoints, include the access token in the Authorization header:

```javascript
// Example with fetch
const response = await fetch('http://localhost:5000/api/admin/some-endpoint', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

## Telegram Login Widget Integration

### Frontend Setup (Vue.js)

1. Include Telegram Login Widget script in your HTML:

```html
<script async src="https://telegram.org/js/telegram-widget.js?22"></script>
```

2. Add the login button:

```html
<div id="telegram-login-button"></div>
```

3. Initialize the widget:

```javascript
window.onTelegramAuth = async (user) => {
  // user contains: id, first_name, last_name, username, photo_url, auth_date, hash

  try {
    const response = await fetch('http://localhost:5000/api/auth/telegram-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(user)
    });

    const data = await response.json();

    if (response.ok) {
      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Redirect to dashboard
      window.location.href = '/dashboard';
    } else {
      alert('Login failed: ' + data.error);
    }
  } catch (error) {
    console.error('Login error:', error);
    alert('An error occurred during login');
  }
};

// Create the widget
const script = document.createElement('script');
script.src = 'https://telegram.org/js/telegram-widget.js?22';
script.setAttribute('data-telegram-login', 'YOUR_BOT_USERNAME');
script.setAttribute('data-size', 'large');
script.setAttribute('data-onauth', 'onTelegramAuth(user)');
script.setAttribute('data-request-access', 'write');
script.async = true;

document.getElementById('telegram-login-button').appendChild(script);
```

### Token Refresh Logic

```javascript
// Intercept API calls to refresh token if needed
async function apiCall(endpoint, options = {}) {
  let accessToken = localStorage.getItem('access_token');

  // Try the request
  let response = await fetch(endpoint, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`
    }
  });

  // If token expired, refresh it
  if (response.status === 401) {
    const data = await response.json();
    if (data.code === 'TOKEN_EXPIRED') {
      const refreshToken = localStorage.getItem('refresh_token');

      // Refresh the access token
      const refreshResponse = await fetch('http://localhost:5000/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });

      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json();
        localStorage.setItem('access_token', refreshData.access_token);

        // Retry the original request
        return apiCall(endpoint, options);
      } else {
        // Refresh failed, redirect to login
        localStorage.clear();
        window.location.href = '/login';
        return;
      }
    }
  }

  return response;
}
```

## Database Collections

### admin_users Collection

Stores admin user information in MongoDB:

```javascript
{
  telegram_id: "123456789",      // Unique Telegram user ID
  first_name: "John",
  last_name: "Doe",
  username: "johndoe",
  photo_url: "https://...",
  role: "admin",
  status: "active",              // "active" or "inactive"
  created_at: ISODate("2024-12-13T10:00:00Z"),
  updated_at: ISODate("2024-12-13T10:00:00Z"),
  last_login: ISODate("2024-12-13T10:30:00Z")
}
```

**Indexes:**
- `telegram_id`: Unique index
- `username`: Non-unique index

## Security Considerations

1. **HMAC Verification**: All Telegram Login Widget data is verified using HMAC-SHA256 with the bot token
2. **Admin Whitelist**: Only Telegram IDs in `ADMIN_TELEGRAM_IDS` can authenticate
3. **Token Expiration**: Access tokens expire after 8 hours, refresh tokens after 30 days
4. **CORS**: Only origins in `CORS_ALLOWED_ORIGINS` can access the API
5. **Status Check**: User status is checked on every request - inactive users are denied
6. **HTTPS**: In production, always use HTTPS for the API

## Testing

Run the test script to verify the authentication system:

```bash
python test_auth.py
```

This will verify:
- MongoDB connection
- All authentication endpoints
- JWT middleware
- Error handling

## Starting the API Server

To start the Flask API server:

```bash
python main.py
```

The API will be available at `http://localhost:5000` (default port).

## Next Steps

1. Set up your admin Telegram ID in `.env` (`ADMIN_TELEGRAM_IDS`)
2. Create a Telegram bot for the Login Widget (use @BotFather)
3. Build the Vue.js admin portal with Telegram Login Widget
4. Connect the Vue.js frontend to these API endpoints
5. In production, change `JWT_SECRET_KEY` to a strong random string
6. Enable HTTPS in production
