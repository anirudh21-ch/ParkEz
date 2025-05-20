const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

// Create Express server
const app = express();

// Enable CORS
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  credentials: true
}));

// Add custom headers
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  next();
});

// Middleware
app.use(express.json());

// Mock users database
const users = [
  {
    id: '1',
    name: 'Test User',
    email: 'user@parkez.com',
    password: '$2a$10$rrCvVFQEGAKZhzMfDEJVZeVxQIkSjbHXxTR0Y3KpKW2R9pBOQgJTK', // password123
    role: 'user',
    phone: '1234567890'
  },
  {
    id: '2',
    name: 'Test Operator',
    email: 'operator@parkez.com',
    password: '$2a$10$rrCvVFQEGAKZhzMfDEJVZeVxQIkSjbHXxTR0Y3KpKW2R9pBOQgJTK', // password123
    role: 'operator',
    phone: '9876543210'
  },
  {
    id: '3',
    name: 'Test Admin',
    email: 'admin@parkez.com',
    password: '$2a$10$rrCvVFQEGAKZhzMfDEJVZeVxQIkSjbHXxTR0Y3KpKW2R9pBOQgJTK', // password123
    role: 'admin',
    phone: '5555555555'
  }
];

// Default route
app.get('/', (req, res) => {
  res.send('Auth server is running');
});

// Login route
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    console.log(`Login attempt for email: ${email}`);
    
    // Find user by email
    const user = users.find(u => u.email === email);
    
    if (!user) {
      console.log(`No user found with email: ${email}`);
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }
    
    // Check password
    const isMatch = await bcrypt.compare(password, user.password);
    
    if (!isMatch) {
      console.log('Password does not match');
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }
    
    // Generate JWT token
    const token = jwt.sign(
      { id: user.id },
      'parkez_secret_key_for_jwt_tokens',
      { expiresIn: '30d' }
    );
    
    console.log('Login successful');
    
    // Send response
    res.status(200).json({
      success: true,
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
        phone: user.phone
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// Register route
app.post('/api/auth/register', async (req, res) => {
  try {
    const { name, email, password, role, phone } = req.body;
    
    console.log(`Registration attempt for email: ${email}, role: ${role}`);
    
    // Check if user exists
    const userExists = users.find(u => u.email === email);
    
    if (userExists) {
      console.log(`User with email ${email} already exists`);
      return res.status(400).json({
        success: false,
        message: 'User already exists'
      });
    }
    
    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // Create new user
    const newUser = {
      id: (users.length + 1).toString(),
      name,
      email,
      password: hashedPassword,
      role: role || 'user',
      phone
    };
    
    // Add user to database
    users.push(newUser);
    
    console.log(`User created with ID: ${newUser.id}`);
    
    // Generate JWT token
    const token = jwt.sign(
      { id: newUser.id },
      'parkez_secret_key_for_jwt_tokens',
      { expiresIn: '30d' }
    );
    
    // Send response
    res.status(201).json({
      success: true,
      token,
      user: {
        id: newUser.id,
        name: newUser.name,
        email: newUser.email,
        role: newUser.role,
        phone: newUser.phone
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
});

// Start server on a different port
const PORT = 3002;
app.listen(PORT, () => {
  console.log(`Auth server running on port ${PORT}`);
});
