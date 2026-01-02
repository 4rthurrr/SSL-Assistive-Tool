// D:\Game new\Backend\basic-server.js
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Simple health endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    message: 'Server is running!',
    timestamp: new Date().toISOString()
  });
});

// Quiz endpoint
app.get('/api/questions/quiz/:grade', (req, res) => {
  const grade = req.params.grade;
  
  console.log(`📚 Quiz request for grade ${grade}`);
  
  // Mock questions for testing
  const mockQuestions = [
    {
      id: 'q1',
      type: 'multiple_choice',
      visualType: 'image',
      imageUrl: 'https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=Sign+1',
      question: 'What does this sign mean?',
      options: ['Hello', 'Thank you', 'Goodbye', 'Please'],
      correctAnswer: 'Hello',
      difficulty: 'easy',
      grade: parseInt(grade)
    },
    {
      id: 'q2',
      type: 'multiple_choice',
      visualType: 'video',
      videoUrl: '/videos/eating.mp4',
      question: 'What is this action?',
      options: ['Eating', 'Drinking', 'Sleeping', 'Playing'],
      correctAnswer: 'Eating',
      difficulty: 'medium',
      grade: parseInt(grade)
    },
    {
      id: 'q3',
      type: 'multiple_choice',
      visualType: 'image',
      imageUrl: 'https://via.placeholder.com/300x200/2196F3/FFFFFF?text=Sign+2',
      question: 'What does this sign represent?',
      options: ['School', 'Book', 'Teacher', 'Student'],
      correctAnswer: 'School',
      difficulty: 'medium',
      grade: parseInt(grade)
    }
  ];
  
  res.json({
    success: true,
    grade: grade,
    questionCount: mockQuestions.length,
    questions: mockQuestions,
    isMockData: true
  });
});

// Registration endpoint
app.post('/api/register', (req, res) => {
  const { name, user_type, grade } = req.body;
  
  console.log(`👤 Registration: ${name} (Grade ${grade})`);
  
  if (!name) {
    return res.status(400).json({
      success: false,
      error: 'Name is required'
    });
  }
  
  res.json({
    success: true,
    user_id: 'user_' + Date.now(),
    name: name,
    hasTakenQuiz: false,
    recommendedLevel: 'basic',
    message: 'Registration successful (mock data)'
  });
});

// Quiz validation endpoint
app.post('/api/questions/validate', (req, res) => {
  const { answers } = req.body;
  
  console.log(`✅ Validating ${answers?.length || 0} answers`);
  
  // Mock validation
  const results = answers?.map(answer => ({
    id: answer.id,
    selectedAnswer: answer.selectedAnswer,
    correctAnswer: 'Hello', // Mock correct answer
    correct: Math.random() > 0.5 // Random result for testing
  })) || [];
  
  const correctCount = results.filter(r => r.correct).length;
  const total = results.length;
  const percentage = total > 0 ? (correctCount / total * 100).toFixed(2) : '0.00';
  
  res.json({
    success: true,
    results: results,
    summary: {
      correct: correctCount,
      total: total,
      percentage: percentage
    }
  });
});

// Quiz submission
app.post('/api/quiz/submit', (req, res) => {
  const { user_id, recommendedLevel, quizScore, quizTotal } = req.body;
  
  console.log(`📝 Quiz submitted by ${user_id}: ${quizScore}/${quizTotal}`);
  
  res.json({
    success: true,
    message: 'Quiz results saved',
    recommendedLevel: recommendedLevel || 'basic'
  });
});

// User quiz status
app.get('/api/user/:userId/quiz-status', (req, res) => {
  const userId = req.params.userId;
  
  console.log(`🔍 Checking status for user: ${userId}`);
  
  res.json({
    success: true,
    hasTakenQuiz: false,
    recommendedLevel: 'basic',
    name: 'Test User'
  });
});

// Start server
const PORT = 5000;
app.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🎮 SINHALA SIGN LANGUAGE GAME - TEST SERVER');
  console.log('='.repeat(60));
  console.log(`🌐 Server: http://localhost:${PORT}`);
  console.log(`✅ Health: http://localhost:${PORT}/api/health`);
  console.log(`📝 Quiz:   http://localhost:${PORT}/api/questions/quiz/2`);
  console.log(`👤 Register: POST http://localhost:${PORT}/api/register`);
  console.log('='.repeat(60));
  console.log('⚠️  This is a TEST server with mock data');
  console.log('='.repeat(60) + '\n');
});