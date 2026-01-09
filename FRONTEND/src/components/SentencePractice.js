import React, { useState, useRef } from 'react';

const SentencePractice = ({
  sentences,
  currentIndex,
  isProcessing,
  onNext,
  onRepeat,
  onExit
}) => {

  const currentSentence = sentences[currentIndex];
  const sentenceText = currentSentence?.custom_text || currentSentence?.text || '';

  // Map expected vs spoken words for highlighting
  const getWordMatchMap = (expected, spoken) => {
    const exp = expected.toLowerCase().split(" ");
    const spk = spoken?.toLowerCase().split(" ") || [];

    return exp.map((word, i) => ({
      word,
      correct: spk[i] === word
    }));
  };

  // Supportive encouragement messages
  const getEncouragement = (score) => {
    if (score >= 0.85)
      return "Great job! Your pronunciation was clear and confident 🎉";

    if (score >= 0.65)
      return "Nice effort — you're very close! Try reading a little slower 🌟";

    return "Good try! Let's practice again — focus on the highlighted words 💪";
  };

  // ---- Recording State ----
  const mediaRecorderRef = useRef(null);
  const [chunks, setChunks] = useState([]);
  const [recording, setRecording] = useState(false);

  // ---- Pronunciation Result ----
  const [result, setResult] = useState(null);

  // ---- START RECORDING ----
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;
    setChunks([]);

    recorder.ondataavailable = e => {
      if (e.data.size > 0) {
        setChunks(prev => [...prev, e.data]);
      }
    };

    recorder.start();
    setRecording(true);
    setResult(null);
  };

  // ---- STOP & SEND ----
  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setRecording(false);

    mediaRecorderRef.current.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });

      const formData = new FormData();
      formData.append("audio", blob, "sentence.webm");
      formData.append("word", sentenceText); // sending full sentence

      const res = await fetch(
        "http://localhost:5000/api/practice/evaluate-pronunciation",
        { method: "POST", body: formData }
      );

      const data = await res.json();
      setResult(data.result);
    };
  };

  return (
    <div className="sentence-practice">

      <div className="practice-header">
        <h2>🎯 Practice Session</h2>
        <button onClick={onExit} className="btn-exit-practice">
          ↩️ Back to Reading
        </button>
      </div>

      <div className="practice-progress">
        <div className="progress-info">
          Sentence {currentIndex + 1} of {sentences.length}
        </div>
      </div>

      <div className="current-sentence-display">
        <div className="sentence-card practice-mode">
          <h3>Read this sentence aloud:</h3>

          <div className="practice-sentence-text">
            {result
              ? getWordMatchMap(sentenceText, result.spoken_text).map((w, i) => (
                <span
                  key={i}
                  style={{
                    padding: "4px",
                    marginRight: "4px",
                    borderRadius: "8px",
                    background: w.correct ? "#c8f7c5" : "#ffbaba",
                    border: w.correct ? "1px solid #4caf50" : "1px solid #ff5252"
                  }}
                >
                  {w.word}
                </span>
              ))
              : sentenceText}
          </div>

        </div>
      </div>

      {/* ---- RECORDING CONTROLS ---- */}
      <div className="practice-controls">

        {!recording ? (
          <button onClick={startRecording}>
            🎤 Start Reading
          </button>
        ) : (
          <button onClick={stopRecording}>
            ⏹ Stop
          </button>
        )}

        <button onClick={onRepeat} disabled={recording}>
          🔄 Repeat Sentence
        </button>

        <button onClick={onNext} disabled={recording}>
          ⏭️ Next Sentence
        </button>
      </div>

      {/* ---- PROCESSING FEEDBACK ---- */}
      {recording && (
        <div className="processing-indicator">
          <p>Listening... Please speak the sentence</p>
        </div>
      )}

      {/* ---- PRONUNCIATION RESULT ---- */}
      {result && (
        <div className="practice-result">

          <p><b>Spoken:</b> {result.spoken_text}</p>

          {/* Score Progress Bar */}
          <div style={{ marginTop: "10px" }}>
            <div style={{
              height: "12px",
              width: "100%",
              background: "#eee",
              borderRadius: "8px"
            }}>
              <div style={{
                height: "100%",
                width: `${result.score * 100}%`,
                borderRadius: "8px",
                background: result.score >= 0.85
                  ? "#4caf50"
                  : result.score >= 0.65
                    ? "#ffa726"
                    : "#ef5350"
              }} />
            </div>

            <p style={{ marginTop: "6px" }}>
              Confidence Score: <b>{Math.round(result.score * 100)}%</b>
            </p>
          </div>

          {/* Encouragement Message */}
          <div style={{
            padding: "10px",
            marginTop: "8px",
            borderRadius: "10px",
            background: "#f3f6ff"
          }}>
            💬 {getEncouragement(result.score)}
          </div>

        </div>
      )}

    </div>
  );
};

export default SentencePractice;
