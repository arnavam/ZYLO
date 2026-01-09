# backend/routes/pdf_routes.py
from flask import Blueprint, request, jsonify
import os
from config import Config
from models.pdf_processor import PDFProcessor
import tempfile

pdf_bp = Blueprint('pdf', __name__)
pdf_processor = PDFProcessor()

@pdf_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF file upload and text extraction"""
    print("[API] PDF upload endpoint called")
    
    if 'pdf' not in request.files:
        print("[ERROR] No PDF file in request")
        return jsonify({'error': 'No PDF file provided'}), 400
    
    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        print("[ERROR] Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    if not pdf_file.filename.lower().endswith('.pdf'):
        print("[ERROR] Not a PDF file")
        return jsonify({'error': 'File must be a PDF'}), 400
    
    try:
        print(f"[PDF] Processing PDF: {pdf_file.filename}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            pdf_file.save(temp_file.name)
            temp_path = temp_file.name
        
        # Extract text from PDF
        sentences = pdf_processor.extract_text_with_positions(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        print(f"[OK] PDF processed successfully: {len(sentences)} sentences found")
        
        response_data = {
            'success': True,
            'filename': pdf_file.filename,
            'total_sentences': len(sentences),
            'pages': len(pdf_processor.page_texts),
            'sentences': sentences,
            'stats': pdf_processor.get_sentence_stats()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[ERROR] PDF processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/pdf-info', methods=['GET'])
def get_pdf_info():
    """Get information about the currently loaded PDF"""
    try:
        stats = pdf_processor.get_sentence_stats()
        
        return jsonify({
            'success': True,
            'has_pdf': len(pdf_processor.sentences) > 0,
            'stats': stats,
            'current_pdf': pdf_processor.current_pdf_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500