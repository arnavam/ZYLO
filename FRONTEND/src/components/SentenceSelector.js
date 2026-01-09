// frontend/src/components/SentenceSelector.js
import React, { useState } from 'react';

const SentenceSelector = ({ 
  sentences, 
  selectedSentences, 
  onSentenceSelect, 
  onSelectAll, 
  onDeselectAll,
  onSentenceEdit 
}) => {
  const [editingIndex, setEditingIndex] = useState(null);
  const [editText, setEditText] = useState('');

  const startEditing = (index, currentText) => {
    setEditingIndex(index);
    setEditText(currentText);
  };

  const saveEdit = () => {
    if (editingIndex !== null) {
      onSentenceEdit(editingIndex, editText);
      setEditingIndex(null);
      setEditText('');
    }
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditText('');
  };

  return (
    <div className="sentence-selector">
      <div className="selector-header">
        <h2>Select Sentences for Practice</h2>
        <div className="selection-controls">
          <button onClick={onSelectAll} className="btn-select-all">
            Select All
          </button>
          <button onClick={onDeselectAll} className="btn-deselect-all">
            Deselect All
          </button>
          <span className="selection-count">
            {selectedSentences.length} of {sentences.length} selected
          </span>
        </div>
      </div>

      <div className="sentences-list">
        {sentences.map((sentence, index) => (
          <div 
            key={index} 
            className={`sentence-item ${sentence.selected ? 'selected' : ''} ${editingIndex === index ? 'editing' : ''}`}
          >
            <div className="sentence-controls">
              <input
                type="checkbox"
                checked={sentence.selected}
                onChange={(e) => onSentenceSelect(index, e.target.checked)}
                className="sentence-checkbox"
              />
              <button 
                className="btn-edit"
                onClick={() => startEditing(index, sentence.custom_text || sentence.text)}
                title="Edit sentence"
              >
                ✏️
              </button>
            </div>
            
            <div className="sentence-content">
              {editingIndex === index ? (
                <div className="edit-mode">
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows="3"
                    className="edit-textarea"
                    placeholder="Edit sentence text..."
                  />
                  <div className="edit-actions">
                    <button onClick={saveEdit} className="btn-save">
                      Save
                    </button>
                    <button onClick={cancelEdit} className="btn-cancel">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <span className="sentence-text">
                    {sentence.custom_text || sentence.text}
                  </span>
                  <div className="sentence-meta">
                    <span className="page-info">Page {sentence.page + 1}</span>
                    <span className="paragraph-info">Paragraph {sentence.paragraph + 1}</span>
                    {sentence.custom_text && <span className="custom-badge">Edited</span>}
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SentenceSelector;