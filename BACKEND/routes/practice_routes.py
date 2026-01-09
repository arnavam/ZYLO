from flask import Blueprint, request, jsonify, send_from_directory
from urllib.parse import quote
import PyPDF2
import io
import re
import os

# ---------- BLUEPRINT ----------
practice_bp = Blueprint('practice', __name__)

# ---------- PRONUNCIATION MODEL ----------
print("🔄 Loading Wav2Vec2 pronunciation model...")
from models.wav2vec2_pronunciation_model import Wav2Vec2PronunciationModel
pronunciation_model = Wav2Vec2PronunciationModel()
print("✅ Pronunciation model ready!")


# ---------- PDF SENTENCE EXTRACTION ----------
def extract_sentences_from_pdf(pdf_file):
    """Extract sentences from PDF file object"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        all_sentences = []

        print(f"[PDF] Processing PDF with {len(pdf_reader.pages)} pages")

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()

            if text:
                sentences = re.split(r'[.!?]+', text)

                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 10:
                        all_sentences.append({
                            'text': sentence,
                            'page': page_num + 1,
                            'line': len(all_sentences) + 1,
                            'original_text': sentence
                        })

        print(f"[OK] Extracted {len(all_sentences)} sentences")
        return all_sentences

    except Exception as e:
        print(f"[ERROR] PDF extraction error: {e}")
        raise e


# ---------- PDF UPLOAD ----------
@practice_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf_practice():
    print("[API] PDF upload endpoint called")

    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400

        pdf_file = request.files['pdf']
        print(f"[PDF] Received file: {pdf_file.filename}")

        if pdf_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

        from werkzeug.utils import secure_filename

        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(pdf_file.filename)
        file_path = os.path.join(upload_dir, filename)

        pdf_file.seek(0)
        pdf_file.save(file_path)

        pdf_file.seek(0)
        sentences = extract_sentences_from_pdf(pdf_file)

        if not sentences:
            return jsonify({
                'success': False,
                'error': 'No readable text found in PDF'
            }), 400

        pdf_url = f'/api/practice/files/{quote(filename)}'

        return jsonify({
            'success': True,
            'filename': pdf_file.filename,
            'sentences': sentences,
            'total_sentences': len(sentences),
            'pdf_url': pdf_url,
            'message': f'PDF processed successfully! Found {len(sentences)} sentences.'
        })

    except Exception as e:
        print(f"[ERROR] PDF processing error: {str(e)}")
        return jsonify({'error': f'PDF processing failed: {str(e)}'}), 500


# ---------- TTS SPEAK SENTENCE ----------
@practice_bp.route('/speak-sentence', methods=['POST'])
def speak_sentence():
    data = request.json
    sentence = data.get('sentence')
    rate = data.get('rate', 150)

    if not sentence:
        return jsonify({'error': 'No sentence provided'}), 400

    try:
        from services.speech_service import SpeechService
        speech_service = SpeechService()

        if rate:
            speech_service.engine.setProperty('rate', rate)

        speech_service.speak(sentence)

        return jsonify({
            'success': True,
            'message': 'Sentence spoken successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- PRACTICE SENTENCE ----------
@practice_bp.route('/practice-sentence', methods=['POST'])
def practice_sentence():
    data = request.json
    sentence_text = data.get('sentence')

    if not sentence_text:
        return jsonify({'error': 'No sentence provided'}), 400

    try:
        from services.speech_service import SpeechService
        speech_service = SpeechService()

        result = speech_service.practice_sentence(sentence_text)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'spoken': None,
            'score': 0.0,
            'is_correct': False,
            'mode': 'error'
        }), 500


# ---------- SERVE UPLOADED FILES ----------
@practice_bp.route('/files/<path:filename>')
def serve_pdf(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, 'static', 'uploads')

    print(f"[DEBUG] Serving PDF: {filename}")

    return send_from_directory(upload_dir, filename)


# ---------- NEW: PRONUNCIATION EVALUATION ----------
@practice_bp.post("/evaluate-pronunciation")
def evaluate_pronunciation():
    """
    Evaluate spoken word pronunciation
    Expects:
      audio (File)
      word  (Text)
    """
    try:
        audio_file = request.files.get("audio")
        expected_word = request.form.get("word")

        if not audio_file or not expected_word:
            return jsonify({
                "success": False,
                "message": "audio and word are required"
            }), 400

        audio_bytes = audio_file.read()

        result = pronunciation_model.evaluate(
            audio_bytes=audio_bytes,
            expected_word=expected_word
        )

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        print("❌ Pronunciation evaluation error:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
