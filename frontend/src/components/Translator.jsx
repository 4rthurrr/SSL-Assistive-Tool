import { useState } from "react";
import axios from "axios";
import "../App.css";

const CULTURAL_EMOJIS = ["🪷","🐘","🦚","🌿","🍃","🥥","☀️","🏝️","🎋","🐾"];

function randomEmoji() {
  return CULTURAL_EMOJIS[Math.floor(Math.random() * CULTURAL_EMOJIS.length)];
}

// Decorative floating emoji spots rendered behind the page
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
          style={{ position:"absolute", fontSize:s.fontSize, opacity:.18,
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
    <div className="sl-bg" style={{ position:"relative", minHeight:"100vh" }}>
      <FloatingDecos />

      {/* ── Header ─────────────────────────────────────── */}
      <header className="sl-header" style={{ zIndex:10, position:"relative" }}>
        <div style={{ display:"flex", alignItems:"center", gap:"12px" }}>
          <span style={{ fontSize:"2.2rem" }}>🪷</span>
          <div>
            <h1 style={{ margin:0, fontSize:"1.6rem", fontWeight:900, color:"#fff",
              textShadow:"2px 2px 6px rgba(0,0,0,.4)" }}>
              සිංහල භාෂා
            </h1>
            <p style={{ margin:0, fontSize:".8rem", color:"rgba(255,255,255,.85)",
              fontFamily:"var(--sl-font)" }}>
              Sinhala Language Translator
            </p>
          </div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:"10px" }}>
          <div className="sl-lang-badge">
            <span>🇬🇧</span> EN → SI <span>🇱🇰</span>
          </div>
          <span style={{ fontSize:"1.8rem" }}>🐘</span>
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────── */}
      <main className="main-container" style={{ position:"relative", zIndex:10 }}>

        {/* Hero title */}
        <div className="sl-trans-hero">
          <div style={{ fontSize:"3.5rem", marginBottom:"10px" }}>
            🪷&nbsp;🤟&nbsp;🪷
          </div>
          <h1>ඉංග්‍රීසි → සිංහල</h1>
          <p>Type English text and get the Sinhala translation instantly!</p>
        </div>

        <div className="split-layout">
          {/* ── Left Panel: Input ───────────────────── */}
          <div className="left-panel">
            <div className="input-section sl-card">
              <div style={{ display:"flex", alignItems:"center", gap:"8px",
                marginBottom:"10px" }}>
                <span style={{ fontSize:"1.5rem" }}>✏️</span>
                <h3 style={{ margin:0, color:"var(--sl-crimson)", fontSize:"1.1rem",
                  fontFamily:"var(--sl-font)", fontWeight:700 }}>
                  English Text
                </h3>
              </div>
              <textarea
                placeholder="Type English words here…  (Ctrl+Enter to translate)"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={5}
                style={{ width:"100%", borderRadius:"14px", padding:"14px",
                  fontSize:"1.05rem", fontFamily:"var(--sl-font)",
                  border:"2px solid rgba(244,168,32,.5)", resize:"vertical",
                  outline:"none", background:"var(--sl-warmwhite)",
                  boxSizing:"border-box", minHeight:"120px" }}
              />

              <div className="action-row">
                <button
                  onClick={handleTranslate}
                  disabled={loading || !text.trim()}
                  style={{ flex:1, fontSize:"1.1rem", padding:"12px 0",
                    borderRadius:"24px", display:"flex", alignItems:"center",
                    justifyContent:"center", gap:"8px" }}
                >
                  {loading ? "⏳ Translating…" : "🪷 Translate to Sinhala"}
                </button>

                {text && (
                  <button
                    onClick={handleClear}
                    style={{ background:"rgba(139,26,26,.12)", color:"var(--sl-crimson)",
                      border:"2px solid rgba(139,26,26,.25)", borderRadius:"20px",
                      padding:"12px 18px", fontSize:"1rem",
                      fontFamily:"var(--sl-font)", fontWeight:700, cursor:"pointer",
                      transition:"background .2s" }}
                  >
                    ✖ Clear
                  </button>
                )}
              </div>

              <p style={{ margin:"8px 0 0", fontSize:".75rem",
                color:"#b87d00", fontFamily:"var(--sl-font)" }}>
                💡 Tip: Press <kbd style={{ background:"rgba(244,168,32,.2)",
                borderRadius:"6px", padding:"1px 6px" }}>Ctrl</kbd> +
                <kbd style={{ background:"rgba(244,168,32,.2)",
                borderRadius:"6px", padding:"1px 6px" }}>Enter</kbd> to translate
              </p>
            </div>

            {/* Cultural fact card */}
            <div className="sl-card" style={{ background:"linear-gradient(135deg,#fffbe6,#fff3cd)",
              border:"3px solid var(--sl-saffron)", textAlign:"center" }}>
              <div style={{ fontSize:"2rem", marginBottom:"6px" }}>🦚</div>
              <p style={{ margin:0, color:"#7a4f20", fontSize:".9rem",
                fontFamily:"var(--sl-font)", fontWeight:600 }}>
                Sinhala is one of Sri Lanka's official languages.<br/>
                Over <strong>16 million</strong> people speak it! 🇱🇰
              </p>
            </div>
          </div>

          {/* ── Right Panel: Output ─────────────────── */}
          <div className="right-panel">
            <div className="video-section sl-card" style={{ minHeight:"320px",
              display:"flex", flexDirection:"column", justifyContent:"center" }}>
              <div style={{ display:"flex", alignItems:"center", gap:"8px",
                marginBottom:"14px" }}>
                <span style={{ fontSize:"1.5rem" }}>🇱🇰</span>
                <h3 style={{ margin:0, color:"var(--sl-jungle)", fontSize:"1.1rem",
                  fontFamily:"var(--sl-font)", fontWeight:700 }}>
                  Sinhala Translation (සිංහල)
                </h3>
              </div>

              {/* Error state */}
              {error && (
                <div className="sl-pop" style={{ background:"#ffe5e5",
                  border:"3px solid #e74c3c", borderRadius:"16px",
                  padding:"16px", textAlign:"center" }}>
                  <span style={{ fontSize:"2rem" }}>😢</span>
                  <p style={{ margin:"8px 0 0", color:"#c0392b",
                    fontFamily:"var(--sl-font)", fontWeight:700 }}>{error}</p>
                </div>
              )}

              {/* Loading */}
              {loading && (
                <div className="loading" style={{ flexDirection:"column", gap:"14px" }}>
                  <div style={{ fontSize:"3rem" }}
                    className="sl-float">🪷</div>
                  <span>Translating your words…</span>
                </div>
              )}

              {/* Empty state */}
              {!loading && !error && !translated && (
                <div className="empty">
                  <span>🇱🇰</span>
                  <p style={{ fontFamily:"var(--sl-font)", fontSize:"1rem",
                    color:"#c8a87a" }}>
                    Your Sinhala translation will appear here
                  </p>
                  <p style={{ fontSize:"1.4rem", color:"rgba(244,168,32,.5)",
                    fontFamily:"var(--sl-font)", letterSpacing:"4px" }}>
                    ☀️ 🪷 🐘 🦚 🥥
                  </p>
                </div>
              )}

              {/* Result */}
              {!loading && translated && (
                <div className={`sl-output-box ${celebration ? "sl-pop" : ""}`}>
                  {celebration && (
                    <div style={{ fontSize:"2.5rem", textAlign:"center", marginBottom:"8px" }}>
                      🎉&nbsp;🪷&nbsp;🎊
                    </div>
                  )}
                  <p className="sl-output-label">සිංහල පරිවර්තනය</p>
                  <p className="sl-output-sinhala">{translated}</p>
                  <div style={{ display:"flex", gap:"8px", justifyContent:"center",
                    marginTop:"14px", flexWrap:"wrap" }}>
                    <button
                      onClick={() => navigator.clipboard?.writeText(translated)}
                      style={{ background:"var(--sl-btn-primary)", color:"#fff",
                        border:"none", borderRadius:"18px", padding:"8px 20px",
                        fontSize:".9rem", fontFamily:"var(--sl-font)",
                        fontWeight:700, cursor:"pointer",
                        boxShadow:"0 3px 10px rgba(192,57,43,.35)",
                        transition:"transform .15s" }}
                      onMouseOver={e => e.target.style.transform="translateY(-2px)"}
                      onMouseOut={e => e.target.style.transform="translateY(0)"}
                    >
                      📋 Copy Sinhala
                    </button>
                    <button
                      onClick={handleClear}
                      style={{ background:"rgba(27,122,56,.12)",
                        color:"var(--sl-jungle)", border:"2px solid rgba(27,122,56,.35)",
                        borderRadius:"18px", padding:"8px 20px", fontSize:".9rem",
                        fontFamily:"var(--sl-font)", fontWeight:700, cursor:"pointer" }}
                    >
                      🔄 New Translation
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* How it works card */}
            <div className="sl-card" style={{ marginTop:"16px" }}>
              <h4 style={{ margin:"0 0 12px", color:"var(--sl-crimson)",
                fontFamily:"var(--sl-font)", fontSize:"1rem", fontWeight:700,
                display:"flex", alignItems:"center", gap:"8px" }}>
                <span>🪷</span> How It Works
              </h4>
              <div style={{ display:"flex", flexDirection:"column", gap:"10px" }}>
                {[
                  { icon:"1️⃣", text:"Type any English word or sentence above" },
                  { icon:"2️⃣", text:'Click "Translate to Sinhala" or press Ctrl+Enter' },
                  { icon:"3️⃣", text:"See the Sinhala translation appear instantly" },
                  { icon:"4️⃣", text:"Copy it and use it in your learning!" },
                ].map(({ icon, text }) => (
                  <div key={icon} style={{ display:"flex", gap:"10px", alignItems:"flex-start" }}>
                    <span style={{ fontSize:"1.1rem" }}>{icon}</span>
                    <p style={{ margin:0, color:"#6b4226", fontFamily:"var(--sl-font)",
                      fontSize:".88rem" }}>{text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* ── Footer decoration ──────────────────────── */}
      <footer style={{ textAlign:"center", padding:"20px",
        color:"rgba(139,26,26,.4)", fontFamily:"var(--sl-font)",
        fontSize:"1.3rem", letterSpacing:"8px", userSelect:"none",
        position:"relative", zIndex:10 }}>
        🪷 🐘 🦚 🌿 🥥 🪷 🐘 🦚 🌿 🥥
      </footer>
    </div>
  );
}

export default Translator;
