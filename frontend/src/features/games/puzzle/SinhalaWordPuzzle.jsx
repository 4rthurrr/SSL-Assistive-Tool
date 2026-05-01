import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Play, Trophy, Heart, Lightbulb, RefreshCw, Home, 
  Target, HelpCircle, Star,
  Volume2, VolumeX, Check, X, SkipForward, Globe
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
  const [language, setLanguage] = useState('english');
  
  // Puzzle State
  const [puzzle, setPuzzle] = useState(null);
  const [grid, setGrid] = useState([]);
  const [selectedCells, setSelectedCells] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [aiHints, setAiHints] = useState([]);
  const [showHintPanel, setShowHintPanel] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [showWordAfterFail, setShowWordAfterFail] = useState(false);
  
  // Attempt tracking
  const [attempts, setAttempts] = useState(0);
  const [wrongAttempts, setWrongAttempts] = useState(0);

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
      secretWord: 'රහස් වචනය',
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
      findSecretWord: 'රහස් වචනය සොයන්න',
      instructions: '🎯 උපදෙස්: වීඩියෝව නරඹා, පෙළෙහි සඟවා ඇති වචනය සොයන්න. අසල්වැසි කොටුවල අකුරු තෝරන්න (තිරස්, සිරස් හෝ විකර්ණ).',
      secretWordText: 'රහස් වචනය',
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
      icon: '🌱',
      difficulty: 1,
    },
    easy: {
      name: language === 'sinhala' ? 'පහසු' : 'EASY',
      nameS: 'පහසු',
      description: 'සරල වචන (2-3 අකුරු)',
      descriptionE: 'Simple words (2-3 letters)',
      gridSize: 7,
      icon: '🔍',
      difficulty: 2,
    },
    medium: {
      name: language === 'sinhala' ? 'මධ්‍යම' : 'MEDIUM',
      nameS: 'මධ්‍යම',
      description: 'මධ්‍යම වචන (4-6 අකුරු)',
      descriptionE: 'Medium words (4-6 letters)',
      gridSize: 8,
      icon: '🏃',
      difficulty: 3,
    },
    hard: {
      name: language === 'sinhala' ? 'දුෂ්කර' : 'HARD',
      nameS: 'දුෂ්කර',
      description: 'දුෂ්කර වචන (7+ අකුරු)',
      descriptionE: 'Hard words (7+ letters)',
      gridSize: 10,
      icon: '🏆',
      difficulty: 4,
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
    if (navigator.vibrate) {
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
    
    setAttempts(0);
    setWrongAttempts(0);
    setShowWordAfterFail(false);
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
        
        setAttempts(0);
        setWrongAttempts(0);
        setShowWordAfterFail(false);
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
    //check adjacency for all selected cells
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
        time_taken: timeTaken,
        language: language  // ← ADD THIS LINE (use the language state variable)
      })
    });
    
    const data = await response.json();
    console.log('Attempt response:', data);
    
    setAttempts(data.attempt_number || attempts + 1);
    
    if (!correct) {
      setWrongAttempts(data.wrong_attempts || wrongAttempts + 1);
    }
    
    if (data.game_over) {
      setShowWordAfterFail(true);
      setFeedback({ 
        type: 'info', 
        message: language === 'sinhala'
          ? `${t.tooManyAttempts} ${puzzle.word} (${puzzle.english})`
          : `${t.tooManyAttempts} ${puzzle.word} (${puzzle.english})`
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
      }, 3000);
      return data;
    }
    
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
//the number of selected letters matches puzzle.syllables.length, and very selected letter exactly equals the corresponding puzzle.syllables[i].

