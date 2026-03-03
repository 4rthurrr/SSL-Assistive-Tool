import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import "./App.css";

function App() {
  const [inputText, setInputText] = useState("");
  const [meaningText, setMeaningText] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  const [grammarSequence, setGrammarSequence] = useState([]);
  const [wordTimings, setWordTimings] = useState([]);
  const [activeWordIndex, setActiveWordIndex] = useState(-1);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [avatarStyle, setAvatarStyle] = useState("normal");

  const videoRef = useRef(null);

  /* Playback speed */
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackSpeed;
    }
  }, [playbackSpeed]);

  /* Reload video */
  useEffect(() => {
    if (videoRef.current && videoUrl) {
      videoRef.current.load();
      videoRef.current.play().catch(() => { });
      setIsPlaying(true);
    }
  }, [videoUrl]);

  const handleTranslate = async () => {
    if (!inputText.trim()) return;

    setLoading(true);
    setMeaningText(inputText); // Store the meaning text
    setVideoUrl(null);
    setGrammarSequence([]);
    setWordTimings([]);
    setActiveWordIndex(-1);
    setShowConfetti(false);

    try {
      const res = await axios.post("http://localhost:5001/translate", {
        text: inputText,
        style: avatarStyle,
      });

      setVideoUrl(res.data.video_url || null);
      setGrammarSequence(res.data.ssl_grammar_display || []);
      setWordTimings(res.data.word_timings || []);
    } catch (e) {
      alert("අපොයි! පොඩි ගැටලුවක්. ආයේ උත්සාහ කරන්න 😊");
    } finally {
      setLoading(false);
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleReplay = () => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = 0;
    videoRef.current.play();
    setIsPlaying(true);
  };

  const handleVideoEnd = () => {
    setIsPlaying(false);
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 2500);
    setActiveWordIndex(-1);
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current || wordTimings.length === 0) return;
    const t = videoRef.current.currentTime;
    const idx = wordTimings.findIndex(
      (w) => t >= w.start && t < w.end
    );
    if (idx !== -1) setActiveWordIndex(idx);
  };

  return (
    <div className="kids-app">
      <header className="kids-header">
        <div className="header-nav">
          <Link to="/" className="nav-btn">🏠 Home</Link>
          <Link to="/game-register" className="nav-btn">🎮 Games</Link>
        </div>
        <h1>🦁 Sign Language Buddy 🐘</h1>
        <p>සිංහලෙන් කියන්න, අපි Sign කරලා පෙන්වන්නම් 🤟</p>
      </header>

      <main className="main-container">
        <div className="split-layout">

          {/* LEFT */}
          <div className="left-panel">
            <div className="input-section">
              <h2>✏️ ඔයාගේ වචන ලියන්න</h2>

              <textarea
                value={inputText}
                placeholder="මෙතන ලියන්න... 🌈 (උදා: මම ගෙදරින් ගියා)"
                onChange={(e) => {
                  setInputText(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = e.target.scrollHeight + "px";
                }}
              />

              <div className="action-row">
                <button onClick={handleTranslate} disabled={loading}>
                  {loading ? "🎬 වීඩියෝ හදනවා..." : "✨ Sign බලන්න"}
                </button>

                <div className="mode-toggle">
                  <label>
                    <input
                      type="radio"
                      checked={avatarStyle === "normal"}
                      onChange={() => setAvatarStyle("normal")}
                    />
                    👤 Normal
                  </label>

                  <label>
                    <input
                      type="radio"
                      checked={avatarStyle === "skeleton"}
                      onChange={() => setAvatarStyle("skeleton")}
                    />
                    💀 Skeleton
                  </label>

                  <label>
                    <input
                      type="radio"
                      checked={avatarStyle === "ai_real"}
                      onChange={() => setAvatarStyle("ai_real")}
                    />
                    🤖 AI Avatar
                  </label>
                </div>
              </div>
            </div>

            {grammarSequence.length > 0 && (
              <div className="grammar-zone">
                <div className="meaning-box">
                  <h3>🗣️ අපි කියන්නේ:</h3>
                  <p className="meaning-text">"{meaningText}"</p>
                </div>

                <div className="sign-box">
                  <h3>🤟 අපි Sign කරන්නෙ:</h3>
                  <div className="chips">
                    {grammarSequence.map((w, i) => (
                      <span
                        key={i}
                        className={`chip ${i === activeWordIndex ? "active" : ""
                          }`}
                      >
                        {w}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT */}
          <div className="right-panel">
            <div className="video-section">
              {videoUrl ? (
                <>


                  <video
                    ref={videoRef}
                    src={videoUrl}
                    onClick={togglePlay}
                    onEnded={handleVideoEnd}
                    onTimeUpdate={handleTimeUpdate}
                    controls={false}
                  />

                  <div className="controls">
                    <button onClick={() => setPlaybackSpeed(0.5)}>🐢</button>
                    <button onClick={togglePlay}>
                      {isPlaying ? "⏸️" : "▶️"}
                    </button>
                    <button onClick={handleReplay}>🔄</button>
                    <button onClick={() => setPlaybackSpeed(1)}>🐰</button>
                  </div>


                </>
              ) : (
                !loading && (
                  <div className="empty">
                    👋 වාක්‍යයක් ටයිප් කරලා බලන්න
                  </div>
                )
              )}

              {loading && <div className="loading">🎬 Loading...</div>}
            </div>

            {showConfetti && (
              <div className="confetti">🎉 නියමයි! 🌟</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
