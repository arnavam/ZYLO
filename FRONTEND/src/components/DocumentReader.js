import React, { useEffect, useRef, useState, useCallback } from "react";
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set worker source
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

const DocumentReader = ({
  onClose,
  currentPdfName,
  pdfUrl,
  isReading: parentIsReading,
  readingSpeed = 120,
  onReadAloud,
  onPractice,
  onSpeedChange,
  isProcessing
}) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);

  // Audio refs
  const utteranceRef = useRef(null);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);

  // --- STATE ---
  const [localSentences, setLocalSentences] = useState([]);
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(0);
  const [domItemsMap, setDomItemsMap] = useState([]); // Array of arrays: sentenceIdx -> element list

  // Load voices
  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
      if (availableVoices.length > 0 && !selectedVoice) {
        const preferred = availableVoices.find(v => v.name.includes("Google US English") || v.name.includes("Zira"));
        setSelectedVoice(preferred || availableVoices[0]);
      }
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }, []);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
  };

  // --- CORE LOGIC: SENTENCE HIGHLIGHTING ---

  const onPageLoadSuccess = useCallback(async (page) => {
    try {
      setLocalSentences([]);
      setActiveSentenceIndex(0);

      const textContent = await page.getTextContent();
      const items = textContent.items;
      if (items.length === 0) return;

      // Get page viewport to determine height for header/footer detection
      const viewport = page.getViewport({ scale: 1 });
      const pageHeight = viewport.height;

      // Define Metadata Zones (Top 10% and Bottom 10% of page)
      // PDF coordinates: (0,0) is usually bottom-left. 
      // So Footer is low Y, Header is high Y.
      const footerThreshold = pageHeight * 0.1;
      const headerThreshold = pageHeight * 0.9;

      const heights = items.map(item => Math.abs(item.transform[3])).sort((a, b) => a - b);
      const medianHeight = heights[Math.floor(heights.length / 2)] || 12;
      const headingThreshold = medianHeight * 1.3;

      let allSentences = [];
      let fullText = "";
      let currentItemIndices = [];

      items.forEach((item, idx) => {
        if (!item.str) return;

        const height = Math.abs(item.transform[3]);
        const y = item.transform[5]; // Y-coordinate

        const isHeading = height > headingThreshold;
        const isSerial = /^\(?[0-9a-zA-Z]{1,2}(\.|\))$/.test(item.str.trim());
        const isHeaderOrFooter = y < footerThreshold || y > headerThreshold;

        const isMetadata = isHeading || isSerial || isHeaderOrFooter;

        if (isMetadata) {
          if (fullText.trim()) {
            const raw = fullText.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [fullText];
            raw.forEach(s => {
              if (s.trim()) allSentences.push({ text: s.trim(), isMetadata: false, itemIndices: [...currentItemIndices] });
            });
            fullText = "";
            currentItemIndices = [];
          }
          allSentences.push({ text: item.str.trim(), isMetadata: true, itemIndices: [idx] });
        } else {
          fullText += item.str + " ";
          currentItemIndices.push(idx);
          // Split if full stop encountered
          if (/[.!?]/.test(item.str)) {
            const raw = fullText.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [fullText];
            if (raw.length > 1 || (raw.length === 1 && /[.!?]$/.test(fullText.trim()))) {
              allSentences.push({ text: fullText.trim(), isMetadata: false, itemIndices: [...currentItemIndices] });
              fullText = "";
              currentItemIndices = [];
            }
          }
        }
      });

      if (fullText.trim()) {
        const raw = fullText.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [fullText];
        raw.forEach(s => {
          if (s.trim()) allSentences.push({ text: s.trim(), isMetadata: false, itemIndices: [...currentItemIndices] });
        });
      }

      setLocalSentences(allSentences);
      setTimeout(() => mapSentencesToDom(allSentences), 1000);

    } catch (e) {
      console.error("Error loading text content:", e);
    }
  }, [pageNumber]);

  const mapSentencesToDom = (sentences) => {
    const container = document.querySelector('.react-pdf__Page__textContent');
    if (!container) return;

    const spans = Array.from(container.querySelectorAll('span'));
    const map = sentences.map((s, sIdx) => {
      const elements = s.itemIndices.map(idx => spans[idx]).filter(Boolean);
      elements.forEach(el => {
        el.classList.add('sentence-token');
        if (!s.isMetadata) {
          el.classList.add('interactive-token');
          el.onclick = (e) => {
            e.stopPropagation();
            handleSentenceClick(sIdx);
          };
        }
      });
      return elements;
    });
    setDomItemsMap(map);
  };

  const handleSentenceClick = (index) => {
    setActiveSentenceIndex(index);
    // If not currently reading, maybe start? Or just select.
    // For now just select. If reading, it will pick up from here.
    if (parentIsReading) {
      window.speechSynthesis.cancel();
    }
  };

  // Highlighting Effect
  useEffect(() => {
    if (domItemsMap.length === 0) return;

    domItemsMap.forEach((elements, idx) => {
      const isActive = idx === activeSentenceIndex;
      elements.forEach(el => {
        if (isActive) {
          el.classList.add('sentence-active');
        } else {
          el.classList.remove('sentence-active');
        }
      });

      if (isActive && elements[0]) {
        elements[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }, [activeSentenceIndex, domItemsMap]);



  // Reading Logic
  useEffect(() => {
    if (parentIsReading && localSentences.length > 0) {
      if (activeSentenceIndex >= localSentences.length) return;
      const sentenceObj = localSentences[activeSentenceIndex];

      // Auto-skip metadata segments (headings/serials)
      if (sentenceObj.isMetadata) {
        let nextIdx = activeSentenceIndex + 1;
        while (nextIdx < localSentences.length && localSentences[nextIdx].isMetadata) {
          nextIdx++;
        }
        if (nextIdx < localSentences.length) {
          setActiveSentenceIndex(nextIdx);
        } else {
          window.speechSynthesis.cancel();
        }
        return;
      }

      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(sentenceObj.text);
      utteranceRef.current = utterance;
      if (selectedVoice) utterance.voice = selectedVoice;
      utterance.rate = readingSpeed / 120;

      utterance.onend = () => {
        if (activeSentenceIndex < localSentences.length - 1) {
          setActiveSentenceIndex(prev => prev + 1);
        }
      };

      utterance.onerror = () => {
        console.error("Speech synthesis error");
      };

      window.speechSynthesis.speak(utterance);
      return () => window.speechSynthesis.cancel();

    } else {
      window.speechSynthesis.cancel();
    }
  }, [parentIsReading, activeSentenceIndex, localSentences, readingSpeed, selectedVoice]);

  const handleNextSentence = () => {
    if (activeSentenceIndex < localSentences.length - 1) setActiveSentenceIndex(prev => prev + 1);
  };

  const handlePrevSentence = () => {
    if (activeSentenceIndex > 0) setActiveSentenceIndex(prev => prev - 1);
  };

  const handlePracticeClick = () => {
    const text = localSentences[activeSentenceIndex]?.text;
    if (text) onPractice(text);
  };

  return (
    <div className="document-reader fade-in" style={{ backgroundColor: '#2d3748', height: '100vh', display: 'flex', flexDirection: 'row' }}>

      <div className="reader-sidebar glass" style={{ width: '320px', flexShrink: 0, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <button className="btn btn-secondary" onClick={onClose} style={{ alignSelf: 'flex-start' }}>← Back</button>
        <div>
          <h3 className="gradient-text" style={{ fontSize: '1.5rem', marginBottom: '5px' }}>Reader</h3>
          <p className="stat-label">{currentPdfName}</p>
        </div>

        <div className="control-group">
          <button onClick={onReadAloud} className={`btn ${parentIsReading ? 'btn-danger' : 'btn-primary'}`} style={{ width: '100%', padding: '12px' }}>
            {parentIsReading ? '⏹ Stop Reading' : '▶ Start Reading'}
          </button>
        </div>

        <div className="control-group box" style={{ padding: '15px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <button className="btn btn-sm btn-secondary" onClick={handlePrevSentence} disabled={activeSentenceIndex <= 0}>◀</button>
            <span className="stat-value" style={{ flex: 1, textAlign: 'center' }}>{activeSentenceIndex + 1} / {localSentences.length}</span>
            <button className="btn btn-sm btn-secondary" onClick={handleNextSentence} disabled={activeSentenceIndex >= localSentences.length - 1}>▶</button>
          </div>

          <div style={{ fontSize: '0.9rem', color: '#e2e8f0', backgroundColor: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '6px', maxHeight: '150px', overflowY: 'auto' }}>
            {localSentences.length > 0 ? (
              localSentences[activeSentenceIndex]?.text
            ) : (
              <div style={{ color: '#a0aec0' }}>
                {loading ? "Loading PDF..." : "Extracting text..."}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '8px', marginTop: '15px' }}>
            <button onClick={handlePracticeClick} className="btn btn-primary" style={{ flex: 1 }}>🎤 Practice</button>
            <button onClick={handleNextSentence} className="btn btn-success" style={{ flex: 1, backgroundColor: '#48BB78' }}>Continue ➡</button>
          </div>
        </div>

        <div className="control-group">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <select className="btn btn-secondary" value={readingSpeed} onChange={(e) => onSpeedChange(Number(e.target.value))}>
              <option value={80}>Slow</option>
              <option value={120}>Normal</option>
              <option value={160}>Fast</option>
            </select>
            <select className="btn btn-secondary" onChange={(e) => {
              const v = voices.find(vo => vo.name === e.target.value);
              setSelectedVoice(v);
            }}>
              {voices.map(v => <option key={v.name} value={v.name}>{v.name.replace(/Microsoft |Google /, '')}</option>)}
            </select>
          </div>
        </div>

        <div className="stat-item" style={{ marginTop: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center' }}>
            <button className="btn btn-secondary" disabled={pageNumber <= 1} onClick={() => setPageNumber(p => p - 1)}>◀</button>
            <span className="stat-value">{pageNumber} / {numPages || '--'}</span>
            <button className="btn btn-secondary" disabled={pageNumber >= numPages} onClick={() => setPageNumber(p => p + 1)}>▶</button>
          </div>
        </div>
      </div>

      <div className="reader-content" style={{ flex: 1, padding: '40px', display: 'flex', justifyContent: 'center', overflow: 'auto', backgroundColor: '#525659' }}>
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div className="text-white">Loading Document...</div>}
          className="pdf-document"
        >
          <Page
            pageNumber={pageNumber}
            onLoadSuccess={onPageLoadSuccess}
            className="pdf-page shadow-2xl"
            width={850}
            renderTextLayer={true}
            renderAnnotationLayer={false}
          />
        </Document>
      </div>

    </div>
  );
};

export default DocumentReader;
