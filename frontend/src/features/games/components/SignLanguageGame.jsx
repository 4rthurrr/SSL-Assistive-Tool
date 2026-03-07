import React, { useState, useEffect } from 'react';
import { Award, RotateCcw, CheckCircle } from 'lucide-react';

// Game data - each word has ONE correct sign pair, mixed with other word signs
const gameWords = [
  { word: "එක", pronunciation: "eka", meaning: "One", sign: "☝️" },
  { word: "දෙක", pronunciation: "deka", meaning: "Two", sign: "✌️" },
  { word: "තුන", pronunciation: "thuna", meaning: "Three", sign: "🤟" },
  { word: "හතර", pronunciation: "hathara", meaning: "Four", sign: "🖖" },
  { word: "පහ", pronunciation: "paha", meaning: "Five", sign: "✋" },
  { word: "හය", pronunciation: "haya", meaning: "Six", sign: "🤙" }
];

const SignLanguageGame = () => {
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [cards, setCards] = useState([]);
  const [flippedCards, setFlippedCards] = useState([]);
  const [foundPairs, setFoundPairs] = useState([]);
  const [score, setScore] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [gameStarted, setGameStarted] = useState(false);
  const [gameCompleted, setGameCompleted] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [wrongAttempt, setWrongAttempt] = useState(false);

  // Initialize game with all cards shuffled
  const initializeGame = () => {
    const allCards = [];
    
    // Create 2 cards for each word (pairs)
    gameWords.forEach((wordData, index) => {
      allCards.push(
        { id: index, wordIndex: index, sign: wordData.sign, word: wordData.word },
        { id: index + 100, wordIndex: index, sign: wordData.sign, word: wordData.word }
      );
    });

    // Shuffle all cards
    const shuffled = allCards.sort(() => Math.random() - 0.5);
    setCards(shuffled);
    setFlippedCards([]);
    setFoundPairs([]);
  };

  useEffect(() => {
    if (gameStarted) {
      initializeGame();
    }
  }, [gameStarted]);

  const handleCardClick = (cardIndex) => {
    const card = cards[cardIndex];
    
    // Prevent clicking if: already flipped, already found, or 2 cards are flipped
    if (flippedCards.includes(cardIndex) || 
        foundPairs.includes(card.wordIndex) || 
        flippedCards.length === 2) {
      return;
    }

    // Vibration feedback
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }

    const newFlipped = [...flippedCards, cardIndex];
    setFlippedCards(newFlipped);

    if (newFlipped.length === 2) {
      setAttempts(attempts + 1);
      checkMatch(newFlipped);
    }
  };

  const checkMatch = (flippedIndices) => {
    const [firstIndex, secondIndex] = flippedIndices;
    const firstCard = cards[firstIndex];
    const secondCard = cards[secondIndex];
    const currentWord = gameWords[currentWordIndex];

    setTimeout(() => {
      // Check if both cards match AND belong to the current word
      if (firstCard.wordIndex === secondCard.wordIndex && 
          firstCard.wordIndex === currentWordIndex) {
        // CORRECT! Found the right pair for current word
        setFoundPairs([...foundPairs, currentWordIndex]);
        setScore(score + 10);
        setShowCelebration(true);
        
        // Success vibration
        if (navigator.vibrate) {
          navigator.vibrate([100, 50, 100, 50, 100]);
        }

        setTimeout(() => setShowCelebration(false), 1000);

        // Move to next word
        setTimeout(() => {
          if (currentWordIndex + 1 < gameWords.length) {
            setCurrentWordIndex(currentWordIndex + 1);
          } else {
            setGameCompleted(true);
          }
        }, 1500);
      } else {
        // WRONG! Either cards don't match or not the current word
        setWrongAttempt(true);
        
        // Error vibration
        if (navigator.vibrate) {
          navigator.vibrate(300);
        }
        
        setTimeout(() => setWrongAttempt(false), 500);
      }
      setFlippedCards([]);
    }, 1000);
  };

  const startGame = () => {
    setGameStarted(true);
    setScore(0);
    setAttempts(0);
    setCurrentWordIndex(0);
    setGameCompleted(false);
  };

  const resetGame = () => {
    setGameStarted(false);
    setScore(0);
    setAttempts(0);
    setCurrentWordIndex(0);
    setGameCompleted(false);
  };

  if (!gameStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-400 via-blue-400 to-yellow-300 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="text-6xl mb-4">🤟</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">සංඥා භාෂා ක්‍රීඩාව</h1>
          <h2 className="text-xl text-gray-600 mb-6">Sign Language Matching Game</h2>
          <div className="bg-blue-50 rounded-xl p-4 mb-6 text-left">
            <p className="text-sm text-gray-700 mb-2"><strong>How to Play:</strong></p>
            <p className="text-sm text-gray-600">
              1. See the Sinhala word at the top<br/>
              2. Find and match the TWO cards with the same sign for that word<br/>
              3. Match all words to win!
            </p>
          </div>
          <button
            onClick={startGame}
            className="bg-gradient-to-r from-sky-500 to-blue-500 text-white px-8 py-4 rounded-full text-xl font-bold hover:scale-105 transform transition shadow-lg"
          >
            ආරම්භ කරන්න / Start Game
          </button>
        </div>
      </div>
    );
  }

  if (gameCompleted) {
    const accuracy = attempts > 0 ? Math.round((foundPairs.length / attempts) * 100) : 0;
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-400 via-blue-400 to-sky-400 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-gray-800 mb-4">ඉවරයි! Game Complete!</h2>
          <div className="bg-gradient-to-r from-yellow-200 to-yellow-300 rounded-2xl p-6 mb-6">
            <div className="text-5xl font-bold text-gray-800 mb-2">{score}</div>
            <div className="text-gray-700">Total Points</div>
          </div>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-100 rounded-xl p-4">
              <div className="text-2xl font-bold text-blue-600">{attempts}</div>
              <div className="text-sm text-gray-600">Attempts</div>
            </div>
            <div className="bg-green-100 rounded-xl p-4">
              <div className="text-2xl font-bold text-green-600">{accuracy}%</div>
              <div className="text-sm text-gray-600">Accuracy</div>
            </div>
          </div>
          <button
            onClick={resetGame}
            className="bg-gradient-to-r from-green-500 to-blue-500 text-white px-8 py-4 rounded-full text-xl font-bold hover:scale-105 transform transition shadow-lg flex items-center justify-center mx-auto"
          >
            <RotateCcw className="mr-2" size={24} />
            නැවත ක්‍රීඩා කරන්න / Play Again
          </button>
        </div>
      </div>
    );
  }

  const currentWord = gameWords[currentWordIndex];

  return (
    <div className={`min-h-screen bg-gradient-to-br from-sky-300 via-blue-400 to-yellow-200 p-2 transition-all ${
      wrongAttempt ? 'animate-shake' : ''
    }`}>
      {/* Celebration overlay */}
      {showCelebration && (
        <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-50">
          <div className="text-8xl animate-bounce">⭐</div>
        </div>
      )}

      <div className="max-w-5xl mx-auto h-[85vh] flex flex-col justify-between">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-4 mb-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-2">
              <Award className="text-yellow-500" size={24} />
              <span className="text-2xl font-bold text-gray-800">{score}</span>
            </div>
            <div className="text-sm text-gray-600">
              Word {currentWordIndex + 1} of {gameWords.length}
            </div>
            <div className="text-sm text-gray-600">
              Attempts: {attempts}
            </div>
          </div>
          
          {/* Current Word Display */}
          <div className={`bg-gradient-to-r from-sky-100 to-blue-100 rounded-xl p-6 text-center transition-all ${
            wrongAttempt ? 'ring-4 ring-red-500' : ''
          }`}>
            <div className="text-sm text-gray-500 mb-2">Find the matching pair for:</div>
            <div className="text-6xl font-bold text-gray-800 mb-2">{currentWord.word}</div>
            <div className="text-2xl text-gray-600">{currentWord.pronunciation}</div>
            <div className="text-lg text-gray-500">({currentWord.meaning})</div>
          </div>

          {/* Progress - Words found */}
          <div className="mt-4 flex justify-center gap-2 flex-wrap">
            {gameWords.map((word, index) => (
              <div 
                key={index}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
                  foundPairs.includes(index) 
                    ? 'bg-green-500 text-white' 
                    : index === currentWordIndex
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {foundPairs.includes(index) && <CheckCircle className="inline mr-1" size={14} />}
                {word.word}
              </div>
            ))}
          </div>
        </div>

        {/* Card Grid - 4x3 grid for 12 cards (6 pairs) */}
        <div className="grid grid-cols-4 gap-2 flex-1 place-items-center">
          {cards.map((card, index) => {
            const isFlipped = flippedCards.includes(index);
            const isFound = foundPairs.includes(card.wordIndex);

            return (
             <div
  key={index}
  onClick={() => handleCardClick(index)}
  className={`aspect-square cursor-pointer transition-all duration-300 transform ${
    isFound ? 'scale-90 opacity-30' : 'hover:scale-105'
  } ${wrongAttempt && isFlipped ? 'animate-wiggle' : ''}`}
  style={{ width: '100%', maxWidth: '100px', minWidth: '70px' }} // ✅ Add this line
>


              <div
  className="relative w-full h-full transition-transform duration-500 transform-style-preserve-3d"
  style={{ transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
>

                  {/* Card Back */}
  <div className="absolute inset-0 bg-gradient-to-br from-sky-500 to-blue-600 rounded-xl shadow-lg flex items-center justify-center backface-hidden">
    <div className="text-4xl">❓</div>
  </div>
                  
                  {/* Card Front */}
                 {/* Card Front */}
  <div className={`absolute inset-0 bg-white rounded-xl shadow-lg flex flex-col items-center justify-center backface-hidden ${isFound ? 'bg-green-100' : ''}`}
       style={{ transform: 'rotateY(180deg)' }}>
    <div className="text-5xl mb-1">{card.sign}</div>
    <div className="text-xs text-gray-500">{card.word}</div>
  </div>
</div>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="mt-6 bg-white rounded-full h-4 overflow-hidden shadow-inner">
          <div 
            className="bg-gradient-to-r from-green-400 to-blue-500 h-full transition-all duration-500 flex items-center justify-end pr-2"
            style={{ width: `${(foundPairs.length / gameWords.length) * 100}%` }}
          >
            {foundPairs.length > 0 && (
              <span className="text-xs font-bold text-white">
                {foundPairs.length}/{gameWords.length}
              </span>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        @keyframes wiggle {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-5deg); }
          75% { transform: rotate(5deg); }
        }
        .animate-shake {
          animation: shake 0.5s;
        }
        .animate-wiggle {
          animation: wiggle 0.5s;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
        .backface-hidden {
          backface-visibility: hidden;
          -webkit-backface-visibility: hidden;
}

        .transform-style-preserve-3d {
           transform-style: preserve-3d;
}

      `}</style>
    </div>
  );
};

export default SignLanguageGame;