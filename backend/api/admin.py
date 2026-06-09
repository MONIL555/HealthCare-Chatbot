"""
Admin API — model metrics, audit logs.
"""

from flask import Blueprint, request, jsonify, current_app
from api.auth import token_required
from datetime import datetime
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)


@admin_bp.route('/metrics', methods=['GET'])
@token_required
def get_metrics():
    """Get current model performance metrics."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    metrics = current_app.db.get_current_metrics()
    if not metrics:
        return jsonify({
            'message': 'No model metrics available yet',
            'model_loaded': current_app.classifier.model is not None
        }), 200

    return jsonify(metrics), 200


@admin_bp.route('/logs', methods=['GET'])
@token_required
def get_logs():
    """Get audit logs (optional date range filter)."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    # Parse optional date filters
    start = request.args.get('date_from')
    end = request.args.get('date_to')
    limit = request.args.get('limit', 100, type=int)

    start_date = None
    end_date = None
    try:
        if start:
            start_date = datetime.fromisoformat(start)
        if end:
            end_date = datetime.fromisoformat(end)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO 8601.'}), 400

    logs = current_app.db.get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        limit=min(limit, 1000)
    )

    return jsonify({
        'total_logs': len(logs),
        'logs': logs
    }), 200
