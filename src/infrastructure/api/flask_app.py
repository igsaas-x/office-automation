from flask import Flask
from flask_cors import CORS
from ...infrastructure.config.settings import settings

def create_app():
    app = Flask(__name__)

    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://web.telegram.org", "https://t.me"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = 'uploads/photos'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Register blueprints
    from .routes.checkin_routes import checkin_bp
    app.register_blueprint(checkin_bp, url_prefix='/api')

    return app
