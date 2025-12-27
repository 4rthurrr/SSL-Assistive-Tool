import { useNavigate } from "react-router-dom";
import { 
  Star, Clock, Trophy, Sparkles, ChevronRight, Play, Award, 
  Brain, TrendingUp, BarChart 
} from "lucide-react";
import { useEffect, useState } from "react";

export default function GameSelection() {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [showAnalyticsBtn, setShowAnalyticsBtn] = useState(false);

  // Load user data from localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem('gameUser');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUserData(parsedUser);
      
      // Show analytics button if user has taken quiz
      if (parsedUser.hasTakenQuiz) {
        setShowAnalyticsBtn(true);
      }
    } else {
      // No user registered, redirect to form
      navigate('/game-register');
    }
  }, [navigate]);

  if (!userData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
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

  // Calculate progress percentage
  const masteryProgress = (userProgress.masteredWords / 50) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-300 to-yellow-300 p-4 md:p-6">
      {/* Header */}
      <div className="bg-white rounded-3xl shadow-lg p-4 md:p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 md:gap-4">
            <div className="w-12 h-12 md:w-16 md:h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xl md:text-2xl font-bold">
              {userData.name?.substring(0, 2).toUpperCase() || 'SS'}
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-bold text-gray-800">
                හෙලෝ, {userData.name}!
              </h2>
              <p className="text-gray-600 text-sm md:text-base">
                Level {userProgress.level}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 md:gap-6">
            <div className="text-center">
              <div className="flex items-center gap-1 text-yellow-500 text-lg md:text-xl">
                <Star fill="currentColor" className="w-5 h-5 md:w-6 md:h-6" />
                <span className="font-bold">{userProgress.totalStars}</span>
              </div>
              <p className="text-xs text-gray-600">Stars</p>
            </div>
            <div className="text-center">
              <div className="flex items-center gap-1 text-blue-500 text-lg md:text-xl">
                <Clock className="w-5 h-5 md:w-6 md:h-6" />
                <span className="font-bold">{userProgress.dailyTimeLeft}</span>
              </div>
              <p className="text-xs text-gray-600">Minutes Left</p>
            </div>
            <div className="text-center">
              <div className="flex items-center gap-1 text-green-500 text-lg md:text-xl">
                <TrendingUp className="w-5 h-5 md:w-6 md:h-6" />
                <span className="font-bold">{userProgress.streak}</span>
              </div>
              <p className="text-xs text-gray-600">Day Streak</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendation Badge */}
      {userData.recommendedLevel && (
        <div className="bg-gradient-to-r from-yellow-400 to-orange-400 rounded-3xl shadow-lg p-4 mb-6 text-white">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Award className="w-7 h-7 md:w-8 md:h-8" />
              <div>
                <p className="font-bold text-base md:text-lg">Recommended for You</p>
                <p className="text-sm text-white/90">
                  Start with <span className="font-bold uppercase">{userData.recommendedLevel}</span> level
                </p>
              </div>
            </div>
            <div className="text-left md:text-right">
              <p className="text-sm">Quiz Score</p>
              <p className="font-bold text-2xl">
                {userData.quizScore || 0}/{userData.quizTotal || 10}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Progress Card - Now Clickable */}
      <button 
        onClick={() => navigate('/ai-analytics')}
        className="w-full bg-white rounded-3xl shadow-lg p-4 md:p-6 mb-6 text-left hover:shadow-xl transition-shadow duration-300 hover:scale-[1.02] active:scale-[0.98]"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Trophy className="text-yellow-500 w-5 h-5 md:w-6 md:h-6" />
            Your Progress
          </h3>
          <div className="flex items-center gap-2 text-purple-600">
            <Brain className="w-4 h-4 md:w-5 md:h-5" />
            <span className="text-sm font-semibold">View AI Analytics</span>
            <ChevronRight className="w-4 h-4" />
          </div>
        </div>
        
        <div className="space-y-4 mb-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Words Mastered</span>
              <span className="font-bold text-purple-600">
                {userProgress.masteredWords}/50
              </span>
            </div>
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-1000"
                style={{ width: `${masteryProgress}%` }}
              />
            </div>
          </div>
          
          {/* Additional progress metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center bg-purple-50 rounded-xl p-3">
              <div className="text-lg font-bold text-purple-600">
                {userProgress.accuracy}%
              </div>
              <div className="text-xs text-gray-600">Accuracy</div>
            </div>
            <div className="text-center bg-pink-50 rounded-xl p-3">
              <div className="text-lg font-bold text-pink-600">
                {userProgress.streak}
              </div>
              <div className="text-xs text-gray-600">Day Streak</div>
            </div>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="flex items-center justify-between text-xs md:text-sm text-gray-500 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1">
            <BarChart className="w-3 h-3 md:w-4 md:h-4" />
            <span>AI-powered insights available</span>
          </div>
          <div className="text-purple-600 font-semibold animate-pulse">
            Click to view →
          </div>
        </div>
      </button>

      {/* Game Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <button
          onClick={() => navigate("/game/puzzle", { 
            state: { 
              userId: userData.userId || userData._id,
              recommendedLevel: userData.recommendedLevel,
              userName: userData.name,
              userGrade: userData.grade
            } 
          })}
          className="bg-gradient-to-br from-blue-400 to-blue-600 rounded-3xl shadow-lg p-6 md:p-8 text-white transform hover:scale-105 transition-all duration-300 relative"
        >
          {userData.recommendedLevel && (
            <div className="absolute top-3 right-3 md:top-4 md:right-4 bg-yellow-400 text-blue-900 text-xs font-bold px-2 py-1 md:px-3 md:py-1 rounded-full">
              ⭐ RECOMMENDED
            </div>
          )}
          <div className="flex items-center justify-between mb-4">
            <Sparkles className="w-10 h-10 md:w-12 md:h-12" />
            <ChevronRight className="w-6 h-6 md:w-8 md:h-8" />
          </div>
          <h3 className="text-2xl md:text-3xl font-bold mb-2">
            සංඥා විදු ප්‍රහේලිකා
          </h3>
          <p className="text-blue-100 text-base md:text-lg">
            Find hidden words from sign videos
          </p>
        </button>

        <button
          onClick={() => navigate("/game/sentence")}
          className="bg-gradient-to-br from-green-400 to-green-600 rounded-3xl shadow-lg p-6 md:p-8 text-white transform hover:scale-105 transition-all duration-300"
        >
          <div className="flex items-center justify-between mb-4">
            <Play className="w-10 h-10 md:w-12 md:h-12" />
            <ChevronRight className="w-6 h-6 md:w-8 md:h-8" />
          </div>
          <h3 className="text-2xl md:text-3xl font-bold mb-2">
            සංඥා වාක්‍ය හුරු ක්‍රීඩා
          </h3>
          <p className="text-green-100 text-base md:text-lg">
            Sign Sentence Familiarity Game
          </p>
        </button>
      </div>

      {/* Quick Analytics Preview */}
      {showAnalyticsBtn && (
        <div className="mt-6 md:mt-8">
          <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-3xl shadow-lg p-5 md:p-6 text-white">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 md:w-12 md:h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
                  <Brain className="w-5 h-5 md:w-6 md:h-6 text-blue-400" />
                </div>
                <div>
                  <h4 className="font-bold text-lg md:text-xl">AI Learning Insights</h4>
                  <p className="text-gray-300 text-sm">
                    Personalized recommendations based on your performance
                  </p>
                </div>
              </div>
              <button
                onClick={() => navigate('/ai-analytics')}
                className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-2 transition-all"
              >
                <TrendingUp className="w-4 h-4 md:w-5 md:h-5" />
                View Full Report
                <ChevronRight className="w-4 h-4 md:w-5 md:h-5" />
              </button>
            </div>
            
            {/* Mini Preview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
              <div className="bg-white/10 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-green-400">85%</div>
                <div className="text-xs text-gray-300">Progress</div>
              </div>
              <div className="bg-white/10 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-yellow-400">4</div>
                <div className="text-xs text-gray-300">Skills</div>
              </div>
              <div className="bg-white/10 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-blue-400">12</div>
                <div className="text-xs text-gray-300">Insights</div>
              </div>
              <div className="bg-white/10 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-purple-400">3</div>
                <div className="text-xs text-gray-300">Tips</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions Footer */}
      <div className="mt-6 md:mt-8 grid grid-cols-2 gap-3">
        <button
          onClick={() => navigate('/game-register')}
          className="bg-white rounded-xl p-3 text-center hover:bg-gray-50 transition-colors"
        >
          <div className="text-lg">👤</div>
          <div className="text-xs font-medium text-gray-700">Edit Profile</div>
        </button>
        <button
          onClick={() => navigate('/ai-analytics')}
          className="bg-purple-600 rounded-xl p-3 text-center text-white hover:bg-purple-700 transition-colors"
        >
          <div className="text-lg">📊</div>
          <div className="text-xs font-medium">Analytics</div>
        </button>
      </div>
    </div>
  );
}