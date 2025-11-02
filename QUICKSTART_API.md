# Quick Start Guide - Flask API

## What Was Added

### 1. Dependencies
Added to `requirements.txt`:
- `flask==3.0.0` - Web framework
- `flask-cors==4.0.0` - CORS support for Telegram Mini Apps
- `pillow==10.1.0` - Image processing

### 2. Database Changes
- Added `photo_url` field to `check_ins` table
- Migration file: `alembic/versions/004_add_photo_url_to_checkins.py`

### 3. API Structure
```
src/infrastructure/api/
├── __init__.py
├── flask_app.py              # Flask app initialization
└── routes/
    ├── __init__.py
    └── checkin_routes.py     # Check-in endpoint
```

### 4. Entry Point
- `run_api.py` - Main script to run the Flask API server

## Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Database Migration
```bash
alembic upgrade head
```

This will add the `photo_url` column to your `check_ins` table.

### Step 3: Configure Environment
Update your `.env` file with API settings:
```env
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
```

### Step 4: Start the API Server
```bash
python run_api.py
```

You should see:
```
Starting Flask API server on 0.0.0.0:5000
Debug mode: False
Check-in Bot is running...
```

### Step 5: Test the API

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "success": true,
  "message": "API is running"
}
```

**Test Check-in (without photo):**
```bash
curl -X POST http://localhost:5000/api/checkin \
  -F "telegram_user_id=YOUR_TELEGRAM_ID" \
  -F "group_chat_id=-1001234567890" \
  -F "latitude=13.7563" \
  -F "longitude=100.5018" \
  -F "group_name=Test Group"
```

**Test Check-in (with photo):**
```bash
curl -X POST http://localhost:5000/api/checkin \
  -F "telegram_user_id=YOUR_TELEGRAM_ID" \
  -F "group_chat_id=-1001234567890" \
  -F "latitude=13.7563" \
  -F "longitude=100.5018" \
  -F "group_name=Test Group" \
  -F "photo=@/path/to/your/photo.jpg"
```

## API Endpoints

### 1. POST /api/checkin
Records a check-in with location and optional photo.

**Required Parameters:**
- `telegram_user_id`: Your Telegram user ID
- `group_chat_id`: Telegram group chat ID
- `latitude`: Location latitude
- `longitude`: Location longitude

**Optional Parameters:**
- `group_name`: Group name
- `photo`: Photo file (PNG, JPG, JPEG, GIF, WEBP)

### 2. GET /api/health
Health check endpoint to verify API is running.

## File Upload

Photos are saved to `uploads/photos/` directory with format:
```
{telegram_user_id}_{timestamp}_{filename}
```

Maximum file size: **16 MB**

## Integration with Telegram Mini App

The API is configured to accept requests from Telegram Mini Apps:
- CORS enabled for `https://web.telegram.org` and `https://t.me`
- Accepts multipart/form-data for file uploads

### Example Mini App Integration

```javascript
// In your Telegram Mini App
const formData = new FormData();
formData.append('telegram_user_id', Telegram.WebApp.initDataUnsafe.user.id);
formData.append('group_chat_id', chatId);
formData.append('latitude', latitude);
formData.append('longitude', longitude);
formData.append('photo', photoFile);

const response = await fetch('http://your-api-url/api/checkin', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

## Running Both Bot and API

You can run both the bot and API simultaneously:

**Terminal 1 - API Server:**
```bash
python run_api.py
```

**Terminal 2 - Telegram Bot:**
```bash
python run_checkin_bot.py
```

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, change the `API_PORT` in your `.env` file.

### Permission Denied on uploads/photos
Ensure the `uploads/photos` directory exists and is writable:
```bash
mkdir -p uploads/photos
chmod 755 uploads/photos
```

### Database Connection Error
Verify your database credentials in `.env` and ensure MySQL is running.

### Migration Error
If you get a migration error, check the current migration status:
```bash
alembic current
alembic history
```

## Production Deployment

For production deployment:
1. Set `API_DEBUG=False`
2. Use a production WSGI server (gunicorn, uWSGI)
3. Set up nginx as reverse proxy
4. Enable HTTPS
5. Configure proper CORS origins
6. Implement rate limiting
7. Set up monitoring and logging

**Example with Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "src.infrastructure.api.flask_app:create_app()"
```

## Further Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.
