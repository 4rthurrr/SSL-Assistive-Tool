import React, { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, Target, Award, Clock, Zap, Star, 
  BarChart, PieChart, LineChart, Calendar, Users,
  ChevronRight, RefreshCw, Download, Share2, Settings
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

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Get user ID from localStorage - check multiple possible sources
      let userId = null;
      
      // Method 1: Direct user ID stored during gameplay
      const directUserId = localStorage.getItem('gameUserId');
      if (directUserId) {
        userId = directUserId;
        console.log('Using direct user ID from localStorage:', userId);
      } 
      // Method 2: Check for game session user ID
      else if (localStorage.getItem('gameUser')) {
        try {
          const gameUser = JSON.parse(localStorage.getItem('gameUser'));
          // Try different possible ID fields
          userId = gameUser.userId || gameUser.id || gameUser._id;
          console.log('Using user ID from gameUser object:', userId);
        } catch (e) {
          console.error('Error parsing gameUser:', e);
        }
      }
      
      // Method 3: Try to extract from recent game sessions
      if (!userId) {
        // Check if we have any recent game data with user ID
        const recentGames = localStorage.getItem('recentGameSessions');
        if (recentGames) {
          try {
            const sessions = JSON.parse(recentGames);
            if (sessions.length > 0) {
              userId = sessions[sessions.length - 1].userId;
              console.log('Using user ID from recent game sessions:', userId);
            }
          } catch (e) {
            console.error('Error parsing recent game sessions:', e);
          }
        }
      }
      
      // Method 4: Try default user ID pattern (from your logs)
      if (!userId) {
        // Check if any localStorage keys match the user_ pattern
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key.startsWith('user_') || key.includes('userId')) {
            const value = localStorage.getItem(key);
            if (value && value.startsWith('user_')) {
              userId = value;
              console.log('Found user ID pattern in localStorage:', key, userId);
              break;
            }
          }
        }
      }
      
      // If still no user ID, show debug info
      if (!userId) {
        console.log('No user ID found, checking available users from backend...');
        
        // Try to get list of users with data from backend
        try {
          const debugResponse = await fetch(`${API_URL}/ai/debug-users`);
          if (debugResponse.ok) {
            const debugData = await debugResponse.json();
            setDebugInfo(debugData);
            
            // Use the first available user for demo
            if (debugData.users_with_data && debugData.users_with_data.length > 0) {
              userId = debugData.users_with_data[0];
              console.log('Using first available user from backend:', userId);
            }
          }
        } catch (debugError) {
          console.error('Debug endpoint error:', debugError);
        }
      }
      
      // If we still don't have a user ID, use a fallback
      if (!userId) {
        userId = 'default';
        console.log('Using fallback user ID:', userId);
      }
      
      console.log('Final user ID for analytics:', userId);
      
      // Fetch analytics with the determined user ID
      const response = await fetch(`${API_URL}/ai/progress-report`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Analytics API response:', data);
      
      if (data.success) {
        setAnalytics(data.report);
      } else {
        // Store the error message to help debugging
        setAnalytics(null);
        console.log('API returned success: false', data.message || data.error);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  };

  // Debug component to show available users
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
            {debugInfo.users_with_data.length > 5 && (
              <p className="text-xs text-gray-400 mt-1">
                ... and {debugInfo.users_with_data.length - 5} more
              </p>
            )}
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
            {debugInfo && debugInfo.total_users > 0 
              ? `Found ${debugInfo.total_users} user(s) with data, but couldn't match your session.`
              : "Play some games to generate AI insights!"}
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
            <button
              onClick={() => {
                // Clear localStorage and try again
                localStorage.removeItem('gameUserId');
                localStorage.removeItem('gameUser');
                fetchAnalytics();
              }}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-6 py-3 rounded-lg text-sm"
            >
              Clear User Cache & Retry
            </button>
          </div>
          
          <div className="mt-8 p-4 bg-gray-800/50 rounded-lg text-left">
            <p className="text-sm text-gray-400 mb-2">Troubleshooting:</p>
            <ul className="text-xs text-gray-500 list-disc pl-5">
              <li>Make sure you've played at least 1 game</li>
              <li>Check if backend is running on port 5001</li>
              <li>Try playing a game first, then check analytics</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

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
        {/* Debug info banner */}
        {debugInfo && (
          <div className="mb-6 p-4 bg-yellow-900/30 border border-yellow-700/50 rounded-xl">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-yellow-300 font-medium">
                  Using demo data from user: <code className="bg-black/30 px-2 py-1 rounded">{debugInfo.users_with_data?.[0] || 'unknown'}</code>
                </p>
                <p className="text-yellow-200/70 text-sm mt-1">
                  To see your own data, make sure to use the same user ID in both game and analytics.
                </p>
              </div>
              <button
                onClick={() => setDebugInfo(null)}
                className="text-yellow-300 hover:text-yellow-200"
              >
                ×
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
                <div className="text-3xl font-bold">{analytics.summary?.overall_accuracy || 0}%</div>
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
                <div className="text-3xl font-bold">{analytics.summary?.total_playtime_minutes || 0}</div>
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
                <div className="text-3xl font-bold">{analytics.summary?.current_streak || 0}</div>
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
            {/* Level Progress */}
            <div className="bg-gray-800/50 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" /> Level Progress
              </h2>
              <div className="space-y-4">
                {Object.entries(analytics.level_progress || {}).map(([level, data]) => (
                  <div key={level} className="flex items-center gap-4">
                    <div className="w-24 capitalize font-medium">{level}</div>
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span>{(data.accuracy || 0).toFixed(1)}% Complete</span>
                        <span className={data.unlocked ? 'text-green-400' : 'text-red-400'}>
                          {data.unlocked ? 'Unlocked' : 'Locked'}
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-3">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                          style={{ width: `${data.accuracy || 0}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {data.correct_attempts || 0}/{data.total_attempts || 0} correct attempts
                      </div>
                    </div>
                  </div>
                ))}
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
                    <div className="text-sm text-gray-400 mb-1">Next Level Performance</div>
                    <div className="text-3xl font-bold text-green-400">
                      {analytics.predictions?.next_level_score || 0}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Confidence</div>
                    <div className="text-2xl font-bold text-blue-400">
                      {analytics.predictions?.confidence || 0}%
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-400 mb-2">Time to Master Current Level</div>
                  <div className="text-lg font-bold text-yellow-400">
                    {analytics.predictions?.time_to_master || "Keep practicing!"}
                  </div>
                  <div className="text-sm text-gray-400 mt-4">
                    Based on your current learning pace and consistency
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Current Level */}
            <div className="bg-gradient-to-br from-blue-900/30 to-cyan-900/30 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-4">Current Level</h2>
              <div className="text-center">
                <div className="text-5xl font-bold mb-2">
                  {analytics.summary?.current_level?.toUpperCase() || 'BASIC'}
                </div>
                <div className="text-gray-300">Optimal difficulty for learning</div>
                {analytics.next_level_unlocked && (
                  <div className="mt-4 p-3 bg-green-500/20 rounded-lg border border-green-500/30">
                    <div className="text-green-400 font-bold">🎉 New Level Unlocked!</div>
                    <div className="text-sm">You can now try {analytics.next_level_unlocked} level</div>
                  </div>
                )}
              </div>
            </div>

            {/* Achievements */}
            <div className="bg-gradient-to-br from-yellow-900/20 to-amber-900/20 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Star className="w-5 h-5" /> Achievements
              </h2>
              <div className="space-y-3">
                {analytics.achievements?.length > 0 ? (
                  analytics.achievements.map((achievement, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-black/30 rounded-lg">
                      <div className="text-2xl">{achievement.icon}</div>
                      <div>
                        <div className="font-bold">{achievement.name}</div>
                        <div className="text-xs text-gray-400">Earned recently</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center p-4 text-gray-500">
                    Play more games to earn achievements!
                  </div>
                )}
              </div>
            </div>

            {/* Quick Insights */}
            <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-4">Quick Insights</h2>
              <div className="space-y-3">
                {analytics.insights?.slice(0, 3).map((insight, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-3 bg-black/30 rounded-lg">
                    <div className="w-2 h-2 bg-purple-400 rounded-full mt-2"></div>
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

        {/* Skill Gaps & Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          {/* Skill Gaps */}
          <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 rounded-2xl p-6 border border-red-800/30">
            <h2 className="text-xl font-bold mb-4">Areas to Improve</h2>
            <div className="space-y-3">
              {analytics.skill_gaps?.length > 0 ? (
                analytics.skill_gaps.slice(0, 3).map((gap, idx) => (
                  <div key={idx} className="p-3 bg-black/30 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <div className="font-bold text-white">{gap.word}</div>
                      <div className="text-red-400 font-bold">{gap.accuracy}%</div>
                    </div>
                    <div className="text-sm text-gray-400 mb-2">{gap.english}</div>
                    <div className="text-xs text-gray-300">{gap.suggestions?.[0] || 'Practice more'}</div>
                  </div>
                ))
              ) : (
                <div className="text-center p-4 text-gray-500">
                  No skill gaps detected - great job!
                </div>
              )}
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 rounded-2xl p-6 border border-green-800/30">
            <h2 className="text-xl font-bold mb-4">Recommended Next Steps</h2>
            <div className="space-y-3">
              {analytics.recommendations?.length > 0 ? (
                analytics.recommendations.slice(0, 3).map((rec, idx) => (
                  <div key={idx} className="p-3 bg-black/30 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <div className="font-bold text-white">{rec.word}</div>
                      <div className="flex items-center gap-2">
                        <div className="text-green-400 font-bold">{rec.accuracy}%</div>
                        <div className="text-xs bg-blue-500/30 px-2 py-1 rounded">P{rec.priority}</div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-400 mb-2">{rec.reason}</div>
                    <button 
                      onClick={() => navigate('/game/puzzle')}
                      className="text-xs text-blue-300 hover:text-blue-200 flex items-center gap-1"
                    >
                      Practice this word <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="text-center p-4 text-gray-500">
                  Complete more games for personalized recommendations
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Personalized Learning Plan */}
        <div className="mt-8 bg-gradient-to-br from-blue-900/20 to-purple-900/20 rounded-2xl p-6 border border-blue-800/30">
          <h2 className="text-xl font-bold mb-6">Personalized Learning Plan</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <div className="font-bold">Daily Goal</div>
                  <div className="text-sm text-gray-400">Practice 3 new words</div>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <Target className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <div className="font-bold">Weekly Target</div>
                  <div className="text-sm text-gray-400">Master 5 new signs</div>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <div className="font-bold">Focus Area</div>
                  <div className="text-sm text-gray-400 capitalize">
                    {analytics.summary?.current_level || 'basic'} level mastery
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAnalyticsDashboard;