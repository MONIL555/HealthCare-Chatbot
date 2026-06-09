"""
MongoDB database operations for the Healthcare Chatbot.

Collections: users, queries, conversations, model_metrics, audit_logs
Follows schema from healthcare_chatbot_master_prompt.md
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from bson import ObjectId
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database operations."""

    def __init__(self, uri: str, db_name: str = 'healthcare_chatbot'):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self._create_indexes()
        logger.info(f"Database '{db_name}' ready")

    def _create_indexes(self):
        """Create database indexes for performance."""
        try:
            # Users collection
            self.db.users.create_index('email', unique=True)
            self.db.users.create_index('created_at')

            # Queries collection
            self.db.queries.create_index([
                ('user_id', ASCENDING),
                ('created_at', DESCENDING)
            ])
            self.db.queries.create_index('intent')
            self.db.queries.create_index('category')
            # TTL: auto-delete queries after 6 months (180 days)
            self.db.queries.create_index(
                'created_at',
                expireAfterSeconds=15552000
            )

            # Audit logs collection
            self.db.audit_logs.create_index('timestamp')
            self.db.audit_logs.create_index('user_id')
            # TTL: auto-delete audit logs after 30 days
            self.db.audit_logs.create_index(
                'created_at',
                expireAfterSeconds=2592000
            )

            # Conversations collection
            self.db.conversations.create_index([
                ('user_id', ASCENDING),
                ('updated_at', DESCENDING)
            ])
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")

    # ═══════════════════════════════════════════════════════
    # USER OPERATIONS
    # ═══════════════════════════════════════════════════════

    def create_user(self, email: str, password_hash: str,
                    full_name: str) -> Dict:
        """Create new user."""
        user = {
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'created_at': datetime.utcnow(),
            'last_login': None,
            'is_active': True,
            'role': 'patient',  # Default role
            'age': None,
            'gender': None,
            'weight': None,
            'height': None,
            'medical_conditions': [],
            'allergies': [],
            'preferences': {
                'theme': 'light',
                'notifications': True
            }
        }
        result = self.db.users.insert_one(user)
        return {'user_id': str(result.inserted_id), **user}

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        user = self.db.users.find_one({'email': email})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        try:
            user = self.db.users.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception:
            return None

    def update_last_login(self, user_id: str):
        """Update last login timestamp."""
        self.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'last_login': datetime.utcnow()}}
        )

    def update_user_profile(self, user_id: str, profile_data: Dict) -> Optional[Dict]:
        """Update user medical profile fields."""
        # Filter to only allow profile fields
        allowed_fields = ['age', 'gender', 'weight', 'height', 'medical_conditions', 'allergies']
        update_doc = {k: v for k, v in profile_data.items() if k in allowed_fields}
        
        if not update_doc:
            return self.get_user_by_id(user_id)
            
        self.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_doc}
        )
        return self.get_user_by_id(user_id)

    # ═══════════════════════════════════════════════════════
    # QUERY OPERATIONS
    # ═══════════════════════════════════════════════════════

    def save_query(self, user_id: str, query_text: str, intent: str,
                   confidence: float, category: str, response: str,
                   recommendations: Dict, entities: Dict,
                   response_time_ms: int = 0,
                   conversation_id: str = None) -> str:
        """Save user query and response, linked to a conversation."""
        query_doc = {
            'user_id': ObjectId(user_id),
            'query_text': query_text,
            'intent': intent,
            'confidence': confidence,
            'category': category,
            'response_text': response,
            'recommendations': recommendations,
            'entities_extracted': entities,
            'response_time_ms': response_time_ms,
            'user_feedback': None,
            'conversation_id': ObjectId(conversation_id) if conversation_id else None,
            'created_at': datetime.utcnow()
        }
        result = self.db.queries.insert_one(query_doc)

        # Update conversation message count and timestamp
        if conversation_id:
            self.db.conversations.update_one(
                {'_id': ObjectId(conversation_id)},
                {
                    '$inc': {'message_count': 1},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )

        return str(result.inserted_id)

    def get_user_queries(self, user_id: str, limit: int = 50,
                         offset: int = 0) -> List[Dict]:
        """Get user's query history (newest first)."""
        queries = list(self.db.queries.find(
            {'user_id': ObjectId(user_id)}
        ).sort('created_at', DESCENDING).skip(offset).limit(limit))

        for query in queries:
            query['_id'] = str(query['_id'])
            query['user_id'] = str(query['user_id'])
            # Convert datetime to ISO string for JSON serialization
            if 'created_at' in query:
                query['created_at'] = query['created_at'].isoformat()

        return queries

    def get_query_count(self, user_id: str) -> int:
        """Get total queries for a user."""
        return self.db.queries.count_documents(
            {'user_id': ObjectId(user_id)}
        )

    def add_feedback(self, query_id: str, feedback: str):
        """Add user feedback ('helpful' or 'not_helpful') to a query."""
        self.db.queries.update_one(
            {'_id': ObjectId(query_id)},
            {'$set': {'user_feedback': feedback}}
        )

    # ═══════════════════════════════════════════════════════
    # CONVERSATION OPERATIONS
    # ═══════════════════════════════════════════════════════

    def create_conversation(self, user_id: str, title: str = 'New Chat') -> str:
        """Create a new conversation session."""
        conv = {
            'user_id': ObjectId(user_id),
            'title': title,
            'message_count': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        result = self.db.conversations.insert_one(conv)
        return str(result.inserted_id)

    def get_user_conversations(self, user_id: str, limit: int = 30,
                                offset: int = 0) -> List[Dict]:
        """Get user's conversations (newest first)."""
        convs = list(self.db.conversations.find(
            {'user_id': ObjectId(user_id)}
        ).sort('updated_at', DESCENDING).skip(offset).limit(limit))

        for c in convs:
            c['_id'] = str(c['_id'])
            c['user_id'] = str(c['user_id'])
            if 'created_at' in c:
                c['created_at'] = c['created_at'].isoformat()
            if 'updated_at' in c:
                c['updated_at'] = c['updated_at'].isoformat()
        return convs

    def get_conversation_messages(self, conversation_id: str,
                                  user_id: str) -> List[Dict]:
        """Get all messages in a conversation (oldest first)."""
        messages = list(self.db.queries.find(
            {
                'conversation_id': ObjectId(conversation_id),
                'user_id': ObjectId(user_id)
            }
        ).sort('created_at', ASCENDING))

        for m in messages:
            m['_id'] = str(m['_id'])
            m['user_id'] = str(m['user_id'])
            if m.get('conversation_id'):
                m['conversation_id'] = str(m['conversation_id'])
            if 'created_at' in m:
                m['created_at'] = m['created_at'].isoformat()
        return messages

    def update_conversation_title(self, conversation_id: str,
                                   user_id: str, title: str):
        """Rename a conversation."""
        self.db.conversations.update_one(
            {'_id': ObjectId(conversation_id), 'user_id': ObjectId(user_id)},
            {'$set': {'title': title}}
        )

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all its messages."""
        # Delete all messages in the conversation
        self.db.queries.delete_many({
            'conversation_id': ObjectId(conversation_id),
            'user_id': ObjectId(user_id)
        })
        # Delete the conversation itself
        result = self.db.conversations.delete_one({
            '_id': ObjectId(conversation_id),
            'user_id': ObjectId(user_id)
        })
        return result.deleted_count > 0

    # ═══════════════════════════════════════════════════════
    # MODEL METRICS OPERATIONS
    # ═══════════════════════════════════════════════════════

    def save_model_metrics(self, version: str, accuracy: float,
                           metrics_dict: Dict):
        """Save model performance metrics."""
        # Deactivate previous metrics
        self.db.model_metrics.update_many(
            {},
            {'$set': {'is_active': False}}
        )
        metrics = {
            'model_version': version,
            'accuracy': accuracy,
            'metrics': metrics_dict,
            'training_date': datetime.utcnow(),
            'is_active': True
        }
        self.db.model_metrics.insert_one(metrics)

    def get_current_metrics(self) -> Optional[Dict]:
        """Get current active model metrics."""
        metrics = self.db.model_metrics.find_one({'is_active': True})
        if metrics:
            metrics['_id'] = str(metrics['_id'])
            if 'training_date' in metrics:
                metrics['training_date'] = metrics['training_date'].isoformat()
        return metrics

    # ═══════════════════════════════════════════════════════
    # AUDIT LOG OPERATIONS
    # ═══════════════════════════════════════════════════════

    def log_action(self, user_id: Optional[str], action: str,
                   endpoint: str, method: str, status_code: int,
                   ip_address: str, details: Dict = None):
        """Log an action for audit trail."""
        log_entry = {
            'user_id': ObjectId(user_id) if user_id else None,
            'action': action,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'ip_address': ip_address,
            'details': details or {},
            'timestamp': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        self.db.audit_logs.insert_one(log_entry)

    def get_audit_logs(self, start_date: datetime = None,
                       end_date: datetime = None,
                       limit: int = 100) -> List[Dict]:
        """Get audit logs within optional date range."""
        query = {}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date

        logs = list(self.db.audit_logs.find(query)
                    .sort('timestamp', DESCENDING).limit(limit))

        for log in logs:
            log['_id'] = str(log['_id'])
            if log.get('user_id'):
                log['user_id'] = str(log['user_id'])
            if 'timestamp' in log:
                log['timestamp'] = log['timestamp'].isoformat()

        return logs
