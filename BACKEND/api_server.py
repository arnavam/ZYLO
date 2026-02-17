"""
Simplified FastAPI backend for phoneme-based pronunciation scoring.

Endpoints:
- POST /auth/register  - Register new user
- POST /auth/login     - Login and get JWT token
- GET  /auth/me        - Get current user (protected)
- POST /score          - Score pronunciation (audio + text)
- WS   /ws/score       - Stream audio for real-time scoring
"""

import io
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import numpy as np
import torch
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from phonemizer import phonemize
from pydantic import BaseModel, EmailStr
from db import get_users_collection
import soundfile as sf
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from dtw import dtw
from pronunciation_model import get_model

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "zylo-jwt-secret-key-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 1

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/dyslexia_assistant")

@app.on_event("startup")
async def startup_db_client():
    from db import init_db
    init_db()


# =============================================================================
# AUTH HELPERS
# =============================================================================

security = HTTPBearer()


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, password_hash: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")




# =============================================================================
# SCHEMAS
# =============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    access_token: Optional[str] = None


class UserResponse(BaseModel):
    success: bool
    user: dict


class ScoreResponse(BaseModel):
    reference_text: str
    spoken_text: str
    expected_phonemes: list[str]
    spoken_phonemes: list[str]
    similarity_score: float  # Combined score
    symbol_score: float      # Approach 1: Symbol comparison
    probability_score: Optional[float]  # Approach 2: Probability comparison (may be None)
    dtw_score: float
    phoneme_error_rate: float
    status: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="ZYLO Pronunciation Scorer",
    description="Phoneme-based pronunciation scoring with Wav2Vec2 + Auth",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@app.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """Register a new user."""
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    users = get_users_collection()

    if await users.find_one({"email": req.email.lower()}):
        raise HTTPException(status_code=409, detail="Email already registered")

    user_doc = {
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "name": req.name,
        "created_at": datetime.utcnow(),
    }
    result = await users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token(str(user_doc["_id"]))

    return {
        "success": True,
        "message": "Account created successfully",
        "user": {"id": str(user_doc["_id"]), "email": user_doc["email"], "name": user_doc["name"]},
        "access_token": token,
    }


@app.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login and receive JWT token."""
    users = get_users_collection()
    user = await users.find_one({"email": req.email.lower()})

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user["_id"]))

    return {
        "success": True,
        "message": "Login successful",
        "user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]},
        "access_token": token,
    }


@app.get("/auth/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user_id)):
    """Get current authenticated user."""
    users = get_users_collection()
    user = await users.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "user": {"id": str(user["_id"]), "email": user["email"], "name": user["name"]},
    }


@app.post("/auth/logout")
async def logout():
    """Logout (client removes token)."""
    return {"success": True, "message": "Logged out successfully"}


# =============================================================================
# PRONUNCIATION SCORING ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health."""
    return {"status": "healthy", "model_loaded": _model is not None}


@app.post("/score", response_model=ScoreResponse)
async def score_pronunciation(
    audio: UploadFile = File(..., description="Audio file (WAV recommended)"),
    text: str = Form(..., description="Reference text"),
):
    """
    Score pronunciation by comparing audio against reference text.

    Returns phoneme-level similarity score (0.0 - 1.0).
    """
    audio_bytes = await audio.read()
    model = get_model()
    return model.evaluate(audio_bytes, text)


@app.websocket("/ws/score")
async def websocket_score(websocket: WebSocket):
    """
    WebSocket for streaming pronunciation scoring.

    Protocol:
    1. Connect
    2. Send JSON: {"text": "reference text"}
    3. Send binary audio data
    4. Receive JSON score result
    5. Repeat or close
    """
    await websocket.accept()
    model = get_model()

    try:
        while True:
            text_msg = await websocket.receive_json()
            reference_text = text_msg.get("text", "")

            if not reference_text:
                await websocket.send_json({"error": "No reference text provided"})
                continue

            audio_bytes = await websocket.receive_bytes()

            try:
                result = model.evaluate(audio_bytes, reference_text)
                await websocket.send_json(result)
            except Exception as e:
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")
        await websocket.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  ZYLO Pronunciation Scorer API")
    print("=" * 60)
    print()
    print("Auth Endpoints:")
    print("  POST /auth/register  - Create account")
    print("  POST /auth/login     - Get JWT token")
    print("  GET  /auth/me        - Current user (protected)")
    print()
    print("Scoring Endpoints:")
    print("  GET  /health         - Health check")
    print("  POST /score          - Score pronunciation")
    print("  WS   /ws/score       - WebSocket streaming")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)
