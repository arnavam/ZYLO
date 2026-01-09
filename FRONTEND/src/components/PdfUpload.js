// frontend/src/components/PdfUpload.js
import React, { useState, useRef } from 'react';

const PdfUpload = ({ onPdfUpload, isUploading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) handleFile(file);
  };

  const handleFile = (file) => {
    if (file.type !== 'application/pdf') {
      alert('Oops! Only PDF storybooks please! 📚');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert('Whoa! That book is too big (over 10MB). Try a smaller one!');
      return;
    }
    onPdfUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  };

  return (
    <div className="upload-section glass fade-in" style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
      <h2 className="gradient-text" style={{ fontSize: '2rem', marginBottom: '10px' }}>
        Ready to Read?
      </h2>
      <p className="text-secondary" style={{ marginBottom: '30px', fontSize: '1.1rem' }}>
        Pick a fun story to practice with! 🚀
      </p>

      <div
        className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
        style={{
          border: '3px dashed ' + (isDragOver ? '#4ADE80' : 'rgba(255,255,255,0.3)'),
          borderRadius: '30px',
          padding: '40px',
          cursor: isUploading ? 'wait' : 'pointer',
          background: isDragOver ? 'rgba(74, 222, 128, 0.1)' : 'rgba(255,255,255,0.05)',
          transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
          transform: isDragOver ? 'scale(1.02)' : 'scale(1)',
          position: 'relative',
          overflow: 'hidden'
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <div className="upload-content">
          {isUploading ? (
            <div className="loading-state">
              <div className="book-loader">📖</div>
              <p className="gradient-text" style={{ fontSize: '1.2rem', fontWeight: 600, marginTop: '20px' }}>
                Opening your book...
              </p>
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          ) : (
            <div className="idle-state">
              <div className="upload-icon bounce-hover" style={{ fontSize: '4rem', marginBottom: '20px' }}>
                📚
              </div>
              <p className="upload-text" style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '10px' }}>
                {isDragOver ? 'Drop it here!' : 'Click to Pick a Story'}
              </p>
              <p className="text-secondary">
                or drag your PDF file here
              </p>
            </div>
          )}
        </div>

        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          disabled={isUploading}
        />
      </div>
    </div>
  );
};

export default PdfUpload;