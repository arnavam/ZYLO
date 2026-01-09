import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import confetti from 'canvas-confetti';
import './App.css';
import Header from './components/Header';
import PdfUpload from './components/PdfUpload';
import DocumentReader from './components/DocumentReader';
import Status from './components/Status';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import { AuthProvider, useAuth } from './context/AuthContext';

// Protected Route Component
const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-screen" style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: '1.5rem'}}>Loading...</div>;
  }
  
  return user ? children : <Navigate to="/signin" />;
};

function ReadingAssistant() {
  const { logout, user } = useAuth();
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [allSentences, setAllSentences] = useState([]);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const [status, setStatus] = useState('Upload a PDF to begin');
  const [feedback, setFeedback] = useState('');
  const [wordFeedback, setWordFeedback] = useState([]);
  const [practiceResult, setPracticeResult] = useState(null);
  const [currentView, setCurrentView] = useState('upload'); // 'upload', 'dashboard', 'reading'
  const [readingSpeed, setReadingSpeed] = useState(120);
  const [sessionStats, setSessionStats] = useState({
    totalSentences: 0,
    completedSentences: 0,
    correctAttempts: 0,
    totalAttempts: 0,
  });

  const handleFileUpload = async (file) => {
    setIsProcessing(true);
    setStatus('Processing PDF...');
    try {
      const formData = new FormData();
      formData.append('pdf', file);
      
      const response = await axios.post('/api/pdf/upload-pdf', formData, {
         headers: { 'Content-Type': 'multipart/form-data' },
         withCredentials: true
      });
      
      if (response.data.success) {
        setAllSentences(response.data.sentences);
        setPdfUrl(response.data.pdf_url);
        setCurrentView('reading');
        setStatus('PDF loaded successfully!');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setStatus(`Upload failed: ${error.response?.data?.error || error.message} `);
    } finally {
      setIsProcessing(false);
    }
  };

  const readCurrentSentence = async () => {
    if (isProcessing || !allSentences[currentSentenceIndex]) return;
    setIsReading(!isReading);
    if (!isReading) {
      setStatus('Listening to sentence...');
    } else {
      setStatus('Stopped listening.');
    }
  };

  const playSuccessSound = () => {
    const audio = new Audio('https://codeskulptor-demos.commondatastorage.googleapis.com/GalaxyInvaders/bonus.wav');
    audio.volume = 0.5;
    audio.play().catch(e => console.log("Audio play failed", e));
  };

  const triggerConfetti = () => {
    confetti({
      particleCount: 150,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#6366f1', '#a855f7', '#ec4899']
    });
  };

  const practiceCurrentSentence = async (audioBlob) => {
    setIsProcessing(true);
    setStatus('Evaluating pronunciation...');
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('text', allSentences[currentSentenceIndex].text);
      
      const response = await axios.post('/api/practice/evaluate-pronunciation', formData, {
         withCredentials: true
      });
      
      if (response.data.success) {
        setPracticeResult(response.data);
        setWordFeedback(response.data.word_feedback || []);
        setFeedback(response.data.feedback);
        
        setSessionStats(prev => ({
          ...prev,
          totalAttempts: prev.totalAttempts + 1,
          correctAttempts: response.data.is_correct ? prev.correctAttempts + 1 : prev.correctAttempts
        }));

        if (response.data.is_correct) {
          playSuccessSound();
          triggerConfetti();
          setStatus('Excellent! Moving to next sentence...');
          setTimeout(() => {
            setCurrentSentenceIndex(prev => prev + 1);
            setSessionStats(prev => ({
              ...prev,
              completedSentences: prev.completedSentences + 1
            }));
            setPracticeResult(null);
            setWordFeedback([]);
            setFeedback('');
          }, 2500);
        }
      }
    } catch (error) {
      setStatus('Practice encounterd an error');
    } finally {
      setIsProcessing(false);
    }
  };

  const jumpToSentence = (index) => {
    setCurrentSentenceIndex(index);
    setPracticeResult(null);
    setWordFeedback([]);
    setFeedback('');
    setStatus(`Listening to sentence ${index + 1} `);
  };

  const restartSession = () => {
    setCurrentSentenceIndex(0);
    setCurrentView('upload');
    setPdfFile(null);
    setAllSentences([]);
    setSessionStats({
      totalSentences: 0,
      completedSentences: 0,
      correctAttempts: 0,
      totalAttempts: 0
    });
  };

  return (
    <div className="App">
      <div className="auth-header-info" style={{position: 'absolute', top: '10px', right: '10px', display: 'flex', alignItems: 'center', gap: '10px', zIndex: 1000}}>
        <span className="user-name-display" style={{color: '#fff', fontWeight: '500'}}>{user?.name}</span>
        <button onClick={logout} className="logout-btn" style={{background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', padding: '5px 12px', borderRadius: '6px', cursor: 'pointer', transition: 'all 0.3s'}}>Logout</button>
      </div>
      <Header />
      
      {currentView === 'reading' ? (
        <DocumentReader 
          sentences={allSentences}
          currentIndex={currentSentenceIndex}
          onJumpTo={jumpToSentence}
          onRestart={restartSession}
          pdfUrl={pdfUrl}
          stats={sessionStats}
          isReading={isReading}
          readingSpeed={readingSpeed}
          onReadAloud={readCurrentSentence}
          onPractice={practiceCurrentSentence}
          onSpeedChange={setReadingSpeed}
          isProcessing={isProcessing}
        />
      ) : (
        <div className="container">
          <h1 className="gradient-text">Dyslexia Assistant</h1>
          <h2 className="text-secondary">Improve your reading with AI feedback</h2>

          {currentView === 'upload' && (
            <div className="fade-in">
              <PdfUpload onPdfUpload={handleFileUpload} isUploading={isProcessing} />
            </div>
          )}
        </div>
      )}

      {currentView === 'reading' && (
        <div style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 2001 }}>
          <Status status={status} feedback={feedback} />
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/" element={
            <PrivateRoute>
              <ReadingAssistant />
            </PrivateRoute>
          } />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
