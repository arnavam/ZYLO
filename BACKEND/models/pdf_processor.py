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
        self.pages: int = 0
        self.current_pdf_path: str | None = None

    # --------------------------------------------------
    # LOAD & PARSE PDF
    # --------------------------------------------------
    def load_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Load a PDF file and extract all words with positions.
        Must be called BEFORE any highlighting.
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

    # --------------------------------------------------
    # WORD SELECTION
    # --------------------------------------------------
    def update_word_selection(self, word_ids: List[str], selected: bool = True):
        """
        Mark words as selected/unselected
        """
        word_id_set = set(word_ids)
        for w in self.words:
            if w["id"] in word_id_set:
                w["selected"] = selected

    def get_selected_words(self) -> List[Dict[str, Any]]:
        """
        Return all selected words
        """
        return [w for w in self.words if w["selected"]]

    # --------------------------------------------------
    # PRACTICE TRACKING
    # --------------------------------------------------
    def record_practice_result(self, word_id: str, success: bool):
        """
        Track reading/practice attempts per word
        """
        for w in self.words:
            if w["id"] == word_id:
                w["read_count"] += 1
                if success:
                    w["success_count"] += 1
                break

    # --------------------------------------------------
    # HIGHLIGHT WORDS IN PDF
    # --------------------------------------------------
    def highlight_words(self, word_ids: List[str], output_path: str):
        """
        Generate a new PDF with highlighted words
        """
        if not self.current_pdf_path:
            raise RuntimeError("No PDF loaded. Call load_pdf() first.")

        doc = fitz.open(self.current_pdf_path)
        word_map = {w["id"]: w for w in self.words}

        for wid in word_ids:
            w = word_map.get(wid)
            if not w:
                continue

            page = doc[w["page"]]
            rect = fitz.Rect(w["x0"], w["y0"], w["x1"], w["y1"])
            page.add_highlight_annot(rect)

        doc.save(output_path)

    # --------------------------------------------------
    # STATS
    # --------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics
        """
        total_words = len(self.words)
        selected_words = len(self.get_selected_words())
        practiced_words = len([w for w in self.words if w["read_count"] > 0])

        return {
            "total_words": total_words,
            "selected_words": selected_words,
            "practiced_words": practiced_words,
            "selection_percentage": (
                selected_words / total_words * 100 if total_words else 0
            )
        }
