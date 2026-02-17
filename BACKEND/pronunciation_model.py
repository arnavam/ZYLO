import io
import os
import numpy as np
import torch
import soundfile as sf
from typing import Optional, List, Dict, Any, Tuple
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from dtw import dtw
from phonemizer import phonemize

class PronunciationModel:
    """
    Wav2Vec2-based pronunciation scoring using:
    1. Phoneme-output model for direct IPA transcription from audio
    2. Frame-level logits for phoneme probability extraction
    3. DTW alignment on phoneme sequences
    4. Phoneme Error Rate (PER) calculation
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Use phoneme-output model (outputs IPA directly from audio)
        # This model outputs phonemes like /f/ /ɑ/ /k/ /s/ instead of letters
        print("[MODEL] Loading Wav2Vec2 Phoneme Model...")
        model_name = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
        
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        self.model.eval()

        # Check for MPS (Apple Silicon) or CUDA
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
            
        self.model.to(self.device)

        print(f"[MODEL] Wav2Vec2 Phoneme Model ready on {self.device}")
        self._initialized = True

    def load_audio(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Load and normalize audio from bytes."""
        audio, sr = sf.read(io.BytesIO(audio_bytes))
        if len(audio.shape) > 1:
            audio = audio[:, 0]  # Convert to mono
        
        # Peak normalization
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
            
        return audio, sr

    def get_phoneme_logits(self, audio: np.ndarray) -> Tuple[torch.Tensor, str]:
        """
        Extract frame-level phoneme logits from audio.
        Returns: (logits tensor, predicted phoneme sequence)
        """
        inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            outputs = self.model(inputs.input_values.to(self.device))
            logits = outputs.logits  # Shape: [batch, frames, vocab_size]
        
        # Get predicted phoneme IDs
        pred_ids = torch.argmax(logits, dim=-1)
        
        # Decode to phoneme string
        phoneme_str = self.processor.decode(pred_ids[0])
        
        return logits, phoneme_str

    def audio_to_phonemes(self, audio: np.ndarray) -> List[str]:
        """Extract phoneme sequence directly from audio using the phoneme model."""
        _, phoneme_str = self.get_phoneme_logits(audio)
        # Clean up and split into individual phonemes
        phonemes = phoneme_str.strip().split()
        return [p for p in phonemes if p]  # Remove empty strings

    def text_to_phonemes(self, text: str) -> List[str]:
        """Convert reference text to phonemes using espeak."""
        ph = phonemize(text, language="en-us", backend="espeak", strip=True)
        return ph.split()

    def compute_phoneme_error_rate(self, reference: List[str], hypothesis: List[str]) -> float:
        """
        Compute Phoneme Error Rate (PER) using edit distance.
        PER = (substitutions + deletions + insertions) / len(reference)
        Returns: Error rate (0.0 = perfect, 1.0 = completely wrong)
        """
        if not reference:
            return 1.0 if hypothesis else 0.0
        
        # Dynamic programming for edit distance
        m, n = len(reference), len(hypothesis)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if reference[i-1] == hypothesis[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        edit_distance = dp[m][n]
        per = edit_distance / len(reference)
        return min(per, 1.0)  # Cap at 1.0

    def compute_dtw_similarity(self, expected_ph: List[str], spoken_ph: List[str]) -> float:
        """Compute similarity using DTW alignment on phoneme sequences."""
        if not expected_ph or not spoken_ph:
            return 0.0
        
        alignment = dtw(
            np.array(expected_ph).reshape(-1, 1),
            np.array(spoken_ph).reshape(-1, 1),
            lambda x, y: 0 if x == y else 1,
        )
        dist = alignment.distance
        return round(max(0, 1 - (dist / max(len(expected_ph), 1))), 4)

    # =========================================================================
    # APPROACH 2: Probability/Logit Comparison (TTS-based)
    # =========================================================================
    
    def text_to_audio(self, text: str) -> np.ndarray:
        """
        Generate audio from text using eSpeak TTS.
        Returns audio as numpy array at 16kHz.
        """
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Use espeak to generate audio file
            subprocess.run(
                ["espeak", "-w", tmp_path, "-s", "150", text],
                check=True,
                capture_output=True
            )
            
            # Read the generated audio
            audio, sr = sf.read(tmp_path)
            
            # Convert to mono if needed
            if len(audio.shape) > 1:
                audio = audio[:, 0]
            
            # Resample to 16kHz if needed (espeak outputs at 22050Hz by default)
            if sr != 16000:
                from scipy import signal
                num_samples = int(len(audio) * 16000 / sr)
                audio = signal.resample(audio, num_samples)
            
            return audio.astype(np.float32)
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def get_frame_probabilities(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract frame-level phoneme probability distributions from audio.
        Returns: numpy array of shape [num_frames, vocab_size]
        """
        inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            outputs = self.model(inputs.input_values.to(self.device))
            logits = outputs.logits  # [batch, frames, vocab_size]
        
        # Apply softmax to get probabilities
        probs = torch.nn.functional.softmax(logits, dim=-1)
        
        return probs[0].cpu().numpy()  # [frames, vocab_size]

    def compare_probability_sequences(self, ref_probs: np.ndarray, user_probs: np.ndarray) -> float:
        """
        Compare two probability sequences using DTW + cosine similarity.
        
        Args:
            ref_probs: Reference audio probabilities [frames_ref, vocab_size]
            user_probs: User audio probabilities [frames_user, vocab_size]
        
        Returns:
            Similarity score (0.0 - 1.0)
        """
        from scipy.spatial.distance import cosine
        
        # Use DTW to align frames
        # Distance function: 1 - cosine_similarity (so 0 = identical, 1 = orthogonal)
        def cosine_dist(x, y):
            return cosine(x.flatten(), y.flatten())
        
        alignment = dtw(ref_probs, user_probs, dist=cosine_dist)
        
        # Normalized distance to similarity
        # alignment.distance is sum of distances along path
        # Normalize by path length
        path_length = len(alignment.index1)
        avg_dist = alignment.distance / path_length if path_length > 0 else 1.0
        
        # Convert distance (0-1) to similarity (1-0)
        similarity = max(0, 1 - avg_dist)
        
        return round(similarity, 4)

    def evaluate(self, audio_bytes: bytes, reference_text: str) -> Dict[str, Any]:
        """
        Main evaluation: compare user audio against reference text.
        
        Uses TWO approaches:
        1. Symbol Comparison: Compare decoded phoneme sequences (robust to speaker)
        2. Probability Comparison: Compare frame-level logits via TTS (more detailed)
        """
        audio, _ = self.load_audio(audio_bytes)
        
        # =====================================================================
        # APPROACH 1: Symbol-based comparison
        # =====================================================================
        spoken_phonemes = self.audio_to_phonemes(audio)
        expected_phonemes = self.text_to_phonemes(reference_text)
        
        dtw_similarity = self.compute_dtw_similarity(expected_phonemes, spoken_phonemes)
        per = self.compute_phoneme_error_rate(expected_phonemes, spoken_phonemes)
        
        symbol_score = round(dtw_similarity * (1 - per * 0.3), 4)
        symbol_score = max(0, min(1, symbol_score))
        
        # =====================================================================
        # APPROACH 2: Probability-based comparison (TTS)
        # =====================================================================
        try:
            # Generate TTS audio from reference text
            ref_audio = self.text_to_audio(reference_text)
            
            # Get frame-level probabilities for both audios
            ref_probs = self.get_frame_probabilities(ref_audio)
            user_probs = self.get_frame_probabilities(audio)
            
            # Compare probability sequences
            prob_score = self.compare_probability_sequences(ref_probs, user_probs)
        except Exception as e:
            print(f"[WARN] Probability comparison failed: {e}")
            prob_score = None
        
        # =====================================================================
        # COMBINED SCORE
        # =====================================================================
        if prob_score is not None:
            # Weight: 60% probability-based, 40% symbol-based
            combined_score = round(0.6 * prob_score + 0.4 * symbol_score, 4)
        else:
            combined_score = symbol_score
        
        # Determine status
        if combined_score >= 0.75:
            status = "correct"
        elif combined_score >= 0.50:
            status = "almost"
        else:
            status = "mispronounced"

        return {
            "reference_text": reference_text,
            "spoken_text": " ".join(spoken_phonemes),
            "expected_phonemes": expected_phonemes,
            "spoken_phonemes": spoken_phonemes,
            "similarity_score": combined_score,
            "symbol_score": symbol_score,
            "probability_score": prob_score,
            "dtw_score": dtw_similarity,
            "phoneme_error_rate": round(per, 4),
            "status": status,
        }

# Lazy model loader
_model: Optional[PronunciationModel] = None

def get_model() -> PronunciationModel:
    global _model
    if _model is None:
        _model = PronunciationModel()
    return _model
