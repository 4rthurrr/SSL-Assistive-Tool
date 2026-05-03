import { useState, useEffect } from 'react';
import './SignToText.css';

const SIGN_API_URL = 'http://127.0.0.1:8001';

export default function SignToText() {
  const [status, setStatus] = useState('connecting');

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${SIGN_API_URL}/health`);
        if (res.ok) setStatus('connected');
        else setStatus('error');
      } catch {
        setStatus('error');
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="sign-to-text-wrapper">
      {/* Status bar */}
      <div className="sign-to-text-status-bar">
        <div className="sign-to-text-title">
          <span className="sign-to-text-icon">🤟</span>
          <span>Sign to Text — Real-time Recognition</span>
          <span className="sign-to-text-badge">Component 1</span>
        </div>
        <div className="sign-to-text-status-indicator">
          <span className={`sign-to-text-dot ${status}`}></span>
          <span className="sign-to-text-status-label">
            {status === 'connected' ? 'Backend Connected' :
             status === 'error' ? 'Backend Offline — Start on port 8001' :
             'Connecting...'}
          </span>
        </div>
      </div>

      {/* Iframe or error */}
      {status === 'error' ? (
        <div className="sign-to-text-offline">
          <div className="sign-to-text-offline-icon">🔌</div>
          <h2>Sign-to-Text Backend is Offline</h2>
          <p>Start the FastAPI server to use this component:</p>
          <code className="sign-to-text-code">
            cd Backend/sign_to_text<br />
            pip install -r requirements.txt<br />
            uvicorn main:app --host 127.0.0.1 --port 8001
          </code>
        </div>
      ) : (
        <iframe
          src={`${SIGN_API_URL}/fresh`}
          title="Sign to Text Recognition"
          className="sign-to-text-iframe"
          allow="camera; microphone"
        />
      )}
    </div>
  );
}
