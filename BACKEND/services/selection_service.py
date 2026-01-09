# backend/services/selection_service.py
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from config import Config

class SelectionService:
    def __init__(self):
        self.selection_sessions = {}
    
    def create_selection_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new selection session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.selection_sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            **session_data
        }
        return session_id
    
    def get_selection_session(self, session_id: str) -> Dict[str, Any]:
        """Get a selection session by ID"""
        return self.selection_sessions.get(session_id)
    
    def update_selection_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update a selection session"""
        if session_id in self.selection_sessions:
            self.selection_sessions[session_id].update(updates)
            self.selection_sessions[session_id]['updated_at'] = datetime.now().isoformat()
            return True
        return False
    
    def save_selections_to_file(self, session_id: str, filename: str = None) -> str:
        """Save selections to a JSON file"""
        if session_id not in self.selection_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        if not filename:
            filename = f"selections_{session_id}"
        
        session_data = self.selection_sessions[session_id]
        
        save_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'pdf_info': {
                'original_filename': session_data.get('pdf_filename'),
                'total_sentences': session_data.get('total_sentences'),
                'total_pages': session_data.get('total_pages')
            },
            'selections': {
                'selected_sentences': session_data.get('selected_sentences', []),
                'customized_sentences': session_data.get('customized_sentences', []),
                'selection_count': len(session_data.get('selected_sentences', [])),
                'customization_count': len(session_data.get('customized_sentences', []))
            },
            'practice_stats': session_data.get('practice_stats', {})
        }
        
        file_path = os.path.join(Config.SELECTIONS_FOLDER, f"{filename}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def load_selections_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load selections from a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Create a new session from loaded data
            session_id = loaded_data.get('session_id', datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            self.selection_sessions[session_id] = {
                'id': session_id,
                'loaded_from': file_path,
                'loaded_at': datetime.now().isoformat(),
                'pdf_filename': loaded_data.get('pdf_info', {}).get('original_filename'),
                'total_sentences': loaded_data.get('pdf_info', {}).get('total_sentences'),
                'total_pages': loaded_data.get('pdf_info', {}).get('total_pages'),
                'selected_sentences': loaded_data.get('selections', {}).get('selected_sentences', []),
                'customized_sentences': loaded_data.get('selections', {}).get('customized_sentences', []),
                'practice_stats': loaded_data.get('practice_stats', {})
            }
            
            return {
                'session_id': session_id,
                'loaded_data': loaded_data
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to load selections: {e}")
    
    def get_all_saved_sessions(self) -> List[Dict[str, Any]]:
        """Get list of all saved selection sessions"""
        try:
            saved_sessions = []
            
            for filename in os.listdir(Config.SELECTIONS_FOLDER):
                if filename.endswith('.json'):
                    file_path = os.path.join(Config.SELECTIONS_FOLDER, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        saved_sessions.append({
                            'filename': filename,
                            'file_path': file_path,
                            'session_id': data.get('session_id'),
                            'timestamp': data.get('timestamp'),
                            'pdf_filename': data.get('pdf_info', {}).get('original_filename'),
                            'selection_count': data.get('selections', {}).get('selection_count', 0),
                            'customization_count': data.get('selections', {}).get('customization_count', 0)
                        })
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")
                        continue
            
            # Sort by timestamp, newest first
            saved_sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return saved_sessions
            
        except Exception as e:
            raise RuntimeError(f"Failed to list saved sessions: {e}")
    
    def delete_saved_session(self, file_path: str) -> bool:
        """Delete a saved selection session"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Failed to delete session: {e}")
    
    def analyze_selection_patterns(self, session_id: str) -> Dict[str, Any]:
        """Analyze patterns in selected sentences"""
        if session_id not in self.selection_sessions:
            return {}
        
        session = self.selection_sessions[session_id]
        selected_sentences = session.get('selected_sentences', [])
        
        if not selected_sentences:
            return {}
        
        # Analyze by page distribution
        page_distribution = {}
        for sentence in selected_sentences:
            page = sentence.get('page', 0)
            page_distribution[page] = page_distribution.get(page, 0) + 1
        
        # Analyze sentence lengths
        sentence_lengths = [len(sentence.get('text', '')) for sentence in selected_sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        # Analyze customization rate
        total_customized = len(session.get('customized_sentences', []))
        customization_rate = (total_customized / len(selected_sentences)) * 100 if selected_sentences else 0
        
        return {
            'total_selected': len(selected_sentences),
            'page_distribution': page_distribution,
            'average_sentence_length': round(avg_length, 2),
            'customization_rate': round(customization_rate, 2),
            'pages_covered': len(page_distribution),
            'concentration_ratio': len(selected_sentences) / len(page_distribution) if page_distribution else 0
        }
    
    def export_selections_report(self, session_id: str, export_format: str = 'json') -> str:
        """Export selections as a comprehensive report"""
        if session_id not in self.selection_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.selection_sessions[session_id]
        analysis = self.analyze_selection_patterns(session_id)
        
        report_data = {
            'export_timestamp': datetime.now().isoformat(),
            'session_info': {
                'session_id': session_id,
                'pdf_filename': session.get('pdf_filename'),
                'created_at': session.get('created_at'),
                'total_sentences_available': session.get('total_sentences'),
                'total_pages': session.get('total_pages')
            },
            'selection_analysis': analysis,
            'selected_sentences': session.get('selected_sentences', []),
            'customized_sentences': session.get('customized_sentences', []),
            'practice_history': session.get('practice_stats', {})
        }
        
        if export_format == 'json':
            filename = f"report_{session_id}.json"
            file_path = os.path.join(Config.SELECTIONS_FOLDER, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return file_path
        
        else:
            raise ValueError(f"Unsupported export format: {export_format}")