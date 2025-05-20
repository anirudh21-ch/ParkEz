const axios = require('axios');

// Test login with an existing user
async function testLogin() {
  try {
    console.log('Testing login with existing user...');
    
    const response = await axios.post('http://localhost:5000/api/auth/login', {
      email: 'user@parkez.com',
      password: 'password123'
    });
    
    console.log('Login response:', response.data);
    console.log('Login successful!');
    
    return response.data;
  } catch (error) {
    console.error('Login error:', error.response ? error.response.data : error.message);
    throw error;
  }
}

// Run the test
testLogin()
  .then(data => {
    console.log('Test completed successfully');
  })
  .catch(error => {
    console.error('Test failed');
  });
