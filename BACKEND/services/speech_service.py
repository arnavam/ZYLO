# backend/services/speech_service.py
import pyttsx3
import speech_recognition as sr
from difflib import SequenceMatcher
import time
import re
import PyPDF2
import io
from config import Config
import torch
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Global model instance
_wav2vec2_processor = None
_wav2vec2_model = None

def load_wav2vec2_model():
    global _wav2vec2_processor, _wav2vec2_model
    if _wav2vec2_model is None:
        try:
            print("[INIT] Loading Wav2Vec2 model...")
            from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
            _wav2vec2_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
            _wav2vec2_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
            print("[INIT] Wav2Vec2 model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load Wav2Vec2: {e}")

class SpeechService:
    def __init__(self):
        # Initialize model if not already loaded
        if _wav2vec2_model is None:
            load_wav2vec2_model()
            
        self.engine = self._init_tts()
        self.recognizer = sr.Recognizer()
        self._configure_recognizer()
        self.microphone_available = self._check_microphone()
        self.current_sentence_index = 0
        self.sentences = []
        self.correct_count = 0
        self.total_practiced = 0
        self.is_reading = False
        self.current_pdf = None
        
        # Use global instances
        self.processor = _wav2vec2_processor
        self.model = _wav2vec2_model
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', Config.SPEECH_RATE)
            return engine
        except Exception as e:
            print(f"Warning: TTS initialization failed: {e}")
            return None
    
    def _check_microphone(self):
        """Check if microphone is available"""
        try:
            with sr.Microphone() as source:
                return True
        except:
            print("Warning: Microphone not available. Speech recognition will be disabled.")
            return False
    
    def _configure_recognizer(self):
        """Configure speech recognition settings"""
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.5
        self.recognizer.energy_threshold = 300

    def extract_text_from_pdf(self, pdf_file) -> list:
        """Extract text from PDF and split into sentences line by line"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            all_sentences = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                
                # Split by lines first, then by sentences within each line
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines):
                    line = line.strip()
                    if line:  # Only process non-empty lines
                        # Split each line into sentences
                        sentences_in_line = self._split_into_sentences(line)
                        
                        for sentence in sentences_in_line:
                            if sentence and len(sentence.strip()) > 5:  # Minimum length
                                all_sentences.append({
                                    'text': sentence.strip(),
                                    'page': page_num,
                                    'line': line_num,
                                    'original_line': line
                                })
            
            print(f"[PDF] Extracted {len(all_sentences)} sentences from PDF")
            return all_sentences
            
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return []

    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences using multiple delimiters"""
        # Improved regex to handle common abbreviations and maintain sentence integrity
        # Split by . ! ? followed by whitespace, but avoid splitting on common abbreviations
        text = text.replace('\n', ' ').strip()
        sentence_endings = re.compile(r'(?<!\b(?:Mr|Mrs|Ms|Dr|Jr|Sr|vs|Prof|St|i\.e|e\.g)\.)(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)
        
        # Filter out empty sentences and short fragments
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
        
        return sentences

    def start_practice_from_pdf(self, pdf_file):
        """Start a new practice session from PDF"""
        self.sentences = self.extract_text_from_pdf(pdf_file)
        self.current_sentence_index = 0
        self.correct_count = 0
        self.total_practiced = 0
        
        print(f"[SESSION] Started practice session with {len(self.sentences)} sentences")
        return {
            'success': True,
            'total_sentences': len(self.sentences),
            'sentences': self.sentences
        }

    def get_current_sentence(self):
        """Get the current sentence for display"""
        if not self.sentences or self.current_sentence_index >= len(self.sentences):
            return {
                'available': False,
                'session_complete': True,
                'message': 'Practice session completed'
            }
            
        current_sentence = self.sentences[self.current_sentence_index]
        return {
            'available': True,
            'sentence': current_sentence['text'],
            'full_data': current_sentence,
            'current_index': self.current_sentence_index + 1,
            'total_sentences': len(self.sentences),
            'session_complete': False
        }

    def speak_sentence(self, sentence: str = None):
        """Speak a specific sentence"""
        if sentence is None:
            if not self.sentences or self.current_sentence_index >= len(self.sentences):
                return {'error': 'No sentence available'}
            sentence = self.sentences[self.current_sentence_index]['text']
        
        self.is_reading = True
        self.speak(sentence)
        self.is_reading = False
        
        return {'success': True, 'sentence': sentence}

    def stop_speaking(self):
        """Stop the current TTS reading"""
        if self.engine and self.is_reading:
            self.engine.stop()
            self.is_reading = False
            return {'success': True, 'message': 'Reading stopped'}
        return {'success': False, 'message': 'No active reading'}

    def practice_sentence(self, sentence: str):
        """Practice a specific sentence provided as argument"""
        try:
            print(f"[PRACTICE] Practicing specific sentence: {sentence}")
            
            # Speak the sentence to the user
            self.speak("Listen carefully:")
            time.sleep(0.3)
            self.speak(sentence)
            time.sleep(0.5)
            
            # Listen to user's attempt
            if self.microphone_available:
                try:
                    print("[MIC] Listening for student's reading...")
                    audio = self.listen_once()
                    spoken_text = self.transcribe(audio)
                    similarity = self.calculate_similarity(sentence, spoken_text)
                    is_correct = similarity >= Config.SIMILARITY_THRESHOLD
                    
                    # Generate feedback
                    feedback = self._generate_feedback(is_correct, similarity)
                    
                    result = {
                        'success': True,
                        'original_sentence': sentence,
                        'spoken_text': spoken_text,
                        'score': round(similarity * 100, 2),
                        'is_correct': is_correct,
                        'feedback': feedback,
                        'word_feedback': self._get_word_level_feedback(sentence, spoken_text),
                        'mode': 'practice_sentence'
                    }
                    
                    return result
                    
                except Exception as listen_error:
                    print(f"[ERROR] Listening failed: {listen_error}")
                    return self._simulate_practice(sentence, f"Listening failed: {listen_error}")
            else:
                return self._simulate_practice(sentence, "Microphone not available")
                
        except Exception as e:
            print(f"[ERROR] Practice session error: {e}")
            return {
                'success': False,
                'error': str(e),
                'spoken_text': None,
                'score': 0.0,
                'is_correct': False,
                'feedback': "Error occurred during practice",
                'mode': 'error'
            }

    def practice_current_sentence(self):
        """Practice the current sentence with immediate feedback"""
        if not self.sentences or self.current_sentence_index >= len(self.sentences):
            return {
                'success': False,
                'error': 'No sentences available',
                'session_complete': True
            }

        current_sentence_data = self.sentences[self.current_sentence_index]
        current_sentence = current_sentence_data['text']
        
        try:
            # Re-use the new generic method but add session management
            result = self.practice_sentence(current_sentence)
            
            if result.get('success'):
                self.total_practiced += 1
                if result.get('is_correct'):
                    self.correct_count += 1
                    self.current_sentence_index += 1
                    result['message'] = "[OK] Correct! Moving to next sentence."
                    result['next_sentence_available'] = self.current_sentence_index < len(self.sentences)
                else:
                    result['message'] = "[X] Try again! Listen carefully."
                    result['next_sentence_available'] = self.current_sentence_index < len(self.sentences)
                
                # Add session stats
                accuracy = (self.correct_count / self.total_practiced) * 100 if self.total_practiced > 0 else 0
                result['accuracy'] = round(accuracy, 1)
                result['correct_count'] = self.correct_count
                result['total_practiced'] = self.total_practiced
                result['session_complete'] = False
                
                return result
            else:
                return result

        except Exception as e:
            # Fallback for outer exception
             print(f"[ERROR] Session practice error: {e}")
             return {
                'success': False,
                'error': str(e),
                'spoken_text': None,
                'score': 0.0,
                'is_correct': False,
                'feedback': "Error occurred during practice",
                'session_complete': False
            }

    def _generate_feedback(self, is_correct: bool, similarity: float) -> str:
        """Generate gentle feedback based on performance"""
        if is_correct:
            if similarity >= 0.95:
                return "Outstanding! That was perfect pronunciation."
            elif similarity >= 0.85:
                return "Great job! Your pronunciation is very clear."
            else:
                return "Well done! You got the sentence right."
        else:
            if similarity >= 0.7:
                return "You're very close! A few words sounded a bit different. Let's try one more time."
            elif similarity >= 0.5:
                return "Good effort! Some words were tricky. Listen to the example again and take your time."
            else:
                return "It's okay! This is a tough one. Listen to the smooth reading again, then try to match that rhythm."

    def _simulate_practice(self, sentence: str, reason: str):
        """Simulate practice session without microphone"""
        print(f"[SIM] Simulation mode: {reason}")
        
        self.total_practiced += 1
        self.correct_count += 1
        accuracy = (self.correct_count / self.total_practiced) * 100
        
        result = {
            'success': True,
            'original_sentence': sentence,
            'spoken_text': f"[SIMULATION] {sentence}",
            'score': 85.0,
            'is_correct': True,
            'accuracy': round(accuracy, 1),
            'correct_count': self.correct_count,
            'total_practiced': self.total_practiced,
            'feedback': "Simulation mode - Good job!",
            'message': "[OK] Correct! Moving to next sentence.",
            'next_sentence_available': self.current_sentence_index + 1 < len(self.sentences),
            'session_complete': False
        }
        
        self.current_sentence_index += 1
        return result

    def skip_to_next_sentence(self):
        """Skip to the next sentence"""
        if self.current_sentence_index + 1 < len(self.sentences):
            self.current_sentence_index += 1
            return {
                'success': True,
                'message': 'Moved to next sentence',
                'current_sentence': self.sentences[self.current_sentence_index]['text']
            }
        else:
            return {
                'success': False,
                'message': 'No more sentences available'
            }

    def get_session_progress(self):
        """Get current session progress"""
        accuracy = (self.correct_count / self.total_practiced) * 100 if self.total_practiced > 0 else 0
        
        return {
            'current_sentence_index': self.current_sentence_index + 1,
            'total_sentences': len(self.sentences),
            'accuracy': round(accuracy, 1),
            'correct_count': self.correct_count,
            'total_practiced': self.total_practiced,
            'session_complete': self.current_sentence_index >= len(self.sentences)
        }
    
    def speak(self, text):
        """Speak text using TTS"""
        if self.engine is None:
            print(f"TTS Simulation: {text}")
            return
            
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            time.sleep(0.3)
        except Exception as e:
            print(f"TTS Error: {e}")
    
    def listen_once(self, calibrate_seconds=1.0):
        """Listen to microphone and return audio"""
        if not self.microphone_available:
            raise RuntimeError("Microphone not available")
            
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=calibrate_seconds)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
                return audio
        except sr.WaitTimeoutError:
            raise RuntimeError("No speech detected within timeout period")
        except Exception as e:
            raise RuntimeError(f"Microphone error: {e}")
    
    def transcribe(self, audio):
        """Convert speech to text using Wav2Vec2"""
        if self.model and self.processor:
            try:
                # Get raw data at 16kHz
                raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                # Convert to numpy array (int16) -> float32
                input_values = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
                # Normalize (16-bit PCM)
                input_values = input_values / 32768.0
                
                # Tokenize
                input_values = self.processor(input_values, return_tensors="pt", sampling_rate=16000).input_values
                
                # Inference
                with torch.no_grad():
                    logits = self.model(input_values).logits
                
                # Decode
                predicted_ids = torch.argmax(logits, dim=-1)
                transcription = self.processor.batch_decode(predicted_ids)[0]
                
                print(f"[TRANSCRIPTION-W2V2] '{transcription}'")
                return transcription.lower()
                
            except Exception as e:
                print(f"[ERROR] Wav2Vec2 Inference error: {e}")
                # Fallback to Google if inference fails
                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"[TRANSCRIPTION-GOOGLE] '{text}'")
                    return text.lower()
                except Exception as e_google:
                     raise RuntimeError(f"Speech recognition service error: {e} | {e_google}")
        else:
             # Fallback to Google if model failed to load
             try:
                text = self.recognizer.recognize_google(audio)
                return text.lower()
             except sr.UnknownValueError:
                raise RuntimeError("Could not understand the audio")
             except sr.RequestError as e:
                raise RuntimeError(f"Speech recognition service error: {e}")
    
    def calculate_similarity(self, original, spoken):
        """Calculate similarity between original and spoken text"""
        if not original or not spoken:
            return 0.0
            
        original_clean = self._clean_text(original)
        spoken_clean = self._clean_text(spoken)
        
        return SequenceMatcher(None, original_clean, spoken_clean).ratio()

    def _clean_text(self, text):
        """Remove punctuation and lowercase text for comparison"""
        return re.sub(r'[^\w\s]', '', text.lower()).strip()

    def _get_word_level_feedback(self, original, spoken):
        """Generate word-by-word feedback"""
        if not original:
            return []
            
        orig_words = original.split()
        spoken_words = spoken.lower().split() if spoken else []
        
        feedback = []
        spoken_ptr = 0
        
        for orig_word in orig_words:
            clean_orig = self._clean_text(orig_word)
            found = False
            
            # Look ahead a bit in spoken words to find the current original word
            # This handles small omissions or extra words
            for i in range(spoken_ptr, min(spoken_ptr + 3, len(spoken_words))):
                if clean_orig == self._clean_text(spoken_words[i]):
                    feedback.append({'word': orig_word, 'status': 'correct'})
                    spoken_ptr = i + 1
                    found = True
                    break
            
            if not found:
                # Check for mispronunciation (high similarity but not exact)
                potential_match = False
                for i in range(spoken_ptr, min(spoken_ptr + 2, len(spoken_words))):
                    sim = SequenceMatcher(None, clean_orig, self._clean_text(spoken_words[i])).ratio()
                    if sim > 0.7:
                        feedback.append({'word': orig_word, 'status': 'mispronounced', 'spoken': spoken_words[i]})
                        spoken_ptr = i + 1
                        potential_match = True
                        break
                
                if not potential_match:
                    feedback.append({'word': orig_word, 'status': 'missed'})
                    
        return feedback