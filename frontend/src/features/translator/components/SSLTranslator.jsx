import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import "../../../shared/styles/App.css";

function App() {
  const [inputText, setInputText] = useState("");
  const [meaningText, setMeaningText] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  const [grammarSequence, setGrammarSequence] = useState([]);
  const [animationBlocks, setAnimationBlocks] = useState([]);  // per-clause ordered blocks
  const [wordTimings, setWordTimings] = useState([]);
  const [activeWordIndex, setActiveWordIndex] = useState(-1);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [avatarStyle, setAvatarStyle] = useState("normal");
  const [translationError, setTranslationError] = useState("");

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
    setTranslationError("");

    try {
      const res = await axios.post("http://localhost:5002/translate", {
        text: inputText,
        style: avatarStyle,
      });

      // Handle graceful backend errors (concept not found, etc.)
      if (res.data.error) {
        setTranslationError(res.data.message || "Sign Language video not found. Please try a different word.");
        return;
      }

      setVideoUrl(res.data.video_url || null);

      // Prefer per-clause animation_blocks (new parser) for ordered chip display
      const blocks = res.data.animation_blocks || [];
      if (blocks.length > 0) {
        setAnimationBlocks(blocks);
        // Build flat sequence from blocks for backward-compat highlighting
        setGrammarSequence(blocks.flatMap(b => b.display_sinhala || []));
      } else {
        setAnimationBlocks([]);
        setGrammarSequence(res.data.ssl_grammar_display || []);
      }

      setWordTimings(res.data.word_timings || []);
    } catch (e) {
      setTranslationError("සම්බන්ධ කිරීමේ ගැටලුවක්. Flask සේවාව ධාවනය වේදැයි පරීක්ෂා කරන්න. 😊");
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

            {translationError && (
              <div className="error-msg" style={{
                background: "#fff3cd", border: "2px solid #ffc107",
                borderRadius: "14px", padding: "14px 18px",
                color: "#856404", fontSize: "1rem", marginTop: "12px",
                fontFamily: "var(--sl-font)"
              }}>
                ⚠️ {translationError}
              </div>
            )}

            {grammarSequence.length > 0 && (
              <div className="grammar-zone">
                <div className="meaning-box">
                  <h3>🗣️ අපි කියන්නේ:</h3>
                  <p className="meaning-text">"{meaningText}"</p>
                </div>

                <div className="sign-box">
                  <h3>🤟 අපි Sign කරන්නෙ:</h3>
                  {animationBlocks.length > 0 ? (
                    // Per-clause display — each clause is a separate chip row
                    <div className="clause-blocks">
                      {animationBlocks.map((block, bi) => (
                        <div key={bi} className="clause-row">
                          {block.display_sinhala.map((w, wi) => {
                            // Map word back to overall flat index for highlight
                            const flatIdx = animationBlocks
                              .slice(0, bi)
                              .reduce((acc, b) => acc + (b.display_sinhala?.length || 0), 0) + wi;
                            return (
                              <span
                                key={wi}
                                className={`chip ${flatIdx === activeWordIndex ? "active" : ""}`}
                              >
                                {w}
                              </span>
                            );
                          })}
                          {block.tense && block.tense !== "UNKNOWN" && (
                            <span className="tense-badge">{block.tense === "PAST" ? "⬅️" : block.tense === "FUTURE" ? "➡️" : "●"}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    // Fallback: flat chip list (old behaviour)
                    <div className="chips">
                      {grammarSequence.map((w, i) => (
                        <span key={i} className={`chip ${i === activeWordIndex ? "active" : ""}`}>{w}</span>
                      ))}
                    </div>
                  )}
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
