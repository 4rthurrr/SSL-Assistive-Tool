import React, { useState, useEffect, useRef } from 'react';
import {
  Star, Trophy, RotateCcw, ArrowRight, Home, Lock,
  Target, Award, ChevronRight, CheckCircle, Languages,
  Volume2, VolumeX, Lightbulb, RefreshCw, Heart,
  AlertCircle, XCircle, TrendingUp, Medal
} from 'lucide-react';

// useState: Manages changing data (score, level, questions)
{/*api configuration*/}
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
  const wordVideoRef = useRef(null);

  // RESEARCH CONTRIBUTION
  // Word-by-word sign video controller that synchronizes Dataset - Original clips with grammar questions
  // ── Word-video sequential player state ────────────────────
  const [activeWordVideoIdx, setActiveWordVideoIdx] = useState(0);
  const [wordVideoPlaying, setWordVideoPlaying] = useState(false);
  const [wordVideoSpeed, setWordVideoSpeed] = useState(1.0);
  const [wordVideoError, setWordVideoError] = useState(false);

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
    let id = localStorage.getItem('gameUserId');  {/*local srorage- minidb*/}
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

  // ── Reset word-video player when question changes ──────────────────
  useEffect(() => {
    if (!currentQuestion) return;
    setActiveWordVideoIdx(0);
    setWordVideoSpeed(1.0);   {/*videospeed*/}
    setWordVideoError(false);
    setWordVideoPlaying(false);
  }, [currentQuestion?.id]);

  // Sync speed to video element
  useEffect(() => {
    if (wordVideoRef.current) wordVideoRef.current.playbackRate = wordVideoSpeed;
  }, [wordVideoSpeed]);

  // Auto-play when activeWordVideoIdx changes
  useEffect(() => {
    if (!wordVideoRef.current) return;
    wordVideoRef.current.load();
    wordVideoRef.current.playbackRate = wordVideoSpeed;
    wordVideoRef.current.play().then(() => setWordVideoPlaying(true)).catch(() => setWordVideoPlaying(false));
    setWordVideoError(false);
  }, [activeWordVideoIdx, currentQuestion?.id]);

  const wordVideos = currentQuestion?.word_videos || [];
  const validWordVideos = wordVideos.filter(Boolean);

  const currentWordVideoUrl = wordVideos[activeWordVideoIdx] || null;

  const toggleWordVideo = () => {
    if (!wordVideoRef.current) return;
    if (wordVideoRef.current.paused) {
      wordVideoRef.current.play(); setWordVideoPlaying(true);
    } else {
      wordVideoRef.current.pause(); setWordVideoPlaying(false);
    }
  };

  const replayAllWords = () => {
    setActiveWordVideoIdx(0);
  };

  const advanceWordVideo = () => {
    const words = currentQuestion?.correct_order || [];
    setActiveWordVideoIdx(prev => (prev + 1) % Math.max(words.length, 1));
  };

  const onWordVideoEnded = () => {
    const words = currentQuestion?.correct_order || [];
    if (words.length === 0) return;
    const next = (activeWordVideoIdx + 1) % words.length;
    setActiveWordVideoIdx(next);
  };

  // RESEARCH CONTRIBUTION
  // Bilingual (EN/SI) copy tuned for sign-language pedagogy and research user studies
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

  // MANUAL IMPLEMENTATION
  // Pedagogical metadata describing difficulty, theming, and story for each level
  const levelConfig = {
    level_1: {
      name: language === 'en' ? 'Beginner' : 'මූලික',
      color: 'from-green-400 to-emerald-500',
      icon: '🌱',
      difficulty: language === 'en' ? 'Easy' : 'පහසු',
      description: language === 'en' ? 'Simple actions with family (2 words)' : 'පවුලේ අය සමඟ සරල ක්‍රියා (වචන 2)'
    },
    level_2: {
      name: language === 'en' ? 'Intermediate' : 'මධ්‍යම',
      color: 'from-sky-400 to-blue-500',
      icon: '🪷',
      difficulty: language === 'en' ? 'Medium' : 'මධ්‍යම',
      description: language === 'en' ? 'Eating, going, and describing (2-3 words)' : 'කෑම, යෑම සහ විස්තර කිරීම (වචන 2-3)'
    },
    level_3: {
      name: language === 'en' ? 'Advanced' : 'සංකීර්ණ',
      color: 'from-yellow-400 to-amber-500',
      icon: '🏆',
      difficulty: language === 'en' ? 'Hard' : 'දුෂ්කර',
      description: language === 'en' ? 'Past tense, questions, and helping others (3-4 words)' : 'අතීත කාලය, ප්‍රශ්න සහ උදව් කිරීම (වචන 3-4)'
    }
  };

  useEffect(() => {
    loadLevels();
    fetchLeaderboard();
    return () => { 
      if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current); 
    };
  }, []);

  const loadLevels = async () => {
    try {
      setLoadingLevels(true);
      const response = await fetch(`${API_URL}/levels`);
      const data = await response.json();
      if (data.success) setLevels(data.levels);
    } catch (error) {
      console.error('Error loading levels:', error);
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

  // RESEARCH CONTRIBUTION
  // Resilient level-start flow with /current-question fallback to handle backend edge cases
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

      let question = data.first_question;

      if (!question) {
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

      //errorquestion
      if (!question) {
        setError('No questions available for this level. Please check your backend has sentences loaded.');
        return;
      }

      setCurrentQuestion(question);
      setShuffledWords(question.shuffled_words || []);
      setGameState('playing');

    } catch (error) {
      console.error('Error starting level:', error);
      setError('Failed to connect to game server. Make sure the backend is running on port 5003.');
    } finally {
      setLoading(false);
    }
  };

  // MANUAL IMPLEMENTATION
  // Advance game state while preserving score, stars, and completion flags from backend responses
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

  const checkLevelCompletion = async () => {
    try {
      const response = await fetch(`${API_URL}/current-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });

      const data = await response.json();

      if (data.success && data.level_complete) {
        const stars = data.stars_earned || 0;
        setLevelStars(prev => ({ ...prev, [currentLevel]: stars }));
        setShowLevelComplete(true);
        if (!completedLevels.includes(currentLevel)) {
          setCompletedLevels(prev => [...prev, currentLevel]);
        }
      }
    } catch (error) {
      console.error('Error checking level completion:', error);
    }
  };

  // RESEARCH CONTRIBUTION
  // Tap-based word selection UX that models drag-and-drop ordering for touchscreen learners
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

  // RESEARCH CONTRIBUTION
  // Tight integration with Flask game API: submits ordering, animates feedback, and controls auto-advance
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

          // AUTO ADVANCE TO NEXT QUESTION AFTER 1.5 SECONDS
          setTimeout(() => {
            if (questionNumber < totalQuestions) {
              loadNextQuestion();
            } else {
              // Check if level is complete
              checkLevelCompletion();
            }
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

  // RESEARCH CONTRIBUTION
  // Frontend hook into progressive hint system, including temporal UX (auto-hide) and haptics
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

  // CUSTOM OPTIMIZATION
  // Lightweight haptic feedback abstraction to reinforce success, errors, and hints without audio
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
      className="fixed bottom-6 sm:bottom-8 right-4 sm:right-6 z-50 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-3 sm:px-4 py-2 sm:py-3 rounded-full font-black text-xs sm:text-sm hover:scale-110 transition-transform shadow-2xl border-2 sm:border-3 border-white flex items-center gap-1 sm:gap-2"
    >
      <Languages className="w-4 sm:w-5 h-4 sm:h-5" />
      <span className="hidden sm:inline text-xs">{language === 'en' ? 'සි' : 'EN'}</span>
    </button>
  );

  const SoundToggle = () => (
    <button
      onClick={() => setSoundOn(s => !s)}
      className="fixed bottom-6 sm:bottom-8 left-4 sm:left-6 z-50 bg-gradient-to-r from-amber-400 to-amber-500 text-white px-3 sm:px-4 py-2 sm:py-3 rounded-full font-black text-xs sm:text-sm hover:scale-110 transition-transform shadow-2xl border-2 sm:border-3 border-white flex items-center gap-1 sm:gap-2"
    >
      {soundOn ? <Volume2 className="w-4 sm:w-5 h-4 sm:h-5" /> : <VolumeX className="w-4 sm:w-5 h-4 sm:h-5" />}
      <span className="hidden sm:inline text-xs">{soundOn ? 'On' : 'Off'}</span>
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
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-sky-500 to-blue-600 text-white flex items-center justify-center font-black text-xl">
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
            className="w-full bg-gradient-to-r from-orange-500 to-red-600 text-white px-6 py-4 rounded-2xl font-bold text-lg hover:scale-105 transition-transform"
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
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 flex items-center justify-center">
        <LanguageToggle /><SoundToggle />
        <div className="text-center">
          <div className="text-7xl animate-bounce mb-6">🌱</div>
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
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 flex items-center justify-center">
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
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 flex items-center justify-center">
        <LanguageToggle /><SoundToggle />
        <div className="bg-white rounded-[40px] shadow-2xl p-12 max-w-md w-full text-center border-8 border-red-400">
          <div className="text-7xl mb-6">😢</div>
          <h2 className="text-3xl font-black text-gray-800 mb-4">{t.error}</h2>
          <p className="text-gray-600 mb-8">{error}</p>
          <div className="space-y-2 sm:space-y-3">
            <button
              onClick={() => { setError(null); setGameState('map'); }}
              className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-xl font-black text-base sm:text-lg hover:scale-105 transition-transform flex items-center justify-center gap-2 border-3 border-blue-700 whitespace-nowrap"
            >
              <Home className="w-5 h-5 flex-shrink-0" /><span>{t.levelMap}</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white px-6 py-3 rounded-xl font-black text-base sm:text-lg hover:scale-105 transition-transform flex items-center justify-center gap-2 border-3 border-emerald-700 whitespace-nowrap"
            >
              <RefreshCw className="w-5 h-5 flex-shrink-0" /><span>{t.refresh}</span>
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
          <div className="space-y-2 sm:space-y-3">
            <button onClick={() => setShowLeaderboard(true)} className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 sm:gap-3 border-3 sm:border-4 border-blue-700 whitespace-nowrap">
              <TrendingUp className="w-5 sm:w-6 h-5 sm:h-6 flex-shrink-0" /><span>{t.leaderboard}</span>
            </button>
            {currentLevel !== 'level_3' ? (
              <button onClick={nextLevel} className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 sm:gap-3 border-3 sm:border-4 border-emerald-700 whitespace-nowrap">
                <span>{t.nextLevel}</span><ArrowRight className="w-5 sm:w-6 h-5 sm:h-6 flex-shrink-0" />
              </button>
            ) : (
              <button onClick={goToMap} className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 sm:gap-3 border-3 sm:border-4 border-blue-700 whitespace-nowrap">
                <Home className="w-5 sm:w-6 h-5 sm:h-6 flex-shrink-0" /><span>{t.levelMap}</span>
              </button>
            )}
            <button onClick={() => startLevel(currentLevel)} className="w-full bg-gradient-to-r from-amber-400 to-amber-500 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 sm:gap-3 border-3 sm:border-4 border-amber-600 whitespace-nowrap">
              <RotateCcw className="w-5 sm:w-6 h-5 sm:h-6 flex-shrink-0" /><span>{t.playAgain}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Level Map Screen ────────────────────────────────────────────────
  // RESEARCH CONTRIBUTION
  // Level map dashboard summarizing stars, total points, and visual difficulty progression
  if (gameState === 'map') {
    const levelOrder = ['level_1', 'level_2', 'level_3'];
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 p-6">
        <LanguageToggle /><SoundToggle /><LeaderboardModal />
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-6xl font-black text-gray-800 mb-4">{t.title}</h1>
            <div className="inline-block bg-gradient-to-r from-orange-600 to-red-700 text-white px-8 py-3 rounded-full text-xl font-bold shadow-lg">
              {t.subtitle}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-6 sm:mb-8">
            <div className="bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4 text-center shadow-lg border-2 border-blue-200">
              <Trophy className="w-6 sm:w-8 h-6 sm:h-8 text-yellow-500 mx-auto mb-1 sm:mb-2" />
              <div className="text-xl sm:text-2xl font-black text-gray-800">{totalScore}</div>
              <div className="text-xs text-gray-600">{t.points}</div>
            </div>
            <div className="bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4 text-center shadow-lg border-2 border-blue-200">
              <Star className="w-6 sm:w-8 h-6 sm:h-8 text-yellow-500 mx-auto mb-1 sm:mb-2" />
              <div className="text-xl sm:text-2xl font-black text-gray-800">{Object.values(levelStars).reduce((a, b) => a + b, 0)}</div>
              <div className="text-xs text-gray-600">{t.totalStars}</div>
            </div>
            <div className="bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4 text-center shadow-lg border-2 border-blue-200">
              <Target className="w-6 sm:w-8 h-6 sm:h-8 text-green-500 mx-auto mb-1 sm:mb-2" />
              <div className="text-xl sm:text-2xl font-black text-gray-800">{Math.round((completedLevels.length / 3) * 100)}%</div>
              <div className="text-xs text-gray-600">{t.progress}</div>
            </div>
          </div>

          {/* Levels Grid - Responsive layout */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
            {levelOrder.map(levelKey => {
              const isLocked = levelKey !== 'level_1' && !completedLevels.includes('level_' + (parseInt(levelKey.split('_')[1]) - 1));
              const stars = levelStars[levelKey] || 0;
              const config = levelConfig[levelKey];
              const levelInfo = levels[levelKey];
              return (
                <div key={levelKey}
                  className={`relative transform transition-all duration-300 ${hoveredLevel === levelKey ? 'scale-105 sm:scale-110 z-20' : 'scale-100'}`}
                  onMouseEnter={() => setHoveredLevel(levelKey)}
                  onMouseLeave={() => setHoveredLevel(null)}
                >
                  <button
                    onClick={() => !isLocked && startLevel(levelKey)}
                    disabled={isLocked || loading}
                    className={`relative w-full ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <div className={`bg-gradient-to-br ${config.color} rounded-2xl sm:rounded-[35px] p-4 sm:p-6 lg:p-8 shadow-lg sm:shadow-xl border-4 sm:border-8 border-white ${isLocked ? 'opacity-60 grayscale' : 'hover:shadow-2xl'}`}>
                      <div className="absolute -top-3 sm:-top-4 -right-3 sm:-right-4 w-12 sm:w-16 h-12 sm:h-16 bg-blue-400 rounded-full flex items-center justify-center text-xl sm:text-2xl font-black text-white border-3 sm:border-4 border-white shadow-lg">
                        {levelOrder.indexOf(levelKey) + 1}
                      </div>
                      <div className="text-5xl sm:text-6xl lg:text-7xl mb-2 sm:mb-4 text-center">{isLocked ? '🔒' : config.icon}</div>
                      <h3 className="text-lg sm:text-2xl font-black text-white text-center mb-1 sm:mb-2 drop-shadow-lg">{config.name}</h3>
                      <p className="text-white text-center text-sm sm:text-base font-bold mb-2 opacity-90">
                        {levelInfo?.question_count || 8} {t.questions}
                      </p>
                      {stars > 0 && (
                        <div className="flex justify-center gap-1 mb-2 sm:mb-3">
                          {[1, 2, 3].map(star => (
                            <Star key={star} className={`w-4 sm:w-6 h-4 sm:h-6 ${star <= stars ? 'fill-yellow-300 text-yellow-400' : 'text-white/30'}`} />
                          ))}
                        </div>
                      )}
                      <div className="bg-white/30 backdrop-blur-sm rounded-full px-3 sm:px-4 py-1 sm:py-2 text-center">
                        <span className="text-white font-bold text-sm sm:text-base">{config.difficulty}</span>
                      </div>
                    </div>
                  </button>
                </div>
              );
            })}
          </div>

          <div className="text-center">
            <button onClick={() => setShowLeaderboard(true)} className="bg-gradient-to-r from-sky-500 to-blue-600 text-white px-4 sm:px-6 py-2 sm:py-3 rounded-full font-bold text-sm sm:text-base hover:scale-105 transition-transform shadow-lg inline-flex items-center gap-2 sm:gap-3 border-2 sm:border-4 border-blue-700 whitespace-nowrap">
              <Medal className="w-4 sm:w-5 h-4 sm:h-5 flex-shrink-0" /><span>{t.leaderboard}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Game Playing Screen ─────────────────────────────────────────────
  // If somehow we reach 'playing' with no question, show a spinner
  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50 flex items-center justify-center p-4">
        <LanguageToggle /><SoundToggle />
        <div className="text-center">
          <div className="text-6xl sm:text-7xl animate-spin mb-6">⏳</div>
          <p className="text-lg sm:text-xl font-bold text-gray-600 mb-6">{t.loading}</p>
          <button
            onClick={goToMap}
            className="bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-2xl font-black text-lg sm:text-xl hover:scale-105 transition-transform flex items-center gap-2 sm:gap-3 mx-auto"
          >
            <Home className="w-5 sm:w-6 h-5 sm:h-6" /><span>{t.levelMap}</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50 p-2 sm:p-4">
      <LanguageToggle /><SoundToggle /><LeaderboardModal />

      {/* Game Over Overlay */}
      {gameOver && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl sm:rounded-[40px] shadow-2xl p-8 sm:p-12 max-w-md w-full text-center border-6 sm:border-8 border-red-400">
            <AlertCircle className="w-24 sm:w-32 h-24 sm:h-32 text-red-500 animate-pulse mx-auto mb-4 sm:mb-6" />
            <h2 className="text-3xl sm:text-5xl font-black text-red-600 mb-2 sm:mb-3">{t.gameOver}</h2>
            <p className="text-lg sm:text-2xl font-bold text-gray-700 mb-4 sm:mb-6">{t.noMoreAttempts}</p>
            {correctAnswer && (
              <div className="bg-red-50 rounded-2xl sm:rounded-3xl p-4 sm:p-6 mb-6 sm:mb-8 border-4 border-red-200">
                <p className="text-gray-600 mb-2 text-sm">{t.correctAnswer}</p>
                <p className="text-2xl sm:text-3xl font-black text-red-600">{correctAnswer.join(' ')}</p>
              </div>
            )}
            <div className="space-y-3">
              <button onClick={resetLevel} className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 sm:px-8 py-4 sm:py-5 rounded-2xl sm:rounded-3xl font-black text-lg sm:text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 sm:gap-3 border-4 border-blue-600">
                <RotateCcw className="w-6 sm:w-7 h-6 sm:h-7" /><span>{t.tryAgain}</span>
              </button>
              <button onClick={goToMap} className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 sm:px-8 py-4 sm:py-5 rounded-2xl sm:rounded-3xl font-black text-lg sm:text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 sm:gap-3 border-4 border-blue-600">
                <Home className="w-6 sm:w-7 h-6 sm:h-7" /><span>{t.levelMap}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto">

        {/* sentenceHome */}
        <div className="bg-white rounded-[30px] shadow-xl p-4 sm:p-6 mb-6 border-8 border-blue-200">
          <div className="flex justify-between items-center mb-4">
            <button onClick={goToMap} className="bg-gradient-to-r from-sky-500 to-blue-600 text-white px-6 py-3 rounded-full font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center gap-2">
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
              <div className="bg-gradient-to-r from-sky-500 to-blue-600 text-white px-4 py-2 rounded-full font-bold text-lg flex items-center gap-2">
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
                  i === questionNumber - 1 ? 'bg-blue-400 animate-pulse' : 'bg-gray-200'
                }`} />
            ))}
          </div>
        </div>

        {/* Attempts Warning */}
        {attempts >= 3 && (
          <div className={`mb-4 p-2 sm:p-3 rounded-2xl text-center font-bold text-sm sm:text-base border-2 ${attempts >= 4 ? 'bg-red-100 text-red-800 border-red-300 animate-pulse' : 'bg-yellow-100 text-yellow-800 border-yellow-300'
            }`}>
            ⚠️ {attempts}/{maxAttempts} {t.attempts} — {maxAttempts - attempts} {t.attemptsLeft}
          </div>
        )}

        {/* Hint Panel */}
        {showHint && currentHint && (
          <div className="bg-gradient-to-r from-yellow-100 to-yellow-50 rounded-[30px] p-4 sm:p-6 mb-6 border-4 border-yellow-300 shadow-xl">
            <div className="flex items-center gap-3 mb-3">
              <Lightbulb className="w-6 sm:w-8 h-6 sm:h-8 text-yellow-600" />
              <h3 className="text-xl sm:text-2xl font-black text-yellow-800">{t.hint}</h3>
            </div>
            <p className="text-lg sm:text-xl text-yellow-900 font-bold">{currentHint.hint}</p>
          </div>
        )}

        {/* ── Word-by-word sign video player (Dataset - Original) ── */}
        <div className="bg-white rounded-[30px] shadow-xl border-8 border-blue-300 mb-6 overflow-hidden">

          {/* Title bar */}
          <div className="bg-gradient-to-r from-sky-500 to-blue-600 px-4 sm:px-6 py-2 sm:py-3 flex items-center gap-3">
            <span className="text-xl sm:text-2xl">🤟</span>
            <span className="text-white font-black text-sm sm:text-lg">SSL Sign Animation</span>
            <span className="ml-auto text-white/70 text-xs sm:text-sm font-bold">
              {language === 'en' ? 'Watch the sign, then arrange the words' : 'සංඥාව බලා, වචන සකසන්න'}
            </span>
          </div>

          <div className="p-3 sm:p-5">
            {/* Video frame */}
            <div className="relative bg-gradient-to-br from-sky-50 to-blue-50 rounded-[20px] border-4 border-sky-200 overflow-hidden mb-4">
              {currentWordVideoUrl && !wordVideoError ? (
                <>
                  <video
                    ref={wordVideoRef}
                    src={`http://localhost:5003${currentWordVideoUrl}`}
                    playsInline
                    onClick={toggleWordVideo}
                    onEnded={onWordVideoEnded}
                    onError={() => setWordVideoError(true)}
                    className="w-full max-h-[180px] sm:max-h-[240px] object-contain block cursor-pointer"
                  />
                  {!wordVideoPlaying && (
                    <button
                      onClick={toggleWordVideo}
                      className="absolute inset-0 flex items-center justify-center bg-black/20"
                    >
                      <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center shadow-2xl">
                        <span className="text-3xl ml-1">▶️</span>
                      </div>
                    </button>
                  )}
                </>
              ) : (
                <div className="min-h-[140px] sm:min-h-[180px] flex flex-col items-center justify-center py-4 sm:py-6">
                  <div className="text-6xl sm:text-7xl mb-3 animate-bounce">👋</div>
                  <p className="text-lg sm:text-2xl font-black text-gray-700 mb-1">
                    {currentQuestion.correct_order?.[activeWordVideoIdx]}
                  </p>
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 mb-4 sm:mb-5">
              <button
                onClick={() => setWordVideoSpeed(0.5)}
                className={`px-3 sm:px-4 py-2 rounded-full font-bold text-xs sm:text-sm transition-all border-2 ${
                  wordVideoSpeed === 0.5
                    ? 'bg-blue-600 text-white border-blue-700 shadow-md'
                    : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                }`}
              >🐢 Slow</button>
{/*stopbutton*/}
              <button
                onClick={toggleWordVideo}
                className="w-11 h-11 sm:w-12 sm:h-12 rounded-full bg-gradient-to-r from-sky-500 to-blue-600 text-white text-lg sm:text-xl shadow-lg hover:scale-110 transition-transform flex items-center justify-center border-4 border-white"
              >{wordVideoPlaying ? '⏸' : '▶️'}</button>

              <button
                onClick={replayAllWords}
                title="Replay from first word"
                className="w-10 h-10 rounded-full bg-gradient-to-r from-yellow-400 to-yellow-500 text-white text-base shadow-lg hover:scale-110 transition-transform flex items-center justify-center border-2 border-white"
              >🔄</button>

              <button
                onClick={advanceWordVideo}
                title="Next word"
                className="w-10 h-10 rounded-full bg-gradient-to-r from-emerald-400 to-green-500 text-white text-base shadow-lg hover:scale-110 transition-transform flex items-center justify-center border-2 border-white"
              >⏭</button>

              <button
                onClick={() => setWordVideoSpeed(1.0)}
                className={`px-3 sm:px-4 py-2 rounded-full font-bold text-xs sm:text-sm transition-all border-2 ${
                  wordVideoSpeed === 1.0
                    ? 'bg-blue-600 text-white border-blue-700 shadow-md'
                    : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                }`}
              >🐰 Normal</button>
            </div>

          </div>
        </div>

        {/* RESEARCH CONTRIBUTION
            Answer Zone: structured word ordering workspace that mirrors SSL sentence structure */}
        {/* Answer Zone */}
        <div className="bg-white rounded-[30px] shadow-xl p-4 sm:p-8 mb-6 border-8 border-blue-200">
          <h3 className="text-lg sm:text-2xl font-black text-gray-800 mb-4 flex items-center gap-3">
            <span className="text-2xl sm:text-3xl">✏️</span>
            <span>{t.yourAnswer}</span>
            <span className="text-xs sm:text-sm text-gray-500 ml-auto">{selectedWords.length}/{currentQuestion.word_count}</span>
          </h3>
          <div className="min-h-[100px] sm:min-h-[120px] bg-gradient-to-r from-blue-50 to-sky-50 rounded-[25px] p-4 sm:p-6 border-4 border-dashed border-blue-300 flex flex-wrap gap-2 sm:gap-3 items-center justify-center">
            {selectedWords.length === 0 ? (
              <p className="text-gray-400 text-lg sm:text-2xl font-bold">👇 {t.selectWords} 👇</p>
            ) : (
              selectedWords.map((word, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectedWordClick(word, index)}
                  className="bg-gradient-to-r from-emerald-500 to-green-600 text-white px-4 sm:px-8 py-3 sm:py-4 rounded-[20px] text-lg sm:text-2xl font-black shadow-lg hover:scale-110 transition-transform border-4 border-emerald-600"
                  disabled={showResult || loading}
                >  {/*wordnumber*/}
                  {word}<span className="ml-2 text-xs sm:text-sm opacity-75">({index + 1})</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* RESEARCH CONTRIBUTION
            Word Bank: adaptive pool of shuffled tokens including distractors for higher cognitive load */}
        {/* Word Bank */}
        <div className="bg-white rounded-[30px] shadow-xl p-4 sm:p-8 mb-6 border-8 border-blue-200">
          <h3 className="text-lg sm:text-2xl font-black text-gray-800 mb-4 flex items-center gap-3">
            <span className="text-2xl sm:text-3xl">📝</span>
            <span>{t.words}</span>
            <span className="text-xs sm:text-sm text-gray-500 ml-auto">{shuffledWords.length} {t.words}</span>
          </h3>
          <div className="flex flex-wrap gap-2 sm:gap-4 justify-center">
            {shuffledWords.map((word, index) => (
              <button
                key={index}
                onClick={() => handleWordClick(word, index)}
                className="bg-gradient-to-r from-sky-500 to-blue-600 text-white px-4 sm:px-8 py-3 sm:py-4 rounded-[20px] text-lg sm:text-2xl font-black shadow-lg hover:scale-110 transition-transform border-4 border-blue-600"
                disabled={showResult || loading}
              >
                {word}
              </button>
            ))}
          </div>
        </div>

        {/* Result Messages */}
        {showResult && isCorrect && (
          <div className="bg-gradient-to-r from-emerald-400 to-green-500 border-8 border-emerald-600 rounded-[30px] shadow-xl p-6 sm:p-8 mb-6 text-center">
            <div className="text-6xl sm:text-8xl mb-4 animate-bounce">🎉</div>
            <h3 className="text-3xl sm:text-5xl font-black text-white mb-4">{t.excellent}</h3>
          </div>
        )}

        {showResult && !isCorrect && !gameOver && (
          <div className="bg-gradient-to-r from-red-400 to-orange-500 border-8 border-red-600 rounded-[30px] shadow-xl p-6 sm:p-8 mb-6 text-center">
            <div className="text-6xl sm:text-8xl mb-4 animate-bounce">💪</div>
            <h3 className="text-3xl sm:text-5xl font-black text-white mb-4">{t.keepTrying}</h3>
            <p className="text-white text-lg sm:text-xl font-bold">{attempts}/{maxAttempts} {t.attempts}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full">
          {(!showResult || (showResult && !isCorrect)) ? (
            <button
              onClick={checkAnswer}
              disabled={selectedWords.length !== currentQuestion.word_count || loading || showResult}
              className="flex-1 bg-gradient-to-r from-emerald-500 to-green-600 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-xl sm:rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:cursor-not-allowed border-4 sm:border-6 border-emerald-700 flex items-center justify-center gap-2 sm:gap-3 whitespace-nowrap"
            >
              <CheckCircle className="w-5 sm:w-6 h-5 sm:h-6 flex-shrink-0" /><span>{t.checkAnswer}</span>
            </button>
          ) : (
            // Only show next button for incorrect answers
            !isCorrect && (
              <button
                onClick={loadNextQuestion}
                disabled={loading}
                className="flex-1 bg-gradient-to-r from-sky-500 to-blue-600 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-xl sm:rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg border-4 sm:border-6 border-blue-700 flex items-center justify-center gap-2 sm:gap-3 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                <span>{questionNumber < totalQuestions ? t.nextQuestion : t.finish}</span>
                <ArrowRight className="w-5 sm:w-6 h-5 sm:h-6 flex-shrink-0" />
              </button>
            )
          )}

          <button
            onClick={getHint}
            disabled={showResult || loading}
            className="bg-gradient-to-r from-amber-400 to-amber-500 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-xl sm:rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-lg border-4 sm:border-6 border-amber-600 flex items-center justify-center gap-2 sm:gap-3 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            <Lightbulb className="w-5 sm:w-6 h-5 sm:h-6" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignLanguageGame;