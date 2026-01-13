import os
import sys
import io
import time
import sounddevice as sd
import soundfile as sf
from phonemizer import phonemize

# Set espeak library path for macOS homebrew
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "/opt/homebrew/lib/libespeak.dylib"

def record_audio(duration=3, fs=16000):
    print(f"\nRecording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    print("Done recording.")
    return recording, fs

def test_recording_phonemes():
    print("--- Phonemizer Recording Test ---")
    
    # 1. Ask for text
    text = input("Enter what you will say: ").strip()
    if not text:
        text = "hello"
    
    # 2. Get expected phonemes
    try:
        expected_ph = phonemize(text, language="en-us", backend="espeak", strip=True)
        print(f"Expected phonemes for '{text}': {expected_ph}")
    except Exception as e:
        print(f"Phonemizer Error: {e}")
        return

    # 3. Record
    record = input("Press Enter to start recording... (or type 'skip' to use default file) ")
    if record.lower() != 'skip':
        audio, fs = record_audio()
        # In a real test, we would transcribe this using Wav2Vec2
        # But this script is just for testing phonemizer/recording logic
        print("Audio captured successfully.")
    else:
        print("Skipping recording.")

if __name__ == "__main__":
    test_recording_phonemes()
