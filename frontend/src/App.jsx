import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Register from "./features/auth/components/Register";
import Login from "./features/auth/components/Login";
import Translator from "./features/translator/components/Translator";
import GameSelection from "./features/games/components/GameSelection";
import GameUserForm from "./features/games/components/GameUserForm";
import SinhalaWordPuzzle from "./features/games/puzzle/SinhalaWordPuzzle";
import AIAnalyticsDashboard from './features/analytics/components/AIAnalyticsDashboard';
import SentenceGame from './features/games/sentence/SentenceGame';
import SSLTranslator from './features/translator/components/SSLTranslator';
import ProtectedRoute from './shared/components/ProtectedRoute';
import "./shared/styles/App.css";

/* ── Auth-aware Navbar ─────────────────────────── */
function Navbar() {
  const navigate = useNavigate();
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
  });

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    navigate("/login");
  };

  // Re-read user from storage on every render (covers post-login redirect)
  useEffect(() => {
    const stored = localStorage.getItem("user");
    try { setUser(stored ? JSON.parse(stored) : null); } catch { setUser(null); }
  }, []);

  const isLoggedIn = !!localStorage.getItem("token");

  return (
    <nav style={{
      background: "linear-gradient(135deg, #C0392B, #8B1A1A, #F4A820)",
      padding: "12px 24px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      boxShadow: "0 4px 18px rgba(139,26,26,.35)",
      fontFamily: "'Fredoka One', 'Comic Sans MS', cursive",
      position: "sticky",
      top: 0,
      zIndex: 100,
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

      <div style={{ display:"flex", gap:"10px", alignItems:"center", zIndex:1 }}>
        <NavLink to="/" label="🏠 Home" />
        <NavLink to="/ssl-translator" label="✨ Translator" locked={!isLoggedIn} />
        <NavLink to={user?.hasTakenQuiz ? "/gameselection" : "/game-register"} label="🎮 Games" locked={!isLoggedIn} />

        {isLoggedIn ? (
          <>
            <span style={{
              color:"#fff", fontWeight:700, fontSize:".85rem",
              padding:"6px 12px", borderRadius:"20px",
              background:"rgba(255,255,255,.18)",
              border:"2px solid rgba(255,255,255,.35)"
            }}>
              👋 {user?.name?.split(" ")[0] || "User"}
            </span>
            <button onClick={handleLogout} style={{
              color:"#C0392B", background:"#fff", border:"none", cursor:"pointer",
              fontWeight:800, fontSize:".85rem", padding:"6px 16px",
              borderRadius:"20px", boxShadow:"0 2px 8px rgba(0,0,0,.2)",
              transition:"transform .15s"
            }}>
              🚪 Logout
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login"    label="👤 Sign In" />
            <NavLink to="/register" label="📝 Register" highlight />
          </>
        )}
      </div>
    </nav>
  );
}

function NavLink({ to, label, locked, highlight }) {
  if (locked) {
    return (
      <Link to="/login" title="Login required" style={{
        color:"rgba(255,255,255,.6)", textDecoration:"none", fontWeight:700,
        fontSize:".92rem", padding:"6px 14px", borderRadius:"20px",
        background:"rgba(255,255,255,.08)", border:"2px dashed rgba(255,255,255,.3)",
        display:"flex", alignItems:"center", gap:"4px"
      }}>
        🔒 {label.split(" ").slice(1).join(" ")}
      </Link>
    );
  }
  return (
    <Link to={to} style={{
      color:"#fff", textDecoration:"none", fontWeight:700,
      fontSize:".92rem", padding:"6px 16px", borderRadius:"20px",
      background: highlight ? "rgba(255,255,255,.95)" : "rgba(255,255,255,.18)",
      color: highlight ? "#C0392B" : "#fff",
      border:"2px solid rgba(255,255,255,.35)",
      transition:"background .2s, transform .15s"
    }}>
      {label}
    </Link>
  );
}

function App() {
  return (
    <Router>
      <Navbar />
      <div>
        <Routes>
          <Route path="/"         element={<HomePage />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login"    element={<Login />} />
          <Route path="/translate" element={<Translator />} />

          {/* ── Protected routes ── */}
          <Route path="/ssl-translator" element={
            <ProtectedRoute><SSLTranslator /></ProtectedRoute>
          } />
          <Route path="/game-register" element={
            <ProtectedRoute><GameUserForm /></ProtectedRoute>
          } />
          <Route path="/gameselection" element={
            <ProtectedRoute><GameSelection /></ProtectedRoute>
          } />
          <Route path="/game/puzzle" element={
            <ProtectedRoute><SinhalaWordPuzzle /></ProtectedRoute>
          } />
          <Route path="/game/sentence" element={
            <ProtectedRoute><SentenceGame /></ProtectedRoute>
          } />
          <Route path="/ai-analytics" element={
            <ProtectedRoute><AIAnalyticsDashboard /></ProtectedRoute>
          } />
        </Routes>
      </div>
    </Router>
  );
}

/* ── Home Page ──────────────────────────────────── */
const HomePage = () => {
  const isLoggedIn = !!localStorage.getItem("token");
  let user = null;
  try { user = JSON.parse(localStorage.getItem("user")); } catch {}

  const protectedCards = [
    {
      to: "/ssl-translator",
      icon: "✨",
      title: "SSL Translator",
      titleSi: "සංඥා පරිවර්තකය",
      desc: "Type Sinhala text and watch it signed by an avatar in real-time",
      btnLabel: "Open Translator",
      color: "#C0392B",
      gradient: "linear-gradient(135deg,#C0392B,#8B1A1A)",
      shadow: "rgba(192,57,43,.25)",
    },
    {
      to: user?.hasTakenQuiz ? "/gameselection" : "/game-register",
      icon: "🎮",
      title: "Learning Games",
      titleSi: "ඉගෙනුම් ක්‍රීඩා",
      desc: "Practice sign language with fun interactive puzzles and sentence games",
      btnLabel: "Play Now",
      color: "#27AE60",
      gradient: "linear-gradient(135deg,#27AE60,#1B7A38)",
      shadow: "rgba(27,122,56,.25)",
    },
    {
      to: "/translate",
      icon: "🪷",
      title: "Word Translator",
      titleSi: "පෙළ පරිවර්තකය",
      desc: "Quick English to Sinhala word lookup for everyday vocabulary",
      btnLabel: "Translate",
      color: "#F4A820",
      gradient: "linear-gradient(135deg,#F4A820,#C0392B)",
      shadow: "rgba(244,168,32,.3)",
      public: true,   // not protected
    },
  ];

  return (
    <div style={{ minHeight:"100vh", fontFamily:"'Fredoka One','Comic Sans MS',cursive",
      background:"linear-gradient(160deg,#FFF8F0 0%,#FEF0E4 50%,#FFF8F0 100%)",
      display:"flex", flexDirection:"column", alignItems:"center",
      gap:"36px", padding:"48px 20px 60px", position:"relative", overflow:"hidden" }}>

      {/* Floating decos */}
      {[
        { top:"4%",  left:"3%",  f:"3rem",   e:"🪷", d:"0s"   },
        { top:"7%",  right:"4%", f:"2.5rem", e:"🐘", d:".5s"  },
        { top:"45%", left:"1%",  f:"2.2rem", e:"🦚", d:"1s"   },
        { top:"75%", right:"2%", f:"2.5rem", e:"🌿", d:".3s"  },
        { top:"88%", left:"5%",  f:"2rem",   e:"🥥", d:"1.5s" },
      ].map((s, i) => (
        <div key={i} style={{ position:"absolute", top:s.top, left:s.left,
          right:s.right, fontSize:s.f, opacity:.15, pointerEvents:"none",
          animation:`float 4s ease-in-out ${s.d} infinite alternate` }}>{s.e}</div>
      ))}

      {/* Hero */}
      <div style={{ textAlign:"center", zIndex:1 }}>
        <div style={{ fontSize:"4.5rem", marginBottom:"10px" }}>🪷 🤟 🪷</div>
        <h1 style={{ margin:"0 0 8px", fontSize:"clamp(2rem,5vw,3.2rem)", fontWeight:900,
          background:"linear-gradient(135deg,#C0392B,#8B1A1A,#F4A820)",
          WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
          backgroundClip:"text" }}>
          සංඥා භාෂා ඉගෙන ගනිමු!
        </h1>
        <p style={{ margin:0, fontSize:"1.2rem", color:"#7a4f20", fontWeight:600 }}>
          Sinhala Sign Language Learning Platform
        </p>
        <div style={{ marginTop:"12px", display:"inline-flex", gap:"8px",
          background:"linear-gradient(135deg,#C0392B,#F4A820)",
          color:"#fff", borderRadius:"30px", padding:"7px 20px",
          fontSize:".9rem", fontWeight:700, boxShadow:"0 4px 12px rgba(192,57,43,.3)" }}>
          🇱🇰 Sri Lanka 🇱🇰
        </div>
      </div>

      {/* Welcome banner for logged-in users */}
      {isLoggedIn && user && (
        <div style={{ background:"linear-gradient(135deg,#C0392B,#F4A820)",
          color:"#fff", borderRadius:"20px", padding:"14px 32px",
          fontWeight:700, fontSize:"1.1rem", zIndex:1,
          boxShadow:"0 6px 20px rgba(192,57,43,.3)" }}>
          👋 Welcome back, {user.name}! &nbsp;🎉 Ready to learn today?
        </div>
      )}

      {/* NOT logged in — CTA banner */}
      {!isLoggedIn && (
        <div style={{ background:"#fff", borderRadius:"20px", padding:"20px 36px",
          border:"3px solid rgba(192,57,43,.2)", textAlign:"center", zIndex:1,
          boxShadow:"0 6px 24px rgba(192,57,43,.1)", maxWidth:"480px" }}>
          <p style={{ margin:"0 0 14px", color:"#7a4f20", fontWeight:700, fontSize:"1rem" }}>
            🔒 Sign in to unlock <strong>Games</strong> and the <strong>SSL Translator</strong>
          </p>
          <div style={{ display:"flex", gap:"12px", justifyContent:"center", flexWrap:"wrap" }}>
            <Link to="/login" style={{
              background:"linear-gradient(135deg,#C0392B,#8B1A1A)",
              color:"#fff", padding:"10px 28px", borderRadius:"22px",
              textDecoration:"none", fontWeight:800, fontSize:"1rem",
              boxShadow:"0 4px 12px rgba(192,57,43,.35)" }}>
              👤 Sign In
            </Link>
            <Link to="/register" style={{
              background:"#fff", color:"#C0392B", padding:"10px 28px",
              borderRadius:"22px", textDecoration:"none", fontWeight:800,
              fontSize:"1rem", border:"2px solid #C0392B" }}>
              📝 Create Account
            </Link>
          </div>
        </div>
      )}

      {/* Feature Cards */}
      <div style={{ display:"flex", flexWrap:"wrap", gap:"24px",
        justifyContent:"center", zIndex:1 }}>
        {protectedCards.map(({ to, icon, title, titleSi, desc, btnLabel,
          color, gradient, shadow, public: isPublic }) => {
          const locked = !isLoggedIn && !isPublic;
          return (
            <div key={to} style={{ position:"relative" }}>
              {locked && (
                <div style={{ position:"absolute", inset:0, borderRadius:"28px",
                  background:"rgba(255,255,255,.55)", backdropFilter:"blur(3px)",
                  zIndex:2, display:"flex", alignItems:"center",
                  justifyContent:"center", flexDirection:"column", gap:"8px" }}>
                  <span style={{ fontSize:"2.5rem" }}>🔒</span>
                  <Link to="/login" style={{
                    background:gradient, color:"#fff", padding:"9px 22px",
                    borderRadius:"20px", textDecoration:"none",
                    fontWeight:800, fontSize:".9rem",
                    boxShadow:`0 4px 12px ${shadow}` }}>
                    Sign in to unlock
                  </Link>
                </div>
              )}
              <Link to={locked ? "/login" : to} style={{
                background:"#fff", borderRadius:"28px",
                boxShadow:`0 8px 30px ${shadow}`,
                border:`3px solid ${color}22`,
                padding:"32px 26px", display:"flex", flexDirection:"column",
                alignItems:"center", gap:"10px", textDecoration:"none",
                width:"210px", opacity: locked ? .7 : 1,
                transition:"transform .2s, box-shadow .2s",
                fontFamily:"'Fredoka One','Comic Sans MS',cursive"
              }}
              onMouseOver={e => { if (!locked) { e.currentTarget.style.transform="scale(1.05)"; e.currentTarget.style.boxShadow=`0 14px 40px ${shadow}`; } }}
              onMouseOut={e => { e.currentTarget.style.transform="scale(1)"; e.currentTarget.style.boxShadow=`0 8px 30px ${shadow}`; }}
              >
                <span style={{ fontSize:"3.5rem" }}>{icon}</span>
                <h2 style={{ margin:0, fontSize:"1.25rem", fontWeight:900, color:"#2C1810", textAlign:"center" }}>{title}</h2>
                <p style={{ margin:0, color:"#8B6347", fontSize:".82rem", textAlign:"center", fontWeight:600 }}>{titleSi}</p>
                <p style={{ margin:0, color:"#a0826a", fontSize:".78rem", textAlign:"center", lineHeight:1.4 }}>{desc}</p>
                {!locked && (
                  <span style={{ background:gradient, color:"#fff", padding:"9px 20px",
                    borderRadius:"22px", fontWeight:700, fontSize:".9rem",
                    marginTop:"4px", boxShadow:`0 3px 10px ${shadow}` }}>
                    {btnLabel} →
                  </span>
                )}
              </Link>
            </div>
          );
        })}
      </div>

      {/* Cultural strip */}
      <div style={{ color:"rgba(139,26,26,.2)", fontSize:"1.3rem",
        letterSpacing:"10px", userSelect:"none", zIndex:1 }}>
        🪷 🐘 🦚 🌿 🥥 🪷 🐘 🦚 🌿 🥥
      </div>
    </div>
  );
};

export default App;