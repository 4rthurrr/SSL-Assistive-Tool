import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User, Award, Trophy, Image, Video, Gamepad2 } from 'lucide-react';

const API_URL = 'http://localhost:5000/api';

const GameUserForm = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState('loading');
  const [userData, setUserData] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    user_type: 'student',
    grade: '2'
  });

  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [quizAnswers, setQuizAnswers] = useState([]);
  const [quizResult, setQuizResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiHint, setAiHint] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [hintWord, setHintWord] = useState('');
  const AI_API = 'http://localhost:5001/api/ai/generate-hint';

  // Helper function to get JWT token
  const getAuthToken = () => {
    return localStorage.getItem('authToken');
  };

  // Helper function to make authenticated API calls
  const authenticatedFetch = async (url, options = {}) => {
    const token = getAuthToken();

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(url, {
      ...options,
      headers
    });
  };

  useEffect(() => {
    checkUserStatus();
  }, [location]);

  // Extract video key from full path
  const getVideoKey = (videoPath) => {
    if (!videoPath) return null;
    const parts = videoPath.split('/');
    const folderName = parts[parts.length - 2];
    return folderName ? folderName.toLowerCase() : null;
  };

  const checkUserStatus = async () => {
    const storedUser = JSON.parse(localStorage.getItem('user') || localStorage.getItem('gameUser') || 'null');

    // First-time user: no quiz taken yet → show profile/grade setup form
    if (storedUser && !storedUser.hasTakenQuiz) {
      if (storedUser.name) {
        setFormData(prev => ({
          ...prev,
          name: storedUser.name,
          user_type: storedUser.userType || 'student',
          grade: storedUser.grade || '2'
        }));
      }
      setUserData(storedUser);
      setStep('register');
      return;
    }

    // Returning user: has taken quiz → verify with API then redirect
    if (storedUser && storedUser._id) {
      try {
        const response = await authenticatedFetch(`${API_URL}/user/quiz-status`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Quiz status response:", data);

        if (data.success) {
          if (data.hasTakenQuiz || storedUser.hasTakenQuiz) {
            const gameUser = {
              ...storedUser,
              hasTakenQuiz: true,
              recommendedLevel: data.recommendedLevel || storedUser.recommendedLevel || 'basic',
              name: data.name || storedUser.name
            };

            setUserData(gameUser);
            localStorage.setItem('gameUser', JSON.stringify(gameUser));
            localStorage.setItem('user', JSON.stringify(gameUser));
            if (gameUser._id) localStorage.setItem('gameUserId', gameUser._id);

            setStep('goToGames');
            setTimeout(() => {
              navigate('/gameselection');
            }, 1000);
            return;
          } else {
            if (storedUser.name) {
              setFormData(prev => ({
                ...prev,
                name: storedUser.name,
                user_type: storedUser.userType || 'student',
                grade: storedUser.grade || '2'
              }));
            }

            setUserData(storedUser);
            setStep('quizIntro');
            return;
          }
        } else {
          if (storedUser.hasTakenQuiz) {
            console.log("API failed but localStorage shows quiz taken");
            setUserData(storedUser);
            setStep('goToGames');
            setTimeout(() => {
              navigate('/gameselection');
            }, 1000);
            return;
          }
          setStep('register');
        }
      } catch (error) {
        console.error('Error checking user status:', error);

        if (storedUser.hasTakenQuiz) {
          console.log("Using localStorage data due to API error");
          setUserData(storedUser);
          setStep('goToGames');
          setTimeout(() => {
            navigate('/gameselection');
          }, 1000);
        } else {
          setStep('register');
        }
      }
    } else {
      setStep('register');
    }
  };

  const handleRegister = async () => {
    if (!formData.name) {
      alert('Please enter your name');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        // Store JWT token
        if (data.token) {
          localStorage.setItem('authToken', data.token);
          console.log('✅ JWT token stored');
        }

        const user = {
          _id: data.user._id,
          mongoId: data.user._id,
          name: data.user.name || formData.name,
          userType: formData.user_type,
          grade: formData.grade,
          hasTakenQuiz: data.user.hasTakenQuiz || false,
          recommendedLevel: data.user.recommendedLevel || 'basic'
        };

        setUserData(user);
        localStorage.setItem('user', JSON.stringify(user));
        localStorage.setItem('gameUser', JSON.stringify(user));
        if (data.user._id) localStorage.setItem('gameUserId', data.user._id);

        if (formData.grade === '1') {
          console.log('Grade 1 student detected - skipping quiz, setting basic level');

          const saveResponse = await authenticatedFetch(`${API_URL}/quiz/submit`, {
            method: 'POST',
            body: JSON.stringify({
              answers: [],
              recommendedLevel: 'basic',
              quizScore: 0,
              quizTotal: 0,
              quizPercentage: 0
            })
          });

          const saveData = await saveResponse.json();
          console.log("Grade 1 auto-quiz response:", saveData);

          const updatedUser = {
            ...user,
            hasTakenQuiz: true,
            recommendedLevel: 'basic'
          };

          localStorage.setItem('user', JSON.stringify(updatedUser));
          localStorage.setItem('gameUser', JSON.stringify(updatedUser));

          setTimeout(() => {
            navigate('/gameselection');
          }, 800);
        } else if (data.user.hasTakenQuiz) {
          setStep('goToGames');
          setTimeout(() => {
            navigate('/gameselection');
          }, 1000);
        } else {
          setStep('quizIntro');
        }
      } else {
        alert('Registration failed: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('Failed to register. Please check server connection.');
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = async () => {
    try {
      setLoading(true);
      console.log(`Loading quiz for grade: ${formData.grade}`);

      // Use authenticatedFetch to include JWT token
      const response = await authenticatedFetch(`${API_URL}/questions/quiz/${formData.grade}`);
      const data = await response.json();

      console.log("Quiz data response:", data);

      if (data.success && data.questions && data.questions.length > 0) {
        setQuestions(data.questions);
        setCurrentQuestion(0);
        setQuizAnswers([]);
        setStep('quiz');
      } else {
        alert('Failed to load quiz questions: ' + (data.error || data.message || 'No questions available'));
      }
    } catch (error) {
      console.error('Quiz load error:', error);
      alert('Failed to load quiz. Please check server connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuizAnswer = (selectedAnswer) => {
    const currentQ = questions[currentQuestion];
    const newAnswer = {
      id: currentQ.id,
      selectedAnswer: selectedAnswer
    };

    const newAnswers = [...quizAnswers, newAnswer];
    setQuizAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitQuiz(newAnswers);
    }
  };

  const submitQuiz = async (answers) => {
    try {
      setLoading(true);

      const validateResponse = await authenticatedFetch(`${API_URL}/questions/validate`, {
        method: 'POST',
        body: JSON.stringify({ answers })
      });

      const validateData = await validateResponse.json();

      if (validateData.success) {
        const { correct, total, percentage } = validateData.summary;

        let recommendedLevel = 'basic';
        let reason = '';

        const grade = parseInt(formData.grade);

        if (grade === 2 || grade === 3) {
          recommendedLevel = percentage === 100 ? 'easy' : 'basic';
          reason = percentage === 100 ? 'Perfect score! Easy level' : 'Starting with basics';
        } else if (grade === 4 || grade === 5) {
          if (percentage === 100) {
            recommendedLevel = 'medium';
            reason = 'Excellent! Medium level recommended';
          } else if (correct >= 2) {
            recommendedLevel = 'easy';
            reason = 'Good performance! Easy level';
          } else {
            recommendedLevel = 'basic';
            reason = 'Building foundation with basic level';
          }
        }

        const saveResponse = await authenticatedFetch(`${API_URL}/quiz/submit`, {
          method: 'POST',
          body: JSON.stringify({
            answers: validateData.results,
            recommendedLevel,
            quizScore: correct,
            quizTotal: total,
            quizPercentage: percentage
          })
        });

        const saveData = await saveResponse.json();
        console.log("Quiz save response:", saveData);

        const updatedUser = {
          ...userData,
          hasTakenQuiz: true,
          recommendedLevel: recommendedLevel,
          quizScore: correct,
          quizTotal: total,
          quizPercentage: percentage
        };

        localStorage.setItem('user', JSON.stringify(updatedUser));
        localStorage.setItem('gameUser', JSON.stringify(updatedUser));
        if (updatedUser._id) localStorage.setItem('gameUserId', updatedUser._id);
        setUserData(updatedUser);

        setQuizResult({
          score: correct,
          total: total,
          percentage: parseFloat(percentage),
          recommendation: {
            level: recommendedLevel,
            reason: reason
          },
          detailedResults: validateData.results
        });

        setStep('recommendation');
      }
    } catch (error) {
      console.error('Quiz submit error:', error);
      alert('Failed to submit quiz');
    } finally {
      setLoading(false);
    }
  };

  const goToGameSelection = () => {
    navigate('/gameselection');
  };

  const fetchAiHint = async ({ user_id, word, level, attempt_count = 3 } = {}) => {
    try {
      setAiLoading(true);
      setAiHint(null);
      const payload = {
        user_id: user_id || userData?._id || localStorage.getItem('gameUserId') || 'guest',
        word: word || hintWord || word,
        level: level || (userData?.recommendedLevel || 'basic'),
        attempt_count: attempt_count
      };

      const res = await fetch(AI_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        setAiHint(data.ai_hint || data.ai_hint_text || 'No hint returned');
      } else {
        setAiHint(data.error || 'AI hint failed');
      }
    } catch (err) {
      console.error('AI hint fetch error:', err);
      setAiHint('Failed to fetch AI hint');
    } finally {
      setAiLoading(false);
    }
  };

  const goDirectToGames = () => {
    navigate('/gameselection');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-xl text-gray-700">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gray-800 mx-auto mb-4"></div>
          <p className="text-xl text-gray-800">Checking your status...</p>
        </div>
      </div>
    );
  }

  if (step === 'goToGames') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
          <Gamepad2 className="w-20 h-20 text-green-600 mx-auto mb-4 animate-bounce" />
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Welcome back, {userData?.name}!</h2>
          <p className="text-xl text-gray-600 mb-6">Redirecting you to games...</p>

          <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 mb-6">
            <Award className="w-12 h-12 text-green-600 mx-auto mb-3" />
            <h3 className="text-xl font-bold text-gray-800 mb-2">Your Current Level</h3>
            <div className="text-3xl font-bold text-green-600 mb-2 capitalize">
              {userData?.recommendedLevel || 'basic'}
            </div>
            <p className="text-gray-600">Since you've already completed the quiz, you can jump straight into games!</p>
          </div>

          <button
            onClick={goDirectToGames}
            className="bg-gradient-to-r from-green-100 to-blue-200 text-gray-800 border border-green-300 px-8 py-4 rounded-xl font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition mb-4"
          >
            Go to Games Now 🎮
          </button>

          <button
            onClick={() => {
              localStorage.removeItem('user');
              localStorage.removeItem('gameUser');
              localStorage.removeItem('gameUserId');
              localStorage.removeItem('authToken');
              setStep('register');
            }}
            className="text-sm text-red-600 hover:text-red-800 underline"
          >
            Start Over (Clear My Progress)
          </button>

          <p className="text-sm text-gray-500 mt-4">
            You will be automatically redirected in a few seconds...
          </p>
        </div>
      </div>
    );
  }

  if (step === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 to-blue-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <User className="w-16 h-16 text-sky-600 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-gray-800">සිංහල සංඥා භාෂා</h1>
            <p className="text-gray-600 mt-2">Sinhala Sign Language Learning</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">නම / Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">පරිශීලක වර්ගය / User Type</label>
              <select
                value={formData.user_type}
                onChange={(e) => setFormData({ ...formData, user_type: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="student">Student / ශිෂ්‍යයා</option>
                <option value="parent">Parent / දෙමාපියා</option>
              </select>
            </div>

            {formData.user_type === 'student' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">ශ්‍රේණිය / Grade</label>
                <select
                  value={formData.grade}
                  onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="1">Grade 1</option>
                  <option value="2">Grade 2</option>
                  <option value="3">Grade 3</option>
                  <option value="4">Grade 4</option>
                  <option value="5">Grade 5</option>
                </select>
              </div>
            )}

            <button
              onClick={handleRegister}
              disabled={!formData.name || loading}
              className="w-full bg-gradient-to-r from-sky-100 to-blue-200 text-gray-800 border border-sky-300 py-3 rounded-lg font-semibold hover:shadow-lg transform hover:scale-105 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ආරම්භ කරන්න / Start
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'quizIntro') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-50 to-orange-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
          <Trophy className="w-20 h-20 text-yellow-500 mx-auto mb-4" />

          <h2 className="text-3xl font-bold text-gray-800 mb-4">Welcome, {formData.name}!</h2>
          <p className="text-gray-600 mb-6">Let's start with a short quiz to determine your appropriate learning level.</p>

          <div className="bg-blue-50 rounded-xl p-4 mb-6">
            <p className="font-medium text-blue-800">📝 You'll answer 3 questions</p>
            <p className="text-sm text-blue-600">Based on your score, we'll recommend the best starting level for you</p>
          </div>

          <button
            onClick={startQuiz}
            className="w-full bg-gradient-to-r from-green-100 to-blue-200 text-gray-800 border border-green-300 py-4 rounded-xl font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition"
          >
            Start Quiz 🚀
          </button>
        </div>
      </div>
    );
  }

  if (step === 'quiz') {
    if (!questions.length) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-xl">Loading quiz...</div>
        </div>
      );
    }

    const question = questions[currentQuestion];
    const videoKey = question.visualType === 'video' ? getVideoKey(question.videoUrl) : null;

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <span className="text-sm font-medium text-gray-600">
                Question {currentQuestion + 1} of {questions.length}
              </span>
              <div className="flex items-center gap-2">
                {question.visualType === 'image' && <Image className="w-5 h-5 text-blue-600" />}
                {question.visualType === 'video' && <Video className="w-5 h-5 text-sky-600" />}
                <div className="flex gap-2">
                  {questions.map((_, i) => (
                    <div
                      key={i}
                      className={`w-3 h-3 rounded-full ${i < currentQuestion ? 'bg-green-500' :
                          i === currentQuestion ? 'bg-blue-500' :
                            'bg-gray-300'
                        }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {question.visualType === 'image' && question.imageUrl && (
              <div className="mb-4 flex justify-center">
                <img
                  src={question.imageUrl}
                  alt={question.imageDescription}
                  className="max-w-full h-48 object-contain rounded-lg shadow-md"
                  onError={(e) => {
                    console.error('Image failed to load:', question.imageUrl);
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            )}

            {question.visualType === 'video' && videoKey && (
              <div className="mb-4">
                <div className="flex justify-center">
                  <video
                    key={videoKey}
                    src={`http://localhost:5001/api/videos/${videoKey}`}
                    controls
                    autoPlay
                    loop
                    className="max-w-full h-64 rounded-lg shadow-md bg-gray-100"
                    onError={(e) => {
                      console.error('Video failed to load. Key:', videoKey, 'Path:', question.videoUrl);
                    }}
                  >
                    Your browser does not support video playback.
                  </video>
                </div>
                <p className="text-center text-xs text-gray-500 mt-2">{question.signDescription}</p>
              </div>
            )}

            <h2 className="text-2xl font-bold text-gray-800 mb-2">{question.question}</h2>
            {question.imageDescription && (
              <p className="text-sm text-gray-500">{question.imageDescription}</p>
            )}
          </div>

          <div className="space-y-3">
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleQuizAnswer(option)}
                className="w-full text-left px-6 py-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition transform hover:scale-105"
              >
                <span className="font-medium text-lg">{option}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (step === 'recommendation' && quizResult) {
    const { score, total, percentage, recommendation } = quizResult;

    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-50 to-orange-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center">
          <Trophy className="w-20 h-20 text-yellow-500 mx-auto mb-4" />

          <h2 className="text-3xl font-bold text-gray-800 mb-4">Quiz Complete!</h2>

          <div className="bg-gradient-to-r from-sky-50 to-blue-50 rounded-xl p-6 mb-6">
            <div className="text-5xl font-bold text-blue-600 mb-2">{score}/{total}</div>
            <div className="text-xl text-gray-700">{percentage.toFixed(0)}% Correct</div>
          </div>

          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6 mb-6">
            <Award className="w-12 h-12 text-yellow-600 mx-auto mb-3" />
            <h3 className="text-xl font-bold text-gray-800 mb-2">Recommended Level</h3>
            <div className="text-3xl font-bold text-yellow-600 mb-2 capitalize">
              {recommendation.level}
            </div>
            <p className="text-gray-600">{recommendation.reason}</p>
          </div>

          <button
            onClick={goToGameSelection}
            className="bg-gradient-to-r from-green-100 to-blue-200 text-gray-800 border border-green-300 px-8 py-4 rounded-xl font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition"
          >
            Continue to Games 🎮
          </button>

          <div className="mt-6 bg-white border rounded-xl p-4 text-left">
            <h4 className="font-bold text-lg mb-2">Try an AI hint (demo)</h4>
            <div className="flex gap-2 mb-3">
              <input
                placeholder="Enter word (Sinhala)"
                value={hintWord}
                onChange={(e) => setHintWord(e.target.value)}
                className="flex-1 px-4 py-2 border rounded-md"
              />
              <button
                onClick={() => fetchAiHint({ word: hintWord })}
                disabled={aiLoading || !hintWord}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md disabled:opacity-50"
              >
                {aiLoading ? 'Loading…' : 'Get AI Hint'}
              </button>
            </div>

            {aiHint && (
              <div className="bg-gray-50 border rounded-md p-3">
                <strong>AI Hint:</strong>
                <p className="mt-2 whitespace-pre-wrap">{aiHint}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default GameUserForm;