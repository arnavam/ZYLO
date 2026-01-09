import sys
import os
import unittest
from unittest.mock import MagicMock

# Mocking modules that might fail to import or initialize
mock_modules = ['pyttsx3', 'speech_recognition', 'PyPDF2', 'pyaudio']
for module in mock_modules:
    sys.modules[module] = MagicMock()

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'BACKEND'))

from services.speech_service import SpeechService

def test_pronunciation_logic():
    # Initialize service with mocks
    service = SpeechService()
    
    # Test cases: (original, spoken, expected_statuses)
    test_cases = [
        (
            "The quick brown fox",
            "The quick brown fox",
            ['correct', 'correct', 'correct', 'correct']
        ),
        (
            "The quick brown fox",
            "The quick fox",
            ['correct', 'correct', 'missed', 'correct']
        ),
        (
            "dyslexia",
            "dislexia",
            ['mispronounced']
        )
    ]
    
    print("Running Pronunciation Logic Tests...\n")
    
    for original, spoken, expected in test_cases:
        feedback = service._get_word_level_feedback(original, spoken)
        actual = [f['status'] for f in feedback]
        
        print(f"Original: {original}")
        print(f"Spoken:   {spoken}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        
        assert actual == expected, f"Failed! Expected {expected} but got {actual}"
        print("PASS\n")

if __name__ == "__main__":
    try:
        test_pronunciation_logic()
        print("All backend logic tests passed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
