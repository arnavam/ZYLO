# backend/services/pdf_service.py
import os
import json
from datetime import datetime
from typing import Dict, Any
from config import Config

class PDFService:
    def __init__(self):
        self.selections = {}
    
    def save_selections(self, selections_data: Dict[str, Any], filename: str = None) -> str:
        """Save sentence selections to a JSON file"""
        try:
            if not filename:
                filename = f"selections_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'selections': selections_data,
                'total_sentences': len(selections_data.get('sentences', [])),
                'selected_count': len([s for s in selections_data.get('sentences', []) if s.get('selected')])
            }
            
            file_path = os.path.join(Config.SELECTIONS_FOLDER, f"{filename}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            return file_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to save selections: {e}")
    
    def load_selections(self, file_path: str) -> Dict[str, Any]:
        """Load sentence selections from a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            return loaded_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to load selections: {e}")
    
    def get_saved_selections(self) -> List[Dict[str, Any]]:
        """Get list of all saved selection files"""
        try:
            selection_files = []
            
            for filename in os.listdir(Config.SELECTIONS_FOLDER):
                if filename.endswith('.json'):
                    file_path = os.path.join(Config.SELECTIONS_FOLDER, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        selection_files.append({
                            'filename': filename,
                            'file_path': file_path,
                            'timestamp': data.get('timestamp'),
                            'total_sentences': data.get('total_sentences', 0),
                            'selected_count': data.get('selected_count', 0)
                        })
                    except:
                        continue
            
            # Sort by timestamp, newest first
            selection_files.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return selection_files
            
        except Exception as e:
            raise RuntimeError(f"Failed to list selections: {e}")