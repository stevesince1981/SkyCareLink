import os
from datetime import timedelta

class Config:
    """Application configuration with security settings"""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('SESSION_SECRET', 'dev-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = False  # Allow HTTP for Replit development
    
    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('FORCE_HTTPS', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@skycarelink.com')
    
    # Analytics
    GA_MEASUREMENT_ID = os.environ.get('GA_MEASUREMENT_ID')
    
    # Password reset
    RESET_TOKEN_EXPIRY_HOURS = 2
    
    # Audit logging
    AUDIT_SENSITIVE_ACTIONS = True
    AUDIT_RETENTION_DAYS = 365
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        # Set secure cookie flags based on environment
        if Config.SESSION_COOKIE_SECURE:
            app.config['SESSION_COOKIE_SECURE'] = True
        
        # Configure CSRF token in templates
        @app.context_processor
        def security_context_processor():
            from flask_wtf.csrf import generate_csrf
            return {'csrf_token': generate_csrf}

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production
    WTF_CSRF_SSL_STRICT = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SESSION_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}