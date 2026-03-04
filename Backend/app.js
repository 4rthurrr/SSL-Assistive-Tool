const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const userRoutes = require('./auth/routes/userroutes');
const gameProfileRoutes = require('./game-engine/routes/gameProfileRoutes');

const GameAttempt = require('./game-engine/models/GameAttempt');
const UserLevel = require('./game-engine/models/UserLevel');

const app = express();

// ========================
// JWT CONFIGURATION
// ========================
const JWT_SECRET = process.env.JWT_SECRET || 'Hf7&9dJk2!vLxQp8rTgMzS4wYb6eW1u3';

// JWT Middleware
const verifyToken = (req, res, next) => {
  const token = req.header('Authorization')?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ 
      success: false, 
      message: 'No token provided, authorization denied' 
    });
  }
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.userId = decoded.id;
    next();
  } catch (error) {
    return res.status(401).json({ 
      success: false, 
      message: 'Token is not valid or has expired' 
    });
  }
};

// ========================
// MIDDLEWARE
// ========================
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ========================
// MONGODB CONNECTION
// ========================
const MONGODB_URI = process.env.MONGODB_URI;

const connectDB = async () => {
  try {
    await mongoose.connect(MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });
    console.log('✅ MongoDB Connected Successfully');
    console.log(`📊 Database: ${mongoose.connection.name}`);
  } catch (error) {
    console.error('❌ MongoDB Connection Error:', error.message);
    process.exit(1);
  }
};

connectDB();

// ========================
// MONGOOSE EVENTS
// ========================
mongoose.connection.on('connected', () => {
  console.log('🔗 Mongoose connected');
});

mongoose.connection.on('error', err => {
  console.error('❌ Mongoose error:', err);
});

mongoose.connection.on('disconnected', () => {
  console.warn('⚠️ Mongoose disconnected');
});

// ========================
// HEALTH CHECK
// ========================
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
    timestamp: new Date().toISOString()
  });
});

// ========================
// USER & GAME PROFILE ROUTES
// ========================
app.use('/users', userRoutes);
app.use('/api/game', gameProfileRoutes);

// ========================
// QUESTION/QUIZ ROUTES
// ========================
app.get('/api/questions/test', verifyToken, (req, res) => {
  res.json({
    success: true,
    message: 'Question routes are working!',
    userId: req.userId
  });
});

