import { useNavigate } from "react-router-dom";
import {
  Star, Clock, Trophy, Sparkles, ChevronRight, Play, Award,
  Brain, TrendingUp, BarChart, User, LogOut
} from "lucide-react";
import { useEffect, useState } from "react";

export default function GameSelection() {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [showAnalyticsBtn, setShowAnalyticsBtn] = useState(false);
  const [showQuizScore, setShowQuizScore] = useState(false);

  // Load user data from localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem('gameUser');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUserData(parsedUser);

      // Show analytics button if user has taken quiz
      if (parsedUser.hasTakenQuiz) {
        setShowAnalyticsBtn(true);
        setShowQuizScore(true);
      }
    } else {
      // No user registered, redirect to form
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

  // Get quiz score display
  const getQuizScoreDisplay = () => {
    if (!userData.hasTakenQuiz || !showQuizScore) return null;

    const score = userData.quizScore || 0;
    const total = userData.quizTotal || 0;
    const percentage = userData.quizPercentage || 0;

    // Grade 1 students have auto-quiz with 0/0
    if (total === 0 && userData.grade === '1') {
      return (
        <div className="flex items-center gap-3 px-4 py-2 bg-green-100 rounded-lg border border-green-200">
          <Award className="w-5 h-5 text-green-600" />
          <div className="text-left">
            <div className="text-xs text-green-800 font-medium">Grade 1 Student</div>
            <div className="text-sm font-bold text-green-700">Basic Level (Auto-set)</div>
          </div>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-3 px-4 py-2 bg-yellow-50 rounded-lg border border-yellow-200">
        <Trophy className="w-5 h-5 text-yellow-600" />
        <div className="text-left">
          <div className="text-xs text-yellow-800 font-medium">Quiz Score</div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-yellow-700">
              {score}/{total}
            </span>
            <span className="text-sm font-medium text-yellow-600">
              ({percentage}%)
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-300 via-blue-200 to-yellow-200 p-3">
      {/* Fixed Navigation Bar with Quiz Score */}
      <div className="sticky top-0 z-50 mb-3">
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-3">
          <div className="flex items-center justify-between">
            {/* User Info */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-sky-500 to-blue-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                {userData.name?.substring(0, 2).toUpperCase() || 'SS'}
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-800">
                  හෙලෝ, {userData.name}!
                </h2>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Level {userProgress.level}</span>
                  {userData.recommendedLevel && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span className="text-sm font-medium text-sky-600 capitalize">
                        {userData.recommendedLevel}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Quiz Score Display - Always visible if quiz taken */}
            {showQuizScore && getQuizScoreDisplay()}

            {/* Stats & Logout */}
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-6">
                <div className="text-center">
                  <div className="flex items-center gap-1 text-yellow-500 text-lg">
                    <Star fill="currentColor" className="w-5 h-5" />
                    <span className="font-bold">{userProgress.totalStars}</span>
                  </div>
                  <p className="text-xs text-gray-600">Stars</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center gap-1 text-blue-500 text-xl">
                    <Clock className="w-6 h-6" />
                    <span className="font-bold">{userProgress.dailyTimeLeft}</span>
                  </div>
                  <p className="text-xs text-gray-600">Minutes</p>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-red-50 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden md:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendation Banner (Only for first time or if not showing quiz score) */}
      {userData.recommendedLevel && !showQuizScore && (
        <div className="bg-gradient-to-r from-yellow-400 to-orange-400 rounded-xl shadow-md p-3 mb-3 text-white text-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <Award className="w-7 h-7 md:w-8 md:h-8" />
              <div>
                <p className="font-bold text-base md:text-lg">Recommended for You</p>
                <p className="text-sm text-white/90">
                  Start with <span className="font-bold uppercase">{userData.recommendedLevel}</span> level
                </p>
              </div>
            </div>
            {userData.quizScore !== undefined && userData.quizTotal !== undefined && (
              <div className="text-left md:text-right">
                <p className="text-xs">Quiz Score</p>
                <p className="font-bold text-xl">
                  {userData.quizScore || 0}/{userData.quizTotal || 10}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress Card - Now Clickable */}
      <button
        onClick={() => navigate('/ai-analytics')}
        className="w-full bg-white rounded-xl shadow-md p-3 mb-3 text-left hover:shadow-lg transition-shadow duration-200 hover:scale-[1.01] active:scale-[0.98]"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Trophy className="text-yellow-500 w-5 h-5 md:w-6 md:h-6" />
            Your Progress
          </h3>
          <div className="flex items-center gap-2 text-sky-600">
            <Brain className="w-4 h-4 md:w-5 md:h-5" />
            <span className="text-sm font-semibold">View AI Analytics</span>
            <ChevronRight className="w-4 h-4" />
          </div>
        </div>

        <div className="space-y-2 mb-3">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Words Mastered</span>
              <span className="font-bold text-sky-600">
                {userProgress.masteredWords}/50
              </span>
            </div>
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-sky-500 to-blue-500 rounded-full transition-all duration-1000"
                style={{ width: `${masteryProgress}%` }}
              />
            </div>
          </div>

          {/* Additional progress metrics */}
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center bg-sky-50 rounded-lg p-2">
              <div className="text-lg font-bold text-sky-600">
                {userProgress.accuracy}%
              </div>
              <div className="text-xs text-gray-600">Accuracy</div>
            </div>
            <div className="text-center bg-yellow-50 rounded-lg p-2">
              <div className="text-lg font-bold text-yellow-600">
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
          <div className="text-sky-600 font-semibold animate-pulse">
            Click to view →
          </div>
        </div>
      </button>

      {/* Game Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
        <button
          onClick={() => navigate("/game/puzzle", {
            state: {
              userId: userData.userId || userData._id,
              recommendedLevel: userData.recommendedLevel,
              userName: userData.name,
              userGrade: userData.grade
            }
          })}
          className="bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl shadow-md p-4 md:p-6 text-white transform hover:scale-102 transition-all duration-200 relative"
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
          <h3 className="text-xl md:text-2xl font-bold mb-1 text-black">
            සංඥා විදු ප්‍රහේලිකා
          </h3>
          <p className="text-black text-sm md:text-base">
            Find hidden words from sign videos
          </p>
        </button>

        <button
          onClick={() => navigate("/game/sentence")}
          className="bg-gradient-to-br from-green-400 to-green-600 rounded-xl shadow-md p-4 md:p-6 text-white transform hover:scale-102 transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-4">
            <Play className="w-10 h-10 md:w-12 md:h-12" />
            <ChevronRight className="w-6 h-6 md:w-8 md:h-8" />
          </div>
          <h3 className="text-xl md:text-2xl font-bold mb-1">
            සංඥා වාක්‍ය හුරු ක්‍රීඩා
          </h3>
          <p className="text-green-100 text-sm md:text-base">
            Sign Sentence Familiarity Game
          </p>
        </button>
      </div>

      {/* Quick Analytics Preview */}
      {showAnalyticsBtn && (
        <div className="mt-4 md:mt-6">
          <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl shadow-md p-3 md:p-4 text-white">
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
                className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-all"
              >
                <TrendingUp className="w-4 h-4 md:w-5 md:h-5" />
                View Full Report
                <ChevronRight className="w-4 h-4 md:w-5 md:h-5" />
              </button>
            </div>

            {/* Mini Preview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3">
              <div className="bg-white/10 rounded-lg p-2 text-center">
                <div className="text-base font-bold text-green-400">85%</div>
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
                <div className="text-lg font-bold text-sky-400">3</div>
                <div className="text-xs text-gray-300">Tips</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions Footer */}
      <div className="mt-4 md:mt-6 grid grid-cols-3 gap-2">
        <button
          onClick={() => navigate('/game-register')}
          className="bg-white rounded-lg p-2 text-center hover:bg-gray-50 transition-colors"
        >
          <div className="text-lg">👤</div>
          <div className="text-xs font-medium text-gray-700">Edit Profile</div>
        </button>
        <button
          onClick={() => navigate('/ai-analytics')}
          className="bg-sky-600 rounded-lg p-2 text-center text-white hover:bg-sky-700 transition-colors"
        >
          <div className="text-lg">📊</div>
          <div className="text-xs font-medium">Analytics</div>
        </button>
        <button
          onClick={() => navigate('/game-history')}
          className="bg-blue-600 rounded-lg p-2 text-center text-white hover:bg-blue-700 transition-colors"
        >
          <div className="text-lg">📝</div>
          <div className="text-xs font-medium">History</div>
        </button>
      </div>

      {/* Quiz Status Summary */}
      {showQuizScore && (
        <div className="mt-4 p-3 bg-white rounded-xl shadow-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-500" />
              <span className="font-medium text-gray-700">Quiz Status:</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-sm text-gray-600">Level</div>
                <div className="text-lg font-bold text-sky-600 capitalize">
                  {userData.recommendedLevel || 'basic'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Completed</div>
                <div className="text-lg font-bold text-green-600">
                  {userData.hasTakenQuiz ? 'Yes' : 'No'}
                </div>
              </div>
              {userData.quizPercentage > 0 && (
                <div className="text-center">
                  <div className="text-sm text-gray-600">Score</div>
                  <div className="text-lg font-bold text-blue-600">
                    {userData.quizPercentage}%
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}