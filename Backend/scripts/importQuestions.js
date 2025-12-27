// // scripts/importQuestions.js
// // Run this ONCE to import questions to MongoDB
// // Usage: node scripts/importQuestions.js

// const mongoose = require('mongoose');
// const fs = require('fs');
// const path = require('path');

// // MongoDB connection
// const MONGODB_URI = 'mongodb+srv://dulmiwitharana:uS1LtYnTvcWkmJtU@cluster0.8tb8jax.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0';

// // Path to questions.json
// const QUESTIONS_FILE = path.join(__dirname, '../data/questions.json');

// // Question Schema
// const questionSchema = new mongoose.Schema({
//   id: { type: String, required: true, unique: true },
//   grade: { type: Number, required: true, min: 2, max: 5 },
//   type: { type: String, enum: ['image_to_word', 'sign_to_word'], required: true },
//   visualType: { type: String, enum: ['image', 'video'], required: true },
//   imageUrl: String,
//   videoUrl: String,
//   signDescription: String,
//   imageDescription: String,
//   question: { type: String, required: true },
//   options: { type: [String], required: true },
//   correctAnswer: { type: String, required: true },
//   difficulty: { type: String, enum: ['easy', 'medium', 'hard'], required: true },
//   createdAt: { type: Date, default: Date.now },
//   updatedAt: { type: Date, default: Date.now }
// });

// const Question = mongoose.model('Question', questionSchema);

// async function importQuestions() {
//   try {
//     // Connect
//     console.log('🔌 Connecting to MongoDB...');
//     await mongoose.connect(MONGODB_URI);
//     console.log('✅ Connected\n');

//     // Read file
//     console.log('📖 Reading questions.json...');
//     const rawData = fs.readFileSync(QUESTIONS_FILE, 'utf8');
//     const data = JSON.parse(rawData);

//     // Extract questions
//     const allQuestions = [];
//     const grades = data.quizDatabase.grades;

//     for (const gradeKey in grades) {
//       const gradeData = grades[gradeKey];
//       const gradeNumber = gradeData.level;
      
//       console.log(`\n📚 Grade ${gradeNumber}...`);
      
//       gradeData.questions.forEach(q => {
//         allQuestions.push({
//           id: q.id,
//           grade: gradeNumber,
//           type: q.type,
//           visualType: q.visualType,
//           imageUrl: q.imageUrl || null,
//           videoUrl: q.videoUrl || null,
//           signDescription: q.signDescription || null,
//           imageDescription: q.imageDescription || null,
//           question: q.question,
//           options: q.options,
//           correctAnswer: q.correctAnswer,
//           difficulty: q.difficulty
//         });
//       });
      
//       console.log(`   ✓ ${gradeData.questions.length} questions`);
//     }

//     console.log(`\n📊 Total: ${allQuestions.length} questions`);

//     // Clear old data
//     console.log('\n🗑️  Clearing old questions...');
//     await Question.deleteMany({});
//     console.log('   ✓ Cleared');

//     // Insert new data
//     console.log('\n💾 Inserting questions...');
//     const result = await Question.insertMany(allQuestions);
//     console.log(`   ✓ Inserted ${result.length} questions`);

//     // Show stats
//     console.log('\n📈 Statistics:');
//     const stats = await Question.aggregate([
//       {
//         $group: {
//           _id: '$grade',
//           count: { $sum: 1 },
//           imageQuestions: {
//             $sum: { $cond: [{ $eq: ['$type', 'image_to_word'] }, 1, 0] }
//           },
//           videoQuestions: {
//             $sum: { $cond: [{ $eq: ['$type', 'sign_to_word'] }, 1, 0] }
//           }
//         }
//       },
//       { $sort: { _id: 1 } }
//     ]);

//     stats.forEach(stat => {
//       console.log(`   Grade ${stat._id}: ${stat.count} total (${stat.imageQuestions} image, ${stat.videoQuestions} video)`);
//     });

//     console.log('\n✅ Import completed!\n');
    
//   } catch (error) {
//     console.error('❌ Import failed:', error);
//     process.exit(1);
//   } finally {
//     await mongoose.connection.close();
//     console.log('🔌 Connection closed');
//   }
// }

// // Run
// importQuestions();

