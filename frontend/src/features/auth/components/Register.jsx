import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [form, setForm] = useState({ name: "", email: "", password: "", age: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState({ type: '', message: '' });
  const navigate = useNavigate();

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!form.name || !form.email || !form.password || !form.age) {
      showVisualFeedback('error', 'Please fill in all fields');
      return;
    }

    if (form.password.length < 6) {
      showVisualFeedback('error', 'Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:5000/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      
      const data = await res.json();
      
      if (res.ok && data.success) {
        // Store JWT token
        localStorage.setItem('token', data.token);
        
        // Store user data
        localStorage.setItem('user', JSON.stringify(data.user));
        
        showVisualFeedback('success', '🎉 Registered Successfully!');
        
        // Redirect to login or game-register after 1.5 seconds
        setTimeout(() => {
          navigate("/login");
        }, 1500);
      } else {
        showVisualFeedback('error', data.message || 'Registration failed');
      }
    } catch (err) {
      console.error(err);
      showVisualFeedback('error', 'Server error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-r from-sky-200 via-blue-300 to-yellow-200 p-4">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-lg p-6 w-full max-w-md space-y-4"
      >
        <div className="text-center">
          <div className="text-5xl mb-3">🧸</div>
          <h1 className="text-2xl font-bold text-sky-600">Create Account</h1>
          <p className="text-gray-600 text-sm mt-1">Join our learning community</p>
        </div>

        {feedback.message && (
          <div className={`p-3 rounded-xl text-center font-semibold text-base ${
            feedback.type === 'success' 
              ? 'bg-green-100 text-green-800 border-2 border-green-300' 
              : 'bg-red-100 text-red-800 border-2 border-red-300'
          }`}>
            <div className="text-xl mb-1">
              {feedback.type === 'success' ? '✅' : '❌'}
            </div>
            {feedback.message}
          </div>
        )}

        <div className="space-y-3">
          <input
            type="text"
            name="name"
            placeholder="👤 Full Name"
            value={form.name}
            onChange={handleChange}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 outline-none transition-all"
            required
          />
          
          <input
            type="email"
            name="email"
            placeholder="📧 Email Address"
            value={form.email}
            onChange={handleChange}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 outline-none transition-all"
            required
          />
          
          <input
            type="password"
            name="password"
            placeholder="🔑 Password (min 6 characters)"
            value={form.password}
            onChange={handleChange}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 outline-none transition-all"
            required
            minLength={6}
          />
          
          <input
            type="number"
            name="age"
            placeholder="🎂 Age"
            value={form.age}
            onChange={handleChange}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 outline-none transition-all"
            required
            min="1"
            max="120"
          />
        </div>

        <button 
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-xl font-bold text-white transition-all duration-200 transform hover:scale-102 ${
            isLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-sky-500 hover:bg-sky-600 shadow-lg'
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              <span>Creating Account...</span>
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <span>Register</span>
              <span className="ml-2">🚀</span>
            </div>
          )}
        </button>

        <div className="text-center text-sm text-gray-600 mt-4">
          Already have an account?{' '}
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="text-sky-600 font-semibold hover:underline"
          >
            Sign In
          </button>
        </div>
      </form>
    </div>
  );
}