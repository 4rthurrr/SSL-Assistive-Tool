// API base URLs
export const API_URLS = {
  // Primary backend app (Flask) runs on port 5001 in this workspace
  auth:       'http://localhost:5001',
  game:       'http://localhost:5001/api',
  translator: 'http://localhost:5002',
  ai:         'http://localhost:5001/api',
  sentence:   'http://localhost:5003/api',
};

// Auth helpers
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

// Generic fetch wrapper
const request = async (url, options = {}) => {
  const res = await fetch(url, {
    headers: getAuthHeaders(),
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Request failed');
  return data;
};

// Auth API
export const authAPI = {
  login:    (form) => request(`${API_URLS.auth}/users/login`,  { method: 'POST', body: JSON.stringify(form) }),
  register: (form) => request(`${API_URLS.auth}/users`,        { method: 'POST', body: JSON.stringify(form) }),
};

// Game API
export const gameAPI = {
  getQuestions: (grade)     => request(`${API_URLS.game}/questions/quiz/${grade}`),
  getProfile:   (userId)    => request(`${API_URLS.game}/game-profile/profile/${userId}`),
  saveAttempt:  (data)      => request(`${API_URLS.game}/game-profile/attempt`, { method: 'POST', body: JSON.stringify(data) }),
};

// Translator API
export const translatorAPI = {
  translate: (text) => request(`${API_URLS.translator}/translate`, { method: 'POST', body: JSON.stringify({ text }) }),
};

// AI API
export const aiAPI = {
  generateHint: (word)  => request(`${API_URLS.ai}/ai/generate-hint`, { method: 'POST', body: JSON.stringify({ word }) }),
  getAnalytics: (userId) => request(`${API_URLS.ai}/analytics/${userId}`),
};
