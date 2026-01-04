import React, { useState, useEffect } from 'react';
import { 
  Star, Trophy, RotateCcw, ArrowRight, Home, Lock, 
  Target, Award, ChevronRight, CheckCircle, Languages
} from 'lucide-react';

const SignLanguageGame = () => {
  const [gameState, setGameState] = useState('map');
  const [currentLevel, setCurrentLevel] = useState(1);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedWords, setSelectedWords] = useState([]);
  const [score, setScore] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [completedLevels, setCompletedLevels] = useState([1]);
  const [showLevelComplete, setShowLevelComplete] = useState(false);
  const [levelStars, setLevelStars] = useState({1: 2, 2: 1});
  const [hoveredLevel, setHoveredLevel] = useState(null);
  const [language, setLanguage] = useState('en');

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
      finish: 'Finish',
      tryAgain: 'Try Again',
      levelMap: 'Level Map',
      excellent: 'Excellent!',
      keepTrying: 'Keep Trying!',
      correctAnswer: 'Correct Answer:',
      yourScore: 'Your Score',
      nextLevel: 'Next Level',
      levelComplete: 'Level Complete!'
    },
    si: {
      title: 'සංඥා භාෂා වික්‍රමය',
      subtitle: 'සින්හල සංඥා භාෂාව ඉගෙන ගන්න',
      yourProgress: 'ඔබේ ප්‍රගතිය',
      levelsCompleted: 'මට්ටම් සම්පූර්ණ කළා',
      totalStars: 'මුළු තරු',
      progress: 'ප්‍රගතිය',
      home: 'මුල් පිටුව',
      questions: 'ප්‍රශ්න',
      yourAnswer: 'ඔබේ පිළිතුර',
      selectWords: 'වචන තෝරන්න',
      words: 'වචන',
      checkAnswer: 'පරීක්ෂා කරන්න',
      nextQuestion: 'ඊළඟ ප්‍රශ්නය',
      finish: 'අවසන්',
      tryAgain: 'නැවත උත්සාහ කරන්න',
      levelMap: 'මට්ටම් සිතියම',
      excellent: 'සුපිරියි!',
      keepTrying: 'උත්සාහ කරන්න!',
      correctAnswer: 'නිවැරදි පිළිතුර:',
      yourScore: 'ඔබේ ලකුණු',
      nextLevel: 'ඊළඟ මට්ටම',
      levelComplete: 'මට්ටම සම්පූර්ණයි!'
    }
  };

  const t = translations[language];

  const levels = [
    {
      level: 1,
      questions: 3,
      title: { en: 'Basic Sentences', si: 'මූලික වාක්‍ය' },
      subtitle: 'Basic Sentences',
      color: 'from-emerald-400 to-green-500',
      icon: '🌱',
      difficulty: { en: 'Easy', si: 'පහසු' },
      sentences: [
        { sinhala: 'මම පාඩම් කරනවා', english: 'I am studying', words: ['මම', 'පාඩම්', 'කරනවා'] },
        { sinhala: 'මම බත් කනවා', english: 'I am eating rice', words: ['මම', 'බත්', 'කනවා'] },
        { sinhala: 'අම්මා ගෙදර', english: 'Mother is at home', words: ['අම්මා', 'ගෙදර'] }
      ]
    },
    {
      level: 2,
      questions: 4,
      title: { en: 'Daily Questions', si: 'දෛනික ප්‍රශ්න' },
      subtitle: 'Daily Questions',
      color: 'from-blue-400 to-indigo-500',
      icon: '🔍',
      difficulty: { en: 'Medium', si: 'මධ්‍යම' },
      sentences: [
        { sinhala: 'අද පාසල් ගියාද', english: 'Did you go to school today?', words: ['අද', 'පාසල්', 'ගියාද'] },
        { sinhala: 'කොහෙද යන්නේ', english: 'Where are you going?', words: ['කොහෙද', 'යන්නේ'] },
        { sinhala: 'දැන් වේලාව කීයද', english: 'What time is it now?', words: ['දැන්', 'වේලාව', 'කීයද'] },
        { sinhala: 'ඔයාට හුරුපුරුදුද', english: 'Are you familiar?', words: ['ඔයාට', 'හුරුපුරුදුද'] }
      ]
    },
    {
      level: 3,
      questions: 5,
      title: { en: 'Complex Sentences', si: 'සංකීර්ණ වාක්‍ය' },
      subtitle: 'Complex Sentences',
      color: 'from-purple-400 to-pink-500',
      icon: '🚀',
      difficulty: { en: 'Hard', si: 'දුෂ්කර' },
      sentences: [
        { sinhala: 'මම උදේ ආහාරය කෑවා', english: 'I ate breakfast', words: ['මම', 'උදේ', 'ආහාරය', 'කෑවා'] },
        { sinhala: 'ඔබේ නම මොකක්ද', english: 'What is your name?', words: ['ඔබේ', 'නම', 'මොකක්ද'] }
      ]
    }
  ];

  const currentLevelData = levels[currentLevel - 1];
  const currentSentence = currentLevelData?.sentences[currentQuestion];
  
  const shuffleArray = (array) => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };

  const [shuffledWords, setShuffledWords] = useState([]);

  useEffect(() => {
    if (currentSentence) {
      setShuffledWords(shuffleArray(currentSentence.words));
    }
  }, [currentLevel, currentQuestion]);

  const handleWordClick = (word) => {
    if (!showResult) {
      setSelectedWords([...selectedWords, word]);
      setShuffledWords(shuffledWords.filter(w => w !== word));
    }
  };

  const handleSelectedWordClick = (word, index) => {
    if (!showResult) {
      setSelectedWords(selectedWords.filter((_, i) => i !== index));
      setShuffledWords([...shuffledWords, word]);
    }
  };

  const checkAnswer = () => {
    const userAnswer = selectedWords.join(' ');
    const correctAnswer = currentSentence.words.join(' ');
    const correct = userAnswer === correctAnswer;
    
    setIsCorrect(correct);
    setShowResult(true);
    
    if (correct) {
      setScore(score + 1);
    }
  };

  const nextQuestion = () => {
    if (currentQuestion < currentLevelData.questions - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedWords([]);
      setShowResult(false);
      setIsCorrect(false);
    } else {
      const finalScore = score + (isCorrect ? 1 : 0);
      const stars = Math.ceil(finalScore / currentLevelData.questions * 3);
      setLevelStars({...levelStars, [currentLevel]: stars});
      setShowLevelComplete(true);
      if (!completedLevels.includes(currentLevel)) {
        setCompletedLevels([...completedLevels, currentLevel]);
      }
    }
  };

  const startLevel = (level) => {
    if (level === 1 || completedLevels.includes(level - 1)) {
      setCurrentLevel(level);
      setCurrentQuestion(0);
      setScore(0);
      setSelectedWords([]);
      setShowResult(false);
      setIsCorrect(false);
      setShowLevelComplete(false);
      setGameState('playing');
    }
  };

  const resetLevel = () => {
    setCurrentQuestion(0);
    setScore(0);
    setSelectedWords([]);
    setShowResult(false);
    setIsCorrect(false);
    setShowLevelComplete(false);
    setGameState('playing');
  };

  const goToMap = () => {
    setGameState('map');
    setShowLevelComplete(false);
  };

  const nextLevel = () => {
    if (currentLevel < levels.length) {
      setCurrentLevel(currentLevel + 1);
      setCurrentQuestion(0);
      setScore(0);
      setSelectedWords([]);
      setShowResult(false);
      setIsCorrect(false);
      setShowLevelComplete(false);
      setGameState('playing');
    }
  };

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'si' : 'en');
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

  // Level Complete Screen
  if (showLevelComplete) {
    const stars = levelStars[currentLevel] || 0;
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 p-4 flex items-center justify-center">
        <LanguageToggle />
        <div className="bg-white rounded-[40px] shadow-2xl p-12 max-w-md w-full text-center border-8 border-yellow-400">
          <div className="relative inline-block mb-6">
            <Trophy className="w-32 h-32 text-yellow-500 animate-bounce" />
            <div className="absolute -top-4 -right-4 w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center text-3xl animate-pulse">
              🎉
            </div>
          </div>
          
          <h2 className="text-5xl font-black text-emerald-600 mb-3">{t.excellent}</h2>
          <p className="text-2xl font-bold text-gray-700 mb-6">{t.levelComplete}</p>
          
          <div className="flex justify-center gap-3 mb-8 bg-yellow-50 p-6 rounded-3xl">
            {[1, 2, 3].map((star) => (
              <Star
                key={star}
                className={`w-16 h-16 ${star <= stars ? 'fill-yellow-400 text-yellow-500 animate-pulse' : 'text-gray-300'}`}
              />
            ))}
          </div>
          
          <div className="bg-emerald-50 rounded-3xl p-6 mb-8 border-4 border-emerald-200">
            <p className="text-gray-600 mb-2">{t.yourScore}</p>
            <p className="text-5xl font-black text-emerald-600">
              {score + (isCorrect ? 1 : 0)} / {currentLevelData.questions}
            </p>
          </div>
          
          <div className="space-y-3">
            {currentLevel < levels.length && (
              <button
                onClick={nextLevel}
                className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-emerald-600"
              >
                <span>{t.nextLevel}</span>
                <ArrowRight className="w-7 h-7" />
              </button>
            )}
            <button
              onClick={resetLevel}
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-blue-600"
            >
              <RotateCcw className="w-7 h-7" />
              <span>{t.tryAgain}</span>
            </button>
            <button
              onClick={goToMap}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-8 py-5 rounded-3xl font-black text-xl hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-3 border-4 border-purple-600"
            >
              <Home className="w-7 h-7" />
              <span>{t.levelMap}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Level Map Screen
  if (gameState === 'map') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
        <LanguageToggle />
        <div className="max-w-6xl mx-auto">
          
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-block relative mb-6">
              <div className="text-8xl animate-bounce mb-4">🤟</div>
              <div className="absolute -top-2 -right-2 w-12 h-12 bg-yellow-400 rounded-full animate-ping"></div>
            </div>
            
            <h1 className="text-6xl font-black text-gray-800 mb-4">
              {t.title}
            </h1>
            <div className="inline-block bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-3 rounded-full text-xl font-bold shadow-lg">
              {t.subtitle}
            </div>
          </div>

          {/* Main Map Container */}
          <div className="bg-white rounded-[40px] shadow-2xl p-10 mb-10 border-8 border-indigo-100">
            
            {/* Progress Bar */}
            <div className="mb-8 bg-indigo-50 rounded-full p-3">
              <div className="flex justify-between items-center mb-2 px-2">
                <span className="text-lg font-bold text-gray-700">{t.yourProgress}</span>
                <span className="text-2xl font-black text-indigo-600">{Math.round((completedLevels.length / levels.length) * 100)}%</span>
              </div>
              <div className="w-full bg-indigo-200 rounded-full h-6">
                <div 
                  className="bg-gradient-to-r from-emerald-500 to-green-600 h-6 rounded-full transition-all duration-1000 flex items-center justify-end pr-3"
                  style={{ width: `${(completedLevels.length / levels.length) * 100}%` }}
                >
                  <span className="text-white font-bold text-sm">🎯</span>
                </div>
              </div>
            </div>

            {/* Levels Grid */}
            <div className="grid grid-cols-3 gap-8">
              {levels.map((level) => {
                const isLocked = level.level !== 1 && !completedLevels.includes(level.level - 1);
                const stars = levelStars[level.level] || 0;
                
                return (
                  <div 
                    key={level.level}
                    className={`relative transform transition-all duration-300 ${
                      hoveredLevel === level.level ? 'scale-110 z-20' : 'scale-100'
                    }`}
                    onMouseEnter={() => setHoveredLevel(level.level)}
                    onMouseLeave={() => setHoveredLevel(null)}
                  >
                    <button
                      onClick={() => startLevel(level.level)}
                      disabled={isLocked}
                      className={`relative w-full ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      {/* Level Card */}
                      <div className={`bg-gradient-to-br ${level.color} rounded-[35px] p-8 shadow-xl border-8 border-white ${
                        isLocked ? 'opacity-60 grayscale' : 'hover:shadow-2xl'
                      }`}>
                        
                        {/* Level Number Badge */}
                        <div className="absolute -top-4 -right-4 w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center text-2xl font-black text-gray-800 border-4 border-white shadow-lg">
                          {level.level}
                        </div>

                        {/* Icon */}
                        <div className="text-7xl mb-4 text-center">
                          {isLocked ? '🔒' : level.icon}
                        </div>

                        {/* Title */}
                        <h3 className="text-2xl font-black text-white text-center mb-2 drop-shadow-lg">
                          {level.title[language]}
                        </h3>
                        <p className="text-white text-center font-bold mb-4 opacity-90">
                          {level.subtitle}
                        </p>

                        {/* Stars */}
                        {stars > 0 && (
                          <div className="flex justify-center gap-2 mb-3">
                            {[1, 2, 3].map((star) => (
                              <Star
                                key={star}
                                className={`w-8 h-8 ${
                                  star <= stars ? 'fill-yellow-300 text-yellow-400' : 'text-white/30'
                                }`}
                              />
                            ))}
                          </div>
                        )}

                        {/* Difficulty Badge */}
                        <div className="bg-white/30 backdrop-blur-sm rounded-full px-4 py-2 text-center">
                          <span className="text-white font-bold">{level.difficulty[language]}</span>
                        </div>

                        {/* Questions Count */}
                        <div className="mt-4 flex items-center justify-center gap-2 text-white">
                          <Target className="w-5 h-5" />
                          <span className="font-bold">{level.questions} {t.questions}</span>
                        </div>
                      </div>

                      {/* Play Button Overlay on Hover */}
                      {!isLocked && hoveredLevel === level.level && (
                        <div className="absolute inset-0 bg-black/20 rounded-[35px] flex items-center justify-center backdrop-blur-sm">
                          <div className="bg-white rounded-full p-6 shadow-2xl">
                            <ChevronRight className="w-12 h-12 text-emerald-600" />
                          </div>
                        </div>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-emerald-400 to-green-500 rounded-[30px] p-6 shadow-xl border-8 border-white text-center">
              <Trophy className="w-16 h-16 text-white mx-auto mb-3" />
              <div className="text-4xl font-black text-white mb-2">{completedLevels.length}</div>
              <p className="text-white font-bold">{t.levelsCompleted}</p>
            </div>

            <div className="bg-gradient-to-br from-yellow-400 to-orange-500 rounded-[30px] p-6 shadow-xl border-8 border-white text-center">
              <Star className="w-16 h-16 text-white mx-auto mb-3" />
              <div className="text-4xl font-black text-white mb-2">
                {Object.values(levelStars).reduce((a, b) => a + b, 0)}
              </div>
              <p className="text-white font-bold">{t.totalStars}</p>
            </div>

            <div className="bg-gradient-to-br from-purple-400 to-pink-500 rounded-[30px] p-6 shadow-xl border-8 border-white text-center">
              <Award className="w-16 h-16 text-white mx-auto mb-3" />
              <div className="text-4xl font-black text-white mb-2">{Math.round((completedLevels.length / levels.length) * 100)}%</div>
              <p className="text-white font-bold">{t.progress}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Game Playing Screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <LanguageToggle />
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="bg-white rounded-[30px] shadow-xl p-6 mb-6 border-8 border-indigo-100">
          <div className="flex justify-between items-center mb-4">
            <button
              onClick={goToMap}
              className="bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-3 rounded-full font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
            >
              <Home className="w-6 h-6" />
              <span>{t.home}</span>
            </button>
            
            <div className="text-center flex-1">
              <h1 className="text-3xl font-black text-gray-800">{currentLevelData.title[language]}</h1>
              <p className="text-lg text-gray-600 font-bold">{currentLevelData.subtitle}</p>
            </div>
            
            <div className="bg-gradient-to-r from-emerald-500 to-green-600 text-white px-6 py-3 rounded-full font-black text-xl shadow-lg">
              {currentQuestion + 1}/{currentLevelData.questions}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="flex gap-2">
            {Array.from({ length: currentLevelData.questions }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 h-4 rounded-full transition-all ${
                  i < currentQuestion ? 'bg-emerald-500' : 
                  i === currentQuestion ? 'bg-yellow-400 animate-pulse' : 
                  'bg-gray-200'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Video Area */}
        <div className="bg-white rounded-[30px] shadow-xl p-8 mb-6 border-8 border-indigo-100">
          <div className="bg-gradient-to-br from-indigo-100 to-purple-100 rounded-[25px] p-10 border-4 border-indigo-200 min-h-[200px] flex items-center justify-center">
            <div className="text-center">
              <div className="text-7xl mb-4 animate-bounce">👋</div>
              <p className="text-4xl font-black text-gray-800 mb-3">{currentSentence?.sinhala}</p>
              <p className="text-2xl text-gray-600 font-bold">{currentSentence?.english}</p>
            </div>
          </div>
        </div>

        {/* Answer Zone */}
        <div className="bg-white rounded-[30px] shadow-xl p-8 mb-6 border-8 border-indigo-100">
          <h3 className="text-2xl font-black text-gray-800 mb-4 flex items-center gap-3">
            <span className="text-3xl">✏️</span>
            <span>{t.yourAnswer}</span>
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
                  disabled={showResult}
                >
                  {word}
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
          </h3>
          <div className="flex flex-wrap gap-4 justify-center">
            {shuffledWords.map((word, index) => (
              <button
                key={index}
                onClick={() => handleWordClick(word)}
                className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-4 rounded-[20px] text-2xl font-black shadow-lg hover:scale-110 transition-transform border-4 border-blue-600"
                disabled={showResult}
              >
                {word}
              </button>
            ))}
          </div>
        </div>

        {/* Result */}
        {showResult && (
          <div className={`rounded-[30px] shadow-xl p-8 mb-6 text-center border-8 ${
            isCorrect 
              ? 'bg-gradient-to-r from-emerald-400 to-green-500 border-emerald-600' 
              : 'bg-gradient-to-r from-red-400 to-pink-500 border-red-600'
          }`}>
            <div className="text-8xl mb-4 animate-bounce">
              {isCorrect ? '🎉' : '💪'}
            </div>
            <h3 className="text-5xl font-black text-white mb-4">
              {isCorrect ? t.excellent : t.keepTrying}
            </h3>
            {!isCorrect && (
              <div className="bg-white/30 backdrop-blur-sm rounded-[20px] p-6">
                <p className="text-white text-xl font-bold mb-2">{t.correctAnswer}</p>
                <p className="text-3xl font-black text-white">{currentSentence.words.join(' ')}</p>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          {!showResult ? (
            <button
              onClick={checkAnswer}
              disabled={selectedWords.length !== currentSentence.words.length}
              className="flex-1 bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-6 rounded-[25px] font-black text-2xl hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:cursor-not-allowed border-8 border-emerald-700 flex items-center justify-center gap-3"
            >
              <CheckCircle className="w-8 h-8" />
              <span>{t.checkAnswer}</span>
            </button>
          ) : (
            <button
              onClick={nextQuestion}
              className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-6 rounded-[25px] font-black text-2xl hover:scale-105 transition-transform shadow-lg border-8 border-blue-700 flex items-center justify-center gap-3"
            >
              <span>{currentQuestion < currentLevelData.questions - 1 ? t.nextQuestion : t.finish}</span>
              <ArrowRight className="w-8 h-8" />
            </button>
          )}
          <button
            onClick={resetLevel}
            className="bg-gradient-to-r from-orange-500 to-red-600 text-white px-8 py-6 rounded-[25px] font-black text-2xl hover:scale-105 transition-transform shadow-lg border-8 border-orange-700 flex items-center justify-center gap-3"
          >
            <RotateCcw className="w-8 h-8" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignLanguageGame;