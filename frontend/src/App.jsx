import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Register from "./components/Register";
import Login from "./components/Login";
import Translator from "./components/Translator";
import GameSelection from "./components/GameSelection";
import GameUserForm from "./components/GameUserForm";
import SinhalaWordPuzzle from "./components/SinhalaWordPuzzle";
import AIAnalyticsDashboard from './components/AIAnalyticsDashboard';
import SentenceGame from './components/sentencegame';
import SSLTranslator from './App.js';
import "./App.css";

function App() {
  return (
    <Router>
      <div>
        {/* ── Sri Lankan Cultural Navbar ────────────── */}
        <nav style={{
          background: "linear-gradient(135deg, #C0392B, #8B1A1A, #F4A820)",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          boxShadow: "0 4px 18px rgba(139,26,26,.35)",
          fontFamily: "'Fredoka One', 'Comic Sans MS', cursive",
          position: "relative",
          overflow: "hidden"
        }}>
          {/* Decorative lotus row */}
          <div style={{ position:"absolute", bottom:"-4px", left:0, right:0,
            textAlign:"center", fontSize:".9rem", opacity:.2, letterSpacing:"6px",
            pointerEvents:"none" }}>
            🪷 🌿 🪷 🌿 🪷 🌿 🪷 🌿 🪷 🌿 🪷
          </div>

          <Link to="/" style={{ color:"#fff", fontWeight:900, fontSize:"1.3rem",
            textDecoration:"none", display:"flex", alignItems:"center", gap:"8px",
            textShadow:"2px 2px 5px rgba(0,0,0,.4)", zIndex:1 }}>
            🪷 සංඥා භාෂා
          </Link>

          <div style={{ display:"flex", gap:"12px", alignItems:"center", zIndex:1 }}>
            {[
              { to:"/",             label:"🏠 Home"       },
              { to:"/ssl-translator", label:"✨ Translator" },
              { to:"/game-register",  label:"🎮 Games"     },
              { to:"/login",          label:"👤 Sign In"   },
            ].map(({ to, label }) => (
              <Link key={to} to={to} style={{
                color:"#fff", textDecoration:"none", fontWeight:700,
                fontSize:".95rem", padding:"6px 16px", borderRadius:"20px",
                background:"rgba(255,255,255,.18)", border:"2px solid rgba(255,255,255,.35)",
                transition:"background .2s, transform .15s"
              }}
              onMouseOver={e => { e.target.style.background="rgba(255,255,255,.38)"; e.target.style.transform="translateY(-2px)"; }}
              onMouseOut={e => { e.target.style.background="rgba(255,255,255,.18)"; e.target.style.transform="translateY(0)"; }}
              >
                {label}
              </Link>
            ))}
          </div>
        </nav>

        <div>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/translate" element={<Translator />} />
            
            {/* SSL Translator */}
            <Route path="/ssl-translator" element={<SSLTranslator />} />

            {/* Game Flow */}
            <Route path="/game-register" element={<GameUserForm />} />
            <Route path="/gameselection" element={<GameSelection />} />
            <Route path="/game/puzzle" element={<SinhalaWordPuzzle />} />
            <Route path="/ai-analytics" element={<AIAnalyticsDashboard />} />
            <Route path="/game/sentence" element={<SentenceGame />} />

          </Routes>
        </div>
      </div>
    </Router>
  );
}

