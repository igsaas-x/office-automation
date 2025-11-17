# Office Automation API Documentation

## Overview
This Flask API provides endpoints for the Office Automation Mini App, allowing users to check in with location and photo data.

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Check-in
Record a check-in with location and optional photo.

**Endpoint:** `POST /api/checkin`

**Content-Type:** `multipart/form-data`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| telegram_user_id | string | Yes | Telegram user ID |
| group_chat_id | string | Yes | Telegram group chat ID |
| latitude | float | Yes | Location latitude |
| longitude | float | Yes | Location longitude |
| group_name | string | No | Group name (defaults to "Group {chat_id}") |
| photo | file | No | Photo file (PNG, JPG, JPEG, GIF, WEBP) |

**Response (Success):**
```json
{
  "success": true,
  "message": "Check-in recorded successfully",
  "data": {
    "employee_name": "John Doe",
    "group_name": "Development Team",
    "timestamp": "2025-10-12 14:30:00",
    "location": "13.7563, 100.5018",
    "photo_url": "/uploads/photos/12345_20251012_143000_photo.jpg"
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error message here"
}
```

**Status Codes:**
- `200 OK`: Check-in recorded successfully
- `400 Bad Request`: Missing or invalid parameters
- `404 Not Found`: Employee not registered
- `500 Internal Server Error`: Server error

**Example cURL Request:**
```bash
curl -X POST http://localhost:5000/api/checkin \
  -F "telegram_user_id=123456789" \
  -F "group_chat_id=-1001234567890" \
  -F "latitude=13.7563" \
  -F "longitude=100.5018" \
  -F "group_name=Development Team" \
  -F "photo=@/path/to/photo.jpg"
```

### 2. Health Check
Check if the API is running.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "success": true,
  "message": "API is running"
}
```

## Running the API

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Database Migrations
```bash
alembic upgrade head
```

### Start the API Server
```bash
python run_api.py
```

### Configuration
Set the following environment variables in your `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=username
DB_PASSWORD=password
DB_NAME=office_automation
```

## File Upload

### Supported Formats
- PNG
- JPG/JPEG
- GIF
- WEBP

### File Size Limit
Maximum file size: **16 MB**

### Storage
Photos are stored in the `uploads/photos/` directory with the following naming convention:
```
{telegram_user_id}_{timestamp}_{original_filename}
```

Example: `123456789_20251012_143000_photo.jpg`

## Error Handling

All errors return a JSON response with the following format:
```json
{
  "success": false,
  "error": "Error description"
}
```

### Common Error Scenarios

1. **Missing Required Fields**
   - Status: 400
   - Error: "Missing required fields: telegram_user_id, group_chat_id, latitude, longitude"

2. **Invalid Coordinate Format**
   - Status: 400
   - Error: "Invalid latitude or longitude format"

3. **Employee Not Registered**
   - Status: 404
   - Error: "Employee not registered. Please register first."

4. **Invalid File Type**
   - Photo file is ignored if not in supported formats

## CORS Configuration

The API is configured to accept requests from:
- `https://web.telegram.org`
- `https://t.me`

Allowed methods: GET, POST, PUT, DELETE, OPTIONS

## Security Notes

1. The API should be run behind a reverse proxy (e.g., nginx) in production
2. Use HTTPS for all production traffic
3. Implement rate limiting to prevent abuse
4. Validate file uploads to prevent malicious files
5. Consider adding authentication tokens for production use
