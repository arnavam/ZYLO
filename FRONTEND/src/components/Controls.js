// frontend/src/components/Controls.js
import React from 'react';

const Controls = ({ 
  sessionActive, 
  isProcessing, 
  onStart, 
  onNext, 
  onRepeat, 
  onExitPractice,
  selectedCount,
  totalSentences,
  selectionMode,
  practiceMode 
}) => {
  if (practiceMode) {
    return (
      <div className="controls">
        <h2>Practice Controls</h2>
        <div className="control-buttons">
          <button onClick={onRepeat} disabled={isProcessing}>
            🔄 Repeat Sentence
          </button>
          <button onClick={onNext} disabled={isProcessing}>
            ⏭️ Next Sentence
          </button>
          <button onClick={onExitPractice} className="btn-exit">
            ↩️ Exit Practice
          </button>
        </div>
      </div>
    );
  }

  if (selectionMode) {
    return (
      <div className="controls">
        <h2>Session Controls</h2>
        <div className="control-buttons">
          <button 
            onClick={onStart} 
            disabled={selectedCount === 0}
            className="btn-start-practice"
          >
            🎯 Start Practice ({selectedCount} sentences)
          </button>
          <div className="selection-info">
            <p>Select sentences you want to practice, then click Start Practice</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="controls">
      <h2>Session Controls</h2>
      <div className="control-buttons">
        <button onClick={onStart} disabled={isProcessing}>
          Start Session
        </button>
        <button onClick={onNext} disabled={!sessionActive || isProcessing}>
          Next Sentence
        </button>
        <button onClick={onRepeat} disabled={!sessionActive || isProcessing}>
          Repeat Sentence
        </button>
      </div>
    </div>
  );
};

export default Controls;