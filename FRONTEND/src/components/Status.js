// frontend/src/components/Status.js
import React from 'react';

const Status = ({ status, feedback, currentIndex, totalSentences }) => {
  const [visible, setVisible] = React.useState(true);
  const progress = totalSentences > 0 ? (currentIndex / totalSentences) * 100 : 0;

  React.useEffect(() => {
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
    }, 3000); // Hide after 3 seconds

    return () => clearTimeout(timer);
  }, [status, feedback, currentIndex]); // Reset timer on updates

  if (!visible) return null;

  return (
    <div className="status-section">
      <h2>Session Status</h2>
      <p>{status}</p>
      {feedback && <p>{feedback}</p>}
      {totalSentences > 0 && (
        <>
          <p>Progress: {currentIndex + 1} of {totalSentences} sentences</p>
          <div style={{ width: '100%', backgroundColor: '#ddd', borderRadius: '4px' }}>
            <div
              style={{
                width: `${progress}%`,
                height: '20px',
                backgroundColor: '#4CAF50',
                borderRadius: '4px',
                transition: 'width 0.3s ease'
              }}
            ></div>
          </div>
        </>
      )}
    </div>
  );
};

export default Status;