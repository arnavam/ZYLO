# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from config import Config
from dotenv import load_dotenv
import os
import shutil


# Load environment variables
load_dotenv()

# Import database
from db import init_db

# Import blueprints
from routes.pdf_routes import pdf_bp
from routes.practice_routes import practice_bp
from routes.selection_routes import selection_bp
from routes.auth_routes import auth_bp
from routes.history_routes import history_bp

# 🔍 Check eSpeak availability at startup
if not (shutil.which("espeak") or shutil.which("espeak-ng")):
    raise RuntimeError(
        "eSpeak not available in PATH. Please install eSpeak or eSpeak-NG."
    )



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # =========================
    # JWT CONFIGURATION (ADDED)
    # =========================
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY',
        'zylo-jwt-secret-key-default-change-me'
    )
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

    jwt = JWTManager(app)

    # =========================
    # DATABASE INIT (ADDED)
    # =========================
    init_db()

    # =========================
    # CORS CONFIG
    # =========================
    CORS(
        app,
        origins=["http://localhost:3000"],
        supports_credentials=True
    )

    # =========================
    # BLUEPRINT REGISTRATION
    # =========================
    app.register_blueprint(pdf_bp, url_prefix='/api/pdf')
    app.register_blueprint(practice_bp, url_prefix='/api/practice')
    app.register_blueprint(selection_bp, url_prefix='/api/selection')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(history_bp, url_prefix='/api/history')

    # =========================
    # SIMPLE TEST ENDPOINT
    # =========================
    @app.route('/api/test-simple', methods=['POST'])
    def test_simple():
        print("[OK] Simple test endpoint called!")
        return jsonify({
            'success': True,
            'message': 'Backend is working!',
            'sentences': [
                {'text': 'Test sentence one.', 'page': 1, 'line': 1},
                {'text': 'Test sentence two.', 'page': 1, 'line': 2},
                {'text': 'Test sentence three.', 'page': 1, 'line': 3}
            ]
        })

    # =========================
    # HEALTH CHECK
    # =========================
    @app.route('/api/health')
    def health_check():
        return {
            'status': 'healthy',
            'service': 'Dyslexia Reading Assistant API',
            'version': '1.0.0',
            'auth': 'enabled'
        }

    # =========================
    # DEBUG ROUTES
    # =========================
    @app.route('/api/debug/routes')
    def debug_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith('/api/'):
                routes.append({
                    'endpoint': rule.rule,
                    'methods': list(rule.methods)
                })
        return {'routes': routes}

    return app


if __name__ == '__main__':
    print(">>> Starting Dyslexia Reading Assistant Backend...")
    # Pre-loading moved to lazy load in services to avoid startup delays
    # from services.speech_service import load_wav2vec2_model
    # load_wav2vec2_model()

    app = create_app()
    print("API available at: http://localhost:5000")
    print("Auth endpoints: POST /api/auth/register, POST /api/auth/login")
    print("History endpoints: GET/POST /api/history")
    print("Test endpoint: POST http://localhost:5000/api/test-simple")
    print("Health check: http://localhost:5000/api/health")
    print("Debug routes: http://localhost:5000/api/debug/routes")

    app.run(debug=True, host='0.0.0.0', port=5000)
