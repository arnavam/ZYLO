import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

client = None
db = None

def init_db():
    global client, db
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/dyslexia_assistant')
    try:
        # Reduced timeout for faster error feedback in dev (increased to 5s for Atlas)
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Note: motor client creation is non-blocking. 
        # We can't easily check connection here without making this async.
        # Connection verification should happen in an async startup event.
        try:
            db = client.get_default_database()
        except Exception:
            # Fallback if URI doesn't have a database name
            db = client.get_database("dyslexia_assistant")
            
        print(f'[OK] Initialized Motor Client: {db.name}')
        return db
    except Exception as e:
        db = None
        print(f'[ERROR] Could not initialize Motor Client: {e}')
        return None

def get_db():
    global db
    if db is None:
        db = init_db()
    
    if db is None:
        raise ConnectionError("MongoDB is not running or accessible. Please ensure the MongoDB service is started.")
    return db

def get_users_collection():
    return get_db()['users']

def get_history_collection():
    return get_db()['history']
