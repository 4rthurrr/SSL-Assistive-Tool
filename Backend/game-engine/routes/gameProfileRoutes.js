// route/gameProfileRoutes.js
const express = require("express");
const router = express.Router();
const GameProfile = require("../models/GameProfile");

// RESEARCH CONTRIBUTION
// Game-profile API exposing per-learner state used to personalize game difficulty
// Get profile by userId
router.get("/profile/:userId", async (req, res) => {
  try {
    const profile = await GameProfile.findOne({ userId: req.params.userId });
    
    if (!profile) {
      return res.status(404).json({
        success: false,
        error: "Profile not found"
      });
    }

    res.json({
      success: true,
      profile
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// RESEARCH CONTRIBUTION
// Upsert profile including recommendedLevel used by adaptive game mode selection
// Create or update profile
router.post("/profile", async (req, res) => {
  try {
    const { userId, userType, grade, recommendedLevel } = req.body;

    const profile = await GameProfile.findOneAndUpdate(
      { userId },
      { 
        userType, 
        grade,
        recommendedLevel: recommendedLevel || 'basic'
      },
      { 
        upsert: true, 
        new: true,
        setDefaultsOnInsert: true
      }
    );

    res.json({
      success: true,
      profile
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// MANUAL IMPLEMENTATION
// Endpoint to adjust recommendedLevel based on external analytics or teacher input
// Update recommended level
router.patch("/profile/:userId/level", async (req, res) => {
  try {
    const { recommendedLevel } = req.body;
    
    const profile = await GameProfile.findOneAndUpdate(
      { userId: req.params.userId },
      { recommendedLevel },
      { new: true }
    );

    if (!profile) {
      return res.status(404).json({
        success: false,
        error: "Profile not found"
      });
    }

    res.json({
      success: true,
      profile
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get all profiles (admin)
router.get("/profiles", async (req, res) => {
  try {
    const profiles = await GameProfile.find()
      .populate('userId', 'name email')
      .sort({ createdAt: -1 });
    
    res.json({
      success: true,
      count: profiles.length,
      profiles
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;