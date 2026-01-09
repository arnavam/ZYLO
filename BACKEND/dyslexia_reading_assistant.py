# dyslexia_reading_assistant.py
import time
from difflib import SequenceMatcher

import pyttsx3
import speech_recognition as sr

# -------- TTS helpers --------
def init_tts(rate=150):
    eng = pyttsx3.init()
    eng.setProperty("rate", rate)  # slower helps dyslexia-friendly pacing
    return eng

engine = init_tts()

def speak(text: str):
    """Speak text reliably each time."""
    engine.stop()          # clear any stuck/queued speech
    engine.say(text)
    engine.runAndWait()    # BLOCKS until finished speaking

# -------- STT helpers --------
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.0     # 1s of silence = end of sentence

def listen_once(calibrate_seconds=0.8):
    """Listen to the mic once, waiting until the user finishes the sentence."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=calibrate_seconds)
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)
    return audio

def transcribe(audio):
    try:
        return recognizer.recognize_google(audio)  # requires internet
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        raise RuntimeError(f"Speech service error: {e}")

def sim(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

# -------- Content to practice (one sentence per line) --------
TEXT = """
The quick brown fox jumps over the lazy dog.
Reading is fun and helps improve your skills.
Practice makes perfect for everyone.
"""

sentences = [s.strip() for s in TEXT.splitlines() if s.strip()]

# -------- Main loop --------
for idx, sentence in enumerate(sentences, 1):
    while True:
        print(f"\n[{idx}/{len(sentences)}] Target: {sentence}")
        speak(sentence)                # 1) system reads the sentence
        time.sleep(0.2)                # tiny gap before listening

        print("Your turn—please repeat the sentence.")
        try:
            audio = listen_once(calibrate_seconds=0.8)
            spoken = transcribe(audio)
        except RuntimeError as e:
            print(e)
            speak("There was a problem with the speech service. Please check your internet and try again.")
            # Fail this sentence gracefully and continue to next
            break

        if not spoken:
            print("Didn't catch that.")
            speak("I didn't catch that. Let's try again.")
            continue

        print("You said:", spoken)
        score = sim(sentence, spoken)
        print(f"Similarity: {score:.1%}")

        if score >= 0.90:              # threshold: tune as needed
            print("Feedback: Correct ✅")
            speak("Correct.")
            break                       # go to next sentence
        else:
            print("Feedback: Incorrect ❌  (will repeat your version, then retry)")
            # 2) ALWAYS speak feedback
            speak("Incorrect.")
            # 3) Repeat the user's incorrect attempt via TTS
            speak("You said:")
            speak(spoken)
            speak("Please try again.")
            # loop continues to retry the SAME sentence

print("\nSession complete. Great job!")
