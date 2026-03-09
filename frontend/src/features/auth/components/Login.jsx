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
        // Store JWT token
        localStorage.setItem('token', data.token);

        // Store user data
        localStorage.setItem('user', JSON.stringify(data.user));

        // Always navigate to home page after login
        showVisualFeedback('success', `Welcome ${data.user.name}!`);

        // Cache game user data if available
        if (data.user.hasTakenQuiz) {
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
        } else {
          const partialGameUser = {
            _id: data.user._id,
            userId: data.user._id,
            mongoId: data.user._id,
            name: data.user.name,
            email: data.user.email,
            age: data.user.age,
            hasTakenQuiz: false
          };
          localStorage.setItem('gameUser', JSON.stringify(partialGameUser));
          localStorage.setItem('gameUserId', data.user._id);
        }

        setTimeout(() => navigate('/', { replace: true }), 1200);
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
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-100 to-yellow-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg p-6 w-full max-w-sm transform hover:scale-102 transition-transform duration-200">

        <div className="text-center mb-8">
          <div className="text-5xl mb-3 animate-bounce">
            👋
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-sky-600 to-blue-500 bg-clip-text text-transparent">
            Welcome Back!
          </h1>
          <p className="text-gray-600 text-sm mt-1">Sign in to continue learning</p>
        </div>

        {feedback.message && (
          <div className={`mb-4 p-3 rounded-xl text-center font-semibold text-base animate-pulse ${feedback.type === 'success'
              ? 'bg-green-100 text-green-800 border-2 border-green-300'
              : 'bg-red-100 text-red-800 border-2 border-red-300'
            }`}>
            <div className="text-xl mb-1">
              {feedback.type === 'success' ? '✅' : '❌'}
            </div>
            {feedback.message}
          </div>
        )}

        <div className="space-y-4">

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
                className="w-full p-3 pl-10 text-base border rounded-lg focus:border-sky-500 focus:ring-2 focus:ring-sky-200 transition-all duration-200 outline-none"
                placeholder="your@email.com"
                required
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-xl">
                📧
              </div>
            </div>
          </div>

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
                className="w-full p-3 pl-10 pr-10 text-base border rounded-lg focus:border-sky-500 focus:ring-2 focus:ring-sky-200 transition-all duration-200 outline-none"
                placeholder="Enter your password"
                required
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-xl">
                🔒
              </div>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xl hover:scale-110 transition-transform"
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className={`w-full py-3 px-5 rounded-xl text-lg font-bold text-gray-800 transition-all duration-200 transform hover:scale-102 ${isLoading
                ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-sky-100 to-blue-200 hover:from-sky-200 hover:to-blue-300 border border-sky-300 shadow'
              }`}
          >
            {isLoading ? (
              <div className="flex items-center justify-center text-sm">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                <span>Signing In...</span>
              </div>
            ) : (
              <div className="flex items-center justify-center text-sm">
                <span>Sign In</span>
                <span className="ml-2 text-xl">🚀</span>
              </div>
            )}
          </button>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>

          <button
            onClick={handleRegisterRedirect}
            className="w-full py-3 px-5 rounded-xl text-lg font-bold text-gray-700 border border-sky-300 bg-white hover:bg-sky-50 transition-all duration-200 transform hover:scale-102"
          >
            <div className="flex items-center justify-center text-sm">
              <span>Create New Account</span>
              <span className="ml-2 text-xl">✨</span>
            </div>
          </button>
        </div>

        <div className="mt-6 p-4 bg-gradient-to-r from-sky-50 to-blue-50 rounded-2xl border border-sky-200">
          <div className="text-center">
            <div className="text-2xl mb-2">💡</div>
            <p className="text-sm text-sky-900 font-bold">
              Smart Learning Path:
            </p>
            <div className="mt-2 space-y-1 text-xs text-gray-700">
              <div className="flex items-center justify-center">
                <span className="w-6 h-6 bg-green-200 rounded-full flex items-center justify-center mr-2 text-green-900 font-bold">1️⃣</span>
                <span>First time? Take a quick quiz</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center mr-2 text-blue-900 font-bold">2️⃣</span>
                <span>Get personalized level recommendation</span>
              </div>
              <div className="flex items-center justify-center">
                <span className="w-6 h-6 bg-yellow-200 rounded-full flex items-center justify-center mr-2 text-yellow-900 font-bold">3️⃣</span>
                <span>Start playing at your own pace!</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-center mt-6 space-x-2">
          <div className="w-3 h-3 bg-sky-400 rounded-full animate-pulse"></div>
          <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
        </div>
      </div>
    </div>
  );
}