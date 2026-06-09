"""
Healthcare Chatbot — Flask Application Factory

Production-grade NLP-driven healthcare chatbot that triages patient
inquiries across 8 medical categories with 80%+ intent classification
accuracy using spaCy, Scikit-Learn, Flask, and MongoDB.
"""

from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config, DevelopmentConfig
from database.db import init_db
from nlp.gemini_fallback import GeminiFallback
from nlp.symptom_classifier import SymptomClassifier
import logging
import os


def create_app(config_class=None):
    """Application factory"""

    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        config_class = DevelopmentConfig if env == 'development' else Config

    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Logging ──────────────────────────────────────────────
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    logger = logging.getLogger(__name__)

    # ── Extensions ───────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": config_class.CORS_ORIGINS}})

    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    # ── Database ─────────────────────────────────────────────
    init_db(app)
    logger.info("Database initialized")

    # ── NLP Models ────────────────────────────────────────────
    # Primary: ML-based symptom classifier (Decision Tree + SVM)
    symptom_classifier = SymptomClassifier()
    symptom_classifier.load_models()
    app.symptom_classifier = symptom_classifier
    logger.info("Symptom Classifier loaded (%d diseases)", len(symptom_classifier.label_encoder.classes_))

    # Fallback: Gemini LLM for general health questions
    gemini_fallback = GeminiFallback()
    app.gemini_fallback = gemini_fallback
    logger.info("Gemini Fallback loaded")

    # ── Blueprints ───────────────────────────────────────────
    from api.auth import auth_bp
    from api.chat import chat_bp
    from api.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # ── Health Check ─────────────────────────────────────────
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'model_loaded': app.classifier.model is not None,
            'db_connected': app.db is not None,
            'timestamp': datetime.utcnow().isoformat()
        })

    # ── Error Handlers ───────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

    logger.info("Healthcare Chatbot API ready")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

# Reloading server for new model

# Reloading for responses update

# Reloading for dynamic response logic

# Reloading for QA matcher

# Hot reload 

# Reloading for dynamic logic

# ELIZA style reflection

# Hot Reload For Variations

# Hot Reload For Variations
