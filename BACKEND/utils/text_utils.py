# backend/utils/text_utils.py
import re
from typing import List

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:]', '', text)
    
    return text.strip()

def calculate_readability_score(text: str) -> float:
    """Calculate simple readability score (higher = easier to read)"""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    
    if not words or not sentences:
        return 0
    
    avg_sentence_length = len(words) / len(sentences)
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    # Simple scoring - shorter sentences and words = easier to read
    readability = 100 - (avg_sentence_length * 2 + avg_word_length * 10)
    return max(0, min(100, readability))

def split_into_chunks(text: str, max_chunk_size: int = 200) -> List[str]:
    """Split text into manageable chunks"""
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > max_chunk_size:
            chunks.append(' '.join(current_chunk[:-1]))
            current_chunk = [word]
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks