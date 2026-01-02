const mongoose = require("mongoose");

/**
 * ========================
 * GameAttempt Schema
 * ========================
 * This schema stores all game attempts for Sinhala Sign Language game.
 * It acts as the shared data source between Express.js and Flask backends.
 * 
 * DATA FLOW:
 * 1. Frontend authenticates with Express.js (port 5000)
 * 2. User gets MongoDB userId from Express.js
 * 3. Frontend sends userId to Flask (port 5001) when starting game
 * 4. Flask records game attempt in MongoDB using userId
 * 5. Flask analytics endpoints query MongoDB for user progress
 * 6. Express.js can also query game data for dashboard
 */

const gameAttemptSchema = new mongoose.Schema({
  // ========================
  // USER REFERENCE
  // ========================
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "usermodel",
    required: true,
    index: true // Index for fast queries
  },

  // ========================
  // GAME METADATA
  // ========================
  level: {
    type: String,
    enum: ["basic", "easy", "medium", "hard"],
    required: true,
    index: true
  },

  word: {
    type: String,
    required: true,
    index: true
  },

  sinhalaWord: {
    type: String,
    required: false
  },

  englishTranslation: {
    type: String,
    required: false
  },

  // ========================
  // ATTEMPT DETAILS
  // ========================
  correct: {
    type: Boolean,
    required: true,
    index: true // Index to quickly calculate accuracy
  },

  confidence: {
    type: Number, // 0-100: Model confidence score
    required: false,
    min: 0,
    max: 100
  },

  timeTaken: {
    type: Number, // Seconds
    required: false
  },

  attemptNumber: {
    type: Number, // 1st attempt, 2nd attempt, etc.
    default: 1
  },

  // ========================
  // FEEDBACK & HINTS
  // ========================
  hintsProvided: [{
    type: String,
    required: false
  }],

  feedbackGiven: {
    type: String,
    required: false
  },

  // ========================
  // TIMESTAMPS
  // ========================
  createdAt: {
    type: Date,
    default: Date.now,
    index: true // Index for time-series queries
  },

  updatedAt: {
    type: Date,
    default: Date.now
  },

  // ========================
  // SESSION INFO
  // ========================
  sessionId: {
    type: String,
    required: false // Allows grouping attempts in same session
  },

  // ========================
  // OPTIONAL: AI MODEL DATA
  // ========================
  modelVersion: {
    type: String,
    required: false
  },

  // Store additional ML features if needed
  features: {
    type: mongoose.Schema.Types.Mixed,
    required: false
  }
});

// ========================
// INDEXES FOR PERFORMANCE
// ========================
// Compound index for common queries
gameAttemptSchema.index({ userId: 1, createdAt: -1 });
gameAttemptSchema.index({ userId: 1, level: 1, correct: 1 });
gameAttemptSchema.index({ userId: 1, word: 1 });

// ========================
// METHODS
// ========================
/**
 * Calculate user's accuracy for a specific level
 */
gameAttemptSchema.statics.getLevelStats = async function(userId, level) {
  const stats = await this.aggregate([
    {
      $match: {
        userId: mongoose.Types.ObjectId(userId),
        level: level
      }
    },
    {
      $group: {
        _id: null,
        total: { $sum: 1 },
        correct: {
          $sum: {
            $cond: ["$correct", 1, 0]
          }
        },
        avgTime: { $avg: "$timeTaken" },
        avgConfidence: { $avg: "$confidence" }
      }
    }
  ]);

  if (stats.length === 0) {
    return {
      total: 0,
      correct: 0,
      accuracy: 0,
      avgTime: 0,
      avgConfidence: 0
    };
  }

  const data = stats[0];
  return {
    total: data.total,
    correct: data.correct,
    accuracy: data.correct / data.total * 100,
    avgTime: data.avgTime || 0,
    avgConfidence: data.avgConfidence || 0
  };
};

/**
 * Get word-level performance for a user
 */
gameAttemptSchema.statics.getWordStats = async function(userId) {
  const stats = await this.aggregate([
    {
      $match: {
        userId: mongoose.Types.ObjectId(userId)
      }
    },
    {
      $group: {
        _id: "$word",
        sinhalaWord: { $first: "$sinhalaWord" },
        englishTranslation: { $first: "$englishTranslation" },
        level: { $first: "$level" },
        total: { $sum: 1 },
        correct: {
          $sum: {
            $cond: ["$correct", 1, 0]
          }
        },
        avgTime: { $avg: "$timeTaken" },
        lastAttempt: { $max: "$createdAt" }
      }
    },
    {
      $project: {
        word: "$_id",
        sinhalaWord: 1,
        englishTranslation: 1,
        level: 1,
        total: 1,
        correct: 1,
        accuracy: {
          $multiply: [
            {
              $divide: ["$correct", "$total"]
            },
            100
          ]
        },
        avgTime: { $round: ["$avgTime", 2] },
        lastAttempt: 1
      }
    },
    {
      $sort: { lastAttempt: -1 }
    }
  ]);

  return stats;
};

/**
 * Get overall user stats
 */
gameAttemptSchema.statics.getUserStats = async function(userId) {
  const stats = await this.aggregate([
    {
      $match: {
        userId: mongoose.Types.ObjectId(userId)
      }
    },
    {
      $group: {
        _id: null,
        totalAttempts: { $sum: 1 },
        correctAttempts: {
          $sum: {
            $cond: ["$correct", 1, 0]
          }
        },
        uniqueWords: { $addToSet: "$word" },
        avgTime: { $avg: "$timeTaken" },
        avgConfidence: { $avg: "$confidence" },
        firstAttempt: { $min: "$createdAt" },
        lastAttempt: { $max: "$createdAt" }
      }
    },
    {
      $project: {
        totalAttempts: 1,
        correctAttempts: 1,
        wordsLearned: { $size: "$uniqueWords" },
        overallAccuracy: {
          $multiply: [
            {
              $divide: ["$correctAttempts", "$totalAttempts"]
            },
            100
          ]
        },
        avgTime: { $round: ["$avgTime", 2] },
        avgConfidence: { $round: ["$avgConfidence", 2] },
        firstAttempt: 1,
        lastAttempt: 1
      }
    }
  ]);

  if (stats.length === 0) {
    return null;
  }

  return stats[0];
};

/**
 * Get recent attempts for a user (for activity feed, etc.)
 */
gameAttemptSchema.statics.getRecentAttempts = async function(userId, limit = 10) {
  return await this.find({ userId })
    .sort({ createdAt: -1 })
    .limit(limit)
    .lean();
};

/**
 * Get attempts for a specific date range
 */
gameAttemptSchema.statics.getAttemptsByDateRange = async function(userId, startDate, endDate) {
  return await this.find({
    userId,
    createdAt: {
      $gte: startDate,
      $lte: endDate
    }
  }).lean();
};

module.exports = mongoose.model("GameAttempt", gameAttemptSchema);
