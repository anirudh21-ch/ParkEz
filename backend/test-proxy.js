const axios = require('axios');

// Test the proxy server
async function testProxy() {
  try {
    console.log('Testing proxy server...');
    
    // Test the root endpoint
    try {
      const rootResponse = await axios.get('http://localhost:3001');
      console.log('Root endpoint response:', rootResponse.data);
    } catch (error) {
      console.error('Root endpoint error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }
    
    // Test the proxied API endpoint
    try {
      const apiResponse = await axios.get('http://localhost:3001/proxy/api/auth');
      console.log('Proxied API endpoint response:', apiResponse.data);
    } catch (error) {
      console.error('Proxied API endpoint error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }
    
    // Test the login endpoint
    try {
      const loginResponse = await axios.post('http://localhost:3001/proxy/api/auth/login', {
        email: 'user@parkez.com',
        password: 'password123'
      });
      console.log('Login endpoint response:', loginResponse.data);
    } catch (error) {
      console.error('Login endpoint error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }
    
  } catch (error) {
    console.error('Test failed:', error.message);
  }
}

// Run the test
testProxy();
