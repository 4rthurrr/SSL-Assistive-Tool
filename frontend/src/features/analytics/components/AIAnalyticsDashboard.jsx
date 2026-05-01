import React, { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, Target, Award, Clock, Zap, Star, 
  BarChart, PieChart, LineChart, Calendar, Users,
  ChevronRight, RefreshCw, Download, Share2, Settings,
  Lock, Unlock, CheckCircle, AlertCircle, PlayCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import "./AIAnalyticsDashboard.css";
import "../../../shared/styles/App.css";

const API_URL = 'http://localhost:5001/api';

const AIAnalyticsDashboard = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('weekly');
  
  const levelConfig = {
    basic: {
      next: 'easy',
      unlockThreshold: 80,
      displayName: 'Basic',
      colorClass: 'ana-bg-green',
      barColor: '#4CAF50',
      description: 'Learn basic signs and greetings'
    },
    easy: {
      next: 'medium',
      unlockThreshold: 80,
      displayName: 'Easy',
      colorClass: 'ana-bg-blue',
      barColor: '#4DA6FF',
      description: 'Simple phrases and questions'
    },
    medium: {
      next: 'hard',
      unlockThreshold: 80,
      displayName: 'Medium',
      colorClass: 'ana-bg-yellow',
      barColor: '#FFD93D',
      description: 'Conversational sentences'
    },
    hard: {
      next: null,
      unlockThreshold: 80,
      displayName: 'Hard',
      colorClass: 'ana-bg-pink',
      barColor: '#FF6B6B',
      description: 'Complex conversations'
    }
  };

  const levelOrder = ['basic', 'easy', 'medium', 'hard'];

  const calculateLevelStatus = (levelProgress) => {
    if (!levelProgress) return { unlockedLevels: ['basic'], currentLevel: 'basic' };
    const unlockedLevels = ['basic'];
    let currentLevel = 'basic';
    
    for (let i = 0; i < levelOrder.length - 1; i++) {
      const currentLevelKey = levelOrder[i];
      const nextLevelKey = levelOrder[i + 1];
      const currentLevelProgress = levelProgress[currentLevelKey];
      
      if (currentLevelProgress && unlockedLevels.includes(currentLevelKey)) {
        currentLevel = currentLevelKey;
        if (currentLevelProgress.accuracy >= levelConfig[currentLevelKey].unlockThreshold) {
          unlockedLevels.push(nextLevelKey);
          currentLevel = nextLevelKey;
        }
      }
    }
    return { unlockedLevels, currentLevel };
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      let userId = localStorage.getItem('gameUserId') || 'default';
      
      const response = await fetch(`${API_URL}/ai/progress-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, time_range: timeRange })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      
      if (data.success) {
        const { unlockedLevels, currentLevel } = calculateLevelStatus(data.report.level_progress);
        setAnalytics({
          ...data.report,
          level_status: {
            unlockedLevels,
            currentLevel,
            nextUnlockableLevel: levelConfig[currentLevel]?.next || null,
            isNextLevelUnlockable: data.report.level_progress?.[currentLevel]?.accuracy >= 80
          }
        });
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePracticeLevel = (level) => {
    localStorage.setItem('selectedLevel', level);
    navigate('/game/puzzle');
  };

  const unlockNextLevel = async () => {
    if (!analytics?.level_status?.nextUnlockableLevel) return;
    try {
      const userId = localStorage.getItem('gameUserId') || 'default';
      const nextLevel = analytics.level_status.nextUnlockableLevel;
      const response = await fetch(`${API_URL}/ai/unlock-level`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, level: nextLevel })
      });
      if (response.ok) fetchAnalytics();
    } catch (error) {
      console.error('Error unlocking level:', error);
    }
  };

  if (loading) {
    return (
      <div className="ana-page" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div className="sl-float" style={{ fontSize: "4rem", marginBottom: "20px" }}>🧠</div>
          <h2 style={{ fontWeight: 900, color: "var(--primary)" }}>Loading Buddy Insights...</h2>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="ana-page" style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
        <div style={{ textAlign: "center", maxWidth: "400px" }}>
          <Brain size={80} className="ana-blue" style={{ marginBottom: "20px" }} />
          <h2 style={{ fontWeight: 900 }}>No Analytics Yet!</h2>
          <p style={{ color: "#64748B", marginBottom: "30px" }}>Play some games to help the AI learn about your progress!</p>
          <button onClick={() => navigate('/game/puzzle')} className="ana-btn ana-btn-primary">Start Playing 🎮</button>
        </div>
      </div>
    );
  }

  const { unlockedLevels, currentLevel, nextUnlockableLevel, isNextLevelUnlockable } = analytics.level_status || {};
  const currentLevelData = analytics.level_progress?.[currentLevel] || {};

  return (
    <div className="ana-page">
      {/* Header */}
      <header className="ana-header">
        <div className="ana-header-inner">
          <div className="ana-header-left">
            <div style={{ background: "rgba(255,255,255,.2)", p: "10px", borderRadius: "14px" }}>
              <Brain size={32} />
            </div>
            <div>
              <h1 className="ana-title">My Learning Buddy</h1>
              <p className="ana-subtitle">AI Insights & Progress</p>
            </div>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button onClick={fetchAnalytics} className="ana-btn ana-btn-white" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <RefreshCw size={18} /> Refresh
            </button>
            <button onClick={() => navigate('/gameselection')} className="ana-btn ana-btn-white">Back to Games</button>
          </div>
        </div>
      </header>

      <div className="ana-container">
        {/* Unlock Banner */}
        {isNextLevelUnlockable && nextUnlockableLevel && (
          <div className="ana-unlock-banner">
            <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
              <div style={{ background: "rgba(255,255,255,.2)", padding: "15px", borderRadius: "50%" }}>
                <Unlock size={32} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.4rem", fontWeight: 900 }}>Level Unlocked! 🎉</h3>
                <p style={{ margin: 0, opacity: .9, fontWeight: 600 }}>
                  You did great in {levelConfig[currentLevel]?.displayName}! Ready for {levelConfig[nextUnlockableLevel]?.displayName}?
                </p>
              </div>
            </div>
            <button onClick={unlockNextLevel} className="ana-btn" style={{ background: "#fff", color: "#2E7D32" }}>Unlock Now</button>
          </div>
        )}

        {/* Stats Grid */}
        <div className="ana-stats-grid">
          <div className="ana-stat-card">
            <div className="ana-stat-icon-wrap ana-bg-blue"><Award size={28} /></div>
            <div>
              <div className="ana-stat-val">{analytics.summary?.words_learned || 0}</div>
              <div className="ana-stat-lbl">Words Learned</div>
            </div>
          </div>
          <div className="ana-stat-card">
            <div className="ana-stat-icon-wrap ana-bg-green"><Target size={28} /></div>
            <div>
              <div className="ana-stat-val">{(analytics.summary?.overall_accuracy || 0).toFixed(0)}%</div>
              <div className="ana-stat-lbl">Accuracy</div>
            </div>
          </div>
          <div className="ana-stat-card">
            <div className="ana-stat-icon-wrap ana-bg-yellow"><Clock size={28} /></div>
            <div>
              <div className="ana-stat-val">{analytics.summary?.total_playtime_minutes || 0}</div>
              <div className="ana-stat-lbl">Minutes Played</div>
            </div>
          </div>
          <div className="ana-stat-card">
            <div className="ana-stat-icon-wrap ana-bg-pink"><Zap size={28} /></div>
            <div>
              <div className="ana-stat-val">{analytics.summary?.current_streak || 0}</div>
              <div className="ana-stat-lbl">Day Streak</div>
            </div>
          </div>
        </div>

        <div className="ana-layout">
          {/* Main Panel */}
          <div className="ana-main-panel">
            <div className="ana-panel">
              <h2 className="ana-panel-title"><TrendingUp size={24} className="ana-blue" /> Level Progression</h2>
              <div className="ana-levels-list">
                {levelOrder.map((level) => {
                  const levelData = analytics.level_progress?.[level] || {};
                  const isUnlocked = unlockedLevels?.includes(level);
                  const isCurrent = currentLevel === level;
                  const config = levelConfig[level];
                  
                  return (
                    <div key={level} className={`ana-level-item ${isCurrent ? 'ana-level-item--active' : ''} ${!isUnlocked ? 'ana-level-item--locked' : ''}`}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                          <div className={`ana-stat-icon-wrap ${config.colorClass}`}>
                            {isUnlocked ? (isCurrent ? <Zap size={20} /> : <CheckCircle size={20} />) : <Lock size={20} />}
                          </div>
                          <div>
                            <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 800 }}>{config.displayName}</h3>
                            <p style={{ margin: 0, fontSize: ".85rem", color: "#64748B" }}>{config.description}</p>
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontSize: "1.2rem", fontWeight: 900, color: isUnlocked ? config.barColor : "#94A3B8" }}>
                            {levelData.accuracy ? `${levelData.accuracy.toFixed(0)}%` : '0%'}
                          </div>
                          <div style={{ fontSize: ".75rem", fontWeight: 700, color: "#94A3B8" }}>
                            {levelData.correct_attempts || 0}/{levelData.total_attempts || 0} Correct
                          </div>
                        </div>
                      </div>
                      
                      <div className="ana-progress-bar-wrap">
                        <div className="ana-progress-bar-track">
                          <div 
                            className="ana-progress-bar-fill" 
                            style={{ width: `${Math.min(levelData.accuracy || 0, 100)}%`, background: config.barColor }} 
                          />
                        </div>
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "15px" }}>
                        <span style={{ fontSize: ".8rem", fontWeight: 700, color: "#94A3B8" }}>
                          {isUnlocked ? "Level Unlocked" : "Keep learning to unlock"}
                        </span>
                        {isUnlocked && (
                          <button onClick={() => handlePracticeLevel(level)} className={`ana-btn ${isCurrent ? 'ana-btn-primary' : 'ana-btn-white'}`} style={{ padding: "6px 14px", fontSize: ".85rem" }}>
                            {isCurrent ? "Play Now" : "Practice"}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="ana-side-panel">
            {/* Prediction Panel */}
            <div className="ana-panel ana-prediction-panel">
              <h2 className="ana-panel-title"><Brain size={24} className="ana-blue" /> AI Predictions</h2>
              <div style={{ marginBottom: "20px" }}>
                <p style={{ margin: "0 0 5px", fontSize: ".85rem", fontWeight: 700, color: "#64748B" }}>Time to Next Level</p>
                <div style={{ fontSize: "1.5rem", fontWeight: 900, color: "var(--primary)" }}>
                  {isNextLevelUnlockable ? "Ready Now! ✨" : (analytics.predictions?.time_to_unlock || "2-3 Sessions")}
                </div>
              </div>
              <div style={{ marginBottom: "20px" }}>
                <p style={{ margin: "0 0 5px", fontSize: ".85rem", fontWeight: 700, color: "#64748B" }}>AI Confidence</p>
                <div style={{ fontSize: "1.5rem", fontWeight: 900, color: "var(--accent)" }}>
                  {analytics.predictions?.confidence || 85}%
                </div>
              </div>
              <div>
                <p style={{ margin: "0 0 8px", fontSize: ".85rem", fontWeight: 700, color: "#64748B" }}>Recommended Focus</p>
                <div style={{ background: "#fff", padding: "12px", borderRadius: "12px", border: "2px solid #E1EFFF", fontWeight: 700, textAlign: "center", color: "#2B8FE8" }}>
                  {analytics.recommendations?.[0]?.word || "Daily Practice"}
                </div>
              </div>
            </div>

            {/* Insights Panel */}
            <div className="ana-panel">
              <h2 className="ana-panel-title">Quick Tips</h2>
              <div className="ana-insights-list">
                {analytics.insights?.length > 0 ? (
                  analytics.insights.slice(0, 4).map((insight, idx) => (
                    <div key={idx} className="ana-insight-item">
                      <div className="ana-insight-dot" />
                      <div style={{ fontSize: ".9rem", fontWeight: 600 }}>{insight}</div>
                    </div>
                  ))
                ) : (
                  <p style={{ textAlign: "center", color: "#94A3B8", fontSize: ".9rem" }}>Play more games for personalized tips!</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <footer style={{ textAlign: "center", padding: "40px", opacity: .3, letterSpacing: "10px", fontSize: "1.2rem" }}>
        🧠 ✨ 🤟 🎮 🌟 🧠 ✨ 🤟 🎮 🌟
      </footer>
    </div>
  );
};

export default AIAnalyticsDashboard;