app.get('/api/questions/quiz/:grade', verifyToken, async (req, res) => {
  try {
    const grade = req.params.grade;
    console.log(`📚 Quiz request for Grade ${grade} by user ${req.userId}`);
    
    if (mongoose.connection.readyState !== 1) {
      return res.status(500).json({
        success: false,
        error: 'Database not connected'
      });
    }
    
    const questionsCollection = mongoose.connection.db.collection('questions');
    const quizDoc = await questionsCollection.findOne({});
    
    if (!quizDoc) {
      return res.status(404).json({
        success: false,
        error: 'No quiz data found in questions collection'
      });
    }
    
    let quizData = quizDoc;
    if (quizDoc.quizDatabase) {
      quizData = quizDoc.quizDatabase;
    }
    
    if (!quizData.grades) {
      return res.status(404).json({
        success: false,
        error: 'No grades found in quiz data'
      });
    }
    
    const gradeKey = `grade${grade}`;
    const gradeData = quizData.grades[gradeKey];
    
    if (!gradeData) {
      return res.status(404).json({
        success: false,
        error: `Grade ${grade} not found`
      });
    }
    
    const questions = gradeData.questions || [];
    
    if (questions.length === 0) {
      return res.status(404).json({
        success: false,
        error: `No questions found for Grade ${grade}`
      });
    }
    
    const shuffled = [...questions].sort(() => 0.5 - Math.random());
    const selected = shuffled.slice(0, 3);
    
    res.json({
      success: true,
      grade: grade,
      questionCount: selected.length,
      questions: selected.map(q => ({
        id: q.id,
        type: q.type,
        visualType: q.visualType,
        imageUrl: q.imageUrl,
        videoUrl: q.videoUrl,
        signDescription: q.signDescription,
        imageDescription: q.imageDescription,
        question: q.question,
        options: q.options,
        difficulty: q.difficulty
      }))
    });
    
  } catch (error) {
    console.error('❌ Quiz error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/questions/validate', verifyToken, async (req, res) => {
  try {
    const { answers } = req.body;
    
    if (!answers || !Array.isArray(answers)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid answers format'
      });
    }
    
    const questionsCollection = mongoose.connection.db.collection('questions');
    const quizDoc = await questionsCollection.findOne({});
    
    if (!quizDoc) {
      return res.status(404).json({
        success: false,
        error: 'Quiz data not found'
      });
    }
    
    let quizData = quizDoc;
    if (quizDoc.quizDatabase) {
      quizData = quizDoc.quizDatabase;
    }
    
    if (!quizData.grades) {
      return res.status(404).json({
        success: false,
        error: 'No grades found in quiz data'
      });
    }
    
    const allQuestions = [];
    for (const gradeKey in quizData.grades) {
      if (quizData.grades[gradeKey].questions) {
        allQuestions.push(...quizData.grades[gradeKey].questions);
      }
    }
    
    const results = [];
    let correctCount = 0;
    
    for (const answer of answers) {
      const question = allQuestions.find(q => q.id === answer.id);
      
      if (!question) {
        results.push({
          id: answer.id,
          correct: false,
          error: 'Question not found'
        });
        continue;
      }
      
      const isCorrect = answer.selectedAnswer === question.correctAnswer;
      if (isCorrect) correctCount++;
      
      results.push({
        id: answer.id,
        question: question.question,
        selectedAnswer: answer.selectedAnswer,
        correctAnswer: question.correctAnswer,
        correct: isCorrect
      });
    }
    
    const total = answers.length;
    const percentage = total > 0 ? ((correctCount / total) * 100).toFixed(2) : '0.00';
    
    res.json({
      success: true,
      results: results,
      summary: {
        correct: correctCount,
        total: total,
        percentage: percentage
      }
    });
    
  } catch (error) {
    console.error('❌ Validation error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ========================
// REGISTRATION ENDPOINT WITH JWT + BCRYPT
// ========================
const User = require('./auth/models/usermodel');
const GameProfile = require('./game-engine/models/GameProfile');

app.post('/api/register', async (req, res) => {
  try {
    const { name, user_type, grade } = req.body;

    if (!name) {
      return res.status(400).json({ 
        success: false, 
        error: 'Name is required' 
      });
    }

    // Generate unique email
    const email = `${name.toLowerCase().replace(/\s+/g, '')}${Date.now()}@game.local`;
    const password = 'gameuser123';
    
    // Check if user already exists
    let existingUser = await User.findOne({ email: email });
    
    if (existingUser) {
      // User exists - generate token
      const token = jwt.sign(
        { id: existingUser._id, email: existingUser.email },
        JWT_SECRET,
        { expiresIn: '7d' }
      );
      
      const gameProfile = await GameProfile.findOne({ userId: existingUser._id });
      
      return res.json({
        success: true,
        token: token,
        user: {
          _id: existingUser._id,
          name: existingUser.name,
          email: existingUser.email,
          hasTakenQuiz: existingUser.hasTakenQuiz || false,
          recommendedLevel: existingUser.recommendedLevel || 'basic',
          gameProfile: gameProfile
        },
        message: 'Welcome back!'
      });
    }

    // Create new user with hashed password
    const hashedPassword = await bcrypt.hash(password, 10);
    const age = grade ? parseInt(grade) + 6 : 10;

    const newUser = new User({
      name: name,
      email: email,
      password: hashedPassword,
      age: age,
      hasTakenQuiz: false,
      recommendedLevel: 'basic'
    });
    
    await newUser.save();

    // Create game profile
    const gameProfile = new GameProfile({
      userId: newUser._id,
      userType: user_type || 'student',
      grade: grade || '2',
      recommendedLevel: 'basic',
      hasTakenQuiz: false
    });

    await gameProfile.save();

    // Generate JWT token
    const token = jwt.sign(
      { id: newUser._id, email: newUser.email },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token: token,
      user: {
        _id: newUser._id,
        name: newUser.name,
        email: newUser.email,
        hasTakenQuiz: false,
        recommendedLevel: 'basic',
        gameProfile: gameProfile
      },
      message: 'Registration successful'
    });

  } catch (error) {
    console.error('❌ Registration error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ========================
// QUIZ SUBMISSION WITH TOKEN VERIFICATION
// ========================
app.post('/api/quiz/submit', verifyToken, async (req, res) => {
  try {
    const { answers, recommendedLevel, quizScore, quizTotal, quizPercentage } = req.body;
    const userId = req.userId;

    console.log(`📝 Quiz submitted by ${userId}: ${quizScore}/${quizTotal} (${quizPercentage}%)`);

    // Update user
    const userUpdate = await User.findByIdAndUpdate(
      userId,
      {
        hasTakenQuiz: true,
        quizCompletedAt: new Date(),
        recommendedLevel: recommendedLevel
      },
      { new: true }
    );

    if (!userUpdate) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }

    // Update game profile
    const profileUpdate = await GameProfile.findOneAndUpdate(
      { userId: userId },
      {
        hasTakenQuiz: true,
        quizScore: quizScore,
        quizTotal: quizTotal,
        quizPercentage: quizPercentage,
        quizCompletedAt: new Date(),
        recommendedLevel: recommendedLevel
      },
      { new: true, upsert: true }
    );

    res.json({
      success: true,
      message: 'Quiz results saved',
      recommendedLevel: recommendedLevel,
      user: {
        _id: userUpdate._id,
        name: userUpdate.name,
        hasTakenQuiz: userUpdate.hasTakenQuiz,
        recommendedLevel: userUpdate.recommendedLevel
      }
    });

  } catch (error) {
    console.error('❌ Quiz submission error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ========================
// USER QUIZ STATUS WITH TOKEN VERIFICATION
// ========================
app.get('/api/user/quiz-status', verifyToken, async (req, res) => {
  try {
    const userId = req.userId;
    
    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }
    
    const profile = await GameProfile.findOne({ userId });
    
    res.json({
      success: true,
      hasTakenQuiz: user.hasTakenQuiz || false,
      recommendedLevel: user.recommendedLevel || profile?.recommendedLevel || 'basic',
      name: user.name,
      quizScore: profile?.quizScore || 0,
      quizTotal: profile?.quizTotal || 0,
      quizPercentage: profile?.quizPercentage || 0
    });
  } catch (error) {
    console.error('❌ Quiz status error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ========================
// DEBUG ENDPOINT (PROTECTED)
// ========================
app.get('/api/test-questions', verifyToken, async (req, res) => {
  try {
    const collections = await mongoose.connection.db.listCollections().toArray();
    const collectionNames = collections.map(c => c.name);
    
    const quizCollection = mongoose.connection.db.collection('questions');
    const count = await quizCollection.countDocuments();
    const allDocs = await quizCollection.find({}).limit(5).toArray();
    
    res.json({
      success: true,
      collections: collectionNames,
      questionsCollection: {
        documentCount: count,
        sampleDocs: allDocs
      },
      userId: req.userId
    });
  } catch (error) {
    res.json({
      success: false,
      error: error.message
    });
  }
});

// Helper functions
function getPreviousLevel(level) {
  const levelOrder = ['basic', 'easy', 'medium', 'hard'];
  const index = levelOrder.indexOf(level);
  return index > 0 ? levelOrder[index - 1] : null;
}

function getNextLevel(level) {
  const levelOrder = ['basic', 'easy', 'medium', 'hard'];
  const index = levelOrder.indexOf(level);
  return index < levelOrder.length - 1 ? levelOrder[index + 1] : null;
}

// Get user's level status
app.get('/api/user/level-status', verifyToken, async (req, res) => {
  try {
    const userId = req.userId;
    
    const levelStatus = await UserLevel.getUserLevelStatus(userId);
    
    res.json({
      success: true,
      levelStatus: levelStatus
    });
  } catch (error) {
    console.error('❌ Level status error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Update game progress and check for level unlocks
app.post('/api/game/progress', verifyToken, async (req, res) => {
  try {
    const userId = req.userId;
    const { level, correct, word, timeTaken, sessionId } = req.body;
    
    // Save game attempt
    const gameAttempt = new GameAttempt({
      userId: userId,
      level: level,
      word: word,
      correct: correct,
      timeTaken: timeTaken,
      sessionId: sessionId,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    
    await gameAttempt.save();
    
    // Update user level progress
    const userLevel = await UserLevel.updateUserProgress(userId, {
      level,
      correct,
      word,
      timeTaken
    });
    
    // Check if any new level was unlocked
    const newUnlock = userLevel.unlockedLevels.find(level => 
      !req.body.previouslyUnlockedLevels?.includes(level)
    );
    
    res.json({
      success: true,
      levelStatus: {
        currentLevel: userLevel.currentLevel,
        unlockedLevels: userLevel.unlockedLevels,
        levelProgress: userLevel.levelProgress
      },
      newUnlock: newUnlock ? {
        level: newUnlock,
        message: `Congratulations! You've unlocked the ${newUnlock} level!`
      } : null
    });
    
  } catch (error) {
    console.error('❌ Game progress error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Manual level unlock (for admin/testing)
app.post('/api/ai/unlock-level', verifyToken, async (req, res) => {
  try {
    const userId = req.userId;
    const { level } = req.body;
    
    // Get user level document
    let userLevel = await UserLevel.findOne({ userId });
    
    if (!userLevel) {
      userLevel = new UserLevel({
        userId,
        currentLevel: "basic",
        unlockedLevels: ["basic"],
        levelProgress: {
          basic: { unlocked: true, unlockedAt: new Date() }
        }
      });
    }
    
    // Check if level is valid
    const validLevels = ['basic', 'easy', 'medium', 'hard'];
    if (!validLevels.includes(level)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid level'
      });
    }
    
    // Check prerequisites
    const previousLevel = getPreviousLevel(level);
    if (previousLevel) {
      // Check if previous level is unlocked and has sufficient progress
      if (!userLevel.unlockedLevels.includes(previousLevel)) {
        return res.status(400).json({
          success: false,
          error: `You must complete ${previousLevel} level first`
        });
      }
      
      const previousLevelData = userLevel.levelProgress[previousLevel];
      if (previousLevelData.accuracy < 80 && previousLevelData.attempts < 10) {
        return res.status(400).json({
          success: false,
          error: `You need 80% accuracy in ${previousLevel} level to unlock ${level}`
        });
      }
    }
    
    // Unlock the level
    if (!userLevel.unlockedLevels.includes(level)) {
      userLevel.unlockedLevels.push(level);
      userLevel.levelProgress[level].unlocked = true;
      userLevel.levelProgress[level].unlockedAt = new Date();
      
      // Update current level to the highest unlocked level
      const levelOrder = ['basic', 'easy', 'medium', 'hard'];
      for (let i = levelOrder.length - 1; i >= 0; i--) {
        if (userLevel.unlockedLevels.includes(levelOrder[i])) {
          userLevel.currentLevel = levelOrder[i];
          break;
        }
      }
      
      await userLevel.save();
    }
    
    res.json({
      success: true,
      message: `Level ${level} unlocked successfully!`,
      unlocked_level: level,
      next_level: getNextLevel(level),
      levelStatus: {
        currentLevel: userLevel.currentLevel,
        unlockedLevels: userLevel.unlockedLevels,
        levelProgress: userLevel.levelProgress
      }
    });
    
  } catch (error) {
    console.error('Error unlocking level:', error);
    res.status(500).json({ success: false, error: 'Failed to unlock level' });
  }
});

// Get detailed level analytics
app.get('/api/ai/level-analytics', verifyToken, async (req, res) => {
  try {
    const userId = req.userId;
    
    // Get level progress from GameAttempt collection
    const levelStats = {};
    const levels = ['basic', 'easy', 'medium', 'hard'];
    
    for (const level of levels) {
      const stats = await GameAttempt.getLevelStats(userId, level);
      levelStats[level] = stats;
    }
    
    // Get user level status
    const userLevel = await UserLevel.findOne({ userId });
    
    // Calculate which levels are unlocked
    const unlockedLevels = userLevel ? userLevel.unlockedLevels : ['basic'];
    
    // Determine current level (highest unlocked level)
    const levelOrder = ['basic', 'easy', 'medium', 'hard'];
    let currentLevel = 'basic';
    for (let i = levelOrder.length - 1; i >= 0; i--) {
      if (unlockedLevels.includes(levelOrder[i])) {
        currentLevel = levelOrder[i];
        break;
      }
    }
    
    // Check if next level can be unlocked
    let nextUnlockableLevel = null;
    let isNextLevelUnlockable = false;
    
    if (currentLevel !== 'hard') {
      const nextLevel = getNextLevel(currentLevel);
      const currentLevelStats = levelStats[currentLevel];
      
      if (currentLevelStats.accuracy >= 80 && currentLevelStats.total >= 10) {
        nextUnlockableLevel = nextLevel;
        isNextLevelUnlockable = true;
      }
    }
    
    res.json({
      success: true,
      analytics: {
        levelProgress: levelStats,
        unlockedLevels: unlockedLevels,
        currentLevel: currentLevel,
        nextUnlockableLevel: nextUnlockableLevel,
        isNextLevelUnlockable: isNextLevelUnlockable,
        progressToNextLevel: levelStats[currentLevel]?.accuracy || 0,
        requiredForNextLevel: 80
      }
    });
    
  } catch (error) {
    console.error('Error getting level analytics:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// ========================
// 404 HANDLER
// ========================
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found'
  });
});

// ========================
// ERROR HANDLER
// ========================
app.use((err, req, res, next) => {
  console.error('❌ Server Error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error'
  });
});

// ========================
// START SERVER
// ========================
const PORT = process.env.PORT || 5000;

const server = app.listen(PORT, () => {
  console.log('\n' + '='.repeat(70));
  console.log('🎮 Sinhala Sign Language Game - Backend Server');
  console.log('='.repeat(70));
  console.log(`🌐 Server:          http://localhost:${PORT}`);
  console.log(`📊 Health Check:    http://localhost:${PORT}/api/health`);
  console.log(`🔍 Quiz Test:       http://localhost:${PORT}/api/questions/quiz/2`);
  console.log(`🎯 Register:        http://localhost:${PORT}/api/register`);
  console.log('='.repeat(70));
  console.log(`🔐 JWT Security:    ✅ Enabled`);
  console.log(`🔒 Bcrypt Hashing:  ✅ Enabled`);
  console.log(`🗄️  Database:        ${mongoose.connection.name || 'Connecting...'}`);
  console.log('='.repeat(70) + '\n');
});

// ========================
// GRACEFUL SHUTDOWN
// ========================
process.on('SIGINT', async () => {
  console.log('\n⚠️ Shutting down gracefully...');
  await mongoose.connection.close();
  console.log('✅ MongoDB connection closed');
  server.close(() => process.exit(0));
});