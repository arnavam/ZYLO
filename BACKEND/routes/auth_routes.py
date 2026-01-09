# backend/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from datetime import timedelta
from models.user import User
from routes.auth_middleware import jwt_required_custom

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        # Validation
        if not email or not password or not name:
            return jsonify({
                'success': False,
                'error': 'Email, password, and name are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Create user
        user, error = User.create_user(email, password, name)
        
        if error:
            return jsonify({'success': False, 'error': error}), 409
        
        # Create access token
        access_token = create_access_token(
            identity=str(user['_id']),
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': User.to_dict(user),
            'access_token': access_token
        }), 201
        
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Find user
        user = User.find_by_email(email)
        
        if not user or not User.verify_password(user, password):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Create access token
        access_token = create_access_token(
            identity=str(user['_id']),
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': User.to_dict(user),
            'access_token': access_token
        }), 200
        
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required_custom
def get_current_user():
    """Get current authenticated user info"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': User.to_dict(user)
        }), 200
        
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Get user failed: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)"""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200