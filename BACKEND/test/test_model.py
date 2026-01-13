import os
import sys
import io
import time
import torch
import numpy as np
import soundfile as sf
import sounddevice as sd

# Add parent directory to path to import api_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set espeak library path for macOS homebrew
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "/opt/homebrew/lib/libespeak.dylib"

try:
    from api_server import PronunciationModel
except ImportError:
    print("Error: Could not import api_server. Make sure you are running this from the BACKEND/test directory.")
    sys.exit(1)

def record_audio(duration=5, fs=16000):
    print(f"\n[REC] Recording for {duration} seconds...")
    print("[REC] Speak now!")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    
    # Visual countdown
    for i in range(duration, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print("\n[REC] Done recording.")
    
    sd.wait()  # Wait until recording is finished
    
    # Convert to bytes
    buffer = io.BytesIO()
    sf.write(buffer, recording, fs, format='WAV')
    return buffer.getvalue()

def test_pronunciation(use_mic=False):
    print("=" * 40)
    print("   ZYLO Model Test Tool")
    print("=" * 40)
    
    # 1. Initialize Model
    model = PronunciationModel()
    
    # 2. Setup Data
    reference_text = input("\nEnter the sentence you will say: ").strip()
    if not reference_text:
        reference_text = "hello my name is alex"
        print(f"Using default: '{reference_text}'")

    if use_mic:
        audio_bytes = record_audio(duration=4)
        # Save for debug
        debug_path = os.path.join(os.path.dirname(__file__), "recorded_debug.wav")
        with open(debug_path, "wb") as f:
            f.write(audio_bytes)
        print(f"[DEBUG] Recorded audio saved to {debug_path}")
    else:
        # Fallback to file if specified or if mic fails
        audio_path = os.path.join(os.path.dirname(__file__), "user_audio.wav")
        if not os.path.exists(audio_path):
            audio_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_audio.wav")
            
        if os.path.exists(audio_path):
            print(f"\n[FILE] Using existing audio file: {audio_path}")
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
        else:
            print("[ERROR] No audio file found and microphone not selected.")
            return

    # 3. Evaluate
    print(f"\n[MODEL] Evaluating pronunciation...")
    try:
        result = model.evaluate(audio_bytes, reference_text)
        
        # 4. Print Results
        print("\n" + "-" * 20 + " RESULTS " + "-" * 20)
        print(f"Reference:    {result['reference_text']}")
        print(f"Recognized:   {result['spoken_text']}")
        print(f"Score:        {result['similarity_score']:.4f}")
        print(f"Status:       {result['status'].upper()}")
        print("-" * 49)
        print(f"Exp Ph:  {' '.join(result['expected_phonemes'])}")
        print(f"Spk Ph:  {' '.join(result['spoken_phonemes'])}")
        print("-" * 49 + "\n")
        
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test ZYLO pronunciation model")
    parser.add_argument("--mic", action="store_true", help="Use microphone to record audio")
    args = parser.parse_args()
    
    test_pronunciation(use_mic=args.mic)
