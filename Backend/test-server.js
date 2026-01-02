const http = require('http');

const options = {
  hostname: 'localhost',
  port: 5000,
  path: '/api/health',
  method: 'GET',
  timeout: 5000
};

const req = http.request(options, (res) => {
  console.log(`✅ Server is running! Status Code: ${res.statusCode}`);
  
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    try {
      const parsed = JSON.parse(data);
      console.log('📊 Server Response:', parsed);
    } catch (e) {
      console.log('📄 Raw Response:', data);
    }
  });
});

req.on('error', (e) => {
  console.log(`❌ Server NOT running on port 5000: ${e.message}`);
  console.log('\n⚠️  Troubleshooting steps:');
  console.log('1. Check if your backend server is running');
  console.log('2. Run: node server.js in your backend folder');
  console.log('3. Check if server is on a different port (like 5001)');
  console.log('4. Look at terminal output when starting server');
});

req.on('timeout', () => {
  console.log('❌ Request timeout - server not responding');
  req.destroy();
});

req.end();