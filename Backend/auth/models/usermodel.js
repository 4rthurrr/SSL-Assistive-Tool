const mongoose = require("mongoose");
const Schema = mongoose.Schema;

const userSchema = new Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  age: { type: Number, required: true },
  hasTakenQuiz: { type: Boolean, default: false },
  quizCompletedAt: { type: Date },
  recommendedLevel: { 
    type: String, 
    enum: ["basic", "easy", "medium", "hard"],
    default: "basic" 
  }
});

module.exports = mongoose.model("usermodel", userSchema);