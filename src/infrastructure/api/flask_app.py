from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from ..config.settings import settings
from ..persistence.mongodb_connection import mongodb
from .middleware import validate_telegram_auth

def create_app():
    app = Flask(__name__)

    # Configure JWT
    app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY
    app.config['JWT_ALGORITHM'] = settings.JWT_ALGORITHM
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.JWT_ACCESS_TOKEN_EXPIRES
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = settings.JWT_REFRESH_TOKEN_EXPIRES

    # Initialize JWT manager
    jwt = JWTManager(app)

    # Initialize MongoDB connection
    try:
        mongodb.connect()
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")

    # Register Telegram authentication middleware
    app.before_request(validate_telegram_auth)

    # Get admin portal origins from settings
    admin_origins = settings.get_cors_origins()
    telegram_origins = ["https://web.telegram.org", "https://t.me"]

    # Check if wildcard is enabled
    if admin_origins and admin_origins[0] == '*':
        # Allow all origins
        CORS(app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
    else:
        # Use specific origins
        all_origins = telegram_origins + admin_origins
        CORS(app, resources={
            r"/api/*": {
                "origins": all_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })

    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = 'uploads/photos'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Configure Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api-docs/"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Office Automation Miniapp API",
            "description": "API for employee management miniapp with features for registration, salary tracking, allowances, and check-ins",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
            }
        },
        "basePath": "/",
        "schemes": ["http", "https"],
        "tags": [
            {
                "name": "Authentication",
                "description": "Admin portal authentication with JWT tokens"
            },
            {
                "name": "Employees",
                "description": "Employee registration and management"
            },
            {
                "name": "Staff Operations",
                "description": "Daily operations including salary advances, allowances, and status"
            },
            {
                "name": "Check-ins",
                "description": "Employee check-in operations"
            },
            {
                "name": "Health",
                "description": "API health check"
            }
        ],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        }
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Register blueprints
    from .routes.checkin_routes import checkin_bp
    from .routes.employee_routes import employee_bp
    from .routes.auth_routes import auth_bp
    from .routes.admin_group_routes import admin_group_bp
    app.register_blueprint(checkin_bp, url_prefix='/api')
    app.register_blueprint(employee_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)  # auth_bp already has /api/auth prefix
    app.register_blueprint(admin_group_bp)  # admin_group_bp already has /api/admin/groups prefix

    return app
