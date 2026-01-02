import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Play, Trophy, Heart, Lightbulb, RefreshCw, Home, 
  Sparkles, Target, Award, ChevronRight, TrendingUp
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
  
  // Puzzle State
  const [puzzle, setPuzzle] = useState(null);
  const [grid, setGrid] = useState([]);
  const [selectedCells, setSelectedCells] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [showVideo, setShowVideo] = useState(true);
  const [aiHints, setAiHints] = useState([]);
  const [showHintPanel, setShowHintPanel] = useState(false);
  
  // User tracking: prefer authenticated MongoDB user id stored by GameUserForm
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

  // Level configurations
  const levelConfig = {
    basic: {
      name: 'Basic',
      nameS: 'මූලික',
      description: 'පිල්ලම් නැති සරල වචන',
      descriptionE: 'Simple words without vowel signs',
      gridSize: 6,
      color: 'from-green-400 to-emerald-500',
      icon: '🟢'
    },
    easy: {
      name: 'Easy',
      nameS: 'පහසු',
      description: 'සරල වචන (2-3 අකුරු)',
      descriptionE: 'Simple words (2-3 letters)',
      gridSize: 7,
      color: 'from-blue-400 to-cyan-500',
      icon: '🔵'
    },
    medium: {
      name: 'Medium',
      nameS: 'මධ්‍යම',
      description: 'මධ්‍යම වචන (4-6 අකුරු)',
      descriptionE: 'Medium words (4-6 letters)',
      gridSize: 8,
      color: 'from-orange-400 to-amber-500',
      icon: '🟠'
    },
    hard: {
      name: 'Hard',
      nameS: 'දුෂ්කර',
      description: 'දුෂ්කර වචන (7+ අකුරු)',
      descriptionE: 'Hard words (7+ letters)',
      gridSize: 10,
      color: 'from-red-500 to-pink-600',
      icon: '🔴'
    }
  };

  // ============= GAME FUNCTIONS =============

  // Start game function - THIS IS MISSING!
  const startGame = (selectedLevel) => {
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
  };

  // Generate random Sinhala letter - Add this function
  const getRandomLetter = () => {
    const letters = ['අ','ආ','ඉ','ඊ','උ','ඌ','එ','ඒ','ඔ','ක','ග','ච','ජ','ට','ඩ','ත','ද','න','ප','බ','ම','ය','ර','ල','ව','ශ','ස','හ'];
    return letters[Math.floor(Math.random() * letters.length)];
  };

  // Create grid with hidden word - Add this function
  const createGrid = (size, syllables) => {
    const newGrid = Array(size).fill(null).map(() => 
      Array(size).fill(null).map(() => ({
        letter: getRandomLetter(),
        isTarget: false
      }))
    );

    // Place target word horizontally in random position
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

  // Load puzzle from API - Add this function
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
        // Split word into syllables
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
      } else {
        console.error('Failed to load puzzle:', data.error);
        setFeedback({ type: 'error', message: 'Failed to load puzzle. Try again.' });
      }
    } catch (error) {
      console.error('Error loading puzzle:', error);
      setFeedback({ type: 'error', message: 'Failed to connect to server' });
    } finally {
      setLoading(false);
    }
  };

  // Load puzzle when game starts
  useEffect(() => {
    if (gameState === 'playing' && puzzle === null) {
      loadPuzzle();
    }
  }, [gameState, round, puzzle]);

  // Check if cells are adjacent
  const areAdjacent = (cell1, cell2) => {
    const [r1, c1] = cell1.split('-').map(Number);
    const [r2, c2] = cell2.split('-').map(Number);
    const rowDiff = Math.abs(r1 - r2);
    const colDiff = Math.abs(c1 - c2);
    return rowDiff <= 1 && colDiff <= 1 && !(rowDiff === 0 && colDiff === 0);
  };

  // Validate path connectivity
  const isValidPath = () => {
    if (selectedCells.length < 2) return true;
    
    for (let i = 1; i < selectedCells.length; i++) {
      if (!areAdjacent(selectedCells[i - 1], selectedCells[i])) {
        return false;
      }
    }
    return true;
  };

  // Toggle cell selection
  const toggleCell = (row, col) => {
    const cellKey = `${row}-${col}`;
    
    if (selectedCells.includes(cellKey)) {
      setSelectedCells(selectedCells.filter(k => k !== cellKey));
    } else {
      setSelectedCells([...selectedCells, cellKey]);
    }
  };

  // Record attempt
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
      
      if (data.success && data.show_hint && data.hints.length > 0) {
        setAiHints(data.hints);
        setShowHintPanel(true);
      }
    } catch (error) {
      console.error('Error recording attempt:', error);
    }
  };

  // Check answer
  const checkAnswer = async () => {
    if (!isValidPath()) {
      setFeedback({ type: 'error', message: '❌ Letters must be connected!' });
      setTimeout(() => setFeedback(null), 1500);
      return;
    }

    const selectedLetters = selectedCells.map(key => {
      const [r, c] = key.split('-').map(Number);
      return grid[r][c].letter;
    });

    const isCorrect = 
      selectedLetters.length === puzzle.syllables.length &&
      selectedLetters.every((letter, i) => letter === puzzle.syllables[i]);

    await recordAttempt(isCorrect);

    if (isCorrect) {
      setFeedback({ type: 'success', message: '✅ හරි! Correct!' });
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
      setFeedback({ type: 'error', message: '❌ වැරදියි! Wrong!' });
      const newLives = lives - 1;
      setLives(newLives);
      
      if (newLives <= 0) {
        setTimeout(() => setGameState('gameover'), 1500);
      } else {
        setTimeout(() => {
          setSelectedCells([]);
          setFeedback(null);
        }, 1500);
      }
    }
  };

  // Use hint
  const useHint = () => {
    if (hintsRemaining > 0 && puzzle) {
      setHintsRemaining(hintsRemaining - 1);
      setAiHints([`💡 First syllable: "${puzzle.syllables[0]}"`]);
      setShowHintPanel(true);
    }
  };

  // Restart game
  const restartGame = () => {
    setGameState('menu');
    setPuzzle(null);
    setFeedback(null);
    setAiHints([]);
    setShowHintPanel(false);
  };

  // ============= COMPONENTS =============

  // Menu Screen - Responsive Version
  if (gameState === 'menu') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 p-4 overflow-y-auto">
        {/* Fixed Background Elements */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-10 w-40 h-40 md:w-64 md:h-64 bg-yellow-400 rounded-full blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute bottom-10 right-10 w-40 h-40 md:w-80 md:h-80 bg-pink-400 rounded-full blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute top-1/4 left-1/4 w-24 h-24 md:w-40 md:h-40 bg-blue-400 rounded-full blur-3xl opacity-15 animate-bounce"></div>
        </div>

        {/* Main Content Container */}
        <div className="relative max-w-4xl mx-auto pt-6 pb-12">
          {/* Header Section */}
          <div className="text-center mb-6">
            <div className="text-5xl md:text-6xl mb-2 animate-bounce">🤟</div>
            <h1 className="text-3xl md:text-4xl font-black text-white mb-1 drop-shadow-lg bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">
              සංඥා විදු ප්‍රහේලිකා
            </h1>
            <p className="text-lg md:text-xl text-yellow-300 font-bold mb-2">
              Sinhala Sign Language Puzzle
            </p>
            <p className="text-white/80 text-sm max-w-md mx-auto">
              Experience the beauty of sign language through interactive puzzles
            </p>
          </div>

          {/* Levels Grid - More Compact */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
            {Object.entries(levelConfig).map(([key, config]) => (
              <button
                key={key}
                onClick={() => startGame(key)} 
                className={`bg-gradient-to-r ${config.color} text-white p-4 rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-300 border border-white/20`}
              >
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{config.icon}</div>
                  <div className="text-left flex-1">
                    <div className="font-bold text-lg">{config.name}</div>
                    <div className="text-sm font-medium opacity-90">{config.nameS}</div>
                    <div className="text-xs opacity-75 mt-1">{config.description}</div>
                  </div>
                  <div className="text-2xl opacity-70">→</div>
                </div>
              </button>
            ))}
          </div>

          {/* Game Selection Button */}
          <div className="mb-6">
            <button
              onClick={() => navigate('/gameselection')}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-bold py-3 px-4 rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-300 border-2 border-cyan-300/30"
            >
              <div className="flex items-center justify-center gap-2">
                <span className="text-xl">🎯</span>
                <div className="text-center">
                  <div className="font-bold">Explore More Games</div>
                  <div className="text-xs opacity-90">Multiple game modes & challenges</div>
                </div>
                <span className="text-xl">➡️</span>
              </div>
            </button>
          </div>

          {/* Quick Stats */}
          <div className="mb-6">
            <div className="bg-white/15 backdrop-blur-sm rounded-xl p-4 border border-white/30">
              <h3 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
                📊 Quick Stats
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center bg-white/10 rounded-lg p-2">
                  <div className="text-lg font-bold text-yellow-300">50+</div>
                  <div className="text-xs text-white/80">Words</div>
                </div>
                <div className="text-center bg-white/10 rounded-lg p-2">
                  <div className="text-lg font-bold text-green-300">4</div>
                  <div className="text-xs text-white/80">Levels</div>
                </div>
                <div className="text-center bg-white/10 rounded-lg p-2">
                  <div className="text-lg font-bold text-blue-300">∞</div>
                  <div className="text-xs text-white/80">Puzzles</div>
                </div>
              </div>
            </div>
          </div>

          {/* How to Play - More Compact */}
          <div className="mb-6">
            <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 backdrop-blur-sm rounded-xl p-4 border border-purple-300/30">
              <h3 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
                🎮 How to Play
              </h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2 text-xs text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center">🎥</div>
                  <span>Watch video</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center">🔍</div>
                  <span>Find word</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center">👆</div>
                  <span>Tap letters</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center">⭐</div>
                  <span>Win stars</span>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center pt-4 border-t border-white/20">
            <div className="flex flex-wrap justify-center gap-3 mb-2">
              <span className="text-white/70 text-xs">🎮 Interactive</span>
              <span className="text-white/70 text-xs">🌟 Progress</span>
              <span className="text-white/70 text-xs">🤖 AI Hints</span>
            </div>
            <p className="text-white/50 text-xs">
              Designed for all ages • Developed with ❤️
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-3 animate-spin">⏳</div>
          <p className="text-white text-xl font-bold">Loading puzzle...</p>
        </div>
      </div>
    );
  }

  // Game Over Screen
  if (gameState === 'gameover') {
    const stars = score >= 800 ? 3 : score >= 500 ? 2 : score >= 200 ? 1 : 0;
    const message = stars === 3 ? 'Outstanding! 🌟' : 
                    stars === 2 ? 'Great Job! 👏' :
                    stars === 1 ? 'Good Try! 💪' :
                    'Keep Practicing! 📚';

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-500 flex items-center justify-center p-4">
        <div className="bg-white/20 backdrop-blur-2xl border border-white/40 rounded-3xl shadow-2xl p-8 max-w-md w-full text-center">
          <Trophy className="w-16 h-16 text-yellow-300 mx-auto mb-3" />
          <h2 className="text-4xl font-black text-white mb-4">Game Complete!</h2>
          
          <div className="bg-white/30 backdrop-blur-sm rounded-2xl p-6 mb-4">
            <div className="text-6xl font-black text-yellow-300 mb-3">{score}</div>
            <div className="text-3xl mb-2">
              {'⭐'.repeat(stars)}{'☆'.repeat(3 - stars)}
            </div>
            <p className="text-white text-xl font-bold">{message}</p>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-white/20 rounded-xl p-3">
              <div className="text-2xl mb-1">🎯</div>
              <div className="text-white text-xs font-bold">Level</div>
              <div className="text-yellow-300 text-lg font-bold capitalize">{level}</div>
            </div>
            <div className="bg-white/20 rounded-xl p-3">
              <div className="text-2xl mb-1">🏆</div>
              <div className="text-white text-xs font-bold">Rounds</div>
              <div className="text-yellow-300 text-lg font-bold">{round}/{totalRounds}</div>
            </div>
          </div>

          <button
            onClick={restartGame}
            className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-black px-6 py-3 rounded-xl shadow-xl transform hover:scale-105 transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-5 h-5" /> Play Again
          </button>
        </div>
      </div>
    );
  }

  // Playing State - The actual game UI
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-3">
      <div className="max-w-6xl mx-auto">
        {/* Compact Header */}
        <div className="bg-white/20 backdrop-blur-xl rounded-2xl shadow-xl p-3 mb-3 flex justify-between items-center">
          <button
            onClick={restartGame}
            className="bg-white/30 hover:bg-white/50 text-white font-bold px-3 py-1.5 rounded-lg flex items-center gap-1 text-sm"
          >
            <Home className="w-4 h-4" /> Menu
          </button>

          <div className="flex gap-4">
            <div className="text-center">
              <Trophy className="w-5 h-5 text-yellow-300 mx-auto" />
              <div className="text-xl font-black text-white">{score}</div>
            </div>
            <div className="text-center">
              <Heart className="w-5 h-5 text-red-300 mx-auto" />
              <div className="text-xl font-black text-white">{lives}</div>
            </div>
            <div className="text-center">
              <Lightbulb className="w-5 h-5 text-yellow-300 mx-auto" />
              <div className="text-xl font-black text-white">{hintsRemaining}</div>
            </div>
            <div className="text-center">
              <Target className="w-5 h-5 text-green-300 mx-auto" />
              <div className="text-xl font-black text-white">{round + 1}/{totalRounds}</div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-3">
          {/* Left Panel */}
          <div className="bg-white/10 backdrop-blur-2xl rounded-2xl shadow-xl p-4 space-y-3">
            {/* Video */}
            <div className="bg-gradient-to-br from-purple-600/30 to-pink-600/30 rounded-xl p-3">
              <p className="text-center text-white font-bold mb-2 flex items-center justify-center gap-2 text-sm">
                <Play className="w-4 h-4" /> Sign Video
              </p>
              {puzzle && puzzle.video_url ? (
                <video
                  key={puzzle.word}
                  src={`http://localhost:5001${puzzle.video_url}`}
                  autoPlay
                  loop
                  muted
                  className="w-full h-36 object-cover rounded-lg border-2 border-white/30"
                  onError={(e) => console.error('Video error:', e)}
                />
              ) : (
                <div className="w-full h-36 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center border-2 border-white/30">
                  <div className="text-5xl animate-bounce">🤟</div>
                </div>
              )}
            </div>

            {/* Word Info */}
            {puzzle && (
              <div className="bg-white/25 backdrop-blur-sm rounded-xl p-3 border-2 border-white/30">
                <p className="text-white/90 text-xs uppercase tracking-wider mb-2 text-center font-bold">
                  🎯 Find This Word
                </p>
                <div className="bg-white/20 rounded-lg p-2 mb-2">
                  <p className="text-3xl font-black text-white text-center">{puzzle.word}</p>
                </div>
                <p className="text-white/90 text-xs text-center mb-1">
                  📝 {puzzle.syllables.join(' · ')}
                </p>
                <p className="text-white/80 text-xs bg-white/10 rounded-lg py-1 px-2 text-center">
                  {puzzle.english}
                </p>
              </div>
            )}

            {/* AI Hints */}
            {showHintPanel && aiHints.length > 0 && (
              <div className="bg-yellow-100/90 border-2 border-yellow-400 rounded-xl p-3">
                <p className="font-bold text-yellow-900 mb-2 text-center text-sm">💡 Hints</p>
                <div className="space-y-1.5">
                  {aiHints.map((hint, idx) => (
                    <p key={idx} className="text-xs text-yellow-900 bg-white/50 rounded-lg p-2">
                      {hint}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Feedback */}
            {feedback && (
              <div className={`p-3 rounded-xl text-center font-bold border-2 text-sm ${
                feedback.type === 'success'
                  ? 'bg-green-500/90 text-white border-green-300'
                  : 'bg-red-500/90 text-white border-red-300'
              }`}>
                {feedback.message}
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              <button
                onClick={useHint}
                disabled={hintsRemaining === 0}
                className={`w-full py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 text-sm ${
                  hintsRemaining > 0
                    ? 'bg-gradient-to-r from-yellow-400 to-orange-400 hover:from-yellow-500 hover:to-orange-500 text-white border-2 border-yellow-300'
                    : 'bg-gray-400/50 text-gray-300 cursor-not-allowed'
                }`}
              >
                <Lightbulb className="w-4 h-4" /> Use Hint ({hintsRemaining})
              </button>

              <button
                onClick={checkAnswer}
                disabled={selectedCells.length === 0}
                className={`w-full py-3 rounded-xl font-bold text-base flex items-center justify-center gap-2 ${
                  selectedCells.length > 0
                    ? 'bg-gradient-to-r from-green-400 to-emerald-500 hover:from-green-500 hover:to-emerald-600 text-white border-2 border-green-300 animate-pulse'
                    : 'bg-gray-400/50 text-gray-300 cursor-not-allowed'
                }`}
              >
                <Award className="w-5 h-5" /> Check Answer
              </button>
            </div>
          </div>

          {/* Grid Panel */}
          <div className="lg:col-span-2 bg-white/10 backdrop-blur-2xl rounded-2xl shadow-xl p-4">
            <h3 className="text-xl font-black text-white text-center mb-4 flex items-center justify-center gap-2">
              <Sparkles className="w-6 h-6" />
              Find the Hidden Word
              <Sparkles className="w-6 h-6" />
            </h3>

            <div className="flex justify-center mb-4">
              <div
                className="grid gap-1.5"
                style={{
                  gridTemplateColumns: `repeat(${levelConfig[level].gridSize}, minmax(0, 48px))`
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
                        className={`w-12 h-12 flex items-center justify-center text-xl font-black rounded-xl transition-all duration-300 border-2 relative ${
                          isSelected
                            ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white scale-105 border-white/50 shadow-xl z-10'
                            : 'bg-white/90 hover:bg-white text-gray-800 hover:scale-105 border-white/50 shadow-md'
                        }`}
                      >
                        {cell.letter}
                        {isSelected && (
                          <div className="absolute -top-1 -right-1 w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center text-xs font-black text-purple-900 border-2 border-white">
                            {selectionIndex + 1}
                          </div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-3 border border-white/30">
              <p className="text-white text-center text-xs font-semibold mb-2">
                💫 Tap letters in sequence • Adjacent cells only
              </p>
              <div className="flex justify-center gap-3 text-xs">
                <span className="bg-purple-500/50 px-2 py-1 rounded-full font-bold text-white">
                  Target: {puzzle ? puzzle.syllables.length : 0}
                </span>
                <span className="bg-pink-500/50 px-2 py-1 rounded-full font-bold text-white">
                  Selected: {selectedCells.length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SinhalaWordPuzzleGame;