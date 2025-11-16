from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
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
        ]
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Register blueprints
    from .routes.checkin_routes import checkin_bp
    from .routes.employee_routes import employee_bp
    app.register_blueprint(checkin_bp, url_prefix='/api')
    app.register_blueprint(employee_bp, url_prefix='/api')

    return app
