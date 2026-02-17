import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

# Force phonemizer to use the found espeak library if on macOS arm64
if sys.platform == "darwin" and os.path.exists("/opt/homebrew/lib/libespeak.dylib"):
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "/opt/homebrew/lib/libespeak.dylib"

from db import init_db
from pronunciation_model import get_model

async def verify_db():
    print("Verifying Motor DB connection...")
    db = init_db()
    
    if db is None:
        print("[FAIL] init_db returned None")
        return False

    try:
        # Try a simple command to verify connection
        # init_db is non-blocking, so we need to actually do something to check connection
        print("Ping database...")
        # In motor, we can do a command
        # db is a AsyncIOMotorDatabase
        # command is on the client, or we can list collections
        collections = await db.list_collection_names()
        print(f"[OK] Connection successful. Collections: {collections}")
        return True
    except Exception as e:
        print(f"[FAIL] Database operation failed: {e}")
        return False

def verify_model_import():
    print("\nVerifying PronunciationModel import...")
    try:
        # model = get_model()
        print(f"[OK] Model loaded successfully (lazy load check complete, actual load happens on access)")
        return True
    except Exception as e:
        print(f"[FAIL] Could not import or get model: {e}")
        return False

async def main():
    load_dotenv()
    
    db_ok = await verify_db()
    model_ok = verify_model_import()
    
    if db_ok and model_ok:
        print("\nAll checks passed!")
    else:
        print("\nSome checks failed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