/* ── Sri Lankan Cultural Home Page ─────────────── */
const HomePage = () => (
  <div className="sl-bg" style={{ minHeight:"100vh", fontFamily:"var(--sl-font)",
    display:"flex", flexDirection:"column", alignItems:"center",
    justifyContent:"center", gap:"32px", padding:"40px 20px",
    position:"relative", overflow:"hidden" }}>

    {/* Floating cultural decos */}
    {[
      { t:"5%",  l:"4%",  f:"3rem",   e:"🪷",  d:"0s"   },
      { t:"8%",  r:"5%",  f:"2.5rem", e:"🐘",  d:".5s"  },
      { t:"50%", l:"2%",  f:"2rem",   e:"🦚",  d:"1s"   },
      { t:"80%", r:"3%",  f:"2.5rem", e:"🌿",  d:".3s"  },
      { t:"90%", l:"6%",  f:"2rem",   e:"🥥",  d:"1.5s" },
    ].map((s, i) => (
      <div key={i} className="sl-float" style={{
        position:"absolute", top:s.t, left:s.l, right:s.r,
        fontSize:s.f, opacity:.2, animationDelay:s.d, pointerEvents:"none"
      }}>{s.e}</div>
    ))}

    {/* Hero Text */}
    <div style={{ textAlign:"center", zIndex:1 }}>
      <div style={{ fontSize:"5rem", marginBottom:"12px" }}>🪷&nbsp;🤟&nbsp;🪷</div>
      <h1 style={{ margin:"0 0 8px", fontSize:"clamp(2.2rem,5vw,3.5rem)", fontWeight:900,
        background:"linear-gradient(135deg,#C0392B,#8B1A1A,#F4A820)",
        WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
        backgroundClip:"text", filter:"drop-shadow(2px 2px 4px rgba(0,0,0,.15))" }}>
        සංඥා භාෂා ඉගෙන ගනිමු!
      </h1>
      <p style={{ margin:0, fontSize:"1.25rem", color:"#7a4f20", fontWeight:600 }}>
        Sinhala Sign Language Learning Platform
      </p>
      <div style={{ marginTop:"14px", display:"inline-flex", gap:"8px",
        background:"linear-gradient(135deg,#C0392B,#F4A820)",
        color:"#fff", borderRadius:"30px", padding:"8px 20px",
        fontSize:".95rem", fontWeight:700,
        boxShadow:"0 4px 12px rgba(192,57,43,.35)" }}>
        🇱🇰 &nbsp;Sri Lanka &nbsp;🇱🇰
      </div>
    </div>

    {/* Feature Cards */}
    <div style={{ display:"flex", flexWrap:"wrap", gap:"24px",
      justifyContent:"center", zIndex:1 }}>
      {[
        {
          to: "/ssl-translator",
          icon: "✨",
          title: "SSL Translator",
          titleSi: "පරිවර්තකය",
          desc: "Type Sinhala text and watch it signed by an avatar",
          btnLabel: "Open →",
          btnBg: "linear-gradient(135deg,#C0392B,#8B1A1A)",
          border: "3px solid rgba(192,57,43,.3)"
        },
        {
          to: "/game-register",
          icon: "🎮",
          title: "Learning Games",
          titleSi: "ඉගෙනුම් ක්‍රීඩා",
          desc: "Practice sign language with fun interactive games",
          btnLabel: "Play →",
          btnBg: "linear-gradient(135deg,#27AE60,#1B7A38)",
          border: "3px solid rgba(27,122,56,.3)"
        },
        {
          to: "/translate",
          icon: "🪷",
          title: "Text Translator",
          titleSi: "පෙළ පරිවර්තකය",
          desc: "Translate English words to Sinhala instantly",
          btnLabel: "Translate →",
          btnBg: "linear-gradient(135deg,#F4A820,#C0392B)",
          border: "3px solid rgba(244,168,32,.4)"
        },
      ].map(({ to, icon, title, titleSi, desc, btnLabel, btnBg, border }) => (
        <Link key={to} to={to} style={{
          background:"#fff", borderRadius:"28px",
          boxShadow:"0 8px 30px rgba(139,26,26,.12)",
          padding:"32px 28px", display:"flex", flexDirection:"column",
          alignItems:"center", gap:"12px", textDecoration:"none",
          width:"220px", border, transition:"transform .2s, box-shadow .2s",
          fontFamily:"var(--sl-font)"
        }}
        onMouseOver={e => { e.currentTarget.style.transform="scale(1.05)"; e.currentTarget.style.boxShadow="0 12px 40px rgba(139,26,26,.2)"; }}
        onMouseOut={e => { e.currentTarget.style.transform="scale(1)"; e.currentTarget.style.boxShadow="0 8px 30px rgba(139,26,26,.12)"; }}
        >
          <span style={{ fontSize:"3.5rem" }}>{icon}</span>
          <h2 style={{ margin:"0 2px", fontSize:"1.3rem", fontWeight:900,
            color:"#2C1810", textAlign:"center" }}>{title}</h2>
          <p style={{ margin:0, color:"#8B6347", fontSize:".85rem",
            textAlign:"center", fontWeight:600 }}>{titleSi}</p>
          <p style={{ margin:0, color:"#a0826a", fontSize:".8rem",
            textAlign:"center", lineHeight:1.4 }}>{desc}</p>
          <span style={{ background:btnBg, color:"#fff", padding:"10px 22px",
            borderRadius:"22px", fontWeight:700, fontSize:".95rem",
            marginTop:"4px", boxShadow:"0 3px 10px rgba(0,0,0,.25)" }}>
            {btnLabel}
          </span>
        </Link>
      ))}
    </div>

    {/* Cultural strip */}
    <div style={{ color:"rgba(139,26,26,.25)", fontSize:"1.4rem",
      letterSpacing:"10px", userSelect:"none", zIndex:1 }}>
      🪷 🐘 🦚 🌿 🥥 🪷 🐘 🦚 🌿 🥥
    </div>
  </div>
);

export default App;