const mongoose = require("mongoose");

const gameProfileSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "usermodel",
    required: true,
    unique: true
  },
  userType: {
    type: String,
    enum: ["student", "parent"],
    required: true,
    default: "student"
  },
  grade: {
    type: String,
    required: true,
    default: "2"
  },
  recommendedLevel: {
    type: String,
    enum: ["basic", "easy", "medium", "hard"],
    default: "basic"
  },
  hasTakenQuiz: {
    type: Boolean,
    default: false
  },
  quizScore: {
    type: Number,
    default: 0
  },
  quizTotal: {
    type: Number,
    default: 0
  },
  quizPercentage: {
    type: Number,
    default: 0
  },
  quizCompletedAt: {
    type: Date
  },
  // ... rest of the schema remains same
});

module.exports = mongoose.model("GameProfile", gameProfileSchema);