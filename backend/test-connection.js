const axios = require('axios');

// Test the API connection
async function testConnection() {
  try {
    console.log('Testing API connection...');
    
    // Test the root endpoint
    try {
      const rootResponse = await axios.get('http://localhost:5000');
      console.log('Root endpoint response:', rootResponse.data);
    } catch (error) {
      console.error('Root endpoint error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }
    
    // Test the auth endpoint
    try {
      const loginResponse = await axios.post('http://localhost:5000/api/auth/login', {
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
testConnection();
