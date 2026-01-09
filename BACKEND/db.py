import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = None
db = None

def init_db():
    global client, db
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/dyslexia_assistant')
    try:
        # Reduced timeout for faster error feedback in dev
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.server_info()
        db = client.get_database()
        print(f'[OK] Connected to MongoDB: {db.name}')
        return db
    except Exception as e:
        db = None
        print(f'[ERROR] Could not connect to MongoDB: {e}')
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
