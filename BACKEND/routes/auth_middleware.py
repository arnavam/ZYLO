# backend/routes/auth_middleware.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def jwt_required_custom(fn):
    """Custom JWT required decorator with better error handling"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': str(e)
            }), 401
    return wrapper

def get_current_user_id():
    """Get current user ID from JWT token"""
    try:
        return get_jwt_identity()
    except:
        return None