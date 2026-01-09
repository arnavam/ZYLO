import speech_recognition as sr

r = sr.Recognizer()

with sr.AudioFile("test.wav") as source:
    audio = r.record(source)

try:
    text = r.recognize_google(audio)
    print("You said:", text)
except Exception as e:
    print("Error:", e)
