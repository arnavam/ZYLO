
# backend/models/user.py
from datetime import datetime
import bcrypt
from bson import ObjectId
from db import get_users_collection

class User:
    """User model for authentication"""
    
    @staticmethod
    def create_user(email, password, name):
        """Create a new user with hashed password"""
        users = get_users_collection()
        
        # Check if user already exists
        if users.find_one({'email': email.lower()}):
            return None, "Email already registered"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_doc = {
            'email': email.lower(),
            'password_hash': password_hash,
            'name': name,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        return user_doc, None
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        users = get_users_collection()
        return users.find_one({'email': email.lower()})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        users = get_users_collection()
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return users.find_one({'_id': user_id})
    
    @staticmethod
    def verify_password(user, password):
        """Verify user password"""
        if not user or 'password_hash' not in user:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), user['password_hash'])
    
    @staticmethod
    def to_dict(user):
        """Convert user document to dict (excluding password)"""
        if not user:
            return None
        return {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'created_at': user['created_at'].isoformat() if user.get('created_at') else None
        }
