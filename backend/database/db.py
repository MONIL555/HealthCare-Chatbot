"""
Database initialization and connection management.
"""

from database.models import Database
import logging

logger = logging.getLogger(__name__)

# Global database instance
_db = None


def get_db() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        from config import Config
        _db = Database(Config.MONGO_URI, Config.MONGO_DB_NAME)
    return _db


def init_db(app):
    """Initialize database and attach to Flask app."""
    global _db
    try:
        uri = app.config.get('MONGO_URI')
        db_name = app.config.get('MONGO_DB_NAME', 'healthcare_chatbot')
        _db = Database(uri, db_name)
        app.db = _db
        logger.info(f"Connected to MongoDB database: {db_name}")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        app.db = None
