from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import os


def create_app(config_name=None):
    """Flask application factory"""
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Load configuration from config.py
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from app.config import get_config
    app.config.from_object(get_config(config_name))
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.api.upload import upload_bp
    from app.api.report import report_bp
    from app.api.config import config_bp
    from app.api.email import email_bp
    from app.api.cleaning import cleaning_bp
    from app.api.visualization import visualization_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(report_bp, url_prefix='/api')
    app.register_blueprint(config_bp, url_prefix='/api')
    app.register_blueprint(email_bp, url_prefix='/api')
    app.register_blueprint(cleaning_bp, url_prefix='/api')
    app.register_blueprint(visualization_bp, url_prefix='/api')
    
    # Initialize Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Reporting System API",
            "description": "API for automated reporting and insight generation system",
            "version": "1.0.0"
        },
        "consumes": [
            "application/json",
            "multipart/form-data"
        ],
        "produces": [
            "application/json"
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Error handlers
    @app.errorhandler(413)
    def file_too_large(error):
        return {'error': 'File too large. Maximum size is 15MB.'}, 413
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Endpoint not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Reporting service is running'}
    
    return app