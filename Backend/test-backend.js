// test-backend.js
const axios = require('axios');

const API_URL = 'http://localhost:5000/api';

async function testEndpoints() {
  try {
    console.log('🔍 Testing backend endpoints...\n');
    
    // Test health endpoint
    const health = await axios.get(`${API_URL}/health`);
    console.log('✅ Health endpoint:', health.data);
    
    // Test questions endpoint (without auth)
    try {
      const questions = await axios.get(`${API_URL}/questions/quiz/2`);
      console.log('✅ Quiz endpoint (no auth):', 'WORKING');
      console.log('   Questions found:', questions.data.questions?.length || 0);
    } catch (error) {
      if (error.response?.status === 401) {
        console.log('❌ Quiz endpoint: REQUIRES AUTH');
      } else {
        console.log('❌ Quiz endpoint error:', error.response?.data?.error);
      }
    }
    
    // Test registration
    try {
      const register = await axios.post(`${API_URL}/register`, {
        name: 'Test User',
        user_type: 'student',
        grade: '2'
      });
      console.log('✅ Registration endpoint:', 'WORKING');
      console.log('   Token returned:', !!register.data.token);
    } catch (error) {
      console.log('❌ Registration error:', error.response?.data?.error);
    }
    
  } catch (error) {
    console.log('❌ Server not reachable:', error.message);
  }
}

testEndpoints();