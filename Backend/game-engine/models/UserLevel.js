const mongoose = require("mongoose");

const userLevelSchema = new mongoose.Schema({
  // ========================
  // USER REFERENCE
  // ========================
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "usermodel",
    required: true,
    index: true
  },

  // ========================
  // LEVEL PROGRESSION
  // ========================
  currentLevel: {
    type: String,
    enum: ["basic", "easy", "medium", "hard"],
    default: "basic",
    required: true
  },

  unlockedLevels: {
    type: [String],
    enum: ["basic", "easy", "medium", "hard"],
    default: ["basic"],
    required: true
  },

  // ========================
  // LEVEL PROGRESS TRACKING
  // ========================
  levelProgress: {
    basic: {
      accuracy: { type: Number, default: 0 },
      attempts: { type: Number, default: 0 },
      correct: { type: Number, default: 0 },
      unlocked: { type: Boolean, default: true },
      unlockedAt: { type: Date }
    },
    easy: {
      accuracy: { type: Number, default: 0 },
      attempts: { type: Number, default: 0 },
      correct: { type: Number, default: 0 },
      unlocked: { type: Boolean, default: false },
      unlockedAt: { type: Date }
    },
    medium: {
      accuracy: { type: Number, default: 0 },
      attempts: { type: Number, default: 0 },
      correct: { type: Number, default: 0 },
      unlocked: { type: Boolean, default: false },
      unlockedAt: { type: Date }
    },
    hard: {
      accuracy: { type: Number, default: 0 },
      attempts: { type: Number, default: 0 },
      correct: { type: Number, default: 0 },
      unlocked: { type: Boolean, default: false },
      unlockedAt: { type: Date }
    }
  },

  // ========================
  // OVERALL STATS
  // ========================
  totalAccuracy: {
    type: Number,
    default: 0
  },

  totalAttempts: {
    type: Number,
    default: 0
  },

  totalCorrect: {
    type: Number,
    default: 0
  },

  // ========================
  // TIMESTAMPS
  // ========================
  createdAt: {
    type: Date,
    default: Date.now
  },

  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// ========================
// METHODS
// ========================
userLevelSchema.statics.updateUserProgress = async function(userId, gameData) {
  const { level, correct, word, timeTaken } = gameData;
  
  // Get or create user level document
  let userLevel = await this.findOne({ userId });
  
  if (!userLevel) {
    userLevel = new this({
      userId,
      currentLevel: "basic",
      unlockedLevels: ["basic"],
      levelProgress: {
        basic: { unlocked: true, unlockedAt: new Date() }
      }
    });
  }
  
  // Update level stats
  if (userLevel.levelProgress[level]) {
    const levelData = userLevel.levelProgress[level];
    levelData.attempts += 1;
    if (correct) levelData.correct += 1;
    levelData.accuracy = levelData.attempts > 0 
      ? (levelData.correct / levelData.attempts) * 100 
      : 0;
  }
  
  // Update overall stats
  userLevel.totalAttempts += 1;
  if (correct) userLevel.totalCorrect += 1;
  userLevel.totalAccuracy = userLevel.totalAttempts > 0
    ? (userLevel.totalCorrect / userLevel.totalAttempts) * 100
    : 0;
  
  // Check for level unlocking
  await this.checkAndUnlockLevels(userLevel, level);
  
  userLevel.updatedAt = new Date();
  await userLevel.save();
  
  return userLevel;
};

userLevelSchema.statics.checkAndUnlockLevels = async function(userLevel, currentLevel) {
  const levelOrder = ["basic", "easy", "medium", "hard"];
  const UNLOCK_THRESHOLD = 80; // 80% accuracy
  
  // Check if current level qualifies for next level
  const currentIndex = levelOrder.indexOf(currentLevel);
  if (currentIndex < levelOrder.length - 1) {
    const nextLevel = levelOrder[currentIndex + 1];
    
    // Check if next level is already unlocked
    if (!userLevel.unlockedLevels.includes(nextLevel)) {
      const currentLevelData = userLevel.levelProgress[currentLevel];
      
      // Need at least 10 attempts to consider unlocking next level
      if (currentLevelData.attempts >= 10 && currentLevelData.accuracy >= UNLOCK_THRESHOLD) {
        // Unlock the next level
        userLevel.unlockedLevels.push(nextLevel);
        userLevel.levelProgress[nextLevel].unlocked = true;
        userLevel.levelProgress[nextLevel].unlockedAt = new Date();
        userLevel.currentLevel = nextLevel; // Auto-switch to newly unlocked level
        
        console.log(`🎉 Level ${nextLevel} unlocked for user ${userLevel.userId}`);
      }
    }
  }
  
  // Update current level to highest unlocked level
  for (let i = levelOrder.length - 1; i >= 0; i--) {
    if (userLevel.unlockedLevels.includes(levelOrder[i])) {
      userLevel.currentLevel = levelOrder[i];
      break;
    }
  }
};

userLevelSchema.statics.getUserLevelStatus = async function(userId) {
  const userLevel = await this.findOne({ userId });
  
  if (!userLevel) {
    // Return default status for new user
    return {
      currentLevel: "basic",
      unlockedLevels: ["basic"],
      levelProgress: {
        basic: { accuracy: 0, attempts: 0, correct: 0, unlocked: true },
        easy: { accuracy: 0, attempts: 0, correct: 0, unlocked: false },
        medium: { accuracy: 0, attempts: 0, correct: 0, unlocked: false },
        hard: { accuracy: 0, attempts: 0, correct: 0, unlocked: false }
      }
    };
  }
  
  return {
    currentLevel: userLevel.currentLevel,
    unlockedLevels: userLevel.unlockedLevels,
    levelProgress: userLevel.levelProgress,
    overallStats: {
      totalAccuracy: userLevel.totalAccuracy,
      totalAttempts: userLevel.totalAttempts,
      totalCorrect: userLevel.totalCorrect
    }
  };
};

module.exports = mongoose.model("UserLevel", userLevelSchema);