from datetime import datetime
from bson import ObjectId
from db import get_history_collection

class PdfHistory:
    """Model for managing PDF reading history and progress"""
    
    @staticmethod
    def add_to_history(user_id, pdf_name, pdf_path=None, total_pages=0, total_sentences=0, file_size=0):
        """Add a new entry to user's history"""
        history = get_history_collection()
        
        entry = {
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id,
            'pdf_name': pdf_name,
            'pdf_path': pdf_path,
            'total_pages': total_pages,
            'total_sentences': total_sentences,
            'file_size': file_size,
            'last_page': 1,
            'status': 'in_progress',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = history.insert_one(entry)
        return str(result.inserted_id)

    @staticmethod
    def get_user_history(user_id, limit=20):
        """Get history for a specific user with limit"""
        history = get_history_collection()
        cursor = history.find({'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id}).sort('updated_at', -1).limit(limit)
        
        results = []
        for entry in cursor:
            entry['id'] = str(entry.pop('_id'))
            entry['user_id'] = str(entry['user_id'])
            if 'created_at' in entry and isinstance(entry['created_at'], datetime):
                entry['created_at'] = entry['created_at'].isoformat()
            if 'updated_at' in entry and isinstance(entry['updated_at'], datetime):
                entry['updated_at'] = entry['updated_at'].isoformat()
            results.append(entry)
            
        return results

    @staticmethod
    def delete_from_history(history_id, user_id):
        """Delete a history entry"""
        history = get_history_collection()
        
        query = {
            '_id': ObjectId(history_id) if isinstance(history_id, str) else history_id,
            'user_id': ObjectId(user_id) if isinstance(user_id, str) else user_id
        }
        
        result = history.delete_one(query)
        return result.deleted_count > 0

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
