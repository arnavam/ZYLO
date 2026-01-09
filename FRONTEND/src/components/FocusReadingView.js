// frontend/src/components/FocusReadingView.js
import React, { useState, useEffect } from 'react';

const FocusReadingView = ({ 
  sentences, 
  onSentenceSelect,
  onStartPractice,
  readingSpeed,
  onSpeedChange,
  onSelectAll,
  onDeselectAll
}) => {
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [highlightColor, setHighlightColor] = useState('#ffeb3b');

  const currentSentence = sentences[currentSentenceIndex];
  const sentenceText = currentSentence?.custom_text || currentSentence?.text || '';

  useEffect(() => {
    let timer;
    if (isPlaying && currentSentenceIndex < sentences.length - 1) {
      timer = setTimeout(() => {
        setCurrentSentenceIndex(prev => prev + 1);
      }, 3000); // 3 seconds per sentence
    } else if (currentSentenceIndex >= sentences.length - 1) {
      setIsPlaying(false);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentSentenceIndex, sentences.length]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleNext = () => {
    if (currentSentenceIndex < sentences.length - 1) {
      setCurrentSentenceIndex(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentSentenceIndex > 0) {
      setCurrentSentenceIndex(prev => prev - 1);
    }
  };

  const handleSentenceClick = (index) => {
    setCurrentSentenceIndex(index);
    setIsPlaying(false);
  };

  const highlightColors = [
    { name: 'Yellow', value: '#ffeb3b' },
    { name: 'Green', value: '#a5d6a7' },
    { name: 'Blue', value: '#90caf9' }
  ];

  return (
    <div className="focus-reading-view">
      <div className="focus-controls">
        <h2>🎯 Focus Reading Mode</h2>
        
        <div className="bulk-controls">
          <button onClick={onSelectAll} className="btn-bulk-select">
            ✅ Select All
          </button>
          <button onClick={onDeselectAll} className="btn-bulk-deselect">
            ❌ Deselect All
          </button>
        </div>

        <div className="control-panel">
          <div className="playback-controls">
            <button onClick={handlePrevious} disabled={currentSentenceIndex === 0}>
              ⏮️ Previous
            </button>
            <button onClick={handlePlayPause}>
              {isPlaying ? '⏸️ Pause' : '▶️ Play'}
            </button>
            <button onClick={handleNext} disabled={currentSentenceIndex === sentences.length - 1}>
              ⏭️ Next
            </button>
          </div>
        </div>

        <div className="progress-info">
          <span>Sentence {currentSentenceIndex + 1} of {sentences.length}</span>
        </div>
      </div>

      <div className="focus-content">
        <div className="focused-sentence" style={{ backgroundColor: highlightColor }}>
          <div className="sentence-text focused">
            {sentenceText}
          </div>
        </div>

        <div className="sentences-list-blurred">
          <h3>All Sentences:</h3>
          <div className="blurred-sentences">
            {sentences.map((sentence, index) => (
              <div
                key={index}
                className={`sentence-item-blurred ${index === currentSentenceIndex ? 'current' : ''}`}
                onClick={() => handleSentenceClick(index)}
              >
                <div className="sentence-checkbox">
                  <input
                    type="checkbox"
                    checked={sentence.selected}
                    onChange={(e) => onSentenceSelect(index, e.target.checked)}
                  />
                  <span className="sentence-number">{index + 1}.</span>
                </div>
                <div className="sentence-text-blurred">
                  {sentence.custom_text || sentence.text}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="focus-actions">
        <button 
          onClick={onStartPractice}
          disabled={!sentences.some(s => s.selected)}
          className="btn-start-practice"
        >
          🎯 Start Practice with Selected Sentences
        </button>
      </div>
    </div>
  );
};

export default FocusReadingView;