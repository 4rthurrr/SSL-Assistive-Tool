import React, { useState, useEffect, useRef } from 'react';
import {
  Star, Trophy, RotateCcw, ArrowRight, Home, Lock,
  Target, Award, ChevronRight, CheckCircle, Languages,
  Volume2, VolumeX, Lightbulb, RefreshCw, Heart,
  AlertCircle, XCircle, TrendingUp, Medal
} from 'lucide-react';

const API_URL = 'http://localhost:5003/api';

const SignLanguageGame = () => {
  const [gameState, setGameState] = useState('map');
  const [currentLevel, setCurrentLevel] = useState('level_1');
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [selectedWords, setSelectedWords] = useState([]);
  const [shuffledWords, setShuffledWords] = useState([]);

  const [score, setScore] = useState(0);
  const [totalScore, setTotalScore] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [showLevelComplete, setShowLevelComplete] = useState(false);

  const autoAdvanceTimer = useRef(null);

  const [attempts, setAttempts] = useState(0);
  const [maxAttempts] = useState(5);
  const [gameOver, setGameOver] = useState(false);
  const [correctAnswer, setCorrectAnswer] = useState(null);

  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(8);
  const [completedLevels, setCompletedLevels] = useState(['level_1']);
  const [levelStars, setLevelStars] = useState({});
  const [hoveredLevel, setHoveredLevel] = useState(null);

  const [levels, setLevels] = useState({});
  const [loadingLevels, setLoadingLevels] = useState(true);

  const [userId] = useState(() => {
    let id = localStorage.getItem('gameUserId');
    if (!id) {
      id = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('gameUserId', id);
    }
    return id;
  });

  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [soundOn, setSoundOn] = useState(true);
  const [showHint, setShowHint] = useState(false);
  const [currentHint, setCurrentHint] = useState(null);
  const [error, setError] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [canAdvance, setCanAdvance] = useState(false);

  const translations = {
    en: {
      title: 'Sign Language Adventure',
      subtitle: 'Learn Sinhala Sign Language',
      yourProgress: 'Your Progress',
      levelsCompleted: 'Levels Completed',
      totalStars: 'Total Stars',
      progress: 'Progress',
      home: 'Home',
      questions: 'Questions',
      yourAnswer: 'Your Answer',
      selectWords: 'Select Words Below',
      words: 'Words',
      checkAnswer: 'Check Answer',
      nextQuestion: 'Next Question',
      finish: 'Finish Level',
      tryAgain: 'Try Again',
      levelMap: 'Level Map',
      excellent: 'Excellent!',
      keepTrying: 'Keep Trying!',
      correctAnswer: 'Correct Answer:',
      yourScore: 'Your Score',
      nextLevel: 'Next Level',
      levelComplete: 'Level Complete!',
      hint: 'Hint',
      loading: 'Loading...',
      error: 'Error loading game',
      refresh: 'Refresh',
      sound: 'Sound',
      attempts: 'Attempts',
      attemptsLeft: 'attempts left',
      gameOver: 'Game Over!',
      noMoreAttempts: 'No more attempts!',
      tryNextLevel: 'Try Next Level',
      score: 'Score',
      starsEarned: 'Stars Earned',
      leaderboard: 'Leaderboard',
      rank: 'Rank',
      player: 'Player',
      points: 'Points',
      close: 'Close',
      playAgain: 'Play Again'
    },
    si: {
      title: 'සංඥා භාෂා වික්‍රමය',
      subtitle: 'සිංහල සංඥා භාෂාව ඉගෙන ගන්න',
      yourProgress: 'ඔබේ ප්‍රගතිය',
      levelsCompleted: 'සම්පූර්ණ කළ මට්ටම්',
      totalStars: 'මුළු තරු',
      progress: 'ප්‍රගතිය',
      home: 'මුල් පිටුව',
      questions: 'ප්‍රශ්න',
      yourAnswer: 'ඔබේ පිළිතුර',
      selectWords: 'පහත වචන තෝරන්න',
      words: 'වචන',
      checkAnswer: 'පරීක්ෂා කරන්න',
      nextQuestion: 'ඊළඟ ප්‍රශ්නය',
      finish: 'මට්ටම අවසන් කරන්න',
      tryAgain: 'නැවත උත්සාහ කරන්න',
      levelMap: 'මට්ටම් සිතියම',
      excellent: 'සුපිරියි!',
      keepTrying: 'උත්සාහ කරන්න!',
      correctAnswer: 'නිවැරදි පිළිතුර:',
      yourScore: 'ඔබේ ලකුණු',
      nextLevel: 'ඊළඟ මට්ටම',
      levelComplete: 'මට්ටම සම්පූර්ණයි!',
      hint: 'ඉඟිය',
      loading: 'පූරණය වෙමින්...',
      error: 'ක්‍රීඩාව පූරණය කිරීමේ දෝෂයකි',
      refresh: 'නැවත උත්සාහ කරන්න',
      sound: 'ශබ්දය',
      attempts: 'උත්සාහ',
      attemptsLeft: 'උත්සාහ ඉතිරි',
      gameOver: 'ක්‍රීඩාව අවසන්!',
      noMoreAttempts: 'තවත් උත්සාහ නැත!',
      tryNextLevel: 'ඊළඟ මට්ටමට යන්න',
      score: 'ලකුණු',
      starsEarned: 'ලැබුණු තරු',
      leaderboard: 'ප්‍රමුඛයන්',
      rank: 'ස්ථානය',
      player: 'ක්‍රීඩකයා',
      points: 'ලකුණු',
      close: 'වසන්න',
      playAgain: 'නැවත ක්‍රීඩා කරන්න'
    }
  };

  const t = translations[language];

  const levelConfig = {
    level_1: {
      name: language === 'en' ? 'Beginner' : 'මූලික',
      color: 'from-emerald-400 to-green-500',
      icon: '🌱',
      difficulty: language === 'en' ? 'Easy' : 'පහසු',
      description: language === 'en' ? 'Simple actions with family (2 words)' : 'පවුලේ අය සමඟ සරල ක්‍රියා (වචන 2)'
    },
    level_2: {
      name: language === 'en' ? 'Intermediate' : 'මධ්‍යම',
      color: 'from-blue-400 to-indigo-500',
      icon: '📘',
      difficulty: language === 'en' ? 'Medium' : 'මධ්‍යම',
      description: language === 'en' ? 'Eating, going, and describing (2-3 words)' : 'කෑම, යෑම සහ විස්තර කිරීම (වචන 2-3)'
    },
    level_3: {
      name: language === 'en' ? 'Advanced' : 'සංකීර්ණ',
      color: 'from-purple-400 to-pink-500',
      icon: '🏆',
      difficulty: language === 'en' ? 'Hard' : 'දුෂ්කර',
      description: language === 'en' ? 'Past tense, questions, and helping others (3-4 words)' : 'අතීත කාලය, ප්‍රශ්න සහ උදව් කිරීම (වචන 3-4)'
    }
  };

  useEffect(() => {
    loadLevels();
    fetchLeaderboard();
    return () => { if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current); };
  }, []);

  const loadLevels = async () => {
    try {
      setLoadingLevels(true);
      const response = await fetch(`${API_URL}/levels`);
      const data = await response.json();
      if (data.success) setLevels(data.levels);
    } catch (error) {
      console.error('Error loading levels:', error);
      // Don't block the UI — just leave levels empty
    } finally {
      setLoadingLevels(false);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch(`${API_URL}/leaderboard`);
      const data = await response.json();
      if (data.success) setLeaderboard(data.leaderboard);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  // ── FIXED startLevel: if API fails or returns no question,
  //    fetch /current-question as a fallback before giving up ──────────
  const startLevel = async (level) => {
    try {
      setLoading(true);
      setError(null);

      if (autoAdvanceTimer.current) {
        clearTimeout(autoAdvanceTimer.current);
        autoAdvanceTimer.current = null;
      }

      const response = await fetch(`${API_URL}/start-level`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, level })
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.error || 'Failed to start level');
        return;
      }

      // Reset all game state
      setCurrentLevel(level);
      setTotalQuestions(data.total_questions || 8);
      setQuestionNumber(1);
      setScore(0);
      setAttempts(0);
      setGameOver(false);
      setShowLevelComplete(false);
      setSelectedWords([]);
      setShowResult(false);
      setIsCorrect(false);
      setShowHint(false);
      setCurrentHint(null);
      setCorrectAnswer(null);
      setCanAdvance(false);

      // ── KEY FIX: use first_question if provided, otherwise fetch it ──
      let question = data.first_question;

      if (!question) {
        // Fallback: fetch the current question explicitly
        const qResp = await fetch(`${API_URL}/current-question`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId })
        });
        const qData = await qResp.json();
        if (qData.success && qData.question) {
          question = qData.question;
          if (qData.total_questions) setTotalQuestions(qData.total_questions);
        }
      }

      if (!question) {
        setError('No questions available for this level. Please check your backend has sentences loaded.');
        return;
      }

      setCurrentQuestion(question);
      setShuffledWords(question.shuffled_words || []);

      // ── Navigate to playing screen ONLY after question is confirmed ──
      setGameState('playing');

    } catch (error) {
      console.error('Error starting level:', error);
      setError('Failed to connect to game server. Make sure the backend is running on port 5003.');
    } finally {
      setLoading(false);
    }
  };

  const loadNextQuestion = async () => {
    if (autoAdvanceTimer.current) {
      clearTimeout(autoAdvanceTimer.current);
      autoAdvanceTimer.current = null;
    }
    setCanAdvance(false);

    try {
      const response = await fetch(`${API_URL}/current-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });

      const data = await response.json();

      if (data.success) {
        if (data.level_complete) {
          const stars = data.stars_earned || 0;
          setLevelStars(prev => ({ ...prev, [currentLevel]: stars }));
          setShowLevelComplete(true);
          if (!completedLevels.includes(currentLevel)) {
            setCompletedLevels(prev => [...prev, currentLevel]);
          }
        } else if (data.game_over) {
          setGameOver(true);
        } else if (data.question) {
          setCurrentQuestion(data.question);
          setShuffledWords(data.question.shuffled_words || []);
          setQuestionNumber(data.question_number || questionNumber + 1);
          setAttempts(0);
          setGameOver(false);
          setSelectedWords([]);
          setShowResult(false);
          setIsCorrect(false);
          setShowHint(false);
          setCurrentHint(null);
          setCorrectAnswer(null);
          setCanAdvance(false);
        }
      }
    } catch (error) {
      console.error('Error loading next question:', error);
    }
  };

  const handleWordClick = (word, idx) => {
    if (!showResult && !gameOver && !showLevelComplete && !loading) {
      setSelectedWords(prev => [...prev, word]);
      setShuffledWords(prev => {
        const next = [...prev];
        next.splice(idx, 1);
        return next;
      });
      vibrate('tap');
    }
  };

  const handleSelectedWordClick = (word, index) => {
    if (!showResult && !gameOver && !showLevelComplete && !loading) {
      setSelectedWords(prev => prev.filter((_, i) => i !== index));
      setShuffledWords(prev => [...prev, word]);
      vibrate('tap');
    }
  };

  const checkAnswer = async () => {
    if (!currentQuestion || selectedWords.length !== currentQuestion.word_count) return;

    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, user_order: selectedWords })
      });

      const data = await response.json();

      if (data.success) {
        setIsCorrect(data.correct);
        setShowResult(true);

        if (data.correct) {
          vibrate('success');
          setScore(data.score);
          setTotalScore(prev => prev + 10);

          setCanAdvance(false);
          autoAdvanceTimer.current = setTimeout(() => {
            autoAdvanceTimer.current = null;
            setCanAdvance(true);
          }, 1500);

        } else {
          setAttempts(data.attempts);
          vibrate('error');

          if (data.game_over) {
            setGameOver(true);
            setCorrectAnswer(data.correct_answer);
          } else {
            setTimeout(() => {
              setSelectedWords([]);
              setShowResult(false);
              if (currentQuestion) {
                setShuffledWords([...(currentQuestion.shuffled_words || [])]);
              }
            }, 1500);
          }
        }
      }
    } catch (error) {
      console.error('Error checking answer:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHint = async () => {
    if (showResult || gameOver || showLevelComplete || loading) return;
    try {
      const response = await fetch(`${API_URL}/hint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await response.json();
      if (data.success) {
        setCurrentHint(data.hint);
        setShowHint(true);
        vibrate('hint');
        setTimeout(() => setShowHint(false), 5000);
      }
    } catch (error) {
      console.error('Error getting hint:', error);
    }
  };

  const resetLevel = () => {
    startLevel(currentLevel);
  };

  const goToMap = () => {
    if (autoAdvanceTimer.current) {
      clearTimeout(autoAdvanceTimer.current);
      autoAdvanceTimer.current = null;
    }
    setGameState('map');
    setShowLevelComplete(false);
    setCurrentQuestion(null);
    setGameOver(false);
    setShowLeaderboard(false);
    setError(null);
    setCanAdvance(false);
  };

  const nextLevel = () => {
    const levelOrder = ['level_1', 'level_2', 'level_3'];
    const currentIndex = levelOrder.indexOf(currentLevel);
    if (currentIndex < levelOrder.length - 1) {
      startLevel(levelOrder[currentIndex + 1]);
    } else {
      setShowLevelComplete(false);
      setGameState('map');
    }
  };

  const toggleLanguage = () => setLanguage(l => l === 'en' ? 'si' : 'en');

  const vibrate = (type = 'default') => {
    if (!soundOn || !navigator.vibrate) return;
    switch (type) {
      case 'success': navigator.vibrate([50, 50, 50]); break;
      case 'error': navigator.vibrate([100, 50, 100]); break;
      case 'hint': navigator.vibrate(30); break;
      case 'tap': navigator.vibrate(10); break;
      default: navigator.vibrate(20);
    }
  };

  const LanguageToggle = () => (
    <button
      onClick={toggleLanguage}
      className="fixed top-6 right-6 z-50 bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-4 rounded-full font-black text-lg hover:scale-110 transition-transform shadow-2xl border-4 border-white flex items-center gap-3"
    >
      <Languages className="w-7 h-7" />
      <span>{language === 'en' ? 'සිංහල' : 'English'}</span>
    </button>
  );

  const SoundToggle = () => (
    <button
      onClick={() => setSoundOn(s => !s)}
      className="fixed top-6 left-6 z-50 bg-gradient-to-r from-gray-500 to-gray-600 text-white px-6 py-4 rounded-full font-black text-lg hover:scale-110 transition-transform shadow-2xl border-4 border-white flex items-center gap-3"
    >
      {soundOn ? <Volume2 className="w-7 h-7" /> : <VolumeX className="w-7 h-7" />}
    </button>
  );

  const LeaderboardModal = () => {
    if (!showLeaderboard) return null;
    return (
      <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[100] p-4">
        <div className="bg-white rounded-[40px] p-8 max-w-md w-full border-8 border-yellow-400 shadow-2xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-black text-gray-800 flex items-center gap-3">
              <Medal className="w-8 h-8 text-yellow-500" />{t.leaderboard}
            </h2>
            <button onClick={() => setShowLeaderboard(false)}>
              <XCircle className="w-8 h-8 text-gray-500" />
            </button>
          </div>
          <div className="space-y-3 mb-6">
            {leaderboard.map(player => (
              <div key={player.rank} className={`flex items-center gap-4 p-4 rounded-2xl ${player.rank === 1 ? 'bg-yellow-100 border-2 border-yellow-400' :
                  player.rank === 2 ? 'bg-gray-100 border-2 border-gray-400' :
                    player.rank === 3 ? 'bg-orange-100 border-2 border-orange-400' : 'bg-gray-50'
                }`}>
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white flex items-center justify-center font-black text-xl">
                  {player.rank}
                </div>
                <div className="flex-1">
                  <p className="font-bold text-gray-800">{player.name}</p>
                  <p className="text-sm text-gray-600">{player.score} {t.points}</p>
                </div>
                <div className="flex gap-1">
                  {[...Array(Math.min(player.stars || 0, 3))].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setShowLeaderboard(false)}
            className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-6 py-4 rounded-2xl font-bold text-lg hover:scale-105 transition-transform"
          >
            {t.close}
          </button>
        </div>
      </div>
    );
  };

  // ── Loading Screen ──────────────────────────────────────────────────
  if (loadingLevels) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <LanguageToggle /><SoundToggle />
        <div className="text-center">
          <div className="text-7xl animate-bounce mb-6">🤟</div>
          <h2 className="text-3xl font-black text-gray-800 mb-4">{t.loading}</h2>
          <div className="w-48 h-3 bg-gray-200 rounded-full overflow-hidden mx-auto">
            <div className="h-full bg-gradient-to-r from-emerald-500 to-green-600 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
        </div>
      </div>
    );
  }

  // ── Loading spinner while starting a level ─────────────────────────
  if (loading && gameState === 'map') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <LanguageToggle /><SoundToggle />
        <div className="text-center">
          <div className="text-7xl animate-spin mb-6">⏳</div>
          <h2 className="text-3xl font-black text-gray-800 mb-4">{t.loading}</h2>
        </div>
      </div>
    );
  }

  // ── Error Screen ────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center">
        <LanguageToggle /><SoundToggle />
        <div className="bg-white rounded-[40px] shadow-2xl p-12 max-w-md w-full text-center border-8 border-red-400">
          <div className="text-7xl mb-6">😢</div>
          <h2 className="text-3xl font-black text-gray-800 mb-4">{t.error}</h2>
          <p className="text-gray-600 mb-8">{error}</p>
          <div className="space-y-3">
            <button
              onClick={() => { setError(null); setGameState('map'); }}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-8 py-4 rounded-2xl font-black text-xl hover:scale-105 transition-transform flex items-center justify-center gap-3"
            >
              <Home className="w-6 h-6" /><span>{t.levelMap}</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-4 rounded-2xl font-black text-xl hover:scale-105 transition-transform flex items-center justify-center gap-3"
            >
              <RefreshCw className="w-6 h-6" /><span>{t.refresh}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Level Complete Screen ───────────────────────────────────────────
  if (showLevelComplete) {
    const stars = levelStars[currentLevel] || 0;
    const levelInfo = levelConfig[currentLevel];
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 p-4 flex items-center justify-center">
        <LanguageToggle /><SoundToggle /><LeaderboardModal />
        <div className="bg-white rounded-[40px] shadow-2xl p-12 max-w-md w-full text-center border-8 border-yellow-400">
          <div className="relative inline-block mb-6">
            <Trophy className="w-32 h-32 text-yellow-500 animate-bounce" />
            <div className="absolute -top-4 -right-4 w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center text-3xl animate-pulse">🎉</div>
          </div>
          <h2 className="text-5xl font-black text-emerald-600 mb-3">{t.excellent}</h2>
          <p className="text-2xl font-bold text-gray-700 mb-6">{t.levelComplete}</p>
          <p className="text-xl text-gray-600 mb-6">{levelInfo?.description}</p>
          <div className="flex justify-center gap-3 mb-8 bg-yellow-50 p-6 rounded-3xl">
            {[1, 2, 3].map(star => (
              <Star key={star} className={`w-16 h-16 ${star <= stars ? 'fill-yellow-400 text-yellow-500 animate-pulse' : 'text-gray-300'}`} />
            ))}
          </div>
          <div className="bg-emerald-50 rounded-3xl p-6 mb-8 border-4 border-emerald-200">
            <p className="text-gray-600 mb-2">{t.yourScore}</p>
            <p className="text-5xl font-black text-emerald-600">{score} / {totalQuestions * 10}</p>
            <p className="text-sm text-gray-500 mt-2">{t.starsEarned}: {stars}/3</p>
          </div>
          <div className="space-y-3">
            <button onClick={() => setShowLeaderboard(true)} className="w-full bg-gradient-to-r from-yellow-500 to-orange-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-yellow-600">
              <TrendingUp className="w-7 h-7" /><span>{t.leaderboard}</span>
            </button>
            {currentLevel !== 'level_3' ? (
              <button onClick={nextLevel} className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-emerald-600">
                <span>{t.nextLevel}</span><ArrowRight className="w-7 h-7" />
              </button>
            ) : (
              <button onClick={goToMap} className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-purple-600">
                <Home className="w-7 h-7" /><span>{t.levelMap}</span>
              </button>
            )}
            <button onClick={() => startLevel(currentLevel)} className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-blue-600">
              <RotateCcw className="w-7 h-7" /><span>{t.playAgain}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Level Map Screen ────────────────────────────────────────────────
  if (gameState === 'map') {
    const levelOrder = ['level_1', 'level_2', 'level_3'];
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
        <LanguageToggle /><SoundToggle /><LeaderboardModal />
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-block relative mb-6">
              <div className="text-8xl animate-bounce mb-4">🤟</div>
              <div className="absolute -top-2 -right-2 w-12 h-12 bg-yellow-400 rounded-full animate-ping" />
            </div>
            <h1 className="text-6xl font-black text-gray-800 mb-4">{t.title}</h1>
            <div className="inline-block bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-3 rounded-full text-xl font-bold shadow-lg">
              {t.subtitle}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-2xl p-4 text-center shadow-lg border-2 border-indigo-200">
              <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
              <div className="text-2xl font-black text-gray-800">{totalScore}</div>
              <div className="text-xs text-gray-600">{t.points}</div>
            </div>
            <div className="bg-white rounded-2xl p-4 text-center shadow-lg border-2 border-indigo-200">
              <Star className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
              <div className="text-2xl font-black text-gray-800">{Object.values(levelStars).reduce((a, b) => a + b, 0)}</div>
              <div className="text-xs text-gray-600">{t.totalStars}</div>
            </div>
            <div className="bg-white rounded-2xl p-4 text-center shadow-lg border-2 border-indigo-200">
              <Target className="w-8 h-8 text-green-500 mx-auto mb-2" />
              <div className="text-2xl font-black text-gray-800">{Math.round((completedLevels.length / 3) * 100)}%</div>
              <div className="text-xs text-gray-600">{t.progress}</div>
            </div>
          </div>

          {/* Levels Grid */}
          <div className="grid grid-cols-3 gap-8">
            {levelOrder.map(levelKey => {
              const isLocked = levelKey !== 'level_1' && !completedLevels.includes('level_' + (parseInt(levelKey.split('_')[1]) - 1));
              const stars = levelStars[levelKey] || 0;
              const config = levelConfig[levelKey];
              const levelInfo = levels[levelKey];
              return (
                <div key={levelKey}
                  className={`relative transform transition-all duration-300 ${hoveredLevel === levelKey ? 'scale-110 z-20' : 'scale-100'}`}
                  onMouseEnter={() => setHoveredLevel(levelKey)}
                  onMouseLeave={() => setHoveredLevel(null)}
                >
                  <button
                    onClick={() => !isLocked && startLevel(levelKey)}
                    disabled={isLocked || loading}
                    className={`relative w-full ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <div className={`bg-gradient-to-br ${config.color} rounded-[35px] p-8 shadow-xl border-8 border-white ${isLocked ? 'opacity-60 grayscale' : 'hover:shadow-2xl'}`}>
                      <div className="absolute -top-4 -right-4 w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center text-2xl font-black text-gray-800 border-4 border-white shadow-lg">
                        {levelOrder.indexOf(levelKey) + 1}
                      </div>
                      <div className="text-7xl mb-4 text-center">{isLocked ? '🔒' : config.icon}</div>
                      <h3 className="text-2xl font-black text-white text-center mb-2 drop-shadow-lg">{config.name}</h3>
                      <p className="text-white text-center font-bold mb-2 opacity-90">
                        {levelInfo?.question_count || 8} {t.questions}
                      </p>
                      {stars > 0 && (
                        <div className="flex justify-center gap-1 mb-3">
                          {[1, 2, 3].map(star => (
                            <Star key={star} className={`w-6 h-6 ${star <= stars ? 'fill-yellow-300 text-yellow-400' : 'text-white/30'}`} />
                          ))}
                        </div>
                      )}
                      <div className="bg-white/30 backdrop-blur-sm rounded-full px-4 py-2 text-center">
                        <span className="text-white font-bold">{config.difficulty}</span>
                      </div>
                    </div>
                  </button>
                </div>
              );
            })}
          </div>

          <div className="mt-8 text-center">
            <button onClick={() => setShowLeaderboard(true)} className="bg-gradient-to-r from-yellow-500 to-orange-600 text-white px-8 py-4 rounded-full font-bold text-xl hover:scale-105 transition-transform shadow-lg inline-flex items-center gap-3">
              <Medal className="w-6 h-6" /><span>{t.leaderboard}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Game Playing Screen ─────────────────────────────────────────────
  // If somehow we reach 'playing' with no question, show a spinner
  // (this should not happen with the fixed startLevel above)
  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <LanguageToggle /><SoundToggle />
        <div className="text-center">
          <div className="text-7xl animate-spin mb-6">⏳</div>
          <p className="text-xl font-bold text-gray-600 mb-6">{t.loading}</p>
          <button
            onClick={goToMap}
            className="bg-gradient-to-r from-purple-500 to-pink-600 text-white px-8 py-4 rounded-2xl font-black text-xl hover:scale-105 transition-transform flex items-center gap-3 mx-auto"
          >
            <Home className="w-6 h-6" /><span>{t.levelMap}</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <LanguageToggle /><SoundToggle /><LeaderboardModal />

      {/* Game Over Overlay */}
      {gameOver && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-[40px] shadow-2xl p-12 max-w-md w-full text-center border-8 border-red-400">
            <AlertCircle className="w-32 h-32 text-red-500 animate-pulse mx-auto mb-6" />
            <h2 className="text-5xl font-black text-red-600 mb-3">{t.gameOver}</h2>
            <p className="text-2xl font-bold text-gray-700 mb-6">{t.noMoreAttempts}</p>
            {correctAnswer && (
              <div className="bg-red-50 rounded-3xl p-6 mb-8 border-4 border-red-200">
                <p className="text-gray-600 mb-2">{t.correctAnswer}</p>
                <p className="text-3xl font-black text-red-600">{correctAnswer.join(' ')}</p>
              </div>
            )}
            <div className="space-y-3">
              <button onClick={resetLevel} className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-emerald-600">
                <RotateCcw className="w-7 h-7" /><span>{t.tryAgain}</span>
              </button>
              <button onClick={goToMap} className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-purple-600">
                <Home className="w-7 h-7" /><span>{t.levelMap}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="bg-white rounded-[30px] shadow-xl p-6 mb-6 border-8 border-indigo-100">
          <div className="flex justify-between items-center mb-4">
            <button onClick={goToMap} className="bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-3 rounded-full font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center gap-2">
              <Home className="w-6 h-6" /><span className="hidden sm:inline">{t.home}</span>
            </button>
            <div className="text-center flex-1">
              <h1 className="text-3xl font-black text-gray-800">{levelConfig[currentLevel]?.name}</h1>
              <p className="text-lg text-gray-600 font-bold flex items-center justify-center gap-2">
                <Heart className="w-5 h-5 text-red-500" />
                <span>{maxAttempts - attempts} {t.attemptsLeft}</span>
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-2 rounded-full font-bold text-lg flex items-center gap-2">
                <Star className="w-5 h-5 fill-white" /><span>{score}</span>
              </div>
              <div className="bg-gradient-to-r from-emerald-500 to-green-600 text-white px-6 py-3 rounded-full font-black text-xl shadow-lg">
                {questionNumber}/{totalQuestions}
              </div>
            </div>
          </div>
          {/* Progress Bar */}
          <div className="flex gap-2">
            {Array.from({ length: totalQuestions }).map((_, i) => (
              <div key={i} className={`flex-1 h-4 rounded-full transition-all ${i < questionNumber - 1 ? 'bg-emerald-500' :
                  i === questionNumber - 1 ? 'bg-yellow-400 animate-pulse' : 'bg-gray-200'
                }`} />
            ))}
          </div>
        </div>

        {/* Attempts Warning */}
        {attempts >= 3 && (
          <div className={`mb-4 p-3 rounded-2xl text-center font-bold border-2 ${attempts >= 4 ? 'bg-red-100 text-red-800 border-red-300 animate-pulse' : 'bg-orange-100 text-orange-800 border-orange-300'
            }`}>
            ⚠️ {attempts}/{maxAttempts} {t.attempts} — {maxAttempts - attempts} {t.attemptsLeft}
          </div>
        )}

        {/* Hint Panel */}
        {showHint && currentHint && (
          <div className="bg-gradient-to-r from-amber-100 to-orange-100 rounded-[30px] p-6 mb-6 border-4 border-amber-300 shadow-xl">
            <div className="flex items-center gap-3 mb-3">
              <Lightbulb className="w-8 h-8 text-amber-600" />
              <h3 className="text-2xl font-black text-amber-800">{t.hint}</h3>
            </div>
            <p className="text-xl text-amber-900 font-bold">{currentHint.hint}</p>
          </div>
        )}

        {/* Video / Sentence Area */}
        <div className="bg-gradient-to-br from-indigo-100 to-purple-100 rounded-[25px] p-10 border-4 border-indigo-200 min-h-[200px] flex items-center justify-center mb-6">
          <div className="text-center w-full" key={`video-container-${currentQuestion.id}`}>
            {currentQuestion.video_url ? (
              <video
                key={currentQuestion.id}
                src={`http://localhost:5003${currentQuestion.video_url}`}
                autoPlay loop muted playsInline
                className="max-h-[200px] rounded-xl mx-auto"
                onError={e => {
                  console.error('❌ Video load error:', e.target.src);
                  console.error('Error code:', e.target.error?.code, e.target.error?.message);
                  e.target.style.display = 'none';
                  const parent = e.target.parentNode;
                  
                  // Remove any existing fallback divs
                  const existingFallbacks = parent.querySelectorAll('.video-fallback');
                  existingFallbacks.forEach(f => f.remove());
                  
                  const fallback = document.createElement('div');
                  fallback.className = 'text-center video-fallback';
                  fallback.innerHTML = `
                    <div class="text-7xl mb-4">👋</div>
                    <p class="text-4xl font-black text-gray-800 mb-3">${currentQuestion.sinhala || currentQuestion.sentence_sinhala || ''}</p>
                    <p class="text-2xl text-gray-600 font-bold">${currentQuestion.english || currentQuestion.sentence_english || ''}</p>
                  `;
                  parent.appendChild(fallback);
                }}
                onLoadedData={(e) => {
                  console.log('✅ Video loaded:', currentQuestion.video_url);
                  // Remove any fallback divs if video loaded successfully
                  const parent = e.target.parentNode;
                  const fallbacks = parent.querySelectorAll('.video-fallback');
                  fallbacks.forEach(f => f.remove());
                }}
              />
            ) : (
              <div className="text-center">
                <div className="text-7xl mb-4 animate-bounce">👋</div>
                <p className="text-4xl font-black text-gray-800 mb-3">
                  {currentQuestion.sinhala || currentQuestion.sentence_sinhala}
                </p>
                <p className="text-2xl text-gray-600 font-bold">
                  {currentQuestion.english || currentQuestion.sentence_english}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Answer Zone */}
        <div className="bg-white rounded-[30px] shadow-xl p-8 mb-6 border-8 border-indigo-100">
          <h3 className="text-2xl font-black text-gray-800 mb-4 flex items-center gap-3">
            <span className="text-3xl">✏️</span>
            <span>{t.yourAnswer}</span>
            <span className="text-sm text-gray-500 ml-auto">{selectedWords.length}/{currentQuestion.word_count}</span>
          </h3>
          <div className="min-h-[120px] bg-gradient-to-r from-yellow-50 to-orange-50 rounded-[25px] p-6 border-4 border-dashed border-yellow-400 flex flex-wrap gap-3 items-center justify-center">
            {selectedWords.length === 0 ? (
              <p className="text-gray-400 text-2xl font-bold">👇 {t.selectWords} 👇</p>
            ) : (
              selectedWords.map((word, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectedWordClick(word, index)}
                  className="bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-4 rounded-[20px] text-2xl font-black shadow-lg hover:scale-110 transition-transform border-4 border-emerald-600"
                  disabled={showResult || loading}
                >
                  {word}<span className="ml-2 text-sm opacity-75">({index + 1})</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Word Bank */}
        <div className="bg-white rounded-[30px] shadow-xl p-8 mb-6 border-8 border-indigo-100">
          <h3 className="text-2xl font-black text-gray-800 mb-4 flex items-center gap-3">
            <span className="text-3xl">📝</span>
            <span>{t.words}</span>
            <span className="text-sm text-gray-500 ml-auto">{shuffledWords.length} {t.words}</span>
          </h3>
          <div className="flex flex-wrap gap-4 justify-center">
            {shuffledWords.map((word, index) => (
              <button
                key={index}
                onClick={() => handleWordClick(word, index)}
                className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-4 rounded-[20px] text-2xl font-black shadow-lg hover:scale-110 transition-transform border-4 border-blue-600"
                disabled={showResult || loading}
              >
                {word}
              </button>
            ))}
          </div>
        </div>

        {/* Result Messages */}
        {showResult && isCorrect && (
          <div className="bg-gradient-to-r from-emerald-400 to-green-500 border-8 border-emerald-600 rounded-[30px] shadow-xl p-8 mb-6 text-center">
            <div className="text-8xl mb-4 animate-bounce">🎉</div>
            <h3 className="text-5xl font-black text-white mb-4">{t.excellent}</h3>
          </div>
        )}

        {showResult && !isCorrect && !gameOver && (
          <div className="bg-gradient-to-r from-red-400 to-pink-500 border-8 border-red-600 rounded-[30px] shadow-xl p-8 mb-6 text-center">
            <div className="text-8xl mb-4 animate-bounce">💪</div>
            <h3 className="text-5xl font-black text-white mb-4">{t.keepTrying}</h3>
            <p className="text-white text-xl font-bold">{attempts}/{maxAttempts} {t.attempts}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          {(!showResult || (showResult && !isCorrect)) ? (
            <button
              onClick={checkAnswer}
              disabled={selectedWords.length !== currentQuestion.word_count || loading || showResult}
              className="flex-1 bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-6 rounded-[25px] font-black text-2xl hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:cursor-not-allowed border-8 border-emerald-700 flex items-center justify-center gap-3"
            >
              <CheckCircle className="w-8 h-8" /><span>{t.checkAnswer}</span>
            </button>
          ) : (
            <button
              onClick={loadNextQuestion}
              disabled={!canAdvance || loading}
              className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-6 rounded-[25px] font-black text-2xl hover:scale-105 transition-transform shadow-lg border-8 border-blue-700 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>{questionNumber < totalQuestions ? t.nextQuestion : t.finish}</span>
              <ArrowRight className="w-8 h-8" />
            </button>
          )}

          <button
            onClick={getHint}
            disabled={showResult || loading}
            className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-8 py-6 rounded-[25px] font-black text-2xl hover:scale-105 transition-transform shadow-lg border-8 border-amber-700 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Lightbulb className="w-8 h-8" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignLanguageGame;