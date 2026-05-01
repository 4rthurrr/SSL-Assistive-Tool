import { useState } from "react";
import axios from "axios";
import "../../../shared/styles/App.css";
import "./Translator.css";

const CULTURAL_EMOJIS = ["🪷","🐘","🦚","🌿","🍃","🥥","☀️","🏝️","🎋","🐾"];

function FloatingDecos() {
  const spots = [
    { top:"8%",  left:"5%",  fontSize:"3rem", emoji:"🪷", delay:"0s"   },
    { top:"15%", right:"6%", fontSize:"2.5rem", emoji:"🐘", delay:".4s"  },
    { top:"40%", left:"3%",  fontSize:"2rem",   emoji:"🌿", delay:"1s"   },
    { top:"55%", right:"4%", fontSize:"2.5rem", emoji:"🦚", delay:"0.7s" },
    { top:"75%", left:"7%",  fontSize:"2rem",   emoji:"🥥", delay:"1.4s" },
    { top:"85%", right:"8%", fontSize:"2rem",   emoji:"🍃", delay:".6s"  },
    { top:"25%", left:"50%", fontSize:"1.8rem", emoji:"☀️", delay:"2s"   },
  ];
  return (
    <div style={{ position:"absolute", inset:0, overflow:"hidden", pointerEvents:"none", zIndex:0 }}>
      {spots.map((s, i) => (
        <div key={i} className="sl-float"
          style={{ position:"absolute", fontSize:s.fontSize, opacity:.12,
            top:s.top, left:s.left, right:s.right, animationDelay:s.delay }}>
          {s.emoji}
        </div>
      ))}
    </div>
  );
}

function Translator() {
  const [text, setText] = useState("");
  const [translated, setTranslated] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [celebration, setCelebration] = useState(false);

  const handleTranslate = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    setTranslated("");
    try {
      const res = await axios.get("https://api.mymemory.translated.net/get", {
        params: { q: text.trim(), langpair: "en|si" },
      });
      const result = res.data?.responseData?.translatedText || "";
      if (!result || result === text) {
        setError("Translation unavailable. Please try again.");
      } else {
        setTranslated(result);
        setCelebration(true);
        setTimeout(() => setCelebration(false), 1800);
      }
    } catch (err) {
      console.error("Error translating:", err);
      setError("Could not connect. Check your internet and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && e.ctrlKey) handleTranslate();
  };

  const handleClear = () => {
    setText("");
    setTranslated("");
    setError("");
  };

  return (
    <div className="sl-page sl-bg">
      <FloatingDecos />

      {/* ── Main Content ─────────────────────────────── */}
      <main className="main-container" style={{ position:"relative", zIndex:10 }}>

        {/* Hero title */}
        <div className="sl-hero">
          <span className="sl-hero-icon">🤟 ✨ 🇱🇰</span>
          <h1>ඉංග්‍රීසි → සිංහල</h1>
          <p>Translate English words to Sinhala buddy! 🦁</p>
        </div>

        <div className="split-layout">
          {/* ── Left Panel: Input ───────────────────── */}
          <div className="left-panel">
            <div className="input-section sl-card">
              <div style={{ display:"flex", alignItems:"center", gap:"10px", marginBottom:"15px" }}>
                <span style={{ fontSize:"1.8rem" }}>✏️</span>
                <h3 style={{ margin:0, color:"var(--primary-dark)", fontSize:"1.2rem", fontWeight:800 }}>
                  English Text
                </h3>
              </div>
              
              <textarea
                placeholder="Type English words here…  (Ctrl+Enter to translate)"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={5}
              />

              <div className="action-row">
                <button
                  onClick={handleTranslate}
                  disabled={loading || !text.trim()}
                  className="sl-btn-primary"
                  style={{ flex: 1 }}
                >
                  {loading ? "⏳ Translating…" : "✨ Translate to Sinhala"}
                </button>

                {text && (
                  <button onClick={handleClear} className="nav-btn" style={{ background: "var(--error)", borderColor: "var(--error)", color: "white" }}>
                    ✖ Clear
                  </button>
                )}
              </div>

              <p style={{ margin:"12px 0 0", fontSize:".8rem", color:"var(--text-muted)", fontWeight:600 }}>
                💡 Tip: Press <kbd style={{ background:"var(--primary-light)", borderRadius:"6px", padding:"2px 6px" }}>Ctrl</kbd> + 
                <kbd style={{ background:"var(--primary-light)", borderRadius:"6px", padding:"2px 6px" }}>Enter</kbd> to translate
              </p>
            </div>

            {/* Cultural fact card */}
            <div className="sl-fact-card">
              <div className="sl-fact-icon">🦚</div>
              <p className="sl-fact-text">
                Sinhala is one of Sri Lanka's official languages.<br/>
                Over <strong>16 million</strong> people speak it! 🇱🇰
              </p>
            </div>
          </div>

          {/* ── Right Panel: Output ─────────────────── */}
          <div className="right-panel">
            <div className="video-section sl-card" style={{ minHeight:"320px", display:"flex", flexDirection:"column" }}>
              <div style={{ display:"flex", alignItems:"center", gap:"10px", marginBottom:"15px" }}>
                <span style={{ fontSize:"1.8rem" }}>🇱🇰</span>
                <h3 style={{ margin:0, color:"var(--accent-dark)", fontSize:"1.2rem", fontWeight:800 }}>
                  Sinhala Translation
                </h3>
              </div>

              {/* Error state */}
              {error && (
                <div className="error-msg sl-pop">
                   😢 {error}
                </div>
              )}

              {/* Loading */}
              {loading && (
                <div className="loading">
                  <div className="sl-float" style={{ fontSize:"3rem" }}>🪷</div>
                  <span>Translating your words…</span>
                </div>
              )}

              {/* Empty state */}
              {!loading && !error && !translated && (
                <div className="empty">
                  <span>✨</span>
                  <p>Your Sinhala translation will appear here!</p>
                </div>
              )}

              {/* Result */}
              {!loading && translated && (
                <div className={`sl-output-card ${celebration ? "sl-pop" : ""}`}>
                  {celebration && (
                    <div style={{ fontSize:"2.5rem", textAlign:"center", marginBottom:"10px" }}>
                      🎉 🪷 🎊
                    </div>
                  )}
                  <p className="sl-output-title">සිංහල පරිවර්තනය</p>
                  <p className="sl-result-text">{translated}</p>
                  
                  <div className="controls">
                    <button
                      onClick={() => navigator.clipboard?.writeText(translated)}
                      style={{ background:"var(--primary)", color:"#fff" }}
                    >
                      📋 Copy
                    </button>
                    <button
                      onClick={handleClear}
                      className="nav-btn"
                      style={{ background:"var(--accent)", borderColor:"var(--accent)", color:"white" }}
                    >
                      🔄 New
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* How it works card */}
            <div className="sl-tip-card">
              <h4 className="sl-tip-title">
                <span>🌟</span> How It Works
              </h4>
              <div style={{ display:"flex", flexDirection:"column", gap:"12px" }}>
                {[
                  { icon:"1️⃣", text:"Type any English word or sentence" },
                  { icon:"2️⃣", text:'Click "Translate" or press Ctrl+Enter' },
                  { icon:"3️⃣", text:"See the Sinhala translation instantly!" },
                  { icon:"4️⃣", text:"Copy it and use it in your learning!" },
                ].map(({ icon, text }) => (
                  <div key={icon} className="sl-tip-item">
                    <span className="sl-tip-icon">{icon}</span>
                    <p className="sl-tip-desc">{text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="sl-footer-deco">
        🪷 🐘 🦚 🌿 🥥 🪷 🐘 🦚 🌿 🥥
      </footer>
    </div>
  );
}

export default Translator;
