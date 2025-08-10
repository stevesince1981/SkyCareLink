import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
migrate = Migrate()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "medifly-dev-secret-key-2025")
    
    # Database configuration with fallback
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        logger.info(f"Using PostgreSQL database: {database_url[:30]}...")
    else:
        # Fallback to SQLite
        os.makedirs('data', exist_ok=True)
        database_url = "sqlite:///data/medifly.db"
        logger.info(f"Using SQLite fallback: {database_url}")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app

# Create app instance
app = create_app()

# Import models after app creation to avoid circular imports
with app.app_context():
    import models  # noqa: F401
    logger.info("Models imported successfully")