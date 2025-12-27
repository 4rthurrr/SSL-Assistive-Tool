const mongoose = require('mongoose');

const questionSchema = new mongoose.Schema(
  {
    id: {
      type: String,
      required: true,
      unique: true
    },

    grade: {
      type: Number,
      required: true,
      min: 2,
      max: 5
    },

    type: {
      type: String,
      enum: ['image_to_word', 'sign_to_word'],
      required: true
    },

    visualType: {
      type: String,
      enum: ['image', 'video'],
      required: true
    },

    imageUrl: {
      type: String
    },

    videoUrl: {
      type: String
    },

    signDescription: {
      type: String
    },

    imageDescription: {
      type: String
    },

    question: {
      type: String,
      required: true
    },

    options: {
      type: [String],
      required: true,
      validate: {
        validator: v => v.length === 4,
        message: 'Must have exactly 4 options'
      }
    },

    correctAnswer: {
      type: String,
      required: true
    },

    difficulty: {
      type: String,
      enum: ['easy', 'medium', 'hard'],
      required: true
    }
  },
  {
    timestamps: true // auto adds createdAt & updatedAt
  }
);

// Performance index (VALID & useful)
questionSchema.index({ grade: 1, difficulty: 1 });

module.exports = mongoose.model('Question', questionSchema);
