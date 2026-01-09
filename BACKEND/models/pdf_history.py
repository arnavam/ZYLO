from datetime import datetime
from bson import ObjectId
from db import get_history_collection

class PdfHistory:
    """Model for managing PDF reading history and progress"""
    
    @staticmethod
    def create_history(user_id, document_id, filename, total_pages):
        """Create a new history entry"""
        history = get_history_collection()
        
        entry = {
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,
            'document_id': document_id,
            'filename': filename,
            'total_pages': total_pages,
            'last_page': 1,
            'status': 'in_progress',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = history.insert_one(entry)
        return str(result.inserted_id)

    @staticmethod
    def get_user_history(user_id):
        """Get all history for a specific user"""
        history = get_history_collection()
        cursor = history.find({'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id}).sort('updated_at', -1)
        
        results = []
        for entry in cursor:
            entry['id'] = str(entry.pop('_id'))
            entry['user_id'] = str(entry['user_id'])
            entry['created_at'] = entry['created_at'].isoformat()
            entry['updated_at'] = entry['updated_at'].isoformat()
            results.append(entry)
            
        return results

    @staticmethod
    def update_progress(history_id, user_id, last_page):
        """Update progress for a document"""
        history = get_history_collection()
        
        query = {
            '_id': ObjectId(history_id) if isinstance(history_id, str) else history_id,
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id
        }
        
        update = {
            '$set': {
                'last_page': last_page,
                'updated_at': datetime.utcnow()
            }
        }
        
        result = history.update_one(query, update)
        return result.modified_count > 0
