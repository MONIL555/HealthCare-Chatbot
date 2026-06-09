"""
Chat API — conversations, query, history, feedback.

Protected endpoints requiring JWT authentication.
"""

import time
from flask import Blueprint, request, jsonify, current_app
from api.auth import token_required
from bson.objectid import ObjectId
import logging
import re
from langdetect import detect
from deep_translator import GoogleTranslator

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# CONVERSATION ENDPOINTS
# ═══════════════════════════════════════════════════════════

@chat_bp.route('/conversations', methods=['POST'])
@token_required
def create_conversation():
    """Create a new conversation."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.json or {}
    title = data.get('title', 'New Chat')

    conv_id = current_app.db.create_conversation(
        user_id=request.user_id,
        title=title
    )
    return jsonify({'conversation_id': conv_id, 'title': title}), 201


@chat_bp.route('/conversations', methods=['GET'])
@token_required
def list_conversations():
    """Get user's conversations (newest first)."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    limit = request.args.get('limit', 30, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    convs = current_app.db.get_user_conversations(
        request.user_id, limit=limit, offset=offset
    )
    return jsonify({'conversations': convs}), 200


@chat_bp.route('/conversations/<conv_id>', methods=['GET'])
@token_required
def get_conversation(conv_id):
    """Get all messages in a conversation."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    messages = current_app.db.get_conversation_messages(
        conv_id, request.user_id
    )
    return jsonify({'messages': messages}), 200


@chat_bp.route('/conversations/<conv_id>', methods=['PATCH'])
@token_required
def rename_conversation(conv_id):
    """Rename a conversation."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.json or {}
    title = data.get('title')
    if not title:
        return jsonify({'error': 'title is required'}), 400

    current_app.db.update_conversation_title(
        conv_id, request.user_id, title
    )
    return jsonify({'success': True}), 200


