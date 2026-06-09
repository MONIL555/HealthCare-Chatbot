"""
Authentication API — signup, login, logout, refresh, profile.

Uses JWT tokens with werkzeug password hashing.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from functools import wraps
import re
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _validate_password(password: str) -> bool:
    """Password must be at least 8 characters."""
    return len(password) >= 8


def create_tokens(user_id: str) -> tuple:
    """Create JWT access and refresh tokens."""
    now = datetime.utcnow()
    secret = current_app.config['JWT_SECRET_KEY']
    algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
    hours = current_app.config.get('JWT_EXPIRATION_HOURS', 24)

    # Access token (24 hours default)
    access_payload = {
        'user_id': user_id,
        'type': 'access',
        'iat': now,
        'exp': now + timedelta(hours=hours)
    }

    # Refresh token (7 days)
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'iat': now,
        'exp': now + timedelta(days=7)
    }

    access_token = jwt.encode(access_payload, secret, algorithm=algorithm)
    refresh_token = jwt.encode(refresh_payload, secret, algorithm=algorithm)

    return access_token, refresh_token


def token_required(f):
    """Decorator to verify JWT access token on protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401

        try:
            secret = current_app.config['JWT_SECRET_KEY']
            algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
            payload = jwt.decode(token, secret, algorithms=[algorithm])

            if payload.get('type') != 'access':
                return jsonify({'error': 'Invalid token type'}), 401

            request.user_id = payload['user_id']

        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except JWTError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User registration."""
    data = request.json
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    # Validation
    if not email or not password or not full_name:
        return jsonify({'error': 'Email, password, and full_name are required'}), 400

    if not _validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    if not _validate_password(password):
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    # Check if user exists
    existing = current_app.db.get_user_by_email(email)
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    # Create user
    password_hash = generate_password_hash(password)
    user = current_app.db.create_user(email, password_hash, full_name)

    # Create tokens
    access_token, refresh_token = create_tokens(user['user_id'])

    logger.info(f"User registered: {email}")

    return jsonify({
        'user_id': user['user_id'],
        'email': email,
        'full_name': full_name,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 86400  # 24 hours in seconds
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login."""
    data = request.json
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    # Find user
    user = current_app.db.get_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        logger.warning(f"Failed login attempt: {email}")
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.get('is_active', True):
        return jsonify({'error': 'Account disabled'}), 403

    # Update last login
    current_app.db.update_last_login(user['_id'])

    # Create tokens
    access_token, refresh_token = create_tokens(user['_id'])

    logger.info(f"User logged in: {email}")

    return jsonify({
        'user_id': user['_id'],
        'email': user['email'],
        'full_name': user['full_name'],
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 86400
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """User logout."""
    logger.info(f"User logged out: {request.user_id}")
    return jsonify({'success': True}), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token."""
    data = request.json
    refresh_token = data.get('refresh_token') if data else None

    if not refresh_token:
        return jsonify({'error': 'Missing refresh token'}), 400

    try:
        secret = current_app.config['JWT_SECRET_KEY']
        algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
        payload = jwt.decode(refresh_token, secret, algorithms=[algorithm])

        if payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid token type'}), 401

        user_id = payload['user_id']

    except ExpiredSignatureError:
        return jsonify({'error': 'Refresh token expired'}), 401
    except JWTError:
        return jsonify({'error': 'Invalid refresh token'}), 401

    # Create new tokens
    access_token, new_refresh_token = create_tokens(user_id)

    return jsonify({
        'access_token': access_token,
        'refresh_token': new_refresh_token,
        'expires_in': 86400
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get user profile."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    user = current_app.db.get_user_by_id(request.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Remove sensitive data
    user.pop('password_hash', None)

    # Convert datetime fields for JSON
    for field in ('created_at', 'last_login'):
        if isinstance(user.get(field), datetime):
            user[field] = user[field].isoformat()

    return jsonify(user), 200
