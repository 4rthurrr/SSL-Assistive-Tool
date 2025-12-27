import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [feedback, setFeedback] = useState({ type: '', message: '' });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (feedback.message) {
      setFeedback({ type: '', message: '' });
    }
  };

  const showVisualFeedback = (type, message) => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback({ type: '', message: '' }), 4000);
  };

  const handleSubmit = async () => {
    // Validation
    if (!form.email || !form.password) {
      showVisualFeedback('error', 'Please fill in all fields');
      return;
    }

    setIsLoading(true);
    
    try {
      const res = await fetch("http://localhost:5000/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      
      const data = await res.json();
      
      if (data.success) {
        // Store user data in localStorage
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Check if user has completed quiz
        if (data.user.hasTakenQuiz) {
          // User has completed quiz - go directly to game selection
          showVisualFeedback('success', `Welcome back ${data.user.name}! Taking you to games...`);
          
          // Store game user data
          const gameUserData = {
            userId: data.user._id,
            mongoId: data.user.gameProfile?._id || data.user._id,
            name: data.user.name,
            userType: data.user.gameProfile?.userType || 'student',
            grade: data.user.gameProfile?.grade || '2',
            recommendedLevel: data.user.recommendedLevel || 'basic',
            hasTakenQuiz: true,
            quizScore: data.user.gameProfile?.quizScore || 0,
            quizTotal: data.user.gameProfile?.quizTotal || 0
          };
          
          localStorage.setItem('gameUser', JSON.stringify(gameUserData));
          
          setTimeout(() => {
            navigate('/game/puzzle');
          }, 1500);
        } else {
          // User hasn't completed quiz - go to registration/quiz flow
          showVisualFeedback('success', `Welcome ${data.user.name}! Let's set up your profile.`);
          
          // Store partial game user data
          const partialGameUser = {
            userId: data.user._id,
            mongoId: data.user._id,
            name: data.user.name,
            email: data.user.email,
            age: data.user.age,
            hasTakenQuiz: false
          };
          
          localStorage.setItem('gameUser', JSON.stringify(partialGameUser));
          
          setTimeout(() => {
            navigate('/game-register');
          }, 1500);
        }
      } else {
        showVisualFeedback('error', data.message || 'Wrong email or password');
      }
    } catch (err) {
      console.error('Login error:', err);
      showVisualFeedback('error', 'Cannot connect to server. Make sure backend is running on port 5000.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  const handleRegisterRedirect = () => {
    navigate('/register');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-yellow-400 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md transform hover:scale-105 transition-transform duration-300">
        
        {/* Header with Large Visual Icon */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4 animate-bounce">
            👋
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Welcome Back!
          </h1>
          <p className="text-gray-600 text-lg mt-2">Sign in to continue learning</p>
        </div>

        {/* Visual Feedback Banner */}
        {feedback.message && (
          <div className={`mb-6 p-4 rounded-2xl text-center font-bold text-lg animate-pulse ${
            feedback.type === 'success' 
              ? 'bg-green-100 text-green-800 border-2 border-green-300' 
              : 'bg-red-100 text-red-800 border-2 border-red-300'
          }`}>
            <div className="text-2xl mb-1">
              {feedback.type === 'success' ? '✅' : '❌'}
            </div>
            {feedback.message}
          </div>
        )}

        <div className="space-y-6">
          
          {/* Email Input */}
          <div className="space-y-2">
            <label className="flex items-center text-lg font-semibold text-gray-700">
              <span className="text-2xl mr-2">📧</span>
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                onKeyPress={handleKeyPress}
                className="w-full p-4 pl-12 text-lg border-2 border-gray-300 rounded-2xl focus:border-purple-500 focus:ring-4 focus:ring-purple-200 transition-all duration-300 outline-none"
                placeholder="your@email.com"
                required
              />
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-2xl">
                📧
              </div>
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <label className="flex items-center text-lg font-semibold text-gray-700">
              <span className="text-2xl mr-2">🔒</span>
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={form.password}
                onChange={handleChange}
                onKeyPress={handleKeyPress}
                className="w-full p-4 pl-12 pr-12 text-lg border-2 border-gray-300 rounded-2xl focus:border-purple-500 focus:ring-4 focus:ring-purple-200 transition-all duration-300 outline-none"
                placeholder="Enter your password"
                required
              />
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-2xl">
                🔒
              </div>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-2xl hover:scale-125 transition-transform"
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {/* Login Button */}
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className={`w-full py-4 px-6 rounded-2xl text-xl font-bold text-white transition-all duration-300 transform hover:scale-105 ${
              isLoading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-lg hover:shadow-xl'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                <span>Signing In...</span>
                <span className="ml-2">⏳</span>
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <span>Sign In</span>
                <span className="ml-2 text-2xl">🚀</span>
              </div>
            )}
          </button>

          {/* Divider */}
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>

          {/* Register Button */}
          <button
            onClick={handleRegisterRedirect}
            className="w-full py-4 px-6 rounded-2xl text-xl font-bold text-gray-700 border-2 border-purple-300 bg-white hover:bg-purple-50 transition-all duration-300 transform hover:scale-105"
          >
            <div className="flex items-center justify-center">
              <span>Create New Account</span>
              <span className="ml-2 text-2xl">✨</span>
            </div>
          </button>
        </div>

        {/* Visual Help Section */}
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl border border-purple-100">
          <div className="text-center">
            <div className="text-2xl mb-2">💡</div>
            <p className="text-sm text-purple-800 font-medium">
              Smart Learning Path:
            </p>
            <div className="mt-2 space-y-1 text-xs text-gray-600">
              <div className="flex items-center justify-center">
                <span className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mr-2">1️⃣</span>
                <span>First time? Take a quick quiz</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-2">2️⃣</span>
                <span>Get personalized level recommendation</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center mr-2">3️⃣</span>
                <span>Start playing at your own pace!</span>
              </div>
            </div>
          </div>
        </div>

        {/* Debug Info (Remove in production) */}
        <div className="mt-4 p-3 bg-gray-50 rounded-xl text-xs text-gray-600">
          <p className="font-medium mb-1">🔧 Backend Status:</p>
          <p>• Server: http://localhost:5000</p>
          <p>• Login: /users/login</p>
          <p className="mt-1 text-green-600">✅ Make sure your backend is running!</p>
        </div>

        {/* Decorative Elements */}
        <div className="flex justify-center mt-6 space-x-2">
          <div className="w-3 h-3 bg-purple-400 rounded-full animate-pulse"></div>
          <div className="w-3 h-3 bg-pink-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
          <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
        </div>
      </div>
    </div>
  );
}