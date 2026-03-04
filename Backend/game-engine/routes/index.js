// features/games/routes/index.js
// Aggregates all game-related routes
const express = require('express');
const router = express.Router();

const gameProfileRoutes = require('./gameProfileRoutes');
const questionRoutes    = require('./question_routes');

router.use('/game-profile', gameProfileRoutes);
router.use('/questions',    questionRoutes);

module.exports = router;
