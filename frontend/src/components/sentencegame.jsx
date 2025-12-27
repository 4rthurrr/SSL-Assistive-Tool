import React, { useState, useEffect } from 'react';
import { 
  Star, Trophy, Volume2, RotateCcw, ArrowRight, Home, Lock, 
  Zap, Target, Award, Users, Brain, Heart, Sparkles, ChevronRight
} from 'lucide-react';
import { Link, useNavigate } from "react-router-dom";


const SignLanguageGame = () => {
  const [gameState, setGameState] = useState('map'); // 'map' or 'playing'
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
  const navigate = useNavigate();

  const levels = [
    {
      level: 1,
      questions: 3,
      title: 'මූලික වචන',
      subtitle: 'Basic Words',
      color: 'from-green-400 to-emerald-500',
      icon: '🟢',
      difficulty: 'Easy',
      description: 'Simple daily words',
      sentences: [
        {
          sinhala: 'මම පාඩම් කරනවා',
          english: 'I am studying',
          words: ['මම', 'පාඩම්', 'කරනවා'],
          videoUrl: '#'
        },
        {
          sinhala: 'මම බත් කනවා',
          english: 'I am eating rice',
          words: ['මම', 'බත්', 'කනවා'],
          videoUrl: '#'
        },
        {
          sinhala: 'අම්මා ගෙදර',
          english: 'Mother is at home',
          words: ['අම්මා', 'ගෙදර'],
          videoUrl: '#'
        }
      ]
    },
    {
      level: 2,
      questions: 4,
      title: 'දෛනික ප්‍රශ්න',
      subtitle: 'Daily Questions',
      color: 'from-blue-400 to-indigo-500',
      icon: '🔵',
      difficulty: 'Medium',
      description: 'Everyday conversations',
      sentences: [
        {
          sinhala: 'අද පාසල් ගියාද',
          english: 'Did you go to school today?',
          words: ['අද', 'පාසල්', 'ගියාද'],
          videoUrl: '#'
        },
        {
          sinhala: 'කොහෙද යන්නේ',
          english: 'Where are you going?',
          words: ['කොහෙද', 'යන්නේ'],
          videoUrl: '#'
        },
        {
          sinhala: 'දැන් වේලාව කීයද',
          english: 'What time is it now?',
          words: ['දැන්', 'වේලාව', 'කීයද'],
          videoUrl: '#'
        },
        {
          sinhala: 'ඔයාට හුරුපුරුදුද',
          english: 'Are you familiar?',
          words: ['ඔයාට', 'හුරුපුරුදුද'],
          videoUrl: '#'
        }
      ]
    },
    {
      level: 3,
      questions: 5,
      title: 'සංකීර්ණ වාක්‍ය',
      subtitle: 'Complex Sentences',
      color: 'from-purple-400 to-pink-500',
      icon: '🟣',
      difficulty: 'Hard',
      description: 'Advanced conversations',
      sentences: [
        {
          sinhala: 'මම උදේ ආහාරය කෑවා',
          english: 'I ate breakfast',
          words: ['මම', 'උදේ', 'ආහාරය', 'කෑවා'],
          videoUrl: '#'
        },
        {
          sinhala: 'ඔබේ නම මොකක්ද',
          english: 'What is your name?',
          words: ['ඔබේ', 'නම', 'මොකක්ද'],
          videoUrl: '#'
        },
        {
          sinhala: 'මම ගෙදර යනවා',
          english: 'I am going home',
          words: ['මම', 'ගෙදර', 'යනවා'],
          videoUrl: '#'
        },
        {
          sinhala: 'ඔබට උදව් ඕනේද',
          english: 'Do you need help?',
          words: ['ඔබට', 'උදව්', 'ඕනේද'],
          videoUrl: '#'
        },
        {
          sinhala: 'අද අලුත් දෙයක් ඉගෙන ගත්තා',
          english: 'Learned something new today',
          words: ['අද', 'අලුත්', 'දෙයක්', 'ඉගෙන', 'ගත්තා'],
          videoUrl: '#'
        }
      ]
    },
    {
      level: 4,
      questions: 6,
      title: 'උසස් මට්ටම',
      subtitle: 'Advanced Level',
      color: 'from-orange-400 to-red-500',
      icon: '🟠',
      difficulty: 'Expert',
      description: 'Professional communication',
      sentences: [
        {
          sinhala: 'මම ගුරුවරයෙක් වීමට අවශ්‍යයි',
          english: 'I want to become a teacher',
          words: ['මම', 'ගුරුවරයෙක්', 'වීමට', 'අවශ්‍යයි'],
          videoUrl: '#'
        },
        {
          sinhala: 'ඔබගේ ජීවිත අරමුණ මොකක්ද',
          english: 'What is your life goal?',
          words: ['ඔබගේ', 'ජීවිත', 'අරමුණ', 'මොකක්ද'],
          videoUrl: '#'
        },
        {
          sinhala: 'සුභ පැතුම් සමඟ ආරම්භ කරමු',
          english: "Let's start with greetings",
          words: ['සුභ', 'පැතුම්', 'සමඟ', 'ආරම්භ', 'කරමු'],
          videoUrl: '#'
        },
        {
          sinhala: 'සංඥා භාෂාව ඉගෙන ගැනීම සතුටක්',
          english: 'Learning sign language is a joy',
          words: ['සංඥා', 'භාෂාව', 'ඉගෙන', 'ගැනීම', 'සතුටක්'],
          videoUrl: '#'
        }
      ]
    },
    {
      level: 5,
      questions: 8,
      title: 'විශේෂඥ මට්ටම',
      subtitle: 'Master Level',
      color: 'from-yellow-400 to-orange-500',
      icon: '⭐',
      difficulty: 'Master',
      description: 'Fluency and expression',
      sentences: [
        {
          sinhala: 'සංඥා භාෂාව සමඟ මම නිදහස ලැබුවා',
          english: 'I found freedom with sign language',
          words: ['සංඥා', 'භාෂාව', 'සමඟ', 'මම', 'නිදහස', 'ලැබුවා'],
          videoUrl: '#'
        },
        {
          sinhala: 'සෑම දෙනාම සන්නිවේදනය කිරීමට අයිතියක් ඇත',
          english: 'Everyone has the right to communicate',
          words: ['සෑම', 'දෙනාම', 'සන්නිවේදනය', 'කිරීමට', 'අයිතියක්', 'ඇත'],
          videoUrl: '#'
        },
        {
          sinhala: 'අපගේ වෙනස්කම් අපව විශේෂිත කරයි',
          english: 'Our differences make us special',
          words: ['අපගේ', 'වෙනස්කම්', 'අපව', 'විශේෂිත', 'කරයි'],
          videoUrl: '#'
        }
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

  // Level Complete Screen
  if (showLevelComplete) {
    const stars = levelStars[currentLevel] || 0;
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 p-8 flex items-center justify-center">
        <div className="bg-white rounded-3xl shadow-2xl p-12 max-w-md w-full text-center">
          <Trophy className="w-24 h-24 mx-auto text-yellow-500 mb-6 animate-bounce" />
          <h2 className="text-4xl font-bold text-purple-600 mb-4">මට්ටම සම්පූර්ණයි!</h2>
          <p className="text-xl text-gray-700 mb-6">Level {currentLevel} Complete!</p>
          
          <div className="flex justify-center gap-2 mb-8">
            {[1, 2, 3].map((star) => (
              <Star
                key={star}
                className={`w-12 h-12 ${star <= stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
              />
            ))}
          </div>
          
          <p className="text-2xl font-semibold text-gray-800 mb-8">
            ලකුණු: {score + (isCorrect ? 1 : 0)} / {currentLevelData.questions}
          </p>
          
          <div className="flex flex-col gap-4">
            {currentLevel < levels.length && (
              <button
                onClick={nextLevel}
                className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-4 rounded-xl font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
              >
                ඊළඟ මට්ටම <ArrowRight className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={resetLevel}
              className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-6 py-4 rounded-xl font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
            >
              <RotateCcw className="w-5 h-5" /> නැවත උත්සාහ කරන්න
            </button>
            <button
              onClick={goToMap}
              className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-4 rounded-xl font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
            >
              <Home className="w-5 h-5" /> මට්ටම් සිතියම
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Level Map Screen - Enhanced Version
  if (gameState === 'map') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 p-4 md:p-6 overflow-hidden relative">
        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-10 w-72 h-72 bg-gradient-to-r from-green-200 to-emerald-200 rounded-full blur-3xl opacity-30 animate-pulse"></div>
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-gradient-to-r from-blue-200 to-purple-200 rounded-full blur-3xl opacity-30 animate-pulse delay-1000"></div>
          <div className="absolute top-1/3 right-1/4 w-48 h-48 bg-gradient-to-r from-yellow-200 to-orange-200 rounded-full blur-3xl opacity-30 animate-bounce"></div>
          <div className="absolute bottom-1/4 left-1/3 w-56 h-56 bg-gradient-to-r from-pink-200 to-rose-200 rounded-full blur-3xl opacity-30 animate-pulse delay-500"></div>
        </div>

        {/* Floating Icons */}
        <div className="absolute top-6 left-6 animate-float text-4xl">🤟</div>
        <div className="absolute top-6 right-6 animate-spin-slow text-3xl">🌟</div>
        <div className="absolute bottom-6 left-6 animate-bounce text-3xl">🎯</div>
        <div className="absolute bottom-6 right-6 animate-pulse text-4xl">💫</div>

        <div className="max-w-7xl mx-auto relative z-10">
          {/* Enhanced Header */}
          <div className="text-center mb-10 pt-8">
            <div className="inline-block relative mb-4">
              <div className="text-7xl md:text-8xl mb-3 animate-bounce">🤟</div>
              <div className="absolute -top-2 -right-2 w-10 h-10 bg-yellow-400 rounded-full animate-ping"></div>
            </div>
            
            <h1 className="text-5xl md:text-6xl font-black text-sky-900 mb-3 drop-shadow-lg bg-gradient-to-r from-sky-600 to-blue-700 bg-clip-text text-transparent">
              සංඥා භාෂා වික්‍රමය
            </h1>
            <p className="text-2xl md:text-3xl text-sky-700 font-bold mb-4">Sign Language Adventure</p>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto bg-white/60 backdrop-blur-sm rounded-2xl p-3">
              ක්‍රමානුකූලව සංඥා භාෂාව හුරු කර ගන්න
            </p>
          </div>

          {/* Main Map Container */}
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl p-6 md:p-8 mb-8 border-2 border-white/50 relative overflow-hidden">
            {/* Decorative Border */}
            <div className="absolute top-0 left-0 w-20 h-20 border-t-4 border-l-4 border-green-400 rounded-tl-3xl"></div>
            <div className="absolute top-0 right-0 w-20 h-20 border-t-4 border-r-4 border-blue-400 rounded-tr-3xl"></div>
            <div className="absolute bottom-0 left-0 w-20 h-20 border-b-4 border-l-4 border-purple-400 rounded-bl-3xl"></div>
            <div className="absolute bottom-0 right-0 w-20 h-20 border-b-4 border-r-4 border-orange-400 rounded-br-3xl"></div>

            {/* Map Path */}
            <div className="relative">
              {/* Curved Path SVG */}
              <svg className="absolute inset-0 w-full h-full" style={{zIndex: 0}}>
                <path
                  d="M 50 250 Q 200 150, 350 250 T 650 150 Q 800 100, 950 250"
                  stroke="url(#gradientPath)"
                  strokeWidth="15"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray="0"
                  filter="drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))"
                />
                <defs>
                  <linearGradient id="gradientPath" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#10B981" />
                    <stop offset="25%" stopColor="#3B82F6" />
                    <stop offset="50%" stopColor="#8B5CF6" />
                    <stop offset="75%" stopColor="#F59E0B" />
                    <stop offset="100%" stopColor="#EF4444" />
                  </linearGradient>
                </defs>
              </svg>

              {/* Levels Container */}
              <div className="relative grid grid-cols-5 gap-4 md:gap-8 py-12" style={{zIndex: 1}}>
                {levels.map((level, index) => {
                  const isLocked = !completedLevels.includes(level.level);
                  const stars = levelStars[level.level] || 0;
                  const isCompleted = completedLevels.includes(level.level);
                  
                  return (
                    <div 
                      key={level.level}
                      className={`flex flex-col items-center transform transition-all duration-500 ${
                        hoveredLevel === level.level ? 'scale-110 z-20' : 'scale-100'
                      }`}
                      onMouseEnter={() => setHoveredLevel(level.level)}
                      onMouseLeave={() => setHoveredLevel(null)}
                    >
                      {/* Level Node */}
                      <button
                        onClick={() => startLevel(level.level)}
                        disabled={isLocked}
                        className={`relative transform transition-all duration-300 ${
                          isLocked 
                            ? 'cursor-not-allowed filter grayscale' 
                            : 'hover:scale-110 hover:shadow-2xl cursor-pointer animate-pulse-slow'
                        }`}
                      >
                        {/* Outer Glow */}
                        <div className={`absolute inset-0 rounded-full ${
                          isLocked ? 'bg-gray-300' : level.color.split(' ')[1]
                        } blur-xl opacity-50 -m-4`}></div>
                        
                        {/* Level Circle */}
                        <div className={`relative w-24 h-24 md:w-28 md:h-28 rounded-full bg-gradient-to-br ${level.color} shadow-2xl flex items-center justify-center border-8 border-white transform transition-all duration-300 ${
                          isLocked ? 'opacity-70' : 'shadow-xl'
                        }`}>
                          {isLocked ? (
                            <div className="relative">
                              <Lock className="w-10 h-10 md:w-12 md:h-12 text-white" />
                              <div className="absolute -inset-2 bg-white/20 rounded-full blur-sm"></div>
                            </div>
                          ) : (
                            <div className="text-center">
                              <div className="text-4xl">{level.icon}</div>
                              <span className="text-2xl md:text-3xl font-black text-white drop-shadow-lg">L{level.level}</span>
                            </div>
                          )}
                          
                          {/* Difficulty Badge */}
                          {!isLocked && (
                            <div className={`absolute -bottom-2 left-1/2 transform -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold text-white ${
                              level.difficulty === 'Easy' ? 'bg-green-500' :
                              level.difficulty === 'Medium' ? 'bg-blue-500' :
                              level.difficulty === 'Hard' ? 'bg-purple-500' :
                              level.difficulty === 'Expert' ? 'bg-orange-500' : 'bg-yellow-500'
                            }`}>
                              {level.difficulty}
                            </div>
                          )}
                          
                          {/* Stars */}
                          {stars > 0 && (
                            <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 flex gap-1">
                              {[1, 2, 3].map((star) => (
                                <Star
                                  key={star}
                                  className={`w-5 h-5 md:w-6 md:h-6 ${
                                    star <= stars ? 'fill-yellow-400 text-yellow-400 animate-pulse' : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      </button>
                      
                      {/* Level Info Panel */}
                      <div className={`mt-4 text-center transition-all duration-300 ${
                        hoveredLevel === level.level ? 'opacity-100 scale-100' : 'opacity-70 scale-95'
                      }`}>
                        <div className="bg-white rounded-xl px-4 py-3 shadow-lg border border-gray-100 min-w-[180px]">
                          <p className="font-bold text-gray-800 text-sm md:text-base">{level.title}</p>
                          <p className="text-xs text-gray-600 mb-1">{level.subtitle}</p>
                          <div className="flex items-center justify-center gap-1 text-xs text-gray-500">
                            <Target className="w-3 h-3" />
                            <span>{level.questions} questions</span>
                          </div>
                          {!isLocked && hoveredLevel === level.level && (
                            <button
                              onClick={() => startLevel(level.level)}
                              className="mt-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs px-3 py-1 rounded-full font-bold flex items-center gap-1 mx-auto hover:scale-105 transition-transform"
                            >
                              Play <ChevronRight className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Progress Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Progress Stats */}
            <div className="bg-gradient-to-br from-white to-gray-50 rounded-3xl p-6 shadow-xl border border-gray-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Trophy className="text-yellow-500" />
                Your Progress
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Levels Completed</span>
                  <span className="text-2xl font-bold text-purple-600">{completedLevels.length}/{levels.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total Stars</span>
                  <span className="text-2xl font-bold text-yellow-600">
                    {Object.values(levelStars).reduce((a, b) => a + b, 0)}/15
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Mastery</span>
                  <span className="text-2xl font-bold text-green-600">
                    {Math.round((completedLevels.length / levels.length) * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-br from-sky-50 to-blue-50 rounded-3xl p-6 shadow-xl border border-sky-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Zap className="text-blue-500" />
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Practice Mode
                </button>
                <button className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2">
                  <Brain className="w-4 h-4" />
                  Daily Challenge
                </button>
                <button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-3 rounded-xl font-bold hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2">
                  <Users className="w-4 h-4" />
                  Multiplayer
                </button>
              </div>
            </div>

            {/* Achievement Badges */}
            <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-3xl p-6 shadow-xl border border-amber-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Award className="text-amber-500" />
                Achievements
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-gradient-to-br from-green-400 to-emerald-500 rounded-xl p-3 text-center text-white">
                  <div className="text-2xl">🥇</div>
                  <div className="text-xs font-bold">First Step</div>
                </div>
                <div className="bg-gradient-to-br from-blue-400 to-indigo-500 rounded-xl p-3 text-center text-white">
                  <div className="text-2xl">🎯</div>
                  <div className="text-xs font-bold">Accuracy</div>
                </div>
                <div className="bg-gradient-to-br from-purple-400 to-pink-500 rounded-xl p-3 text-center text-white">
                  <div className="text-2xl">⚡</div>
                  <div className="text-xs font-bold">Speed</div>
                </div>
                <div className="bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl p-3 text-center text-white">
                  <div className="text-2xl">🌟</div>
                  <div className="text-xs font-bold">Star Hunter</div>
                </div>
                <div className="bg-gradient-to-br from-red-400 to-rose-500 rounded-xl p-3 text-center text-white">
                  <div className="text-2xl">💪</div>
                  <div className="text-xs font-bold">Streak</div>
                </div>
                <div className="bg-gradient-to-br from-cyan-400 to-blue-500 rounded-xl p-3 text-center text-white">
                  <div className="text-2xl">📚</div>
                  <div className="text-xs font-bold">Learner</div>
                </div>
              </div>
            </div>
          </div>

          {/* Character Progress */}
          <div className="bg-gradient-to-r from-sky-500 to-blue-600 rounded-3xl p-6 shadow-2xl text-white mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-2xl">
                    👤
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-400 rounded-full border-2 border-white"></div>
                </div>
                <div>
                  <h3 className="text-2xl font-bold">Student Explorer</h3>
                  <p className="text-blue-100">Learning sign language step by step</p>
                </div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold">L{Math.max(...completedLevels, 0)}</div>
                <p className="text-sm text-blue-200">Current Level</p>
              </div>
            </div>
            
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Learning Progress</span>
                <span>{Math.round((completedLevels.length / levels.length) * 100)}%</span>
              </div>
              <div className="w-full bg-white/30 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-yellow-400 to-orange-400 h-3 rounded-full transition-all duration-1000"
                  style={{ width: `${(completedLevels.length / levels.length) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Footer Navigation */}
          <div className="flex flex-col md:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate("/gameselection")}
              className="bg-white hover:bg-gray-50 text-gray-800 font-bold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2">
              <Home className="w-5 h-5" />
              Home Dashboard
            </button>
            <button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2">
              <Brain className="w-5 h-5" />
              View Analytics
            </button>
            <button className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2">
              <Heart className="w-5 h-5" />
              Accessibility Settings
            </button>
          </div>
        </div>

        {/* Add CSS for animations */}
        <style>{`
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
          }
          
          @keyframes spin-slow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          
          @keyframes pulse-slow {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
          }
          
          .animate-float {
            animation: float 3s ease-in-out infinite;
          }
          
          .animate-spin-slow {
            animation: spin-slow 20s linear infinite;
          }
          
          .animate-pulse-slow {
            animation: pulse-slow 2s ease-in-out infinite;
          }
        `}</style>
      </div>
    );
  }

  // Game Playing Screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 p-3 md:p-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-xl p-3 mb-3">
          <div className="flex justify-between items-center">
            <button
              onClick={goToMap}
              className="flex items-center gap-1 text-purple-600 hover:text-purple-800 font-semibold transition-colors"
            >
              <Home className="w-4 h-4" />
              <span className="hidden sm:inline text-sm">මුල් පිටුව</span>
            </button>
            <div className="text-center flex-1">
              <h1 className="text-lg md:text-xl font-bold text-purple-600">{currentLevelData.title}</h1>
              <p className="text-xs text-gray-600">{currentLevelData.subtitle}</p>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-purple-600">L{currentLevel}</div>
              <div className="text-xs text-gray-600">{currentQuestion + 1}/{currentLevelData.questions}</div>
            </div>
          </div>
          
          <div className="mt-2 flex gap-1">
            {Array.from({ length: currentLevelData.questions }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 h-2 rounded-full transition-all ${
                  i < currentQuestion ? 'bg-green-500' : i === currentQuestion ? 'bg-purple-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Sign Language Video Area */}
        <div className="bg-white rounded-xl shadow-xl p-4 mb-3">
          <h2 className="text-sm md:text-base font-bold text-purple-600 mb-2 flex items-center gap-2">
            <Volume2 className="w-4 h-4" />
            සංඥා වීඩියෝව
          </h2>
          
          <div className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg p-4 mb-2 min-h-[140px] flex items-center justify-center border-2 border-purple-300">
            <div className="text-center">
              <div className="text-4xl mb-2 animate-pulse">👋🤟✋</div>
              <p className="text-xl md:text-2xl font-bold text-purple-700 mb-1">{currentSentence?.sinhala}</p>
              <p className="text-sm md:text-base text-gray-600">{currentSentence?.english}</p>
            </div>
          </div>
        </div>

        {/* Drop Zone */}
        <div className="bg-white rounded-xl shadow-xl p-4 mb-3">
          <h3 className="text-sm font-bold text-purple-600 mb-2">ඔබේ පිළිතුර</h3>
          <div className="min-h-[80px] bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-3 border-2 border-dashed border-purple-300 flex flex-wrap gap-2 items-center justify-center">
            {selectedWords.length === 0 ? (
              <p className="text-gray-400 text-sm">වචන තෝරන්න ↓</p>
            ) : (
              selectedWords.map((word, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectedWordClick(word, index)}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg text-lg font-bold shadow-lg hover:scale-110 transition-transform cursor-pointer"
                  disabled={showResult}
                >
                  {word}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Word Bank */}
        <div className="bg-white rounded-xl shadow-xl p-4 mb-3">
          <h3 className="text-sm font-bold text-purple-600 mb-2">වචන</h3>
          <div className="flex flex-wrap gap-2 justify-center">
            {shuffledWords.map((word, index) => (
              <button
                key={index}
                onClick={() => handleWordClick(word)}
                className="bg-gradient-to-r from-green-400 to-blue-500 text-white px-5 py-2 rounded-lg text-lg font-bold shadow-lg hover:scale-110 transition-transform cursor-pointer"
                disabled={showResult}
              >
                {word}
              </button>
            ))}
          </div>
        </div>

        {/* Result */}
        {showResult && (
          <div className={`bg-white rounded-xl shadow-xl p-4 mb-3 text-center ${isCorrect ? 'border-2 border-green-500' : 'border-2 border-red-500'}`}>
            <div className="text-4xl mb-2 animate-bounce">{isCorrect ? '🎉' : '😢'}</div>
            <h3 className={`text-2xl font-bold mb-2 ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
              {isCorrect ? 'හරි!' : 'වැරදියි'}
            </h3>
            {!isCorrect && (
              <p className="text-base text-gray-700">
                නිවැරදි පිළිතුර: <span className="font-bold text-purple-600">{currentSentence.words.join(' ')}</span>
              </p>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-2">
          {!showResult ? (
            <button
              onClick={checkAnswer}
              disabled={selectedWords.length !== currentSentence.words.length}
              className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-6 py-3 rounded-xl font-bold text-base hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              පරීක්ෂා කරන්න
            </button>
          ) : (
            <button
              onClick={nextQuestion}
              className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-6 py-3 rounded-xl font-bold text-base hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
            >
              {currentQuestion < currentLevelData.questions - 1 ? 'ඊළඟ ප්‍රශ්නය' : 'අවසන්'} <ArrowRight className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={resetLevel}
            className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-6 py-3 rounded-xl font-bold text-base hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-5 h-5" /> නැවත
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignLanguageGame;