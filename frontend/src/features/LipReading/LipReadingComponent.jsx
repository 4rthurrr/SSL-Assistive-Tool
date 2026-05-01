import { useEffect, useMemo, useRef, useState } from 'react';
import './LipReadingComponent.css';
import { API_URLS } from '../../utils/api';

const BACKEND_URL = API_URLS.auth;
const LETTERS = [
  { key: 'Letter A', display: 'Letter - අ' },
  { key: 'Letter B', display: 'Letter - ඉ' },
  { key: 'Letter C', display: 'Letter - උ' },
  { key: 'Letter D', display: 'Letter - ම' },
  { key: 'Letter E', display: 'Letter - ඔ' },
  { key: 'Letter F', display: 'Letter - ච' },
  { key: 'Letter G', display: 'Word - අම්මා' },
  { key: 'Letter H', display: 'Word - ගස' },
  { key: 'Letter I', display: 'Word - මල්' },
];

const LETTER_TO_VIDEO = {
  'Letter A': 'L1.mp4',
  'Letter B': 'L2.mp4',
  'Letter C': 'L3.mp4',
  'Letter D': 'L4.mp4',
  'Letter E': 'L5.mp4',
  'Letter F': 'L6.mp4',
  'Letter G': 'L7.mp4',
  'Letter H': 'L8.mp4',
  'Letter I': 'L9.mp4',
};

const initialStatus = 'Select a letter and press Start to begin training.';

const LipReadingComponent = () => {
  const [selectedKey, setSelectedKey] = useState(null);
  const [selectedDisplay, setSelectedDisplay] = useState(null);
  const [practiceLoops, setPracticeLoops] = useState(0);
  const [studentTurnFired, setStudentTurnFired] = useState(false);
  const [lastPhase, setLastPhase] = useState('idle');
  const [statusIcon, setStatusIcon] = useState('💡');
  const [statusText, setStatusText] = useState(initialStatus);
  const [statusType, setStatusType] = useState('');
  const [phase, setPhase] = useState('idle');
  const [countdown, setCountdown] = useState('—');
  const [result, setResult] = useState({ visible: false, ok: false, label: '', confidence: 0 });

  const [resultStyle, setResultStyle] = useState({ width: '0%', background: 'linear-gradient(90deg,#3b9eff,#56d0ff)' });
  const [videoLoaded, setVideoLoaded] = useState(false);

  const practiceVideoRef = useRef(null);
  const pollRef = useRef(null);

  const liveFeedSrc = useMemo(() => `${BACKEND_URL}/video_feed`, []);
  const practiceVideoSrc = useMemo(() => selectedKey ? `/practis_letters/${LETTER_TO_VIDEO[selectedKey]}` : '', [selectedKey]);

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, []);

  const setStatus = (icon, text, type) => {
    setStatusIcon(icon);
    setStatusText(text);
    setStatusType(type || '');
  };

  const resetUI = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setLastPhase('idle');
    setPracticeLoops(0);
    setStudentTurnFired(false);
    setSelectedKey((current) => current);
    setStatus('💡', initialStatus, '');
    setCountdown('—');
    setPhase('idle');
    if (practiceVideoRef.current) {
      practiceVideoRef.current.pause();
    }
    setVideoLoaded(false);
  };

  const loadPracticeVideo = (letterKey) => {
    setVideoLoaded(true);
    setPracticeLoops(0);
    setStudentTurnFired(false);
    if (practiceVideoRef.current) {
      practiceVideoRef.current.load();
      practiceVideoRef.current.play().catch(() => {});
    }
  };

  const pollStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/status`);
      const data = await response.json();
      const nextPhase = data.phase;

      if (nextPhase === lastPhase && nextPhase !== 'countdown') {
        return;
      }
      setLastPhase(nextPhase);
      setPhase(nextPhase);

      switch (nextPhase) {
        case 'watching':
          setStatus('👀', `Watch the practice video: ${data.display_letter}`, 'warn');
          break;
        case 'countdown':
          setCountdown(data.countdown > 0 ? data.countdown : '▶');
          setStatus('⏱', `Get ready! Starting in ${data.countdown}...`, 'warn');
          break;
        case 'recording':
          setCountdown('🔴');
          setStatus('🔴', 'Recording... Show the sign now!', 'danger');
          break;
        case 'analyzing':
          setCountdown('🧠');
          setStatus('🧠', 'Analyzing your movement...', '');
          break;
        case 'result':
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          const ok = !!data.result_ok;
          const conf = Number(data.result_confidence || 0);
          setResult({ visible: true, ok, label: data.result_label, confidence: conf });
          setResultStyle({
            width: `${Math.min(conf, 100)}%`,
            background: ok ? 'linear-gradient(90deg,#4ade80,#22c55e)' : 'linear-gradient(90deg,#f87171,#ef4444)',
          });
          setStatus(ok ? '✅' : '❌', `${data.result_label} — ${conf.toFixed(1)}%`, ok ? 'ok' : 'danger');
          setCountdown('—');
          break;
        case 'idle':
        default:
          resetUI();
          break;
      }
    } catch {
      return;
    }
  };

  const startPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }
    pollRef.current = setInterval(pollStatus, 500);
  };

  const handleLetterSelect = (item) => {
    if (lastPhase !== 'idle') {
      return;
    }
    setSelectedKey(item.key);
    setSelectedDisplay(item.display);
    setResult((current) => ({ ...current, visible: false }));
    setStatus('💡', `Ready: ${item.display}`, '');
    setVideoLoaded(true);
    window.requestAnimationFrame(() => {
      if (practiceVideoRef.current) {
        practiceVideoRef.current.load();
      }
    });
  };

  const handleStart = async () => {
    if (!selectedKey) {
      return;
    }

    setPracticeLoops(0);
    setStudentTurnFired(false);
    setResult((current) => ({ ...current, visible: false }));

    const response = await fetch(`${BACKEND_URL}/start_training`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ letter: selectedKey }),
    });

    const data = await response.json();
    if (!data.ok) {
      return;
    }

    loadPracticeVideo(selectedKey);
    setStatus('👀', `Watch carefully: ${selectedDisplay}`, 'warn');
    startPolling();
  };

  const handleStop = async () => {
    await fetch(`${BACKEND_URL}/stop_training`, { method: 'POST' });
    resetUI();
    setSelectedKey(null);
    setSelectedDisplay(null);
  };

  const handlePracticeEnded = async () => {
    setPracticeLoops((currentLoops) => {
      const nextLoops = currentLoops + 1;
      if (nextLoops < 3) {
        if (practiceVideoRef.current) {
          practiceVideoRef.current.play().catch(() => {});
        }
      } else if (!studentTurnFired) {
        setStudentTurnFired(true);
        if (practiceVideoRef.current) {
          practiceVideoRef.current.pause();
        }
        setStatus('⏱', 'Get ready! Your turn is coming...', 'warn');
        fetch(`${BACKEND_URL}/student_turn`, { method: 'POST' });
      }
      return nextLoops;
    });
  };

  return (
    <>
      <header className="top-bar">
        <div className="brand">
          <span className="brand-icon">🤟</span>
          <span className="brand-title">Sign Language Trainer</span>
        </div>
        <div className="header-badge">
          <span className="dot pulse"></span> Live System
        </div>
      </header>

      <main className="layout">
        <aside className="panel letter-panel">
          <h2 className="panel-title">📚 Select Letter</h2>
          <p className="panel-hint">Pick a letter then press <strong>Start</strong></p>
          <ul className="letter-list" id="letterList">
            {LETTERS.map((item, index) => (
              <li
                key={item.key}
                className={`letter-item${selectedKey === item.key ? ' active' : ''}`}
                onClick={() => handleLetterSelect(item)}
              >
                <span className="letter-badge">{index + 1}</span>
                <span className="letter-text">{item.display}</span>
              </li>
            ))}
          </ul>
        </aside>

        <section className="panel center-panel">
          <div className={`status-bar${statusType ? ` ${statusType}` : ''}`} id="statusBar">
            <span id="statusIcon">{statusIcon}</span>
            <span id="statusText">{statusText}</span>
          </div>

          <div className="video-row">
            <div className="video-block">
              <div className="video-label">📷 Live Camera</div>
              <div className="video-frame">
                <img id="liveFeed" src={liveFeedSrc} alt="Live Camera" />
              </div>
            </div>

            <div className="video-block">
              <div className="video-label">🎬 Practice Video</div>
              <div className="video-frame">
                <video
                  id="practiceVideo"
                  ref={practiceVideoRef}
                  muted
                  playsInline
                  preload="auto"
                  autoPlay
                  src={practiceVideoSrc || undefined}
                  key={practiceVideoSrc || 'no-practice-video'}
                  onEnded={handlePracticeEnded}
                >
                </video>
                <div className={`video-placeholder${videoLoaded ? ' hidden' : ''}`} id="videoPh">
                  <span>▶ Select a letter to see practice video</span>
                </div>
              </div>
            </div>
          </div>

          <div className={`result-card${result.visible ? '' : ' hidden'}${result.ok ? ' ok-card' : ' fail-card'}`} id="resultCard">
            <div className="result-icon" id="resultIcon">{result.ok ? '🎉' : '🔄'}</div>
            <div className="result-text" id="resultText">{result.visible ? result.label : 'GOOD JOB!'}</div>
            <div className="result-bar-wrap">
              <div className="result-bar" id="resultBar" style={resultStyle}></div>
            </div>
            <div className="result-confidence" id="resultConfidence">{result.visible ? `Confidence: ${result.confidence.toFixed(1)}%` : '0%'}</div>
          </div>

          <div className="controls">
            <button className="btn btn-start" id="startBtn" disabled={!selectedKey} onClick={handleStart}>▶ Start Training</button>
            <button className="btn btn-stop" id="stopBtn" disabled={phase === 'idle'} onClick={handleStop}>⏹ Stop</button>
          </div>
        </section>

        <aside className="panel info-panel">
          <h2 className="panel-title">📊 Session Info</h2>

          <div className="info-block">
            <div className="info-label">Selected</div>
            <div className="info-value sinhala" id="infoSelected">{selectedDisplay || '—'}</div>
          </div>

          <div className="info-block">
            <div className="info-label">Phase</div>
            <div className="info-value" id="infoPhase">{phase.charAt(0).toUpperCase() + phase.slice(1)}</div>
          </div>

          <div className="info-block">
            <div className="info-label">Countdown</div>
            <div className={`countdown-circle${phase === 'countdown' ? ' active' : ''}`} id="countdownCircle">
              <span id="countdownNum">{countdown}</span>
            </div>
          </div>

          <div className="phase-legend">
            <div className={`phase-step${phase === 'watching' ? ' active' : ''}`} id="ps-watching">👀 Watch Video</div>
            <div className={`phase-step${phase === 'countdown' ? ' active' : ''}`} id="ps-countdown">⏱ Get Ready</div>
            <div className={`phase-step${phase === 'recording' ? ' active' : ''}`} id="ps-recording">🔴 Recording</div>
            <div className={`phase-step${phase === 'analyzing' ? ' active' : ''}`} id="ps-analyzing">🧠 Analyzing</div>
            <div className={`phase-step${phase === 'result' ? ' active' : ''}`} id="ps-result">🏆 Result</div>
          </div>
        </aside>
      </main>

      <footer className="footer">
        🤟 Deaf Kids Sign Language Training System &nbsp;|&nbsp; Flask Web Edition
      </footer>
    </>
  );
};

export default LipReadingComponent;
