// frontend/src/components/SingleSentenceView.js
import React from 'react';

const SingleSentenceView = ({
  currentSentence,
  currentIndex,
  totalSentences,
  isProcessing,
  isReading,
  practiceResult,
  wordFeedback,
  onReadAloud,
  onPractice,
  readingSpeed,
  onSpeedChange
}) => {
  const sentenceText = currentSentence?.text || currentSentence || '';

  const renderWordFeedback = () => {
    if (wordFeedback && wordFeedback.length > 0) {
      return wordFeedback.map((item, index) => (
        <span key={index} className={`word ${item.status}`}>
          {item.word}
        </span>
      ));
    }

    // Fallback to plain text if no feedback yet
    return sentenceText.split(' ').map((word, index) => (
      <span key={index} className="word">
        {word}
      </span>
    ));
  };

  return (
    <div className="single-sentence-view sentence-card glass fade-in">
      <div className="sentence-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h4 className="gradient-text" style={{ margin: 0 }}>Now Practicing</h4>
        <span className="stat-label">Sentence {currentIndex + 1} of {totalSentences}</span>
      </div>

      <div className="sentence-display">
        {renderWordFeedback()}
      </div>

      {practiceResult && (
        <div className={`feedback-summary fade-in ${practiceResult.is_correct ? 'text-success' : 'text-warning'}`}
          style={{ textAlign: 'center', marginBottom: '20px', padding: '10px', borderRadius: '12px', background: 'rgba(255,255,255,0.05)' }}>
          <strong style={{ fontSize: '1.2rem' }}>
            {practiceResult.is_correct ? '✨ Excellent Reading!' : '💪 Keep Trying!'}
          </strong>
          <p className="text-secondary" style={{ margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            {practiceResult.feedback}
          </p>
        </div>
      )}

      <div className="sentence-controls" style={{ display: 'flex', gap: '15px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <div className="speed-control" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginRight: 'auto' }}>
          <span className="stat-label">Speed</span>
          <select
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            value={readingSpeed}
            onChange={(e) => onSpeedChange(parseInt(e.target.value))}
            disabled={isProcessing || isReading}
          >
            <option value={80}>Slow</option>
            <option value={120}>Normal</option>
            <option value={160}>Fast</option>
          </select>
        </div>

        <button
          onClick={onReadAloud}
          disabled={isProcessing || isReading}
          className="btn btn-secondary"
        >
          {isReading ? '🔊 Reading...' : '🔊 Listen'}
        </button>

        <button
          onClick={onPractice}
          disabled={isProcessing || isReading}
          className="btn btn-primary"
          style={{ minWidth: '180px' }}
        >
          {isProcessing ? '🎤 Listening...' : '🎤 Read Aloud'}
        </button>
      </div>
    </div>
  );
};

export default SingleSentenceView;
