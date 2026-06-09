import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database
    MONGO_URI = os.getenv(
        'MONGO_URI',
        'mongodb://localhost:27017/healthcare_chatbot'
    )
    MONGO_DB_NAME = 'healthcare_chatbot'

    # Authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

    # CORS
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5173'
    ).split(',')

    # Rate Limiting
    RATE_LIMIT_QUERIES_PER_HOUR = int(
        os.getenv('RATE_LIMIT_QUERIES_PER_HOUR', 50)
    )

    # Model Settings
    MODEL_CONFIDENCE_THRESHOLD = float(
        os.getenv('MODEL_CONFIDENCE_THRESHOLD', 0.45)
    )

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGO_DB_NAME = 'healthcare_chatbot_test'
