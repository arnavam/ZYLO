import React, { useEffect, useRef, useState, useCallback } from "react";
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set worker source
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

const DocumentReader = ({
  onClose,
  sentences: parentSentences,
  currentIndex: parentIndex,
  onJumpTo,
  currentPdfName,
  pdfUrl,
  isReading: parentIsReading,
  readingSpeed = 120,
  onReadAloud,
  onPractice,
  onSpeedChange,
  isProcessing,
  practiceResult,
  wordFeedback: parentWordFeedback
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
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(parentIndex || 0);
  const [domItemsMap, setDomItemsMap] = useState([]); // Array of arrays: sentenceIdx -> element list

  // Sync with parent index
  useEffect(() => {
    if (parentIndex !== undefined && parentIndex !== activeSentenceIndex) {
      setActiveSentenceIndex(parentIndex);
    }
  }, [parentIndex]);

  // --- RECORDING STATE ---
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

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

  // --- RECORDING LOGIC ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const webmBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        try {
          // Convert WebM to WAV (16kHz mono) for backend compatibility
          console.log("Converting recording to WAV...");
          const wavBlob = await convertToWav(webmBlob);
          onPractice(wavBlob);
        } catch (err) {
          console.error("WAV Conversion error:", err);
          // Fallback to original blob if conversion fails
          onPractice(webmBlob);
        }

        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const convertToWav = async (blob) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const arrayBuffer = await blob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    // Get PCM data from mono (or first channel)
    const pcmData = audioBuffer.getChannelData(0);
    const wavBuffer = encodeWav(pcmData, 16000);

    return new Blob([wavBuffer], { type: 'audio/wav' });
  };

  const encodeWav = (samples, sampleRate) => {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // RIFF identifier
    writeString(view, 0, 'RIFF');
    // RIFF chunk length
    view.setUint32(4, 36 + samples.length * 2, true);
    // RIFF type
    writeString(view, 8, 'WAVE');
    // format chunk identifier
    writeString(view, 12, 'fmt ');
    // format chunk length
    view.setUint32(16, 16, true);
    // sample format (raw)
    view.setUint16(20, 1, true);
    // channel count
    view.setUint16(22, 1, true);
    // sample rate
    view.setUint32(24, sampleRate, true);
    // byte rate (sample rate * block align)
    view.setUint32(28, sampleRate * 2, true);
    // block align (channel count * bytes per sample)
    view.setUint16(32, 2, true);
    // bits per sample
    view.setUint16(34, 16, true);
    // data chunk identifier
    writeString(view, 36, 'data');
    // data chunk length
    view.setUint32(40, samples.length * 2, true);

    // Write the PCM samples
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return buffer;
  };

  const writeString = (view, offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handlePracticeClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
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
    if (onJumpTo) onJumpTo(index);
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

      utterance.onerror = (event) => {
        console.error("Speech synthesis error:", event.error, event);
      };

      window.speechSynthesis.speak(utterance);
      return () => window.speechSynthesis.cancel();

    } else {
      window.speechSynthesis.cancel();
    }
  }, [parentIsReading, activeSentenceIndex, localSentences, readingSpeed, selectedVoice]);

  // --- LIVELY CORRECTION LOGIC ---
  const getWordFeedback = () => {
    if (!practiceResult || !localSentences[activeSentenceIndex]) return [];

    const expected = localSentences[activeSentenceIndex].text.toLowerCase().replace(/[^\w\s]/g, '').split(/\s+/);
    const spoken = (practiceResult.result?.spoken_text || "").toLowerCase().replace(/[^\w\s]/g, '').split(/\s+/);

    return expected.map((word, i) => ({
      word,
      correct: spoken.includes(word) // Simple check, can be improved with alignment
    }));
  };

  const wordFeedback = getWordFeedback();

  // Auto-correction audio
  useEffect(() => {
    if (practiceResult && practiceResult.result && practiceResult.result.score < 0.85) {
      const missedWords = wordFeedback
        .filter(w => !w.correct)
        .map(w => w.word);

      if (missedWords.length > 0) {
        window.speechSynthesis.cancel();
        const correctionText = `Let's try these words again: ${missedWords.join(", ")}`;
        const utterance = new SpeechSynthesisUtterance(correctionText);
        if (selectedVoice) utterance.voice = selectedVoice;
        utterance.rate = 0.9; // Slightly slower for correction

        setTimeout(() => {
          window.speechSynthesis.speak(utterance);
        }, 1000);
      }
    }
  }, [practiceResult]);

  const handleNextSentence = () => {
    if (activeSentenceIndex < localSentences.length - 1) {
      const nextIndex = activeSentenceIndex + 1;
      setActiveSentenceIndex(nextIndex);
      if (onJumpTo) onJumpTo(nextIndex);
    }
  };

  const handlePrevSentence = () => {
    if (activeSentenceIndex > 0) {
      const prevIndex = activeSentenceIndex - 1;
      setActiveSentenceIndex(prevIndex);
      if (onJumpTo) onJumpTo(prevIndex);
    }
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
              practiceResult ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {wordFeedback.map((w, i) => (
                    <span
                      key={i}
                      style={{
                        color: w.correct ? '#48BB78' : '#F56565',
                        fontWeight: w.correct ? 'normal' : 'bold',
                        textDecoration: w.correct ? 'none' : 'underline'
                      }}
                    >
                      {w.word}
                    </span>
                  ))}
                </div>
              ) : (
                localSentences[activeSentenceIndex]?.text
              )
            ) : (
              <div style={{ color: '#a0aec0' }}>
                {loading ? "Loading PDF..." : "Extracting text..."}
              </div>
            )}
          </div>

          {practiceResult && (
            <div className="practice-feedback fade-in" style={{ marginTop: '10px', padding: '10px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                <span style={{ fontSize: '0.8rem', color: '#a0aec0' }}>Accuracy Score:</span>
                <span style={{ fontWeight: 'bold', color: practiceResult.result.score >= 0.85 ? '#48BB78' : '#ED8936' }}>
                  {Math.round(practiceResult.result.score * 100)}%
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', margin: 0, fontStyle: 'italic' }}>
                {practiceResult.result.feedback}
              </p>
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px', marginTop: '15px' }}>
            <button
              onClick={handlePracticeClick}
              className={`btn ${isRecording ? 'btn-danger pulse' : 'btn-primary'}`}
              style={{ flex: 1 }}
              disabled={isProcessing}
            >
              {isRecording ? '⏹ Stop' : '🎤 Practice'}
            </button>
            <button onClick={handleNextSentence} className="btn btn-success" style={{ flex: 1, backgroundColor: '#48BB78' }}>Continue ➡</button>
          </div>
          {isRecording && <p style={{ color: '#ff5252', fontSize: '0.8rem', textAlign: 'center', marginTop: '5px' }}>Recording in progress...</p>}
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
