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
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client.get_database()
        print(f'[OK] Connected to MongoDB: {db.name}')
    except Exception as e:
        print(f'[ERROR] Could not connect to MongoDB: {e}')

def get_db():
    global db
    if db is None:
        init_db()
    return db

def get_users_collection():
    return get_db()['users']

def get_history_collection():
    return get_db()['history']
