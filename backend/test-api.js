const axios = require('axios');

// Test the API endpoints
async function testAPI() {
  try {
    // Test the root endpoint
    console.log('\n1. Testing root endpoint...');
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
    console.log('\n2. Testing auth endpoint...');
    try {
      const authResponse = await axios.get('http://localhost:5000/api/auth');
      console.log('Auth endpoint response:', authResponse.data);
    } catch (error) {
      console.error('Auth endpoint error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }

    // Test login with incorrect credentials
    console.log('\n3. Testing login with incorrect credentials...');
    try {
      const loginResponse = await axios.post('http://localhost:5000/api/auth/login', {
        email: 'test@example.com',
        password: 'wrongpassword'
      });
      console.log('Login response:', loginResponse.data);
    } catch (error) {
      console.error('Login error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }

    // Test login with correct credentials
    console.log('\n4. Testing login with correct credentials...');
    try {
      const loginResponse = await axios.post('http://localhost:5000/api/auth/login', {
        email: 'user@parkez.com',
        password: 'password123'
      });
      console.log('Login response:', loginResponse.data);
    } catch (error) {
      console.error('Login error:', error.message);
      if (error.response) {
        console.error('Status:', error.response.status);
        console.error('Data:', error.response.data);
      }
    }

    // Test register endpoint
    console.log('\n5. Testing register endpoint...');
    try {
      const registerResponse = await axios.post('http://localhost:5000/api/auth/register', {
        name: 'Test User',
        email: 'newuser@example.com',
        password: 'password123',
        role: 'user',
        phone: '1234567890'
      });
      console.log('Register response:', registerResponse.data);
    } catch (error) {
      console.error('Register error:', error.message);
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
testAPI();
