import pyttsx3

# initialize the engine
engine = pyttsx3.init()

# change the speech rate
rate = engine.getProperty('rate')      # get current speed
engine.setProperty('rate', rate - 100) # reduce speed by 100 (you can adjust)

# optional: choose voice (male/female)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # 0=male, 1=female

# get text input
text = input("Enter something to speak: ")

# speak
engine.say(text)
engine.runAndWait()
