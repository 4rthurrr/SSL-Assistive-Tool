// route/question_routes.js
const express = require('express');
const router = express.Router();
const mongoose = require('mongoose');

// Test endpoint
router.get('/test', (req, res) => {
  res.json({
    success: true,
    message: 'Question routes are working!'
  });
});

// Get quiz questions
router.get('/quiz/:grade', async (req, res) => {
  try {
    const grade = req.params.grade;
    console.log(`📚 Quiz request for Grade ${grade}`);
    
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

// Validate answers
router.post('/validate', async (req, res) => {
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
    
    const allQuestions = [];
    for (const gradeKey in quizData.grades || {}) {
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
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;