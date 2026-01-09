// frontend/src/components/TextDisplay.js
import React from 'react';

const TextDisplay = ({ sentences, currentIndex }) => {
  if (sentences.length === 0) {
    return (
      <div className="text-display">
        <p>No text to display. Please upload a PDF.</p>
      </div>
    );
  }

  return (
    <div className="text-display">
      <h2>Reading Text ({sentences.length} sentences)</h2>
      {sentences.map((sentence, index) => {
        // Handle both object and string formats
        const sentenceText = sentence.text || sentence;
        const isCurrent = index === currentIndex;
        const pageInfo = sentence.page !== undefined ? ` (Page ${sentence.page + 1})` : '';
        
        return (
          <div 
            key={index} 
            className={`sentence-item ${isCurrent ? 'current-sentence' : ''}`}
          >
            <span className="sentence-text">{sentenceText}</span>
            {pageInfo && <span className="page-info">{pageInfo}</span>}
          </div>
        );
      })}
    </div>
  );
};

export default TextDisplay;