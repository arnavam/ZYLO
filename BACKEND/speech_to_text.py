import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.0  # Waits 1 second of silence to consider speech complete
recognizer.energy_threshold = 300  # Adjust microphone sensitivity if needed

with sr.Microphone() as source:
    print("Listening... Speak your sentence now!")
    recognizer.adjust_for_ambient_noise(source, duration=1)  # Short ambient noise calibration

    try:
        audio = recognizer.listen(source, timeout=None)  # Waits until you finish speaking
        text = recognizer.recognize_google(audio)
        print("You said:", text)

    except sr.WaitTimeoutError:
        print("No speech detected. Try speaking louder or check your mic.")
    except sr.UnknownValueError:
        print("Could not understand audio.")
    except sr.RequestError as e:
        print(f"Google Speech Recognition error: {e}")
