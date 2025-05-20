const axios = require('axios');

// Test the simple server
async function testSimpleServer() {
  try {
    console.log('Testing simple server...');
    
    // Test the root endpoint
    const rootResponse = await axios.get('http://localhost:3000');
    console.log('Root endpoint response:', rootResponse.data);
    
    // Test the login endpoint
    const loginResponse = await axios.post('http://localhost:3000/login', {
      email: 'test@example.com',
      password: 'password123'
    });
    console.log('Login endpoint response:', loginResponse.data);
    
    console.log('Simple server test successful!');
  } catch (error) {
    console.error('Simple server test failed:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    }
  }
}

// Run the test
testSimpleServer();
