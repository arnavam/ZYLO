import io
import numpy as np
import soundfile as sf

import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

from phonemizer import phonemize
from dtw import dtw


class Wav2Vec2PronunciationModel:

    def __init__(self, model_name="facebook/wav2vec2-base-960h"):
        print("Loading wav2vec2 model...")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        self.model.eval()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        print("Wav2vec2 ready")

    # ---------- AUDIO ----------
    def load_audio_from_bytes(self, audio_bytes):
        audio, sr = sf.read(io.BytesIO(audio_bytes))
        if len(audio.shape) > 1:
            audio = audio[:, 0]
        return audio, sr

    # ---------- ASR ----------
    def transcribe(self, audio):
        inputs = self.processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            logits = self.model(inputs.input_values.to(self.device)).logits

        pred_ids = torch.argmax(logits, dim=-1)
        text = self.processor.decode(pred_ids[0])

        return text.lower().strip()

    # ---------- PHONEMES ----------
    def word_to_phonemes(self, text):
        ph = phonemize(
            text,
            language="en-us",
            backend="espeak",
            strip=True
        )
        return ph.split()

    # ---------- PRONUNCIATION SCORE ----------
    def pronunciation_score(self, expected, spoken):
        exp_ph = self.word_to_phonemes(expected)
        spk_ph = self.word_to_phonemes(spoken)

        dist, _, _, _ = dtw(
            np.array(exp_ph).reshape(-1, 1),
            np.array(spk_ph).reshape(-1, 1),
            lambda x, y: 0 if x == y else 1
        )

        score = max(0, 1 - (dist / max(len(exp_ph), 1)))
        return round(score, 2), exp_ph, spk_ph

    # ---------- MAIN ENTRYPOINT ----------
    def evaluate(self, audio_bytes, expected_word):

        audio, _ = self.load_audio_from_bytes(audio_bytes)

        spoken_text = self.transcribe(audio)

        score, expected_ph, spoken_ph = self.pronunciation_score(
            expected_word,
            spoken_text
        )

        # thresholds — tune later
        if score >= 0.85:
            status = "correct"
            feedback = f"Great job — {expected_word} sounds clear."

        elif score >= 0.65:
            status = "almost"
            feedback = f"Good try — let's say {expected_word} again slowly."

        else:
            status = "mispronounced"
            feedback = f"The correct pronunciation is {expected_word}. Try again."

        return {
            "expected_word": expected_word,
            "spoken_text": spoken_text,
            "score": score,
            "status": status,
            "expected_phonemes": expected_ph,
            "spoken_phonemes": spoken_ph,
            "feedback": feedback
        }
