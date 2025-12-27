const Question = require('../model/question_model');

exports.getQuizForGrade = async (req, res) => {
  try {
    const { grade } = req.params;
    const gradeNumber = parseInt(grade);

    if (isNaN(gradeNumber) || gradeNumber < 2 || gradeNumber > 5) {
      return res.status(400).json({
        success: false,
        error: 'Invalid grade. Must be between 2 and 5.'
      });
    }

    console.log(`📚 Fetching 3 random questions for Grade ${gradeNumber}...`);

    const questions = await Question.aggregate([
      { $match: { grade: gradeNumber } },
      { $sample: { size: 3 } },
      {
        $project: {
          _id: 0,
          __v: 0
        }
      }
    ]);

    if (questions.length === 0) {
      return res.status(404).json({
        success: false,
        error: `No questions found for grade ${gradeNumber}`
      });
    }

    console.log(`✅ Found ${questions.length} questions`);

    const questionsForQuiz = questions.map(q => ({
      id: q.id,
      grade: q.grade,
      type: q.type,
      visualType: q.visualType,
      imageUrl: q.imageUrl || null,
      videoUrl: q.videoUrl || null,
      signDescription: q.signDescription || null,
      imageDescription: q.imageDescription || null,
      question: q.question,
      options: q.options,
      difficulty: q.difficulty
    }));

    res.json({
      success: true,
      grade: gradeNumber,
      questionCount: questions.length,
      questions: questionsForQuiz,
      answerKey: questions.map(q => ({
        id: q.id,
        correctAnswer: q.correctAnswer
      }))
    });

  } catch (error) {
    console.error('❌ Error fetching quiz:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch quiz questions',
      details: error.message
    });
  }
};

exports.validateQuizAnswers = async (req, res) => {
  try {
    const { answers } = req.body;
    
    if (!answers || !Array.isArray(answers)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid answers format'
      });
    }

    console.log(`🔍 Validating ${answers.length} answers...`);

    const questionIds = answers.map(a => a.id);
    const questions = await Question.find({ id: { $in: questionIds } })
      .select('id correctAnswer');

    const correctAnswersMap = {};
    questions.forEach(q => {
      correctAnswersMap[q.id] = q.correctAnswer;
    });

    const results = answers.map(answer => {
      const correct = correctAnswersMap[answer.id] === answer.selectedAnswer;
      return {
        id: answer.id,
        selectedAnswer: answer.selectedAnswer,
        correctAnswer: correctAnswersMap[answer.id],
        isCorrect: correct
      };
    });

    const correctCount = results.filter(r => r.isCorrect).length;
    const totalQuestions = results.length;
    const percentage = (correctCount / totalQuestions) * 100;

    console.log(`✅ Score: ${correctCount}/${totalQuestions}`);

    res.json({
      success: true,
      results: results,
      summary: {
        correct: correctCount,
        total: totalQuestions,
        percentage: percentage.toFixed(2)
      }
    });

  } catch (error) {
    console.error('❌ Error validating answers:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to validate answers'
    });
  }
};

exports.getAllQuestionsForGrade = async (req, res) => {
  try {
    const { grade } = req.params;
    const gradeNumber = parseInt(grade);

    if (isNaN(gradeNumber) || gradeNumber < 2 || gradeNumber > 5) {
      return res.status(400).json({
        success: false,
        error: 'Invalid grade'
      });
    }

    console.log(`📚 Fetching all questions for Grade ${gradeNumber}...`);

    const questions = await Question.find({ grade: gradeNumber })
      .select('-__v')
      .sort({ id: 1 });

    console.log(`✅ Found ${questions.length} questions`);

    res.json({
      success: true,
      grade: gradeNumber,
      totalQuestions: questions.length,
      questions: questions
    });

  } catch (error) {
    console.error('❌ Error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch questions'
    });
  }
};

exports.getQuizStatistics = async (req, res) => {
  try {
    console.log('📊 Calculating statistics...');

    const stats = await Question.aggregate([
      {
        $group: {
          _id: '$grade',
          totalQuestions: { $sum: 1 },
          imageQuestions: {
            $sum: { $cond: [{ $eq: ['$type', 'image_to_word'] }, 1, 0] }
          },
          videoQuestions: {
            $sum: { $cond: [{ $eq: ['$type', 'sign_to_word'] }, 1, 0] }
          }
        }
      },
      { $sort: { _id: 1 } }
    ]);

    const totalQuestions = await Question.countDocuments();

    console.log(`✅ Total: ${totalQuestions}`);

    res.json({
      success: true,
      totalQuestions: totalQuestions,
      byGrade: stats
    });

  } catch (error) {
    console.error('❌ Error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch statistics'
    });
  }
};