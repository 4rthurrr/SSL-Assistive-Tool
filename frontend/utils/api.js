// API Helper to make authenticated requests

const API_BASE_URL = "http://localhost:5000";

// Get token from localStorage
const getToken = () => {
  return localStorage.getItem('token');
};

// Make authenticated API request
export const apiRequest = async (endpoint, options = {}) => {
  const token = getToken();
  
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const data = await response.json();

    // Handle token expiration
    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
      throw new Error('Session expired. Please login again.');
    }

    return { response, data };
  } catch (error) {
    console.error('API Request Error:', error);
    throw error;
  }
};

// Specific API methods
export const api = {
  // Get all users (protected)
  getAllUsers: async () => {
    const { data } = await apiRequest('/users', { method: 'GET' });
    return data;
  },

  // Get user by ID (protected)
  getUserById: async (id) => {
    const { data } = await apiRequest(`/users/${id}`, { method: 'GET' });
    return data;
  },

  // Update user (protected)
  updateUser: async (id, userData) => {
    const { data } = await apiRequest(`/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
    return data;
  },

  // Delete user (protected)
  deleteUser: async (id) => {
    const { data } = await apiRequest(`/users/${id}`, { method: 'DELETE' });
    return data;
  },
};

// Check if user is authenticated
export const isAuthenticated = () => {
  const token = getToken();
  return !!token;
};

// Logout user
export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('gameUser');
  localStorage.removeItem('gameUserId');
  window.location.href = '/login';
};

export default api;