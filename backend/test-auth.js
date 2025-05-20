const axios = require('axios');

// Test the auth server
async function testAuth() {
  try {
    console.log('Testing auth server...');

    // Test the root endpoint
    try {
      const rootResponse = await axios.get('http://localhost:3002');
      console.log('Root endpoint response:', rootResponse.data);
    } catch (error) {
      console.error('Root endpoint error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }

    // Test the login endpoint with correct password
    try {
      const loginResponse = await axios.post('http://localhost:3002/api/auth/login', {
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

    // Test the register endpoint
    try {
      const registerResponse = await axios.post('http://localhost:3002/api/auth/register', {
        name: 'New User',
        email: 'newuser@example.com',
        password: 'password123',
        role: 'user',
        phone: '1234567890'
      });
      console.log('Register endpoint response:', registerResponse.data);
    } catch (error) {
      console.error('Register endpoint error:', error.message);
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
testAuth();
