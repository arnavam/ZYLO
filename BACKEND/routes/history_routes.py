# backend/routes/history_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models.pdf_history import PdfHistory
from routes.auth_middleware import jwt_required_custom

history_bp = Blueprint('history', __name__)

@history_bp.route('', methods=['GET'])
@jwt_required_custom
def get_history():
    """Get user's PDF viewing history"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        history = PdfHistory.get_user_history(user_id, limit=limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        }), 200
        
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Get history failed: {e}")
        return jsonify({'success': False, 'error': 'Failed to get history'}), 500


@history_bp.route('', methods=['POST'])
@jwt_required_custom
def add_to_history():
    """Add a PDF to user's viewing history"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        pdf_name = data.get('pdf_name')
        if not pdf_name:
            return jsonify({'success': False, 'error': 'PDF name is required'}), 400
        
        history_id = PdfHistory.add_to_history(
            user_id=user_id,
            pdf_name=pdf_name,
            pdf_path=data.get('pdf_path'),
            total_pages=data.get('total_pages', 0),
            total_sentences=data.get('total_sentences', 0),
            file_size=data.get('file_size', 0)
        )
        
        return jsonify({
            'success': True,
            'message': 'Added to history',
            'history_id': history_id
        }), 201
        
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Add to history failed: {e}")
        return jsonify({'success': False, 'error': 'Failed to add to history'}), 500


@history_bp.route('/<history_id>', methods=['DELETE'])
@jwt_required_custom
def delete_from_history(history_id):
    """Delete a PDF from user's history"""
    try:
        user_id = get_jwt_identity()
        
        success = PdfHistory.delete_from_history(history_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Removed from history'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'History entry not found'
            }), 404
            
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Delete from history failed: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete from history'}), 500


@history_bp.route('/<history_id>/progress', methods=['PATCH'])
@jwt_required_custom
def update_progress(history_id):
    """Update reading progress for a PDF"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'last_page' not in data:
            return jsonify({'success': False, 'error': 'last_page is required'}), 400
        
        success = PdfHistory.update_progress(history_id, user_id, data['last_page'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Progress updated'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'History entry not found'
            }), 404
            
    except ConnectionError as e:
        print(f"[ERROR] Database error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Database connection error. Please ensure MongoDB is running.'
        }), 503
    except Exception as e:
        print(f"[ERROR] Update progress failed: {e}")
        return jsonify({'success': False, 'error': 'Failed to update progress'}), 500