@chat_bp.route('/conversations/<conv_id>', methods=['DELETE'])
@token_required
def delete_conversation(conv_id):
    """Delete a conversation and all its messages."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    deleted = current_app.db.delete_conversation(conv_id, request.user_id)
    if deleted:
        return jsonify({'success': True}), 200
    return jsonify({'error': 'Conversation not found'}), 404


# ═══════════════════════════════════════════════════════════
# QUERY (SEND MESSAGE) ENDPOINT
# ═══════════════════════════════════════════════════════════

@chat_bp.route('/query', methods=['POST'])
@token_required
def chat_query():
    """
    Process a user's medical query within a conversation.

    If no conversation_id provided, creates a new conversation
    automatically (title = first query text).
    """
    start_time = time.time()

    data = request.json
    if not data or 'user_query' not in data:
        return jsonify({'error': 'user_query is required'}), 400

    user_query = data['user_query'].strip()
    conversation_id = data.get('conversation_id')

    # Input validation
    if not user_query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    if len(user_query) > 500:
        return jsonify({'error': 'Query too long (max 500 characters)'}), 400

    # Auto-create conversation if none provided
    new_conversation = False
    if not conversation_id and current_app.db is not None:
        # Title = first 50 chars of the first query
        title = user_query[:50] + ('...' if len(user_query) > 50 else '')
        conversation_id = current_app.db.create_conversation(
            user_id=request.user_id,
            title=title
        )
        new_conversation = True

    # ── Language Detection & Translation ──────────────────
    user_lang = 'en'
    translated_query = user_query
    try:
        user_lang = detect(user_query)
        if user_lang != 'en':
            translator = GoogleTranslator(source=user_lang, target='en')
            translated_query = translator.translate(user_query)
    except Exception as e:
        logger.warning(f"Language detection/translation failed: {e}")

    entities = {}

    # ── Primary: ML Symptom Classifier ────────────────────
    ml_result = current_app.symptom_classifier.predict(translated_query)

    if ml_result.get('success'):
        intent = 'disease_prediction'
        confidence = ml_result['confidence']
        category = ml_result['disease']

        response_data = {
            'response': ml_result['response'],
            'home_remedies': ml_result.get('precautions', []),
            'specialist': ml_result.get('specialist'),
            'urgency': ml_result.get('urgency', 'low'),
            'emergency': ml_result.get('urgency') == 'emergency',
        }

        entities = {
            'matched_symptoms': ml_result.get('matched_symptoms', []),
            'severity_score': ml_result.get('severity_score', 0),
            'description': ml_result.get('description', ''),
            'dt_prediction': ml_result.get('dt_prediction', ''),
            'svm_prediction': ml_result.get('svm_prediction', ''),
        }
    else:
        # ── Pre-flight check to avoid API requests for non-medical queries ────
        medical_keywords = {
            'health', 'medical', 'medicine', 'doctor', 'hospital', 'pain', 'ache',
            'pill', 'tablet', 'disease', 'ill', 'illness', 'sick', 'sickness',
            'syndrome', 'therapy', 'treatment', 'vitamin', 'sleep', 'diet',
            'nutrition', 'heart', 'blood', 'brain', 'stomach', 'liver', 'kidney',
            'lung', 'symptom', 'symptoms', 'surgery', 'clinic', 'pharmacy',
            'prescription', 'fever', 'cough', 'cold', 'flu', 'virus', 'infection',
            'cancer', 'diabetes', 'pressure', 'injury', 'wound', 'heal', 'pregnant',
            'pregnancy', 'mental', 'depression', 'anxiety', 'stress', 'dental',
            'tooth', 'teeth', 'eye', 'vision', 'ear', 'nose', 'throat', 'skin',
            'bone', 'joint', 'muscle', 'weight', 'fatigue', 'energy'
        }
        
        query_words = set(re.findall(r'\w+', translated_query.lower()))
        is_medical = bool(query_words.intersection(medical_keywords))
        
        if not is_medical:
            gemini_response = "I am a specialized healthcare assistant. I can only answer medical and health-related questions. Please ask me about symptoms, conditions, medications, or general health advice."
            intent = 'non_medical_query'
        else:
            # ── Fallback: Gemini LLM for general health questions ────
            user_profile = None
            if current_app.db is not None:
                user_profile = current_app.db.get_user_by_id(request.user_id)
                
            gemini_response = current_app.gemini_fallback.generate_response(translated_query, user_profile)
            intent = 'general_query'
        
        confidence = 0.90
        category = 'general_health'

        response_data = {
            'response': gemini_response,
            'home_remedies': [],
            'specialist': None,
            'urgency': 'low',
            'emergency': False,
        }

    # ── Translate Response Back ─────────────────────────────
    if user_lang != 'en':
        try:
            translator_back = GoogleTranslator(source='en', target=user_lang)
            response_data['response'] = translator_back.translate(response_data['response'])
            if response_data['home_remedies']:
                response_data['home_remedies'] = [
                    translator_back.translate(r) for r in response_data['home_remedies']
                ]
            if response_data['specialist']:
                response_data['specialist'] = translator_back.translate(response_data['specialist'])
        except Exception as e:
            logger.warning(f"Failed to translate response back: {e}")

    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)

    # ── Save to Database ──────────────────────────────────
    query_id = None
    if current_app.db is not None:
        try:
            query_id = current_app.db.save_query(
                user_id=request.user_id,
                query_text=user_query,
                intent=intent,
                confidence=confidence,
                category=category,
                response=response_data['response'],
                recommendations={
                    'home_remedies': response_data['home_remedies'],
                    'specialist': response_data['specialist'],
                    'urgency': response_data['urgency'],
                    'emergency': response_data['emergency'],
                },
                entities=entities,
                response_time_ms=response_time_ms,
                conversation_id=conversation_id,
            )

            # Audit log
            current_app.db.log_action(
                user_id=request.user_id,
                action='chat_query',
                endpoint='/api/chat/query',
                method='POST',
                status_code=200,
                ip_address=request.remote_addr,
                details={'intent': intent, 'confidence': confidence}
            )
        except Exception as e:
            logger.error(f"DB save error: {e}")

    # ── Build Response ────────────────────────────────────
    result = {
        'query': user_query,
        'intent': intent,
        'confidence': confidence,
        'category': category,
        'response': response_data['response'],
        'recommendations': {
            'home_remedies': response_data['home_remedies'],
            'specialist': response_data['specialist'],
            'urgency': response_data['urgency'],
            'emergency': response_data['emergency'],
        },
        'entities': entities,
        'response_time_ms': response_time_ms,
        'query_id': query_id,
        'conversation_id': conversation_id,
        'new_conversation': new_conversation,
        'follow_up_question': ml_result.get('follow_up_question') if ml_result.get('success') else None
    }

    return jsonify(result), 200


# ═══════════════════════════════════════════════════════════
# HISTORY & FEEDBACK (kept for backward compatibility)
# ═══════════════════════════════════════════════════════════

@chat_bp.route('/history', methods=['GET'])
@token_required
def chat_history():
    """Get user's query history (paginated)."""
    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    queries = current_app.db.get_user_queries(
        request.user_id, limit=limit, offset=offset
    )
    total = current_app.db.get_query_count(request.user_id)

    return jsonify({
        'total_queries': total,
        'limit': limit,
        'offset': offset,
        'queries': queries
    }), 200


@chat_bp.route('/feedback', methods=['POST'])
@token_required
def chat_feedback():
    """Add user feedback to a query."""
    data = request.json
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    query_id = data.get('query_id')
    feedback = data.get('feedback')

    if not query_id or not feedback:
        return jsonify({'error': 'query_id and feedback are required'}), 400

    if feedback not in ('helpful', 'not_helpful'):
        return jsonify({
            'error': 'feedback must be "helpful" or "not_helpful"'
        }), 400

    if current_app.db is None:
        return jsonify({'error': 'Database unavailable'}), 503

    try:
        current_app.db.add_feedback(query_id, feedback)
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({'error': 'Failed to save feedback'}), 500


@chat_bp.route('/history/<query_id>', methods=['DELETE'])
@token_required
def delete_chat_history(query_id):
    """Delete a specific query from history."""
    if current_app.db is not None:
        try:
            result = current_app.db.db.queries.delete_one({
                '_id': ObjectId(query_id),
                'user_id': ObjectId(request.user_id)
            })
            if result.deleted_count > 0:
                return jsonify({'success': True}), 200
            return jsonify({'error': 'Query not found'}), 404
        except Exception as e:
            logger.error(f"Error deleting query: {e}")
            return jsonify({'error': 'Server error'}), 500
    return jsonify({'error': 'Database not connected'}), 500
