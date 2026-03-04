// API Endpoints
export const API_BASE = {
  AUTH:       'http://localhost:5000',
  GAME:       'http://localhost:5000/api',
  TRANSLATOR: 'http://localhost:5002',
  AI:         'http://localhost:5001/api',
  SENTENCE:   'http://localhost:5003/api',
};

// Game levels
export const GAME_LEVELS = ['basic', 'easy', 'medium', 'hard', 'expert'];

// Local storage keys
export const STORAGE_KEYS = {
  TOKEN:     'token',
  USER:      'user',
  GAME_USER: 'gameUser',
};

// Routes
export const ROUTES = {
  HOME:           '/',
  LOGIN:          '/login',
  REGISTER:       '/register',
  SSL_TRANSLATOR: '/ssl-translator',
  TRANSLATE:      '/translate',
  GAME_REGISTER:  '/game-register',
  GAME_SELECTION: '/gameselection',
  PUZZLE:         '/game/puzzle',
  SENTENCE:       '/game/sentence',
  ANALYTICS:      '/ai-analytics',
};
