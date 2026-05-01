import { useNavigate } from "react-router-dom";
import {
  Star, Clock, Trophy, Sparkles, ChevronRight, Play, Award,
  Brain, TrendingUp, BarChart, LogOut
} from "lucide-react";
import { useEffect, useState } from "react";
import "../../../shared/styles/App.css";
import "../../../shared/styles/GameSelection.css";

export default function GameSelection() {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [showAnalyticsBtn, setShowAnalyticsBtn] = useState(false);
  const [showQuizScore, setShowQuizScore] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem('gameUser');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUserData(parsedUser);
      if (parsedUser.hasTakenQuiz) {
        setShowAnalyticsBtn(true);
        setShowQuizScore(true);
      }
    } else {
      navigate('/game-register');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('gameUser');
    localStorage.removeItem('gameUserId');
    navigate('/game-register');
  };

  if (!userData) {
    return (
      <div className="gs-loading">
        <div className="gs-loading-text">⏳ Loading...</div>
      </div>
    );
  }

  const userProgress = {
    level: userData.grade || 3,
    totalStars: 120,
    dailyTimeLeft: 25,
    masteredWords: 32,
    accuracy: 78,
    streak: 5
  };

  const masteryProgress = (userProgress.masteredWords / 50) * 100;

  const getQuizScoreDisplay = () => {
    if (!userData.hasTakenQuiz || !showQuizScore) return null;
    const score = userData.quizScore || 0;
    const total = userData.quizTotal || 0;
    const percentage = userData.quizPercentage || 0;

    if (total === 0 && userData.grade === '1') {
      return (
        <div className="gs-quiz-badge gs-quiz-badge--green">
          <Award size={18} />
          <div>
            <div className="gs-quiz-badge-label">Grade 1 Student</div>
            <div className="gs-quiz-badge-value">Basic Level (Auto-set)</div>
          </div>
        </div>
      );
    }

    return (
      <div className="gs-quiz-badge gs-quiz-badge--yellow">
        <Trophy size={18} />
        <div>
          <div className="gs-quiz-badge-label">Quiz Score</div>
          <div className="gs-quiz-badge-value">
            {score}/{total}
            <span className="gs-quiz-badge-pct">({percentage}%)</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="gs-page sl-bg">

      {/* ── Sticky Nav Bar ─────────────────────────────────── */}
      <div className="gs-nav-wrap">
        <div className="gs-nav sl-card">
          <div className="gs-nav-left">
            {/* Avatar */}
            <div className="gs-avatar">
              {userData.name?.substring(0, 2).toUpperCase() || 'SS'}
            </div>
            <div>
              <h2 className="gs-greeting">හෙලෝ, {userData.name}! 👋</h2>
              <div className="gs-greeting-sub">
                <span>Level {userProgress.level}</span>
                {userData.recommendedLevel && (
                  <>
                    <span className="gs-dot-sep">•</span>
                    <span className="gs-level-tag">{userData.recommendedLevel}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Quiz score chip */}
          {showQuizScore && getQuizScoreDisplay()}

          {/* Stats + logout */}
          <div className="gs-nav-right">
            <div className="gs-stat">
              <div className="gs-stat-val gs-stat-val--yellow">
                <Star size={18} fill="currentColor" /> {userProgress.totalStars}
              </div>
              <div className="gs-stat-lbl">Stars</div>
            </div>
            <div className="gs-stat">
              <div className="gs-stat-val gs-stat-val--blue">
                <Clock size={18} /> {userProgress.dailyTimeLeft}
              </div>
              <div className="gs-stat-lbl">Minutes</div>
            </div>
            <button className="gs-logout-btn" onClick={handleLogout} title="Logout">
              <LogOut size={16} /> <span>Logout</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Recommendation Banner ──────────────────────────── */}
      {userData.recommendedLevel && !showQuizScore && (
        <div className="gs-rec-banner">
          <div className="gs-rec-left">
            <Award size={28} />
            <div>
              <p className="gs-rec-title">Recommended for You 🌟</p>
              <p className="gs-rec-sub">
                Start with <strong>{userData.recommendedLevel.toUpperCase()}</strong> level
              </p>
            </div>
          </div>
          {userData.quizScore !== undefined && userData.quizTotal !== undefined && (
            <div className="gs-rec-score">
              <p className="gs-rec-score-lbl">Quiz Score</p>
              <p className="gs-rec-score-val">{userData.quizScore || 0}/{userData.quizTotal || 10}</p>
            </div>
          )}
        </div>
      )}

      {/* ── Progress Card ──────────────────────────────────── */}
      <button className="gs-progress-card sl-card" onClick={() => navigate('/ai-analytics')}>
        <div className="gs-progress-card-header">
          <h3 className="gs-section-title">
            <Trophy size={22} className="gs-icon-yellow" /> Your Progress
          </h3>
          <div className="gs-analytics-link">
            <Brain size={18} /> View AI Analytics <ChevronRight size={16} />
          </div>
        </div>

        <div className="gs-progress-bar-wrap">
          <div className="gs-progress-bar-labels">
            <span>Words Mastered</span>
            <span className="gs-progress-bar-count">{userProgress.masteredWords}/50</span>
          </div>
          <div className="gs-progress-bar-track">
            <div className="gs-progress-bar-fill" style={{ width: `${masteryProgress}%` }} />
          </div>
        </div>

        <div className="gs-stats-grid">
          <div className="gs-mini-stat gs-mini-stat--blue">
            <div className="gs-mini-stat-val">{userProgress.accuracy}%</div>
            <div className="gs-mini-stat-lbl">Accuracy</div>
          </div>
          <div className="gs-mini-stat gs-mini-stat--yellow">
            <div className="gs-mini-stat-val">{userProgress.streak}</div>
            <div className="gs-mini-stat-lbl">Day Streak 🔥</div>
          </div>
        </div>

        <div className="gs-progress-footer">
          <div className="gs-progress-footer-left">
            <BarChart size={14} /> AI-powered insights available
          </div>
          <div className="gs-progress-footer-right">Click to view →</div>
        </div>
      </button>

      {/* ── Game Selection Cards ────────────────────────────── */}
      <div className="gs-games-grid">
        {/* Puzzle Game */}
        <button
          className="gs-game-card gs-game-card--blue"
          onClick={() => navigate("/game/puzzle", {
            state: {
              userId: userData.userId || userData._id,
              recommendedLevel: userData.recommendedLevel,
              userName: userData.name,
              userGrade: userData.grade
            }
          })}
        >
          {userData.recommendedLevel && (
            <div className="gs-recommended-badge">⭐ RECOMMENDED</div>
          )}
          <div className="gs-game-card-top">
            <Sparkles size={40} />
            <ChevronRight size={28} />
          </div>
          <h3 className="gs-game-title">සංඥා විදු ප්‍රහේලිකා</h3>
          <p className="gs-game-sub">Find hidden words from sign videos</p>
        </button>

        {/* Sentence Game */}
        <button
          className="gs-game-card gs-game-card--green"
          onClick={() => navigate("/game/sentence")}
        >
          <div className="gs-game-card-top">
            <Play size={40} />
            <ChevronRight size={28} />
          </div>
          <h3 className="gs-game-title">සංඥා වාක්‍ය හුරු ක්‍රීඩා</h3>
          <p className="gs-game-sub">Sign Sentence Familiarity Game</p>
        </button>
      </div>

      {/* ── AI Analytics Preview ────────────────────────────── */}
      {showAnalyticsBtn && (
        <div className="gs-analytics-card">
          <div className="gs-analytics-inner">
            <div className="gs-analytics-icon-wrap">
              <Brain size={24} />
            </div>
            <div>
              <h4 className="gs-analytics-title">AI Learning Insights 🧠</h4>
              <p className="gs-analytics-sub">
                Personalized recommendations based on your performance
              </p>
            </div>
          </div>
          <button className="gs-analytics-btn" onClick={() => navigate('/ai-analytics')}>
            <TrendingUp size={18} /> View Full Report <ChevronRight size={18} />
          </button>
          <div className="gs-analytics-metrics">
            {[
              { val: '85%', lbl: 'Progress', cls: 'green' },
              { val: '4',   lbl: 'Skills',   cls: 'yellow' },
              { val: '12',  lbl: 'Insights', cls: 'blue' },
              { val: '3',   lbl: 'Tips',     cls: 'sky' },
            ].map(({ val, lbl, cls }) => (
              <div key={lbl} className={`gs-metric gs-metric--${cls}`}>
                <div className="gs-metric-val">{val}</div>
                <div className="gs-metric-lbl">{lbl}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Quick Actions ───────────────────────────────────── */}
      <div className="gs-quick-actions">
        <button className="gs-quick-btn gs-quick-btn--white" onClick={() => navigate('/game-register')}>
          <span>👤</span> Edit Profile
        </button>
        <button className="gs-quick-btn gs-quick-btn--blue" onClick={() => navigate('/ai-analytics')}>
          <span>📊</span> Analytics
        </button>
        <button className="gs-quick-btn gs-quick-btn--sky" onClick={() => navigate('/game-history')}>
          <span>📝</span> History
        </button>
      </div>

      {/* ── Quiz Status Summary ─────────────────────────────── */}
      {showQuizScore && (
        <div className="gs-quiz-summary sl-card">
          <div className="gs-quiz-summary-left">
            <Trophy size={20} className="gs-icon-yellow" />
            <span>Quiz Status:</span>
          </div>
          <div className="gs-quiz-summary-right">
            <div className="gs-quiz-info">
              <div className="gs-quiz-info-lbl">Level</div>
              <div className="gs-quiz-info-val gs-quiz-info-val--blue">
                {userData.recommendedLevel || 'basic'}
              </div>
            </div>
            <div className="gs-quiz-info">
              <div className="gs-quiz-info-lbl">Completed</div>
              <div className="gs-quiz-info-val gs-quiz-info-val--green">
                {userData.hasTakenQuiz ? 'Yes ✅' : 'No'}
              </div>
            </div>
            {userData.quizPercentage > 0 && (
              <div className="gs-quiz-info">
                <div className="gs-quiz-info-lbl">Score</div>
                <div className="gs-quiz-info-val gs-quiz-info-val--blue">
                  {userData.quizPercentage}%
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}