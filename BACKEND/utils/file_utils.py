# backend/utils/file_utils.py
import os
import shutil
from typing import List

def ensure_directory(path: str):
    """Ensure a directory exists, create if it doesn't"""
    os.makedirs(path, exist_ok=True)

def safe_delete_file(file_path: str):
    """Safely delete a file if it exists"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except:
        pass
    return False

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def list_files_in_directory(directory: str, extensions: List[str] = None) -> List[str]:
    """List files in directory with optional extension filter"""
    if not os.path.exists(directory):
        return []
    
    files = []
    for filename in os.listdir(directory):
        if extensions:
            if any(filename.lower().endswith(ext.lower()) for ext in extensions):
                files.append(filename)
        else:
            files.append(filename)
    
    return files