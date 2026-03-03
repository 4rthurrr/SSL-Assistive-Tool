import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Play, Trophy, Heart, Lightbulb, RefreshCw, Home, 
  Sparkles, Target, Award, ChevronRight, TrendingUp,
  Volume2, VolumeX, Eye, HelpCircle, Star, Music,
  Check, X, SkipForward, Globe, Languages
} from 'lucide-react';

const API_URL = 'http://localhost:5001/api';

const SinhalaWordPuzzleGame = () => {
  const navigate = useNavigate();
  
  // Game State
  const [gameState, setGameState] = useState('menu');
  const [level, setLevel] = useState('basic');
  const [score, setScore] = useState(0);
  const [lives, setLives] = useState(3);
  const [hintsRemaining, setHintsRemaining] = useState(3);
  const [round, setRound] = useState(0);
  const [totalRounds] = useState(10);
  const [soundOn, setSoundOn] = useState(true);
  const [vibrationOn, setVibrationOn] = useState(true);
  const [language, setLanguage] = useState('english');
  
  // Puzzle State
  const [puzzle, setPuzzle] = useState(null);
  const [grid, setGrid] = useState([]);
  const [selectedCells, setSelectedCells] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [showVideo, setShowVideo] = useState(true);
  const [aiHints, setAiHints] = useState([]);
  const [showHintPanel, setShowHintPanel] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [showWordAfterFail, setShowWordAfterFail] = useState(false);
  
  // Attempt tracking
  const [attempts, setAttempts] = useState(0);
  const [wrongAttempts, setWrongAttempts] = useState(0);
  const [gameOverDueToAttempts, setGameOverDueToAttempts] = useState(false);

  // User tracking
  const getStoredUserId = () => {
    try {
      const stored = localStorage.getItem('gameUser') || localStorage.getItem('user');
      if (stored) {
        const obj = JSON.parse(stored);
        return obj._id || obj.mongoId || obj.userId || obj.id || `user_${Date.now()}`;
      }
    } catch (e) {
      console.error('Error reading stored user id:', e);
    }
    return `user_${Date.now()}`;
  };

  const [userId] = useState(getStoredUserId());
  const [attemptStartTime, setAttemptStartTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [celebration, setCelebration] = useState(false);
  const [shake, setShake] = useState(false);

  // Language dictionary
  const gameText = {
    sinhala: {
      title: 'සංඥා විදු ප්‍රහේලිකා',
      subtitle: 'සෑම කෙනෙකුටම සංඥා භාෂාව ඉගෙන ගත හැකිය',
      instructionTitle: '🎮 ක්‍රීඩා උපදෙස්',
      instructionStart: 'අරඹන්න! Start!',
      videoInstructions: [
        { icon: '🎥', title: 'වීඩියෝව නරඹන්න', desc: 'අත්සන් දක්වන ආකාරය ඉගෙන ගන්න' },
        { icon: '🔍', title: 'වචනය සොයන්න', desc: 'අකුරු පෙළෙහි වචනය සොයා ගන්න' },
        { icon: '👆', title: 'අකුරු තෝරන්න', desc: 'සමීප කොටුවල අකුරු තෝරන්න' },
        { icon: '✅', title: 'පිළිතුර පරීක්ෂා කරන්න', desc: 'ඔබේ පිළිතුර පරීක්ෂා කර ලකුණු ලබා ගන්න' }
      ],
      moreGames: 'වැඩිදුර ක්‍රීඩා',
      myProfile: 'මගේ විස්තර',
      achievements: 'සම්භාවනා',
      signVideo: 'සංඥා වීඩියෝව',
      secretWord: 'ගුප්ත වචනය',
      wordHas: 'මෙම වචනයේ අකුරු',
      selectConnected: 'සම්බන්ධ අකුරු තෝරන්න',
      attempts: 'උත්සාහ',
      wrongAttempts: 'වැරදි උත්සාහ',
      wordWas: 'වචනය වූයේ',
      hint: 'උපදෙස්',
      hintText: 'උපදෙස්',
      clear: 'මකන්න',
      checkAnswer: 'පිළිතුර පරීක්ෂා කරන්න',
      nextWord: 'ඊළඟ වචනයට',
      findSecretWord: 'ගුප්ත වචනය සොයන්න',
      instructions: '🎯 උපදෙස්: වීඩියෝව නරඹා, පෙළෙහි සඟවා ඇති වචනය සොයන්න. අසල්වැසි කොටුවල අකුරු තෝරන්න (තිරස්, සිරස් හෝ විකර්ණ).',
      secretWordText: 'ගුප්ත වචනය',
      selectedLetters: 'තෝරාගත් අකුරු',
      note: '💡 සටහන: අකුරු අනුපිළිවෙලට තෝරන්න (1, 2, 3...)',
      aiHint: 'AI සහායක උපදෙස්',
      mainMenu: 'මුල් පිටුව',
      level: 'මට්ටම',
      points: 'ලකුණු',
      lives: 'ජීවිත',
      round: 'රවුම',
      preparing: 'ප්‍රහේලිකා සූදානම් වෙමින්...',
      finding: '✨ Finding the perfect sign language word for you...',
      gameOver: 'ක්‍රීඩාව අවසන්!',
      gameComplete: 'Game Complete!',
      restartGame: 'නැවත ක්‍රීඩා කරන්න',
      otherGames: 'වෙනත් ක්‍රීඩා',
      tooManyAttempts: 'උත්සාහ 5 ඉක්මවිය! වචනය වූයේ:',
      gameOverMessages: {
        3: { text: 'පුදුමයි! නියම කාර්යයක්!', subtitle: 'You are a Sign Language Master!' },
        2: { text: 'හොඳටම ක්‍රීඩා කළා!', subtitle: 'Excellent performance!' },
        1: { text: 'හරිම හොඳයි!', subtitle: 'Great effort!' },
        0: { text: 'අඛණ්ඩව උත්සාහ කරන්න!', subtitle: 'Keep practicing!' }
      }
    },
    english: {
      title: 'Sinhala Sign Language Puzzle',
      subtitle: 'Everyone can learn sign language',
      instructionTitle: '🎮 Game Instructions',
      instructionStart: 'Start Game!',
      videoInstructions: [
        { icon: '🎥', title: 'Watch the Video', desc: 'Learn how the sign is performed' },
        { icon: '🔍', title: 'Find the Word', desc: 'Find the hidden word in the letter grid' },
        { icon: '👆', title: 'Select Letters', desc: 'Select adjacent letters in the grid' },
        { icon: '✅', title: 'Check Answer', desc: 'Check your answer and earn points' }
      ],
      moreGames: 'More Games',
      myProfile: 'My Profile',
      achievements: 'Achievements',
      signVideo: 'Sign Language Video',
      secretWord: 'Secret Word',
      wordHas: 'This word has',
      selectConnected: 'connected letters',
      attempts: 'Attempts',
      wrongAttempts: 'Wrong Attempts',
      wordWas: 'The word was',
      hint: 'Hint',
      hintText: 'Hints',
      clear: 'Clear',
      checkAnswer: 'Check Answer',
      nextWord: 'Next Word',
      findSecretWord: 'Find the Secret Word',
      instructions: '🎯 Instructions: Watch the video, then find the hidden word in the grid. Select adjacent letters (horizontal, vertical, or diagonal).',
      secretWordText: 'Secret Word',
      selectedLetters: 'Selected Letters',
      note: '💡 Note: Select letters in order (1, 2, 3...)',
      aiHint: 'AI Assistant Hints',
      mainMenu: 'Main Menu',
      level: 'Level',
      points: 'Points',
      lives: 'Lives',
      round: 'Round',
      preparing: 'Preparing Your Puzzle Adventure!',
      finding: '✨ Finding the perfect sign language word for you...',
      gameOver: 'Game Complete!',
      gameComplete: 'Game Complete!',
      restartGame: 'Play Again',
      otherGames: 'Other Games',
      tooManyAttempts: 'Too many attempts (5)! The word was:',
      gameOverMessages: {
        3: { text: 'Amazing! Perfect Score!', subtitle: 'You are a Sign Language Master!' },
        2: { text: 'Great Job!', subtitle: 'Excellent performance!' },
        1: { text: 'Well Done!', subtitle: 'Great effort!' },
        0: { text: 'Keep Practicing!', subtitle: 'Try again to improve!' }
      }
    }
  };

  const t = gameText[language];

  // Level configurations
  const levelConfig = {
    basic: {
      name: language === 'sinhala' ? 'මූලික' : 'BASIC',
      nameS: 'මූලික',
      description: 'පිල්ලම් නැති සරල වචන',
      descriptionE: 'Simple words without vowel signs',
      gridSize: 6,
      bgGradient: 'from-emerald-100 to-green-200',
      textColor: 'text-emerald-800',
      borderColor: 'border-emerald-300',
      icon: '🌱',
      difficulty: 1,
      color: 'bg-gradient-to-r from-emerald-100 to-green-200'
    },
    easy: {
      name: language === 'sinhala' ? 'පහසු' : 'EASY',
      nameS: 'පහසු',
      description: 'සරල වචන (2-3 අකුරු)',
      descriptionE: 'Simple words (2-3 letters)',
      gridSize: 7,
      bgGradient: 'from-sky-100 to-blue-200',
      textColor: 'text-blue-800',
      borderColor: 'border-sky-300',
      icon: '🔍',
      difficulty: 2,
      color: 'bg-gradient-to-r from-sky-100 to-blue-200'
    },
    medium: {
      name: language === 'sinhala' ? 'මධ්‍යම' : 'MEDIUM',
      nameS: 'මධ්‍යම',
      description: 'මධ්‍යම වචන (4-6 අකුරු)',
      descriptionE: 'Medium words (4-6 letters)',
      gridSize: 8,
      bgGradient: 'from-indigo-100 to-blue-200',
      textColor: 'text-indigo-800',
      borderColor: 'border-indigo-300',
      icon: '🏃',
      difficulty: 3,
      color: 'bg-gradient-to-r from-indigo-100 to-blue-200'
    },
    hard: {
      name: language === 'sinhala' ? 'දුෂ්කර' : 'HARD',
      nameS: 'දුෂ්කර',
      description: 'දුෂ්කර වචන (7+ අකුරු)',
      descriptionE: 'Hard words (7+ letters)',
      gridSize: 10,
      bgGradient: 'from-rose-100 to-pink-200',
      textColor: 'text-rose-800',
      borderColor: 'border-pink-300',
      icon: '🏆',
      difficulty: 4,
      color: 'bg-gradient-to-r from-rose-100 to-pink-200'
    }
  };

  // Animation functions
  const triggerCelebration = () => {
    setCelebration(true);
    setTimeout(() => setCelebration(false), 2000);
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const vibrate = () => {
    if (vibrationOn && navigator.vibrate) {
      navigator.vibrate(50);
    }
  };

  // Toggle language
  const toggleLanguage = () => {
    setLanguage(prev => prev === 'sinhala' ? 'english' : 'sinhala');
    vibrate();
  };

  // Game functions
  const startGame = (selectedLevel) => {
    vibrate();
    console.log(`Starting ${selectedLevel} level game`);
    setLevel(selectedLevel);
    setGameState('playing');
    setScore(0);
    setLives(3);
    setHintsRemaining(3);
    setRound(0);
    setPuzzle(null);
    setFeedback(null);
    setAiHints([]);
    setShowHintPanel(false);
    setShowInstructions(false);
    
    // Reset attempt tracking
    setAttempts(0);
    setWrongAttempts(0);
    setShowWordAfterFail(false);
    setGameOverDueToAttempts(false);
  };

  const getRandomLetter = () => {
    const letters = ['අ','ආ','ඉ','ඊ','උ','ඌ','එ','ඒ','ඔ','ක','ග','ච','ජ','ට','ඩ','ත','ද','න','ප','බ','ම','ය','ර','ල','ව','ශ','ස','හ'];
    return letters[Math.floor(Math.random() * letters.length)];
  };

  const createGrid = (size, syllables) => {
    const newGrid = Array(size).fill(null).map(() => 
      Array(size).fill(null).map(() => ({
        letter: getRandomLetter(),
        isTarget: false
      }))
    );

    const startRow = Math.floor(Math.random() * size);
    const startCol = Math.floor(Math.random() * (size - syllables.length + 1));
    
    syllables.forEach((syllable, i) => {
      newGrid[startRow][startCol + i] = {
        letter: syllable,
        isTarget: true
      };
    });

    return newGrid;
  };

  const loadPuzzle = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/puzzle/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level, user_id: userId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const syllables = data.target_word.match(/[\u0D80-\u0DFF][\u0DCA-\u0DDF]*/g) || [data.target_word];
        
        setPuzzle({
          word: data.target_word,
          english: data.target_english,
          video_url: data.video_url,
          syllables: syllables
        });
        
        setGrid(createGrid(levelConfig[level].gridSize, syllables));
        setSelectedCells([]);
        setFeedback(null);
        setShowHintPanel(false);
        setAttemptStartTime(Date.now());
        
        // Reset attempt tracking for new word
        setAttempts(0);
        setWrongAttempts(0);
        setShowWordAfterFail(false);
        setGameOverDueToAttempts(false);
        setAiHints([]);
      }
    } catch (error) {
      console.error('Error loading puzzle:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (gameState === 'playing' && puzzle === null) {
      loadPuzzle();
    }
  }, [gameState, round, puzzle]);

  const areAdjacent = (cell1, cell2) => {
    const [r1, c1] = cell1.split('-').map(Number);
    const [r2, c2] = cell2.split('-').map(Number);
    const rowDiff = Math.abs(r1 - r2);
    const colDiff = Math.abs(c1 - c2);
    return rowDiff <= 1 && colDiff <= 1 && !(rowDiff === 0 && colDiff === 0);
  };

  const isValidPath = () => {
    if (selectedCells.length < 2) return true;
    
    for (let i = 1; i < selectedCells.length; i++) {
      if (!areAdjacent(selectedCells[i - 1], selectedCells[i])) {
        return false;
      }
    }
    return true;
  };

  const toggleCell = (row, col) => {
    vibrate();
    const cellKey = `${row}-${col}`;
    
    if (selectedCells.includes(cellKey)) {
      setSelectedCells(selectedCells.filter(k => k !== cellKey));
    } else {
      setSelectedCells([...selectedCells, cellKey]);
    }
  };

  const recordAttempt = async (correct) => {
    try {
      const timeTaken = attemptStartTime ? (Date.now() - attemptStartTime) / 1000 : 0;
      
      const response = await fetch(`${API_URL}/attempt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          word: puzzle.word,
          level: level,
          correct: correct,
          time_taken: timeTaken
        })
      });
      
      const data = await response.json();
      console.log('Attempt response:', data);
      
      // Update attempts count
      setAttempts(data.attempt_number || attempts + 1);
      
      if (!correct) {
        setWrongAttempts(data.wrong_attempts || wrongAttempts + 1);
      }
      
      // Check if game over due to too many wrong attempts
      if (data.game_over) {
        setGameOverDueToAttempts(true);
        setShowWordAfterFail(true);
        setFeedback({ 
          type: 'info', 
          message: language === 'sinhala'
            ? `${t.tooManyAttempts} ${puzzle.word} (${puzzle.english})`
            : `${t.tooManyAttempts} ${puzzle.word} (${puzzle.english})`
        });
        
        // Move to next word after delay
        setTimeout(() => {
          const nextRound = round + 1;
          if (nextRound >= totalRounds) {
            setGameState('gameover');
          } else {
            setRound(nextRound);
            setPuzzle(null);
            setShowWordAfterFail(false);
            setGameOverDueToAttempts(false);
          }
        }, 3000);
        return data;
      }
      
      // Show hint if provided (attempts >= 2)
      if (data.hint) {
        setAiHints([data.hint]);
        setShowHintPanel(true);
      }
      
      return data;
    } catch (error) {
      console.error('Error recording attempt:', error);
    }
  };

  const checkAnswer = async () => {
    vibrate();
    
    if (!isValidPath()) {
      setFeedback({ 
        type: 'error', 
        message: language === 'sinhala' ? '❌ අකුරු සම්බන්ධ විය යුතුය!' : '❌ Letters must be connected!' 
      });
      setTimeout(() => setFeedback(null), 1500);
      return;
    }

    if (!puzzle) return;

    const selectedLetters = selectedCells.map(key => {
      const [r, c] = key.split('-').map(Number);
      return grid[r][c].letter;
    });

    const isCorrect = 
      selectedLetters.length === puzzle.syllables.length &&
      selectedLetters.every((letter, i) => letter === puzzle.syllables[i]);

    const attemptData = await recordAttempt(isCorrect);
    
    // If game over triggered, return early
    if (attemptData?.game_over) {
      return;
    }

    if (isCorrect) {
      setFeedback({ 
        type: 'success', 
        message: language === 'sinhala' ? '✅ හරි! Correct!' : '✅ Correct!' 
      });
      triggerCelebration();
      setScore(score + 100);
      setShowHintPanel(false);
      
      setTimeout(() => {
        const nextRound = round + 1;
        if (nextRound >= totalRounds) {
          setGameState('gameover');
        } else {
          setRound(nextRound);
          setPuzzle(null);
        }
      }, 1500);
    } else {
      setFeedback({ 
        type: 'error', 
        message: language === 'sinhala' ? '❌ වැරදියි! Wrong!' : '❌ Wrong! Try again!' 
      });
      triggerShake();
      
      // Show hints when attempts >= 2
      if (attempts + 1 >= 2) {
        setShowHintPanel(true);
      }
      
      // Reduce lives
      const newLives = lives - 1;
      setLives(newLives);
      
      if (newLives <= 0) {
        setGameState('gameover');
      } else {
        setTimeout(() => {
          setSelectedCells([]);
          setFeedback(null);
        }, 1500);
      }
    }
  };

  const useHint = () => {
    vibrate();
    if (hintsRemaining > 0 && puzzle) {
      setHintsRemaining(hintsRemaining - 1);
      setAiHints([
        language === 'sinhala' 
          ? `💡 පළමු අකුර: "${puzzle.syllables[0]}"`
          : `💡 First letter: "${puzzle.syllables[0]}"`,
        language === 'sinhala'
          ? `🎯 වචනයේ අකුරු ${puzzle.syllables.length}ක් ඇත`
          : `🎯 Word has ${puzzle.syllables.length} letters`
      ]);
      setShowHintPanel(true);
    }
  };

  const skipWord = () => {
    vibrate();
    setShowWordAfterFail(true);
    setFeedback({ 
      type: 'info', 
      message: language === 'sinhala'
        ? `අත්හැරියා! වචනය: ${puzzle?.word}`
        : `Skipped! The word was: ${puzzle?.word}`
    });
    
    setTimeout(() => {
      const nextRound = round + 1;
      if (nextRound >= totalRounds) {
        setGameState('gameover');
      } else {
        setRound(nextRound);
        setPuzzle(null);
        setShowWordAfterFail(false);
      }
    }, 1500);
  };

  const clearSelection = () => {
    vibrate();
    setSelectedCells([]);
  };

  const restartGame = () => {
    vibrate();
    setGameState('menu');
    setPuzzle(null);
    setFeedback(null);
    setAiHints([]);
    setShowHintPanel(false);
    setAttempts(0);
    setWrongAttempts(0);
    setShowWordAfterFail(false);
    setGameOverDueToAttempts(false);
  };

  // ---------- MENU SCREEN ----------
  if (gameState === 'menu') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 overflow-hidden relative">
        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-10 w-48 h-48 bg-blue-200 rounded-full blur-3xl opacity-40 animate-pulse"></div>
          <div className="absolute bottom-10 right-10 w-64 h-64 bg-indigo-200 rounded-full blur-3xl opacity-30 animate-bounce" style={{animationDuration: '3s'}}></div>
          <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-sky-200 rounded-full blur-3xl opacity-40 animate-ping" style={{animationDuration: '4s'}}></div>
          
          <div className="absolute top-20 right-20 text-8xl opacity-10 animate-spin-slow">🪷</div>
          <div className="absolute bottom-20 left-20 text-8xl opacity-10 animate-spin-slow-reverse">🐘</div>
        </div>

        {/* Main Content */}
        <div className="relative max-w-6xl mx-auto p-4 h-screen flex flex-col">
          {/* Header */}
          <div className="text-center mb-6 pt-4">
            <div className="flex justify-center items-center gap-3 mb-2">
              <div className="text-6xl animate-bounce">🤟</div>
              <h1 className="text-4xl md:text-5xl font-black text-gray-800 drop-shadow-lg">
                <span className="bg-gradient-to-r from-indigo-600 to-blue-700 bg-clip-text text-transparent">
                  {t.title}
                </span>
              </h1>
              <div className="text-6xl animate-bounce" style={{animationDelay: '0.5s'}}>✊</div>
            </div>
            <p className="text-xl text-gray-700 font-bold mb-1">Sinhala Sign Language Puzzle</p>
            <p className="text-gray-600 text-sm">{t.subtitle}</p>
          </div>

          {/* Controls */}
          <div className="flex justify-end gap-2 mb-4">
            <button 
              onClick={toggleLanguage}
              className="p-2 rounded-full bg-gradient-to-r from-indigo-600 to-blue-700 text-white flex items-center gap-2"
            >
              <Globe size={20} />
              <span className="font-bold">{language === 'sinhala' ? 'සිං' : 'EN'}</span>
            </button>
            <button 
              onClick={() => setSoundOn(!soundOn)}
              className={`p-2 rounded-full ${soundOn ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}
            >
              {soundOn ? <Volume2 size={20} /> : <VolumeX size={20} />}
            </button>
            <button 
              onClick={() => setShowInstructions(!showInstructions)}
              className="p-2 rounded-full bg-blue-500 text-white"
            >
              <HelpCircle size={20} />
            </button>
          </div>

          {/* Instructions Modal */}
          {showInstructions && (
            <div className="absolute inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border-4 border-blue-300">
                <h2 className="text-2xl font-black text-blue-800 mb-4 text-center">{t.instructionTitle}</h2>
                <div className="space-y-3 mb-6">
                  {t.videoInstructions.map((instruction, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="bg-blue-100 p-2 rounded-lg text-gray-700">{instruction.icon}</div>
                      <div>
                        <p className="font-bold text-blue-700">{instruction.title}</p>
                        <p className="text-sm text-gray-600">{instruction.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={() => setShowInstructions(false)}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold py-3 rounded-xl"
                >
                  {t.instructionStart}
                </button>
              </div>
            </div>
          )}

          {/* Level Selection Grid */}
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6 overflow-y-auto">
            {Object.entries(levelConfig).map(([key, config]) => (
              <button
                key={key}
                onClick={() => startGame(key)}
                className={`${config.color} rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-[1.02] transition-all duration-300 border-4 ${config.borderColor} overflow-hidden`}
              >
                <div className="p-6 flex items-center gap-4">
                  <div className="text-6xl animate-bounce">{config.icon}</div>
                  <div className="text-left flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="text-2xl font-black text-gray-800">{config.name}</div>
                      {language === 'english' && (
                        <div className="text-gray-600 font-bold">({config.nameS})</div>
                      )}
                    </div>
                    <p className={`${config.textColor} font-medium mb-2`}>
                      {language === 'sinhala' ? config.description : config.descriptionE}
                    </p>
                    <p className="text-gray-600 text-sm">
                      {language === 'sinhala' ? config.descriptionE : config.description}
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      {[...Array(config.difficulty)].map((_, i) => (
                        <Star key={i} size={16} className="text-blue-500 fill-blue-400" />
                      ))}
                    </div>
                  </div>
                  <div className="text-4xl text-gray-700 opacity-70">➤</div>
                </div>
              </button>
            ))}
          </div>

          {/* Bottom Navigation */}
          <div className="pb-4">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-4 border border-gray-200">
              <div className="grid grid-cols-3 gap-4">
                <button
                  onClick={() => navigate('/gameselection')}
                  className="bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
                >
                  <div className="text-xl">🎯</div>
                  <div className="text-left">
                    <div className="text-sm font-bold">{t.moreGames}</div>
                    <div className="text-xs">More Games</div>
                  </div>
                </button>
                
                <button
                  onClick={() => navigate('/profile')}
                  className="bg-gradient-to-r from-indigo-600 to-blue-700 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
                >
                  <div className="text-xl">👤</div>
                  <div className="text-left">
                    <div className="text-sm font-bold">{t.myProfile}</div>
                    <div className="text-xs">My Profile</div>
                  </div>
                </button>
                
                <button
                  onClick={() => navigate('/achievements')}
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2"
                >
                  <div className="text-xl">🏆</div>
                  <div className="text-left">
                    <div className="text-sm font-bold">{t.achievements}</div>
                    <div className="text-xs">Achievements</div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------- LOADING STATE ----------
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 flex flex-col items-center justify-center relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-gradient-to-r from-blue-200/40 to-indigo-200/40 animate-float"
              style={{
                width: `${Math.random() * 60 + 20}px`,
                height: `${Math.random() * 60 + 20}px`,
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${Math.random() * 5 + 5}s`,
              }}
            />
          ))}
        </div>

        <div className="relative z-10 text-center space-y-6">
          <div className="flex justify-center gap-4 mb-4">
            <div className="text-6xl animate-bounce" style={{ animationDelay: '0s' }}>🤟</div>
            <div className="text-6xl animate-bounce" style={{ animationDelay: '0.2s' }}>✋</div>
            <div className="text-6xl animate-bounce" style={{ animationDelay: '0.4s' }}>👌</div>
          </div>

          <div>
            <h2 className="text-3xl md:text-4xl font-black text-gray-800 mb-2 drop-shadow-lg">
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                {language === 'sinhala' ? 'ප්‍රහේලිකා සූදානම් වෙමින්...' : 'Preparing Puzzle...'}
              </span>
            </h2>
            <p className="text-gray-700 text-lg font-medium mb-6">{t.preparing}</p>
          </div>

          <div className="w-64 h-4 bg-gray-200 rounded-full overflow-hidden mx-auto">
            <div className="h-full bg-gradient-to-r from-blue-500 via-indigo-400 to-sky-400 rounded-full animate-progress"></div>
          </div>

          <div className="bg-gradient-to-r from-blue-100 to-cyan-100 backdrop-blur-sm rounded-2xl p-4 border-2 border-blue-200 max-w-md mx-auto">
            <p className="text-gray-700 font-medium text-sm">
              <span className="text-blue-500">✨</span> {t.finding}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ---------- GAME OVER SCREEN ----------
  if (gameState === 'gameover') {
    const stars = score >= 800 ? 3 : score >= 500 ? 2 : score >= 200 ? 1 : 0;
    const messages = {
      3: { 
        text: t.gameOverMessages[3].text, 
        emoji: '🏆', 
        color: 'from-blue-300 to-indigo-400',
        subtitle: t.gameOverMessages[3].subtitle
      },
      2: { 
        text: t.gameOverMessages[2].text, 
        emoji: '🎉', 
        color: 'from-green-300 to-emerald-400',
        subtitle: t.gameOverMessages[2].subtitle
      },
      1: { 
        text: t.gameOverMessages[1].text, 
        emoji: '👏', 
        color: 'from-sky-300 to-blue-400',
        subtitle: t.gameOverMessages[1].subtitle
      },
      0: { 
        text: t.gameOverMessages[0].text, 
        emoji: '💪', 
        color: 'from-indigo-300 to-violet-400',
        subtitle: t.gameOverMessages[0].subtitle
      }
    };

    const message = messages[stars];

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Celebration Particles */}
        {Array.from({ length: 30 }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-bounce"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              fontSize: `${Math.random() * 30 + 20}px`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${Math.random() * 3 + 2}s`,
              opacity: 0.7
            }}
          >
            {['🎉', '🎊', '🌟', '⭐', '🏆', '✨', '🥳', '🎈'][Math.floor(Math.random() * 8)]}
          </div>
        ))}

        <div className="relative bg-white/90 backdrop-blur-2xl border-4 border-white/60 rounded-3xl shadow-2xl p-8 max-w-lg w-full text-center">
          <div className="relative inline-block mb-2">
            <div className="text-8xl animate-bounce">{message.emoji}</div>
            <div className="absolute -top-2 -right-2 w-10 h-10 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
              {score}
            </div>
          </div>

          <h2 className="text-4xl font-black text-gray-800 mb-2 drop-shadow-lg">{t.gameOver}</h2>
          <p className="text-gray-600 text-lg mb-2">{t.gameComplete}</p>

          <div className={`bg-gradient-to-r ${message.color} backdrop-blur-sm rounded-2xl p-6 mb-6 border-4 border-white/70 shadow-inner`}>
            <div className="text-7xl font-black text-gray-800 mb-2 drop-shadow-lg">{score}</div>
            <div className="text-4xl mb-3">
              {'⭐'.repeat(stars)}{'☆'.repeat(3 - stars)}
            </div>
            <div className="text-2xl font-bold text-gray-800 mb-1">{message.text}</div>
            <p className="text-gray-700 text-sm">{message.subtitle}</p>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl p-3 border-2 border-green-200 shadow-lg">
              <div className="text-2xl mb-1 text-green-800">🎯</div>
              <div className="text-gray-600 text-xs font-bold uppercase">{t.level}</div>
              <div className="text-green-800 text-lg font-bold capitalize">{level}</div>
            </div>
            <div className="bg-gradient-to-br from-sky-100 to-blue-100 rounded-xl p-3 border-2 border-sky-200 shadow-lg">
              <div className="text-2xl mb-1 text-blue-800">🔄</div>
              <div className="text-gray-600 text-xs font-bold uppercase">{t.round}</div>
              <div className="text-blue-800 text-lg font-bold">{round}/{totalRounds}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-xl p-3 border-2 border-purple-200 shadow-lg">
              <div className="text-2xl mb-1 text-purple-800">❤️</div>
              <div className="text-gray-600 text-xs font-bold uppercase">{t.lives}</div>
              <div className="text-purple-800 text-lg font-bold">{lives}</div>
            </div>
          </div>

          <div className="space-y-3">
            <button
              onClick={restartGame}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-black px-6 py-4 rounded-2xl shadow-xl transform hover:scale-105 transition-all flex items-center justify-center gap-3 text-lg border-4 border-green-300/50"
            >
              <RefreshCw className="w-6 h-6" />
              <span>{t.restartGame}</span>
            </button>

            <button
              onClick={() => navigate('/gameselection')}
              className="w-full bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white font-bold px-6 py-3 rounded-xl shadow-lg transform hover:scale-105 transition-all flex items-center justify-center gap-2 border-2 border-teal-300/50"
            >
              <span className="text-xl">🎮</span>
              <span>{t.otherGames}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- PLAYING STATE ----------
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 overflow-auto">
      {/* Celebration Animation */}
      {celebration && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {Array.from({ length: 30 }).map((_, i) => (
            <div
              key={i}
              className="absolute animate-bounce"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                fontSize: `${Math.random() * 30 + 20}px`,
                animationDelay: `${Math.random() * 0.5}s`,
              }}
            >
              {['🎉', '🎊', '🌟', '✨', '🥳', '👏'][Math.floor(Math.random() * 6)]}
            </div>
          ))}
        </div>
      )}

      <div className="p-4 flex flex-col min-h-screen">
        {/* Top Game Header */}
        <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-lg p-4 mb-4 flex justify-between items-center border border-gray-200 flex-shrink-0">
          
          {/* Left Section */}
          <div className="flex items-center gap-3">
            <button
              onClick={restartGame}
              className="bg-gradient-to-r from-indigo-600 to-blue-700 text-white font-bold px-4 py-2 rounded-xl flex items-center gap-2 hover:scale-105 transition-transform border border-indigo-400 shadow-md"
            >
              <Home className="w-5 h-5" />
              <span className="hidden sm:inline">{t.mainMenu}</span>
            </button>
            
            <div className="bg-gradient-to-r from-blue-50 to-indigo-100 rounded-xl px-4 py-2 border border-blue-200 shadow-md">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-700" />
                <div>
                  <div className="text-sm font-bold text-gray-600">{t.level}:</div>
                  <div className="font-black text-lg text-gray-800">
                    {language === 'sinhala' ? levelConfig[level].nameS : levelConfig[level].name}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-3">
            <div className="flex gap-3">
              <div className="text-center bg-white/80 backdrop-blur-sm rounded-xl p-3 min-w-[80px] border border-gray-200 shadow-md">
                <Trophy className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                <div className="text-xl font-black text-gray-800">{score}</div>
                <div className="text-xs text-gray-600 font-bold">{t.points}</div>
              </div>
              
              <div className="text-center bg-white/80 backdrop-blur-sm rounded-xl p-3 min-w-[80px] border border-gray-200 shadow-md">
                <Heart className="w-5 h-5 text-red-500 mx-auto mb-1" />
                <div className="text-xl font-black text-gray-800">{lives}</div>
                <div className="text-xs text-gray-600 font-bold">{t.lives}</div>
              </div>
              
              <div className="text-center bg-white/80 backdrop-blur-sm rounded-xl p-3 min-w-[80px] border border-gray-200 shadow-md">
                <Lightbulb className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                <div className="text-xl font-black text-gray-800">{hintsRemaining}</div>
                <div className="text-xs text-gray-600 font-bold">{t.hintText}</div>
              </div>
              
              <div className="text-center bg-white/80 backdrop-blur-sm rounded-xl p-3 min-w-[80px] border border-gray-200 shadow-md">
                <Target className="w-5 h-5 text-green-500 mx-auto mb-1" />
                <div className="text-xl font-black text-gray-800">{round + 1}/{totalRounds}</div>
                <div className="text-xs text-gray-600 font-bold">{t.round}</div>
              </div>
            </div>

            <button
              onClick={toggleLanguage}
              className="bg-gradient-to-r from-blue-500 to-cyan-600 text-white font-bold px-4 py-2 rounded-xl flex items-center gap-2 hover:scale-105 transition-transform border border-blue-400 shadow-md"
            >
              <Languages className="w-5 h-5" />
              <span className="font-bold">{language === 'english' ? 'EN' : 'සිං'}</span>
            </button>
          </div>
        </div>

        {/* Main Game Area */}
        <div className="flex-1 overflow-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
            {/* Left Panel */}
            <div className="space-y-4">
              {/* Video Section */}
              <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-lg">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <div className="text-2xl text-blue-600">🤟</div>
                  <h3 className="text-gray-800 font-bold text-lg">{t.signVideo}</h3>
                  <div className="text-2xl text-blue-600">👀</div>
                </div>
                
                <div className="relative rounded-xl overflow-hidden border-2 border-gray-300 shadow-inner">
                  {puzzle && puzzle.video_url ? (
                    <video
                      key={puzzle.word}
                      src={`http://localhost:5001${puzzle.video_url}`}
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="w-full h-56 object-cover"
                      onError={(e) => console.error('Video error:', e)}
                    />
                  ) : (
                    <div className="w-full h-56 bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
                      <div className="text-6xl text-blue-400 animate-bounce">🤟</div>
                    </div>
                  )}
                  <div className="absolute bottom-3 right-3 bg-black/70 rounded-full p-2 shadow-lg">
                    <Play className="w-5 h-5 text-white" />
                  </div>
                </div>
              </div>

              {/* Secret Word Info */}
              {puzzle && !showWordAfterFail && (
                <div className="bg-white rounded-2xl p-5 border border-gray-200 shadow-lg">
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <div className="text-2xl text-blue-600">❓</div>
                    <h3 className="text-gray-800 font-bold text-lg">{t.secretWord}</h3>
                    <div className="text-2xl text-blue-600">🔍</div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 mb-4 border border-blue-200">
                    <p className="text-gray-700 text-center font-medium mb-3">{t.wordHas} {puzzle.syllables.length} {t.selectConnected}</p>
                    
                    <div className="flex justify-center gap-3 mb-4">
                      {puzzle.syllables.map((_, index) => (
                        <div key={index} className="w-12 h-14 bg-white rounded-lg flex items-center justify-center border-2 border-blue-200 shadow-sm relative group">
                          {selectedCells.length > index ? (
                            <span className="text-2xl font-bold text-blue-600">
                              {(() => {
                                const [r, c] = selectedCells[index].split('-').map(Number);
                                return grid[r]?.[c]?.letter || '?';
                              })()}
                            </span>
                          ) : (
                            <>
                              <span className="text-gray-300 text-xl">?</span>
                              <div className="absolute inset-0 bg-gradient-to-br from-transparent to-blue-50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            </>
                          )}
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full text-xs flex items-center justify-center text-white font-bold">
                            {index + 1}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* MODIFIED: Enhanced Attempt Tracking with Wrong Attempts */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div className="text-center">
                        <span className="text-gray-700 font-medium text-sm">{t.attempts}:</span>
                        <div className={`text-2xl font-bold ${
                          attempts >= 4 ? 'text-red-500' : 
                          attempts >= 2 ? 'text-yellow-500' : 
                          'text-green-500'
                        }`}>{attempts}</div>
                      </div>
                      <div className="text-center">
                        <span className="text-gray-700 font-medium text-sm">{t.wrongAttempts}:</span>
                        <div className={`text-2xl font-bold ${
                          wrongAttempts >= 4 ? 'text-red-500' : 
                          wrongAttempts >= 2 ? 'text-yellow-500' : 
                          'text-blue-400'
                        }`}>{wrongAttempts}</div>
                      </div>
                    </div>
                    
                    {/* Progress bar for wrong attempts out of 5 */}
                    <div className="relative pt-1">
                      <div className="flex mb-2 items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-red-600 bg-red-200">
                            Game Over at 5
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-semibold inline-block text-red-600">
                            {wrongAttempts}/5
                          </span>
                        </div>
                      </div>
                      <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-red-200">
                        <div 
                          style={{ width: `${(wrongAttempts / 5) * 100}%` }}
                          className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-red-500 transition-all duration-500"
                        ></div>
                      </div>
                    </div>
                    
                    {/* Hint indicator */}
                    {attempts >= 2 && (
                      <div className="mt-3 p-2 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-lg border border-blue-200">
                        <p className="text-blue-800 text-sm font-medium text-center">
                          💡 {language === 'sinhala' ? 'ඉඟි ලබා ගත හැක!' : 'Hints available!'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Word Reveal on Game Over or Skip */}
              {puzzle && showWordAfterFail && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-5 border border-blue-200 shadow-lg">
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <div className="text-2xl text-blue-500">💡</div>
                    <h3 className="text-gray-800 font-bold text-lg">{t.wordWas}:</h3>
                    <div className="text-2xl text-blue-500">📝</div>
                  </div>
                  
                  <div className="bg-white rounded-xl p-4 mb-4 border border-blue-100">
                    <p className="text-3xl font-black text-gray-800 text-center mb-3">{puzzle.word}</p>
                    <div className="flex justify-center gap-2 flex-wrap">
                      {puzzle.syllables.map((syllable, index) => (
                        <span key={index} className="bg-gradient-to-r from-sky-100 to-blue-100 px-3 py-1 rounded-lg text-blue-700 font-bold border border-sky-200">
                          {syllable}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-sky-50 to-blue-50 rounded-xl p-3 border border-sky-200">
                    <p className="text-gray-700 text-center font-bold">📝 {puzzle.english}</p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={useHint}
                    disabled={hintsRemaining === 0}
                    className={`py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                      hintsRemaining > 0
                        ? 'bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white border border-teal-400 shadow-md hover:scale-105'
                        : 'bg-gray-300 text-gray-500 border border-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <Lightbulb className="w-5 h-5" />
                    <span>{t.hint} ({hintsRemaining})</span>
                  </button>
                  
                  <button
                    onClick={clearSelection}
                    disabled={selectedCells.length === 0}
                    className={`py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                      selectedCells.length > 0
                        ? 'bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white border border-red-400 shadow-md hover:scale-105'
                        : 'bg-gray-300 text-gray-500 border border-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <X className="w-5 h-5" />
                    <span>{t.clear}</span>
                  </button>
                </div>

                <button
                  onClick={checkAnswer}
                  disabled={selectedCells.length === 0}
                  className={`w-full py-4 rounded-2xl font-bold text-xl flex items-center justify-center gap-3 transition-all ${
                    selectedCells.length > 0
                      ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white border border-green-400 shadow-lg hover:shadow-xl hover:scale-105 animate-pulse'
                      : 'bg-gray-400 text-gray-300 border border-gray-400 cursor-not-allowed'
                  }`}
                >
                  <Check className="w-7 h-7" />
                  <span>{t.checkAnswer}</span>
                </button>

                <button
                  onClick={skipWord}
                  className="w-full py-3 rounded-xl font-bold text-lg flex items-center justify-center gap-2 bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white border border-gray-400 shadow-md hover:scale-105 transition-all"
                >
                  <SkipForward className="w-5 h-5" />
                  <span>{t.nextWord}</span>
                </button>
              </div>
            </div>

            {/* Center Panel - Game Grid */}
            <div className={`lg:col-span-2 bg-white rounded-2xl p-5 border border-gray-200 shadow-lg flex flex-col ${shake ? 'animate-shake' : ''}`}>
              {/* Hint Panel */}
              {showHintPanel && aiHints.length > 0 && (
                <div className="sticky top-2 z-[999] space-y-3 mb-4">
                  <div className="bg-gradient-to-r from-blue-100 to-indigo-100 rounded-2xl p-4 border-2 border-blue-300 shadow-lg">
                    <div className="flex items-center gap-2 mb-3 justify-center">
                      <span className="text-2xl">💡</span>
                      <h4 className="text-lg font-black text-blue-900">
                        {t.aiHint}
                      </h4>
                      <span className="text-2xl">🤖</span>
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      {aiHints.map((hint, idx) => (
                        <div
                          key={idx}
                          className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-3 border border-blue-200"
                        >
                          <p className="text-blue-800 font-medium text-sm">
                            {hint}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-center gap-3 mb-6">
                <div className="text-3xl text-blue-400 animate-spin" style={{animationDuration: '3s'}}>✨</div>
                <h3 className="text-2xl font-black text-gray-800 text-center">{t.findSecretWord}</h3>
                <div className="text-3xl text-blue-400 animate-spin" style={{animationDuration: '3s', animationDirection: 'reverse'}}>✨</div>
              </div>

              <div className="mb-6 bg-gradient-to-r from-sky-50 to-blue-50 rounded-xl p-4 border border-sky-200">
                <p className="text-gray-700 text-center text-sm font-medium">
                  {t.instructions}
                </p>
              </div>

              <div className="flex-1 flex items-center justify-center p-3 min-h-[400px]">
                <div 
                  className="grid gap-2 p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border-2 border-blue-200 shadow-inner"
                  style={{
                    gridTemplateColumns: `repeat(${levelConfig[level].gridSize}, minmax(0, 1fr))`,
                    maxWidth: 'min(600px, 90vw)',
                    maxHeight: 'min(600px, 60vh)'
                  }}
                >
                  {grid.map((row, rowIdx) =>
                    row.map((cell, colIdx) => {
                      const cellKey = `${rowIdx}-${colIdx}`;
                      const isSelected = selectedCells.includes(cellKey);
                      const selectionIndex = selectedCells.indexOf(cellKey);

                      return (
                        <button
                          key={cellKey}
                          onClick={() => toggleCell(rowIdx, colIdx)}
                          className={`aspect-square flex items-center justify-center text-3xl font-black rounded-xl transition-all duration-200 border-2 relative ${
                            isSelected
                              ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white scale-105 border-yellow-400 shadow-lg z-10'
                              : 'bg-white text-gray-800 hover:bg-blue-50 hover:scale-102 border-gray-300 shadow-sm hover:shadow-md'
                          }`}
                        >
                          {cell.letter}
                          {isSelected && (
                            <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center text-base font-black text-white border-2 border-white shadow-lg">
                              {selectionIndex + 1}
                            </div>
                          )}
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="mt-6 p-4 bg-gradient-to-r from-sky-50 to-blue-50 rounded-xl border border-sky-200 shadow-sm">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center bg-white rounded-xl p-3 border border-gray-300">
                    <div className="text-sm text-gray-600 font-bold mb-1">{t.secretWordText}</div>
                    <div className="text-2xl font-black text-indigo-600">{puzzle ? puzzle.syllables.length : 0}</div>
                  </div>
                  <div className="text-center bg-white rounded-xl p-3 border border-gray-300">
                    <div className="text-sm text-gray-600 font-bold mb-1">{t.selectedLetters}</div>
                    <div className={`text-2xl font-black ${
                      selectedCells.length === puzzle?.syllables.length ? 'text-green-500' : 'text-blue-500'
                    }`}>
                      {selectedCells.length}
                    </div>
                  </div>
                  <div className="text-center bg-white rounded-xl p-3 border border-gray-300">
                    <div className="text-sm text-gray-600 font-bold mb-1">{t.attempts}</div>
                    <div className="text-2xl font-black text-gray-800">{attempts}</div>
                  </div>
                </div>
                
                <div className="bg-gradient-to-r from-blue-100 to-indigo-100 rounded-lg p-3 border border-blue-200">
                  <p className="text-center text-blue-800 text-sm font-medium">
                    {t.note}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Feedback Message */}
          {feedback && (
            <div className={`p-4 rounded-2xl text-center font-bold text-lg border shadow-lg animate-bounce ${
              feedback.type === 'success'
                ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border-green-300'
                : feedback.type === 'error'
                ? 'bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border-red-300'
                : 'bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 border-blue-300'
            }`}>
              <div className="flex items-center justify-center gap-3">
                <div className="text-2xl">
                  {feedback.type === 'success' ? '🎉' : feedback.type === 'error' ? '🤔' : '💡'}
                </div>
                <span>{feedback.message}</span>
                <div className="text-2xl">
                  {feedback.type === 'success' ? '✨' : feedback.type === 'error' ? '💪' : '👂'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.3; }
          50% { transform: translateY(-20px) rotate(180deg); opacity: 0.6; }
        }
        
        @keyframes progress {
          0% { width: 0%; }
          50% { width: 70%; }
          100% { width: 100%; }
        }
        
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes spin-slow-reverse {
          from { transform: rotate(360deg); }
          to { transform: rotate(0deg); }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
          20%, 40%, 60%, 80% { transform: translateX(10px); }
        }
        
        .animate-float {
          animation: float infinite ease-in-out;
        }
        
        .animate-progress {
          animation: progress 2s ease-in-out infinite;
        }
        
        .animate-spin-slow {
          animation: spin-slow 20s linear infinite;
        }
        
        .animate-spin-slow-reverse {
          animation: spin-slow-reverse 25s linear infinite;
        }
        
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default SinhalaWordPuzzleGame;