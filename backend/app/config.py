import os
from typing import Dict, Any


class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15MB max file size
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Email SMTP settings
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SMTP_USE_TLS = True
    
    # Report generation settings
    REPORTS_FOLDER = os.environ.get('REPORTS_FOLDER') or 'reports'
    REPORT_TEMPLATE_PATH = os.environ.get('REPORT_TEMPLATE_PATH') or 'templates'
    
    # Anomaly detection thresholds
    ANOMALY_THRESHOLD_PERCENTAGE = float(os.environ.get('ANOMALY_THRESHOLD_PERCENTAGE', 30.0))
    ANOMALY_MIN_SAMPLE_SIZE = int(os.environ.get('ANOMALY_MIN_SAMPLE_SIZE', 3))
    
    # KPI monitoring settings
    MONITORED_METRICS = [
        'revenue',
        'expenses', 
        'profit_margin',
        'customer_count',
        'average_order_value'
    ]
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Use local SQLite for development if needed
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev.db'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Stricter security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Smaller file size for testing
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for tests


# Configuration mapping
config_map: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Any:
    """Get configuration class based on environment name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(config_name, config_map['default'])