// This ensures that the player has selected the correct letters in the correct order to form the target word.
    const isCorrect = 
      selectedLetters.length === puzzle.syllables.length &&
      selectedLetters.every((letter, i) => letter === puzzle.syllables[i]);

    const attemptData = await recordAttempt(isCorrect);
    
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
      
      if (attempts + 1 >= 2) {
        setShowHintPanel(true);
      }
      
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

  const useHint = async () => {
  vibrate();
  if (hintsRemaining > 0 && puzzle) {
    // Try to get AI hint from backend
    try {
      const response = await fetch(`${API_URL}/ai/hint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
    user_id: userId,
    word: puzzle.word,
    level: level,
    language: language   // ← ADD LANGUAGE HERE TOO
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.hint) {
        setAiHints([data.hint]);
      } else {
        // Fallback to local hints
        setAiHints([
          language === 'sinhala' 
            ? `💡 පළමු අකුර: "${puzzle.syllables[0]}"`
            : `💡 First letter: "${puzzle.syllables[0]}"`,
          language === 'sinhala'
            ? `🎯 වචනයේ අකුරු ${puzzle.syllables.length}ක් ඇත`
            : `🎯 Word has ${puzzle.syllables.length} letters`
        ]);
      }
      
      setHintsRemaining(hintsRemaining - 1);
      setShowHintPanel(true);
    } catch (error) {
      console.error('Error getting AI hint:', error);
      // Fallback to local hints
      setAiHints([
        language === 'sinhala' 
          ? `💡 පළමු අකුර: "${puzzle.syllables[0]}"`
          : `💡 First letter: "${puzzle.syllables[0]}"`,
        language === 'sinhala'
          ? `🎯 වචනයේ අකුරු ${puzzle.syllables.length}ක් ඇත`
          : `🎯 Word has ${puzzle.syllables.length} letters`
      ]);
      setHintsRemaining(hintsRemaining - 1);
      setShowHintPanel(true);
    }
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
  };

  // MENU SCREEN
  if (gameState === 'menu') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 overflow-hidden relative">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-10 w-48 h-48 bg-blue-200 rounded-full blur-3xl opacity-40 animate-pulse"></div>
          <div className="absolute bottom-10 right-10 w-64 h-64 bg-indigo-200 rounded-full blur-3xl opacity-30 animate-bounce" style={{animationDuration: '3s'}}></div>
          <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-sky-200 rounded-full blur-3xl opacity-40 animate-ping" style={{animationDuration: '4s'}}></div>
        </div>

        {/* Main Content */}
        <div className="relative max-w-6xl mx-auto p-4 h-screen flex flex-col">
          {/* Header */}
          <div className="text-center mb-6 pt-4">
            <div className="flex justify-center items-center gap-3 mb-2">
              <div className="text-6xl animate-bounce">🤟</div>
              <h1 className="text-4xl md:text-5xl font-black">
                <span className="text-red-600 font-black">{t.title}</span>
              </h1>
              <div className="text-6xl animate-bounce" style={{animationDelay: '0.5s'}}>✊</div>
            </div>
            <p className="text-xl text-gray-700 font-bold mb-1">Sinhala Sign Language Puzzle</p>
            <p className="text-gray-600 text-sm">{t.subtitle}</p>
          </div>

          {/* Controls */}
          <div className="flex justify-end gap-2 mb-4">
            <button onClick={toggleLanguage} className="bg-indigo-500 hover:bg-indigo-600 text-white p-2 rounded-full">
              <Globe size={20} />
            </button>
            <button onClick={() => setSoundOn(!soundOn)} className={`p-2 rounded-full ${soundOn ? 'bg-green-500' : 'bg-gray-400'} text-white`}>
              {soundOn ? <Volume2 size={20} /> : <VolumeX size={20} />}
            </button>
            <button onClick={() => setShowInstructions(!showInstructions)} className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-full">
              <HelpCircle size={20} />
            </button>
          </div>

          {/* Instructions Modal */}
          {showInstructions && (
            <div className="absolute inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
                <h2 className="text-2xl font-black text-blue-600 mb-4 text-center">{t.instructionTitle}</h2>
                <div className="space-y-3 mb-6">
                  {t.videoInstructions.map((instruction, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="bg-blue-100 p-2 rounded-lg">{instruction.icon}</div>
                      <div>
                        <p className="font-bold text-blue-600">{instruction.title}</p>
                        <p className="text-sm text-gray-600">{instruction.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <button onClick={() => setShowInstructions(false)} className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 rounded-xl">
                  {t.instructionStart}
                </button>
              </div>
            </div>
          )}

          {/* Level Selection */}
<div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6 overflow-y-auto">
  {Object.entries(levelConfig).map(([key, config]) => {
    // Define different colors for each level
    const levelColors = {
      basic: 'bg-emerald-400 hover:bg-emerald-500',
      easy: 'bg-sky-400 hover:bg-sky-500',
      medium: 'bg-indigo-400 hover:bg-indigo-500',
      hard: 'bg-amber-400 hover:bg-amber-500'
    };
    
    return (
      <button 
        key={key} 
        onClick={() => startGame(key)} 
        className={`${levelColors[key]} text-white rounded-2xl p-6 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300`}
      >
        <div className="flex items-center gap-4">
          <div className="text-6xl">{config.icon}</div>
          <div className="text-left flex-1">
            <div className="text-2xl font-black">{config.name}</div>
            <p className="text-white/90 text-sm mt-1">
              {language === 'sinhala' ? config.description : config.descriptionE}
            </p>
            <div className="mt-2 flex gap-1">
              {[...Array(config.difficulty)].map((_, i) => (
                <Star key={i} size={14} className="fill-yellow-400 text-yellow-400" />
              ))}
            </div>
          </div>
          <div className="text-white/70 text-2xl">➤</div>
        </div>
      </button>
    );
  })}
</div>

          {/* Bottom Navigation */}
          <div className="pb-4">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-4">
              <div className="grid grid-cols-3 gap-4">
                <button onClick={() => navigate('/gameselection')} className="bg-teal-500 hover:bg-teal-600 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2">
                  <span className="text-xl">🎯</span>
                  <span>{t.moreGames}</span>
                </button>
                <button onClick={() => navigate('/profile')} className="bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2">
                  <span className="text-xl">👤</span>
                  <span>{t.myProfile}</span>
                </button>
                <button onClick={() => navigate('/achievements')} className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2">
                  <span className="text-xl">🏆</span>
                  <span>{t.achievements}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // LOADING STATE
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 flex flex-col items-center justify-center">
        <div className="text-center space-y-6">
          <div className="flex justify-center gap-4">
            <div className="text-6xl animate-bounce">🤟</div>
            <div className="text-6xl animate-bounce" style={{ animationDelay: '0.2s' }}>✋</div>
            <div className="text-6xl animate-bounce" style={{ animationDelay: '0.4s' }}>👌</div>
          </div>
          <h2 className="text-3xl font-black text-gray-800">{language === 'sinhala' ? 'ප්‍රහේලිකා සූදානම් වෙමින්...' : 'Preparing Puzzle...'}</h2>
          <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden mx-auto">
            <div className="h-full bg-blue-500 rounded-full animate-progress w-full"></div>
          </div>
        </div>
      </div>
    );
  }

  // GAME OVER SCREEN
  if (gameState === 'gameover') {
    const stars = score >= 800 ? 3 : score >= 500 ? 2 : score >= 200 ? 1 : 0;
    const messages = {
      3: { text: t.gameOverMessages[3].text, emoji: '🏆', subtitle: t.gameOverMessages[3].subtitle },
      2: { text: t.gameOverMessages[2].text, emoji: '🎉', subtitle: t.gameOverMessages[2].subtitle },
      1: { text: t.gameOverMessages[1].text, emoji: '👏', subtitle: t.gameOverMessages[1].subtitle },
      0: { text: t.gameOverMessages[0].text, emoji: '💪', subtitle: t.gameOverMessages[0].subtitle }
    };
    const message = messages[stars];

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 flex items-center justify-center p-4">
        <div className="bg-white/90 backdrop-blur-2xl rounded-3xl shadow-2xl p-8 max-w-lg w-full text-center">
          <div className="text-8xl animate-bounce mb-4">{message.emoji}</div>
          <h2 className="text-4xl font-black text-gray-800 mb-2">{t.gameOver}</h2>
          <div className="bg-gradient-to-r from-blue-100 to-indigo-100 rounded-2xl p-6 mb-6">
            <div className="text-7xl font-black text-gray-800 mb-2">{score}</div>
            <div className="text-4xl mb-3">{'⭐'.repeat(stars)}{'☆'.repeat(3 - stars)}</div>
            <div className="text-2xl font-bold text-gray-800 mb-1">{message.text}</div>
            <p className="text-gray-700 text-sm">{message.subtitle}</p>
          </div>
          <div className="space-y-3">
            <button onClick={restartGame} className="w-full bg-green-500 hover:bg-green-600 text-white font-black py-4 rounded-2xl">
              <RefreshCw className="inline w-5 h-5 mr-2" /> {t.restartGame}
            </button>
            <button onClick={() => navigate('/gameselection')} className="w-full bg-teal-500 hover:bg-teal-600 text-white font-bold py-3 rounded-xl">
              🎮 {t.otherGames}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // PLAYING STATE
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-sky-50 overflow-auto">
      {/* Celebration Animation */}
      {celebration && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {Array.from({ length: 30 }).map((_, i) => (
            <div key={i} className="absolute animate-bounce" style={{ left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%`, fontSize: `${Math.random() * 30 + 20}px` }}>
              {['🎉', '🎊', '🌟', '✨', '🥳', '👏'][Math.floor(Math.random() * 6)]}
            </div>
          ))}
        </div>
      )}

      <div className="p-4 flex flex-col min-h-screen">
        {/* Game Header */}
        <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-lg p-4 mb-4 flex justify-between items-center flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <button onClick={restartGame} className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-xl flex items-center gap-2">
              <Home size={18} /> {t.mainMenu}
            </button>
            <div className="bg-blue-100 px-4 py-2 rounded-xl">
              <div className="text-sm font-bold text-gray-600">{t.level}:</div>
              <div className="font-black text-lg">{language === 'sinhala' ? levelConfig[level].nameS : levelConfig[level].name}</div>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="text-center bg-white rounded-xl p-2 min-w-[70px] shadow">
              <Trophy size={18} className="text-blue-500 mx-auto" />
              <div className="font-black">{score}</div>
              <div className="text-xs text-gray-600">{t.points}</div>
            </div>
            <div className="text-center bg-white rounded-xl p-2 min-w-[70px] shadow">
              <Heart size={18} className="text-red-500 mx-auto" />
              <div className="font-black">{lives}</div>
              <div className="text-xs text-gray-600">{t.lives}</div>
            </div>
            <div className="text-center bg-white rounded-xl p-2 min-w-[70px] shadow">
              <Lightbulb size={18} className="text-yellow-500 mx-auto" />
              <div className="font-black">{hintsRemaining}</div>
              <div className="text-xs text-gray-600">{t.hintText}</div>
            </div>
            <div className="text-center bg-white rounded-xl p-2 min-w-[70px] shadow">
              <Target size={18} className="text-green-500 mx-auto" />
              <div className="font-black">{round + 1}/{totalRounds}</div>
              <div className="text-xs text-gray-600">{t.round}</div>
            </div>
            <button onClick={toggleLanguage} className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-xl">
              {language === 'english' ? 'EN' : 'සිං'}
            </button>
          </div>
        </div>

        {/* Main Game Area */}
        <div className="flex-1 overflow-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Left Panel */}
            <div className="space-y-4">
              {/* Video */}
              <div className="bg-white rounded-2xl p-4 shadow-lg">
                <h3 className="text-center font-bold text-lg mb-3">🤟 {t.signVideo} 👀</h3>
                <div className="rounded-xl overflow-hidden border">
                  {puzzle && puzzle.video_url ? (
                    <video src={`http://localhost:5001${puzzle.video_url}`} autoPlay loop muted playsInline className="w-full h-48 object-cover" />
                  ) : (
                    <div className="w-full h-48 bg-blue-100 flex items-center justify-center">
                      <div className="text-6xl">🤟</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Secret Word Info */}
              {puzzle && !showWordAfterFail && (
                <div className="bg-white rounded-2xl p-4 shadow-lg">
                  <h3 className="text-center font-bold text-lg mb-3">❓ {t.secretWord} 🔍</h3>
                  <div className="bg-blue-50 rounded-xl p-4">
                    <p className="text-center mb-3">{t.wordHas} {puzzle.syllables.length} {t.selectConnected}</p>
                    <div className="flex justify-center gap-2 mb-4">
                      {puzzle.syllables.map((_, index) => (
                        <div key={index} className="w-12 h-14 bg-white rounded-lg flex items-center justify-center border-2 border-blue-200 relative">
                          {selectedCells.length > index ? (
                            <span className="text-2xl font-bold text-blue-600">
                              {(() => {
                                const [r, c] = selectedCells[index].split('-').map(Number);
                                return grid[r]?.[c]?.letter || '?';
                              })()}
                            </span>
                          ) : (
                            <span className="text-gray-300 text-xl">?</span>
                          )}
                          <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 rounded-full text-xs flex items-center justify-center text-white">{index + 1}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Attempt Tracking */}
                  <div className="bg-blue-50 rounded-xl p-4 mt-3">
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div className="text-center">
                        <div className="text-sm text-gray-600">{t.attempts}</div>
                        <div className={`text-2xl font-bold ${attempts >= 4 ? 'text-red-500' : attempts >= 2 ? 'text-yellow-500' : 'text-green-500'}`}>{attempts}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-600">{t.wrongAttempts}</div>
                        <div className={`text-2xl font-bold ${wrongAttempts >= 4 ? 'text-red-500' : wrongAttempts >= 2 ? 'text-yellow-500' : 'text-blue-500'}`}>{wrongAttempts}</div>
                      </div>
                    </div>
                    <div className="h-2 bg-red-200 rounded-full overflow-hidden">
                      <div className="h-full bg-red-500 transition-all" style={{ width: `${(wrongAttempts / 5) * 100}%` }}></div>
                    </div>
                    {attempts >= 2 && (
                      <div className="mt-3 p-2 bg-blue-100 rounded-lg text-center text-sm text-blue-800">💡 Hints available!</div>
                    )}
                  </div>
                </div>
              )}

              {/* Word Reveal */}
              {puzzle && showWordAfterFail && (
                <div className="bg-white rounded-2xl p-4 shadow-lg">
                  <h3 className="text-center font-bold text-lg mb-3">💡 {t.wordWas} 📝</h3>
                  <div className="bg-blue-50 rounded-xl p-4 text-center">
                    <div className="text-3xl font-black mb-2">{puzzle.word}</div>
                    <div className="text-gray-600">{puzzle.english}</div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={useHint} disabled={hintsRemaining === 0} className={`px-4 py-2 rounded-xl font-bold flex items-center justify-center gap-2 ${hintsRemaining > 0 ? 'bg-teal-500 hover:bg-teal-600 text-white' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}>
                    <Lightbulb size={18} /> {t.hint} ({hintsRemaining})
                  </button>
                  <button onClick={clearSelection} disabled={selectedCells.length === 0} className={`px-4 py-2 rounded-xl font-bold flex items-center justify-center gap-2 ${selectedCells.length > 0 ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}>
                    <X size={18} /> {t.clear}
                  </button>
                </div>
                <button onClick={checkAnswer} disabled={selectedCells.length === 0} className={`w-full py-3 rounded-xl font-bold text-xl flex items-center justify-center gap-2 ${selectedCells.length > 0 ? 'bg-green-500 hover:bg-green-600 text-white' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}>
                  <Check size={20} /> {t.checkAnswer}
                </button>
                <button onClick={skipWord} className="w-full py-2 rounded-xl font-bold flex items-center justify-center gap-2 bg-gray-500 hover:bg-gray-600 text-white">
                  <SkipForward size={18} /> {t.nextWord}
                </button>
              </div>
            </div>

            {/* Center Panel - Game Grid */}
            <div className={`lg:col-span-2 bg-white rounded-2xl p-5 shadow-lg ${shake ? 'animate-shake' : ''}`}>
              {/* Hint Panel */}
              {showHintPanel && aiHints.length > 0 && (
                <div className="bg-blue-100 rounded-xl p-4 mb-4">
                  <h4 className="font-bold text-blue-900 text-center mb-2">💡 {t.aiHint} 🤖</h4>
                  {aiHints.map((hint, idx) => (
                    <div key={idx} className="bg-white rounded-lg p-2 mb-2 text-blue-800 text-sm">{hint}</div>
                  ))}
                </div>
              )}

              <h3 className="text-2xl font-black text-center mb-4">✨ {t.findSecretWord} ✨</h3>
              <div className="bg-blue-50 rounded-xl p-3 mb-4 text-center text-sm">{t.instructions}</div>

              <div className="flex justify-center p-4">
                <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${levelConfig[level].gridSize}, minmax(0, 80px))` }}>
                  {grid.map((row, rowIdx) => (
                    row.map((cell, colIdx) => {
                      const cellKey = `${rowIdx}-${colIdx}`;
                      const isSelected = selectedCells.includes(cellKey);
                      const selectionIndex = selectedCells.indexOf(cellKey);
                      //selected letter numbering {String.fromCharCode(65 + selectionIndex)}A,B..
                      return (
                        <button
                          key={cellKey}
                          onClick={() => toggleCell(rowIdx, colIdx)}
                          className={`aspect-square flex items-center justify-center text-2xl font-bold rounded-xl border-2 relative transition-all ${
                            isSelected 
                              ? 'bg-blue-500 text-white border-yellow-400 scale-105' 
                              : 'bg-white text-gray-800 border-gray-300 hover:bg-blue-50'
                          }`}
                        >
                          {cell.letter}
                          {isSelected && (
                            <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-500 rounded-full text-xs flex items-center justify-center text-white">
                              {selectionIndex + 1}
                            </div>
                          )}
                        </button>
                      );
                    })
                  ))}
                </div>
              </div>

              <div className="mt-4 p-4 bg-blue-50 rounded-xl">
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div className="text-center bg-white rounded-lg p-2">
                    <div className="text-xs text-gray-600">{t.secretWordText}</div>
                    <div className="font-black text-xl">{puzzle ? puzzle.syllables.length : 0}</div>
                  </div>
                  <div className="text-center bg-white rounded-lg p-2">
                    <div className="text-xs text-gray-600">{t.selectedLetters}</div>
                    <div className={`font-black text-xl ${selectedCells.length === puzzle?.syllables.length ? 'text-green-500' : 'text-blue-500'}`}>{selectedCells.length}</div>
                  </div>
                  <div className="text-center bg-white rounded-lg p-2">
                    <div className="text-xs text-gray-600">{t.attempts}</div>
                    <div className="font-black text-xl">{attempts}</div>
                  </div>
                </div>
                <div className="text-center text-sm text-blue-800">{t.note}</div>
              </div>
            </div>
          </div>

          {/* Feedback */}
          {feedback && (
            <div className={`mt-4 p-3 rounded-xl text-center font-bold ${feedback.type === 'success' ? 'bg-green-100 text-green-800' : feedback.type === 'error' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
              {feedback.message}
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
        @keyframes progress { 0% { width: 0%; } 100% { width: 100%; } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-10px); } 75% { transform: translateX(10px); } }
        .animate-float { animation: float 3s ease-in-out infinite; }
        .animate-progress { animation: progress 2s ease-in-out infinite; }
        .animate-shake { animation: shake 0.5s ease-in-out; }
      `}</style>
    </div>
  );
};

export default SinhalaWordPuzzleGame;