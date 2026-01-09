# backend/routes/selection_routes.py (Updated)
from flask import Blueprint, request, jsonify
from models.pdf_processor import PDFProcessor
from services.selection_service import SelectionService

selection_bp = Blueprint('selection', __name__)
pdf_processor = PDFProcessor()
selection_service = SelectionService()

# Store current session ID (in production, use user sessions)
current_session_id = None

@selection_bp.route('/create-session', methods=['POST'])
def create_selection_session():
    """Create a new selection session"""
    global current_session_id
    
    data = request.json
    
    try:
        session_data = {
            'pdf_filename': data.get('pdf_filename'),
            'total_sentences': data.get('total_sentences'),
            'total_pages': data.get('total_pages'),
            'selected_sentences': [],
            'customized_sentences': [],
            'practice_stats': {}
        }
        
        session_id = selection_service.create_selection_session(session_data)
        current_session_id = session_id
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Selection session created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/update-selections', methods=['POST'])
def update_selections():
    """Update selection status for sentences"""
    global current_session_id
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    sentence_indices = data.get('sentence_indices', [])
    selected = data.get('selected', True)
    
    try:
        # Update PDF processor
        pdf_processor.update_sentence_selection(sentence_indices, selected)
        selected_sentences = pdf_processor.get_selected_sentences()
        
        # Update selection service
        if current_session_id:
            selection_service.update_selection_session(current_session_id, {
                'selected_sentences': selected_sentences
            })
        
        return jsonify({
            'success': True,
            'selected_count': len(selected_sentences),
            'selected_sentences': selected_sentences,
            'stats': pdf_processor.get_sentence_stats(),
            'session_id': current_session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/update-sentence-text', methods=['POST'])
def update_sentence_text():
    """Update custom text for a sentence"""
    data = request.json
    sentence_index = data.get('sentence_index')
    new_text = data.get('new_text')
    
    if sentence_index is None or new_text is None:
        return jsonify({'error': 'Missing sentence_index or new_text'}), 400
    
    try:
        pdf_processor.update_sentence_text(sentence_index, new_text)
        
        # Track customized sentences
        if current_session_id:
            session = selection_service.get_selection_session(current_session_id)
            if session:
                customized = session.get('customized_sentences', [])
                if sentence_index not in customized:
                    customized.append(sentence_index)
                    selection_service.update_selection_session(current_session_id, {
                        'customized_sentences': customized
                    })
        
        return jsonify({
            'success': True,
            'message': 'Sentence text updated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/get-selected-sentences', methods=['GET'])
def get_selected_sentences():
    """Get all selected sentences"""
    try:
        selected_sentences = pdf_processor.get_selected_sentences()
        
        return jsonify({
            'success': True,
            'selected_sentences': selected_sentences,
            'count': len(selected_sentences),
            'session_id': current_session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/save-selections', methods=['POST'])
def save_selections():
    """Save current selections to file"""
    data = request.json
    filename = data.get('filename')
    
    if not current_session_id:
        return jsonify({'error': 'No active selection session'}), 400
    
    try:
        file_path = selection_service.save_selections_to_file(current_session_id, filename)
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'session_id': current_session_id,
            'message': 'Selections saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/load-selections', methods=['POST'])
def load_selections():
    """Load selections from file"""
    data = request.json
    file_path = data.get('file_path')
    
    try:
        result = selection_service.load_selections_from_file(file_path)
        
        # Apply loaded selections to PDF processor
        loaded_sentences = result['loaded_data']['selections']['selected_sentences']
        sentence_indices = [s['global_index'] for s in loaded_sentences]
        pdf_processor.update_sentence_selection(sentence_indices, True)
        
        return jsonify({
            'success': True,
            'session_id': result['session_id'],
            'loaded_count': len(sentence_indices),
            'message': 'Selections loaded successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/saved-sessions', methods=['GET'])
def get_saved_sessions():
    """Get list of all saved selection sessions"""
    try:
        saved_sessions = selection_service.get_all_saved_sessions()
        
        return jsonify({
            'success': True,
            'saved_sessions': saved_sessions,
            'total_count': len(saved_sessions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@selection_bp.route('/session-analysis', methods=['GET'])
def get_session_analysis():
    """Get analysis of current selection patterns"""
    if not current_session_id:
        return jsonify({'error': 'No active session'}), 400
    
    try:
        analysis = selection_service.analyze_selection_patterns(current_session_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'session_id': current_session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500