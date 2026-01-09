import fitz  # PyMuPDF
import pdfplumber
import uuid
from typing import List, Dict, Any


class PDFProcessor:
    """
    Full PDF reader backend:
    - Extracts every word with exact coordinates
    - Supports word selection
    - Generates highlighted PDF
    - Tracks practice statistics
    """

    def __init__(self):
        self.words: List[Dict[str, Any]] = []
        self.sentences: List[Dict[str, Any]] = []
        self.page_texts: List[str] = []
        self.pages: int = 0
        self.current_pdf_path: str | None = None

    # --------------------------------------------------
    # LOAD & PARSE PDF
    # --------------------------------------------------
    def load_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Load a PDF file and extract all words with positions.
        """
        self.words = []
        self.pages = 0
        self.current_pdf_path = pdf_path

        with pdfplumber.open(pdf_path) as pdf:
            self.pages = len(pdf.pages)

            for page_number, page in enumerate(pdf.pages):
                extracted_words = page.extract_words(
                    use_text_flow=True,
                    keep_blank_chars=False
                )

                for w in extracted_words:
                    self.words.append({
                        "id": str(uuid.uuid4()),
                        "text": w["text"],
                        "page": page_number,
                        "x0": w["x0"],
                        "y0": w["top"],
                        "x1": w["x1"],
                        "y1": w["bottom"],
                        "selected": False,
                        "read_count": 0,
                        "success_count": 0
                    })

        return self.words

    def extract_text_with_positions(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF and split into sentences with page/line info.
        This matches the structure expected by the frontend.
        """
        self.sentences = []
        self.page_texts = []
        self.current_pdf_path = pdf_path
        
        import re
        
        with pdfplumber.open(pdf_path) as pdf:
            self.pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                self.page_texts.append(text)
                
                # Simple sentence splitting
                # In a real app, use nltk or spacy for better sentence segmentation
                raw_sentences = re.split(r'(?<=[.!?])\s+', text)
                
                line_in_page = 1
                for s_text in raw_sentences:
                    s_text = s_text.strip()
                    if len(s_text) > 5:  # Ignore very short fragments
                        self.sentences.append({
                            'text': s_text,
                            'page': page_num + 1,
                            'line': line_in_page,
                            'selected': False,
                            'global_index': len(self.sentences)
                        })
                        line_in_page += 1
                        
        return self.sentences

    # --------------------------------------------------
    # SENTENCE SELECTION & MANAGEMENT
    # --------------------------------------------------
    def update_sentence_selection(self, sentence_indices: List[int], selected: bool = True):
        """Mark specific sentences as selected/unselected by their global index"""
        for idx in sentence_indices:
            if 0 <= idx < len(self.sentences):
                self.sentences[idx]['selected'] = selected

    def get_selected_sentences(self) -> List[Dict[str, Any]]:
        """Return all selected sentences"""
        return [s for s in self.sentences if s.get('selected')]

    def update_sentence_text(self, index: int, new_text: str):
        """Update the text of a sentence (customization)"""
        if 0 <= index < len(self.sentences):
            self.sentences[index]['text'] = new_text

    # --------------------------------------------------
    # STATS
    # --------------------------------------------------
    def get_sentence_stats(self) -> Dict[str, Any]:
        """Get statistics for sentences"""
        total = len(self.sentences)
        selected = len(self.get_selected_sentences())
        
        return {
            'total_sentences': total,
            'selected_sentences': selected,
            'completion_rate': (selected / total * 100) if total > 0 else 0,
            'total_pages': self.pages
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get overall word-level statistics"""
        total_words = len(self.words)
        selected_words = len([w for w in self.words if w.get("selected")])
        practiced_words = len([w for w in self.words if w.get("read_count", 0) > 0])

        return {
            "total_words": total_words,
            "selected_words": selected_words,
            "practiced_words": practiced_words,
            "selection_percentage": (
                selected_words / total_words * 100 if total_words else 0
            )
        }
