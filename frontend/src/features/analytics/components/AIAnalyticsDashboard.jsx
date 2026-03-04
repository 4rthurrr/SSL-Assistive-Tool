import React, { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, Target, Award, Clock, Zap, Star, 
  BarChart, PieChart, LineChart, Calendar, Users,
  ChevronRight, RefreshCw, Download, Share2, Settings,
  Lock, Unlock, CheckCircle, AlertCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:5001/api';

const AIAnalyticsDashboard = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('weekly');
  const [selectedView, setSelectedView] = useState('overview');
  const [debugInfo, setDebugInfo] = useState(null);
  
  // Level configuration - defines the progression order and requirements
  const levelConfig = {
    basic: {
      next: 'easy',
      unlockThreshold: 80, // 80% accuracy to unlock next level
      displayName: 'Basic',
      color: 'from-emerald-500 to-green-600',
      description: 'Learn basic signs and greetings'
    },
    easy: {
      next: 'medium',
      unlockThreshold: 80,
      displayName: 'Easy',
      color: 'from-blue-500 to-indigo-600',
      description: 'Simple phrases and questions'
    },
    medium: {
      next: 'hard',
      unlockThreshold: 80,
      displayName: 'Medium',
      color: 'from-purple-500 to-pink-600',
      description: 'Conversational sentences'
    },
    hard: {
      next: null, // Last level
      unlockThreshold: 80,
      displayName: 'Hard',
      color: 'from-red-500 to-orange-600',
      description: 'Complex conversations'
    }
  };

  const levelOrder = ['basic', 'easy', 'medium', 'hard'];

  // Calculate unlocked levels and current level
  const calculateLevelStatus = (levelProgress) => {
    if (!levelProgress) return { unlockedLevels: ['basic'], currentLevel: 'basic' };
    
    const unlockedLevels = [];
    let currentLevel = 'basic';
    
    // Always start with basic level unlocked
    unlockedLevels.push('basic');
    
    // Check each level in order
    for (let i = 0; i < levelOrder.length - 1; i++) {
      const currentLevelKey = levelOrder[i];
      const nextLevelKey = levelOrder[i + 1];
      
      const currentLevelProgress = levelProgress[currentLevelKey];
      
      // If we have progress data for this level
      if (currentLevelProgress) {
        // Check if user has unlocked this level (it should be in unlockedLevels already)
        if (unlockedLevels.includes(currentLevelKey)) {
          // Update current level to this one
          currentLevel = currentLevelKey;
          
          // Check if they qualify for next level
          if (currentLevelProgress.accuracy >= levelConfig[currentLevelKey].unlockThreshold) {
            unlockedLevels.push(nextLevelKey);
            // Also update current level to the unlocked one
            currentLevel = nextLevelKey;
          }
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
      
      // Get user ID from localStorage
      let userId = null;
      
      // Check various storage locations for user ID
      const directUserId = localStorage.getItem('gameUserId');
      if (directUserId) {
        userId = directUserId;
      } else if (localStorage.getItem('gameUser')) {
        try {
          const gameUser = JSON.parse(localStorage.getItem('gameUser'));
          userId = gameUser.userId || gameUser.id || gameUser._id;
        } catch (e) {
          console.error('Error parsing gameUser:', e);
        }
      }
      
      // Try to get user from recent game sessions
      if (!userId) {
        const recentGames = localStorage.getItem('recentGameSessions');
        if (recentGames) {
          try {
            const sessions = JSON.parse(recentGames);
            if (sessions.length > 0) {
              userId = sessions[sessions.length - 1].userId;
            }
          } catch (e) {
            console.error('Error parsing recent game sessions:', e);
          }
        }
      }
      
      // Try debug endpoint for available users
      if (!userId) {
        try {
          const debugResponse = await fetch(`${API_URL}/ai/debug-users`);
          if (debugResponse.ok) {
            const debugData = await debugResponse.json();
            setDebugInfo(debugData);
            if (debugData.users_with_data && debugData.users_with_data.length > 0) {
              userId = debugData.users_with_data[0];
            }
          }
        } catch (debugError) {
          console.error('Debug endpoint error:', debugError);
        }
      }
      
      // Fallback to default
      if (!userId) {
        userId = 'default';
      }
      
      // Fetch analytics
      const response = await fetch(`${API_URL}/ai/progress-report`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          user_id: userId,
          time_range: timeRange
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Analytics API response:', data);
      
      if (data.success) {
        // Calculate unlocked levels and current level
        const { unlockedLevels, currentLevel } = calculateLevelStatus(data.report.level_progress);
        
        // Enhance the report with level status
        const enhancedReport = {
          ...data.report,
          level_status: {
            unlockedLevels,
            currentLevel,
            nextUnlockableLevel: levelConfig[currentLevel]?.next || null,
            isNextLevelUnlockable: data.report.level_progress?.[currentLevel]?.accuracy >= 80
          }
        };
        
        setAnalytics(enhancedReport);
      } else {
        setAnalytics(null);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  };

  // Handle level selection for practice
  const handlePracticeLevel = (level) => {
    // Store selected level in localStorage for game to use
    localStorage.setItem('selectedLevel', level);
    localStorage.setItem('selectedLevelName', levelConfig[level]?.displayName || level);
    navigate('/game/puzzle');
  };

  // Unlock next level function
  const unlockNextLevel = async () => {
    if (!analytics?.level_status?.nextUnlockableLevel) return;
    
    try {
      const userId = localStorage.getItem('gameUserId') || 'default';
      const nextLevel = analytics.level_status.nextUnlockableLevel;
      
      const response = await fetch(`${API_URL}/ai/unlock-level`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_id: userId,
          level: nextLevel
        })
      });
      
      if (response.ok) {
        // Refresh analytics to show updated status
        fetchAnalytics();
      }
    } catch (error) {
      console.error('Error unlocking level:', error);
    }
  };

  // Debug component
  const DebugPanel = () => {
    if (!debugInfo) return null;
    
    return (
      <div className="bg-gray-800/70 rounded-xl p-4 mt-4 border border-gray-700">
        <h3 className="text-lg font-bold mb-2 text-yellow-400">Debug Info</h3>
        <p className="text-sm text-gray-300 mb-2">
          Found {debugInfo.total_users || 0} users with data in backend
        </p>
        {debugInfo.users_with_data && debugInfo.users_with_data.length > 0 && (
          <div className="text-sm">
            <p className="font-bold mb-1">Available User IDs:</p>
            <ul className="list-disc pl-5 text-gray-300">
              {debugInfo.users_with_data.slice(0, 5).map((userId, idx) => (
                <li key={idx}>{userId}</li>
              ))}
            </ul>
          </div>
        )}
        <button
          onClick={() => setDebugInfo(null)}
          className="mt-3 text-xs text-gray-400 hover:text-white"
        >
          Hide debug info
        </button>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading AI Analytics...</p>
          <p className="text-gray-500 text-sm mt-2">Fetching your learning insights...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <Brain className="w-20 h-20 text-gray-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">No Analytics Data</h2>
          <p className="text-gray-400 mb-4">
            Play some games to generate AI insights!
          </p>
          
          {debugInfo && <DebugPanel />}
          
          <div className="flex flex-col gap-3 mt-6">
            <button
              onClick={() => navigate('/game/puzzle')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-bold"
            >
              Start Playing
            </button>
            <button
              onClick={fetchAnalytics}
              className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium"
            >
              Retry Loading Analytics
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { unlockedLevels, currentLevel, nextUnlockableLevel, isNextLevelUnlockable } = analytics.level_status || {};
  const currentLevelData = analytics.level_progress?.[currentLevel] || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <div className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold">AI Learning Analytics</h1>
                <p className="text-gray-400 text-sm">Personalized insights powered by AI</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={fetchAnalytics}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
              >
                <RefreshCw className="w-4 h-4" /> Refresh
              </button>
              <button
                onClick={() => navigate('/game/puzzle')}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              >
                Back to Game
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Level Unlock Banner */}
        {isNextLevelUnlockable && nextUnlockableLevel && (
          <div className="mb-6 p-6 bg-gradient-to-r from-green-900/40 to-emerald-900/40 rounded-2xl border-2 border-green-500/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center">
                  <Unlock className="w-8 h-8 text-green-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">New Level Unlocked! 🎉</h3>
                  <p className="text-green-300">
                    You've achieved {currentLevelData.accuracy?.toFixed(1)}% in {levelConfig[currentLevel]?.displayName || currentLevel}!
                  </p>
                  <p className="text-gray-300 text-sm mt-1">
                    You can now access the <span className="font-bold">{levelConfig[nextUnlockableLevel]?.displayName || nextUnlockableLevel}</span> level.
                  </p>
                </div>
              </div>
              <button
                onClick={unlockNextLevel}
                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-3 rounded-lg font-bold transition"
              >
                Unlock Now
              </button>
            </div>
          </div>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-900/30 to-cyan-900/30 rounded-2xl p-6 border border-blue-800/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
                <Award className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <div className="text-3xl font-bold">{analytics.summary?.words_learned || 0}</div>
                <div className="text-gray-400">Words Learned</div>
              </div>
            </div>
            <div className="text-sm text-gray-300">
              {analytics.summary?.words_learned > 0 ? 'Great progress!' : 'Start learning!'}
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 rounded-2xl p-6 border border-green-800/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
                <Target className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <div className="text-3xl font-bold">
                  {analytics.summary?.overall_accuracy ? analytics.summary.overall_accuracy.toFixed(1) : 0}%
                </div>
                <div className="text-gray-400">Accuracy Rate</div>
              </div>
            </div>
            <div className="text-sm text-gray-300">
              {analytics.summary?.overall_accuracy > 70 ? 'Excellent!' : 'Keep practicing!'}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-2xl p-6 border border-purple-800/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center">
                <Clock className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-3xl font-bold">
                  {analytics.summary?.total_playtime_minutes || 0}
                </div>
                <div className="text-gray-400">Minutes Played</div>
              </div>
            </div>
            <div className="text-sm text-gray-300">Total learning time</div>
          </div>

          <div className="bg-gradient-to-br from-yellow-900/30 to-amber-900/30 rounded-2xl p-6 border border-yellow-800/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-yellow-500/20 rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <div className="text-3xl font-bold">
                  {analytics.summary?.current_streak || 0}
                </div>
                <div className="text-gray-400">Day Streak</div>
              </div>
            </div>
            <div className="text-sm text-gray-300">
              {analytics.summary?.current_streak > 0 ? 'Keep it up!' : 'Start a streak!'}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Level Progress with Unlock Status */}
            <div className="bg-gray-800/50 rounded-2xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" /> Level Progress
                </h2>
                <div className="text-sm text-gray-400">
                  Unlock next level at 80% accuracy
                </div>
              </div>
              
              <div className="space-y-6">
                {levelOrder.map((level) => {
                  const levelData = analytics.level_progress?.[level] || {};
                  const isUnlocked = unlockedLevels?.includes(level);
                  const isCurrent = currentLevel === level;
                  const config = levelConfig[level];
                  
                  return (
                    <div 
                      key={level}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        isCurrent 
                          ? 'border-blue-500 bg-blue-500/10' 
                          : isUnlocked 
                            ? 'border-green-500/30 bg-green-500/5' 
                            : 'border-gray-700 bg-gray-800/30 opacity-60'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            isCurrent 
                              ? 'bg-blue-500/20' 
                              : isUnlocked 
                                ? 'bg-green-500/20' 
                                : 'bg-gray-700'
                          }`}>
                            {isCurrent ? (
                              <Zap className="w-5 h-5 text-blue-400" />
                            ) : isUnlocked ? (
                              <CheckCircle className="w-5 h-5 text-green-400" />
                            ) : (
                              <Lock className="w-5 h-5 text-gray-500" />
                            )}
                          </div>
                          <div>
                            <h3 className="font-bold capitalize">{config?.displayName || level}</h3>
                            <p className="text-sm text-gray-400">{config?.description}</p>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className={`text-xl font-bold ${
                            isCurrent 
                              ? 'text-blue-400' 
                              : isUnlocked 
                                ? 'text-green-400' 
                                : 'text-gray-500'
                          }`}>
                            {levelData.accuracy ? `${levelData.accuracy.toFixed(1)}%` : '0%'}
                          </div>
                          <div className="text-xs text-gray-500">
                            {levelData.correct_attempts || 0}/{levelData.total_attempts || 0} correct
                          </div>
                        </div>
                      </div>
                      
                      <div className="mb-2">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Progress to next level</span>
                          <span>
                            {isUnlocked && levelData.accuracy >= 80 
                              ? 'Ready to unlock next!' 
                              : `${levelData.accuracy || 0}/80%`}
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-3">
                          <div 
                            className={`h-3 rounded-full transition-all duration-500 ${
                              levelData.accuracy >= 80 
                                ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                                : 'bg-gradient-to-r from-blue-500 to-purple-500'
                            }`}
                            style={{ width: `${Math.min(levelData.accuracy || 0, 100)}%` }}
                          />
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center mt-4">
                        <div className="text-sm text-gray-400">
                          {isCurrent 
                            ? '🎯 Currently Active Level' 
                            : isUnlocked 
                              ? '✅ Level Unlocked' 
                              : '🔒 Locked - Complete previous level'}
                        </div>
                        
                        {isUnlocked && (
                          <button
                            onClick={() => handlePracticeLevel(level)}
                            className={`px-4 py-2 rounded-lg font-medium text-sm ${
                              isCurrent 
                                ? 'bg-blue-600 hover:bg-blue-700' 
                                : 'bg-gray-700 hover:bg-gray-600'
                            }`}
                          >
                            {isCurrent ? 'Continue Practice' : 'Practice Level'}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              
              {/* Progress Summary */}
              <div className="mt-6 p-4 bg-gray-900/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Current Active Level</p>
                    <p className="text-lg font-bold capitalize">
                      {levelConfig[currentLevel]?.displayName || currentLevel}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Next Level</p>
                    <p className="text-lg font-bold capitalize">
                      {nextUnlockableLevel 
                        ? (levelConfig[nextUnlockableLevel]?.displayName || nextUnlockableLevel)
                        : 'Maximum Level Reached'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Progress</p>
                    <p className="text-lg font-bold">
                      {currentLevelData.accuracy ? `${currentLevelData.accuracy.toFixed(1)}%` : '0%'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Predictions */}
            <div className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-2xl p-6 border border-green-800/30">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Brain className="w-5 h-5" /> AI Predictions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Time to Unlock Next Level</div>
                    <div className="text-3xl font-bold text-green-400">
                      {isNextLevelUnlockable 
                        ? 'Ready Now!'
                        : analytics.predictions?.time_to_unlock || '2-3 sessions'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Confidence Score</div>
                    <div className="text-2xl font-bold text-blue-400">
                      {analytics.predictions?.confidence || 85}%
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-400 mb-2">Recommended Focus</div>
                  <div className="text-lg font-bold text-yellow-400">
                    {analytics.recommendations?.[0]?.word || 'Practice consistently'}
                  </div>
                  <div className="text-sm text-gray-400 mt-4">
                    Based on your learning patterns and accuracy trends
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Current Level Card */}
            <div className="bg-gradient-to-br from-blue-900/30 to-cyan-900/30 rounded-2xl p-6 border-2 border-blue-500/50">
              <h2 className="text-xl font-bold mb-4">Current Active Level</h2>
              <div className="text-center mb-4">
                <div className="inline-block p-6 bg-blue-500/20 rounded-full mb-3">
                  <Zap className="w-16 h-16 text-blue-400" />
                </div>
                <div className="text-5xl font-bold mb-2 uppercase">
                  {levelConfig[currentLevel]?.displayName || currentLevel}
                </div>
                <div className="text-gray-300 mb-4">{levelConfig[currentLevel]?.description}</div>
                
                {/* Progress Circle */}
                <div className="relative w-32 h-32 mx-auto mb-4">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="#374151"
                      strokeWidth="8"
                      fill="none"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="#3B82F6"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${(currentLevelData.accuracy || 0) * 3.51} 352`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-3xl font-bold">
                        {currentLevelData.accuracy ? `${currentLevelData.accuracy.toFixed(0)}%` : '0%'}
                      </div>
                      <div className="text-xs text-gray-400">Progress</div>
                    </div>
                  </div>
                </div>
                
                {/* Next Level Info */}
                {nextUnlockableLevel && (
                  <div className={`p-4 rounded-lg border mt-4 ${
                    isNextLevelUnlockable 
                      ? 'border-green-500/50 bg-green-500/10' 
                      : 'border-gray-700 bg-gray-800/30'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400">Next Level:</span>
                      <span className="font-bold capitalize">
                        {levelConfig[nextUnlockableLevel]?.displayName || nextUnlockableLevel}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Status:</span>
                      <span className={`font-bold ${isNextLevelUnlockable ? 'text-green-400' : 'text-yellow-400'}`}>
                        {isNextLevelUnlockable ? 'Ready to Unlock' : 'In Progress'}
                      </span>
                    </div>
                    {!isNextLevelUnlockable && currentLevelData.accuracy && (
                      <div className="mt-2 text-sm text-gray-400">
                        Need {80 - Math.floor(currentLevelData.accuracy)}% more to unlock
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Level Access Panel */}
            <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Unlock className="w-5 h-5" /> Level Access
              </h2>
              <div className="space-y-3">
                {levelOrder.map((level) => {
                  const isUnlocked = unlockedLevels?.includes(level);
                  const config = levelConfig[level];
                  
                  return (
                    <div 
                      key={level}
                      className={`p-3 rounded-lg flex items-center justify-between ${
                        isUnlocked ? 'bg-green-500/10 border border-green-500/30' : 'bg-gray-800/50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          isUnlocked ? 'bg-green-500/20' : 'bg-gray-700'
                        }`}>
                          {isUnlocked ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <Lock className="w-4 h-4 text-gray-500" />
                          )}
                        </div>
                        <div>
                          <div className="font-bold capitalize">{config?.displayName || level}</div>
                          <div className="text-xs text-gray-400">
                            {isUnlocked ? 'Available to play' : 'Locked'}
                          </div>
                        </div>
                      </div>
                      
                      {isUnlocked && (
                        <button
                          onClick={() => handlePracticeLevel(level)}
                          className="px-3 py-1 text-sm bg-purple-600 hover:bg-purple-700 rounded"
                        >
                          Play
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Quick Insights */}
            <div className="bg-gradient-to-br from-yellow-900/20 to-amber-900/20 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-4">Quick Insights</h2>
              <div className="space-y-3">
                {analytics.insights?.slice(0, 3).map((insight, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-3 bg-black/30 rounded-lg">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2"></div>
                    <div className="text-sm">{insight}</div>
                  </div>
                ))}
                {(!analytics.insights || analytics.insights.length === 0) && (
                  <div className="text-center p-4 text-gray-500">
                    Complete more games for insights
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Level Achievement Summary */}
        <div className="mt-8 bg-gradient-to-br from-blue-900/20 to-purple-900/20 rounded-2xl p-6 border border-blue-800/30">
          <h2 className="text-xl font-bold mb-6">Level Achievement Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {levelOrder.map((level) => {
              const levelData = analytics.level_progress?.[level] || {};
              const isUnlocked = unlockedLevels?.includes(level);
              
              return (
                <div key={level} className="text-center p-4 bg-black/20 rounded-xl">
                  <div className="text-2xl font-bold mb-2 capitalize">
                    {levelConfig[level]?.displayName || level}
                  </div>
                  <div className={`text-3xl font-bold mb-1 ${
                    levelData.accuracy >= 80 ? 'text-green-400' : 'text-blue-400'
                  }`}>
                    {levelData.accuracy ? `${levelData.accuracy.toFixed(1)}%` : '0%'}
                  </div>
                  <div className="text-sm text-gray-400 mb-3">
                    {levelData.correct_attempts || 0} correct attempts
                  </div>
                  <div className={`text-sm font-medium px-3 py-1 rounded-full inline-block ${
                    isUnlocked
                      ? levelData.accuracy >= 80
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-blue-500/20 text-blue-400'
                      : 'bg-gray-700 text-gray-400'
                  }`}>
                    {isUnlocked
                      ? (levelData.accuracy >= 80 ? '✅ Level Mastered' : '🔓 Level Unlocked')
                      : '🔒 Locked'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAnalyticsDashboard;