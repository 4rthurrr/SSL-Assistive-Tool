const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const userRoutes = require('./route/userroutes');
const gameProfileRoutes = require('./route/gameProfileRoutes');

const app = express();

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
    await mongoose.connect(MONGODB_URI);
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
// QUESTION/QUIZ ROUTES (INLINE - NO EXTERNAL FILE)
// ========================
app.get('/api/questions/test', (req, res) => {
  res.json({
    success: true,
    message: 'Question routes are working inline!'
  });
});

app.get('/api/questions/quiz/:grade', async (req, res) => {
  try {
    const grade = req.params.grade;
    console.log(`📚 Quiz request for Grade ${grade}`);
    
    // Check MongoDB connection
    if (mongoose.connection.readyState !== 1) {
      return res.status(500).json({
        success: false,
        error: 'Database not connected'
      });
    }
    
    // Use the correct collection name: 'questions'
    const questionsCollection = mongoose.connection.db.collection('questions');
    
    // Try to find any document in the questions collection
    const quizDoc = await questionsCollection.findOne({});
    
    console.log('📄 Questions doc found:', quizDoc ? 'YES' : 'NO');
    
    if (!quizDoc) {
      return res.status(404).json({
        success: false,
        error: 'No quiz data found in questions collection'
      });
    }
    
    console.log('📄 Document structure keys:', Object.keys(quizDoc));
    
    // Check the structure - from your data, it has a quizDatabase field
    let quizData = quizDoc;
    
    // If the document has a quizDatabase field, use that
    if (quizDoc.quizDatabase) {
      quizData = quizDoc.quizDatabase;
      console.log('✅ Using nested quizDatabase field');
    }
    
    // Check if we have grades
    if (!quizData.grades) {
      return res.status(404).json({
        success: false,
        error: 'No grades found in quiz data',
        availableKeys: Object.keys(quizData)
      });
    }
    
    // Get the specific grade
    const gradeKey = `grade${grade}`;
    const gradeData = quizData.grades[gradeKey];
    
    if (!gradeData) {
      return res.status(404).json({
        success: false,
        error: `Grade ${grade} not found`,
        availableGrades: Object.keys(quizData.grades)
      });
    }
    
    const questions = gradeData.questions || [];
    
    if (questions.length === 0) {
      return res.status(404).json({
        success: false,
        error: `No questions found for Grade ${grade}`
      });
    }
    
    // Select 3 random questions
    const shuffled = [...questions].sort(() => 0.5 - Math.random());
    const selected = shuffled.slice(0, 3);
    
    console.log(`✅ Returning ${selected.length} questions for Grade ${grade}`);
    
    res.json({
      success: true,
      grade: grade,
      questionCount: selected.length,
      totalAvailable: questions.length,
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
      })),
      answerKey: selected.map(q => ({
        id: q.id,
        correctAnswer: q.correctAnswer
      }))
    });
    
  } catch (error) {
    console.error('❌ Quiz error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

app.post('/api/questions/validate', async (req, res) => {
  try {
    const { answers } = req.body;
    
    if (!answers || !Array.isArray(answers)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid answers format'
      });
    }
    
    console.log(`🔍 Validating ${answers.length} answers`);
    
    // Get quiz data from questions collection
    const questionsCollection = mongoose.connection.db.collection('questions');
    const quizDoc = await questionsCollection.findOne({});
    
    if (!quizDoc) {
      return res.status(404).json({
        success: false,
        error: 'Quiz data not found'
      });
    }
    
    // Handle nested structure
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
    
    // Collect all questions from all grades
    const allQuestions = [];
    for (const gradeKey in quizData.grades) {
      if (quizData.grades[gradeKey].questions) {
        allQuestions.push(...quizData.grades[gradeKey].questions);
      }
    }
    
    // Validate each answer
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
    
    console.log(`✅ Score: ${correctCount}/${total} (${percentage}%)`);
    
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
// REGISTRATION ENDPOINT
// ========================
const User = require('./model/usermodel');
const GameProfile = require('./model/GameProfile');

// Update the registration endpoint
app.post('/api/register', async (req, res) => {
  try {
    const { name, user_type, grade } = req.body;

    if (!name) {
      return res.status(400).json({ 
        success: false, 
        error: 'Name is required' 
      });
    }

    // Check if user already exists
    const existingUser = await User.findOne({ 
      email: `${name.toLowerCase().replace(/\s+/g, '')}@game.local` 
    });

    if (existingUser) {
      // User exists, get their profile
      const gameProfile = await GameProfile.findOne({ userId: existingUser._id });
      
      return res.json({
        success: true,
        user_id: existingUser._id,
        mongo_id: gameProfile?._id || null,
        name: existingUser.name,
        hasTakenQuiz: existingUser.hasTakenQuiz || false,
        recommendedLevel: existingUser.recommendedLevel || 'basic',
        message: 'User already exists'
      });
    }

    // Create new user
    const email = `${name.toLowerCase().replace(/\s+/g, '')}@game.local`;
    const password = 'gameuser123';
    const age = grade ? parseInt(grade) + 6 : 10;

    const mongoUser = new User({
      name: name,
      email: email,
      password: password,
      age: age,
      hasTakenQuiz: false
    });
    
    await mongoUser.save();

    // Create game profile
    const gameProfile = new GameProfile({
      userId: mongoUser._id,
      userType: user_type || 'student',
      grade: grade || '2',
      recommendedLevel: 'basic',
      hasTakenQuiz: false
    });

    await gameProfile.save();

    console.log(`✅ Registered: ${name} (${user_type}, Grade ${grade})`);

    res.json({
      success: true,
      user_id: mongoUser._id,
      mongo_id: gameProfile._id.toString(),
      name: mongoUser.name,
      hasTakenQuiz: false,
      recommendedLevel: 'basic',
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

// Update quiz submission endpoint
app.post('/api/quiz/submit', async (req, res) => {
  try {
    const { user_id, answers, recommendedLevel, quizScore, quizTotal, quizPercentage } = req.body;

    console.log(`📝 Quiz submitted by ${user_id}: ${quizScore}/${quizTotal} (${quizPercentage}%)`);
    console.log(`🎯 Recommended Level: ${recommendedLevel}`);

    // Update user
    await User.findByIdAndUpdate(user_id, {
      hasTakenQuiz: true,
      quizCompletedAt: new Date(),
      recommendedLevel: recommendedLevel
    });

    // Update game profile
    await GameProfile.findOneAndUpdate(
      { userId: user_id },
      {
        hasTakenQuiz: true,
        quizScore: quizScore,
        quizTotal: quizTotal,
        quizPercentage: quizPercentage,
        quizCompletedAt: new Date(),
        recommendedLevel: recommendedLevel
      }
    );

    res.json({
      success: true,
      message: 'Quiz results saved',
      recommendedLevel: recommendedLevel
    });

  } catch (error) {
    console.error('❌ Quiz submission error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Add this endpoint in your server.js after other routes
app.get('/api/user/:userId/quiz-status', async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Check if user exists
    const User = require('./model/usermodel');
    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }
    
    // Check game profile
    const GameProfile = require('./model/GameProfile');
    const profile = await GameProfile.findOne({ userId });
    
    res.json({
      success: true,
      hasTakenQuiz: profile ? profile.hasTakenQuiz : false,
      recommendedLevel: profile ? profile.recommendedLevel : 'basic',
      name: user.name,
      profile: profile
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ========================
// DEBUG ENDPOINT
// ========================
app.get('/api/test-questions', async (req, res) => {
  try {
    const collections = await mongoose.connection.db.listCollections().toArray();
    const collectionNames = collections.map(c => c.name);
    
    // Try to get quiz data
    const quizCollection = mongoose.connection.db.collection('quizDatabase');
    const count = await quizCollection.countDocuments();
    const allDocs = await quizCollection.find({}).limit(5).toArray();
    
    res.json({
      success: true,
      message: 'Backend is working',
      collections: collectionNames,
      quizDatabase: {
        documentCount: count,
        sampleDocs: allDocs.map(doc => ({
          _id: doc._id,
          hasQuizDatabase: !!doc.quizDatabase,
          hasGrades: !!doc.grades,
          topLevelKeys: Object.keys(doc)
        }))
      }
    });
  } catch (error) {
    res.json({
      success: false,
      error: error.message
    });
  }
});


// ========================
// 404 HANDLER
// ========================
app.use((req, res) => {
  console.log(`⚠️ 404 Not Found: ${req.method} ${req.path}`);
  res.status(404).json({
    success: false,
    error: 'Route not found',
    requested_path: req.path,
    method: req.method
  });
});

// ========================
// ERROR HANDLER
// ========================
app.use((err, req, res, next) => {
  console.error('❌ Server Error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: err.message
  });
});

// ========================
// START SERVER
// ========================
const PORT = process.env.PORT || 5000;

const server = app.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🎮 Sinhala Sign Language Game - Backend');
  console.log(`🌐 Server: http://localhost:${PORT}`);
  console.log(`📊 Health: http://localhost:${PORT}/api/health`);
  console.log(`🧪 Test: http://localhost:${PORT}/api/questions/test`);
  console.log(`📝 Quiz: http://localhost:${PORT}/api/questions/quiz/2`);
  console.log(`👤 Login: http://localhost:${PORT}/users/login`);
  console.log(`🎯 Register: http://localhost:${PORT}/api/register`);
  console.log('='.repeat(60) + '\n');
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