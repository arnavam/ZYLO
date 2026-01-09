import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

fs = 16000
seconds = 3

print("Speak now...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()

write("test.wav", fs, audio)
print("Saved test.wav (PCM format)")
