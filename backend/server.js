const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const connectDB = require('./config/db');
const User = require('./models/User');

// Load environment variables from backend/.env
dotenv.config({ path: path.resolve(__dirname, '.env') });

// Connect to database
connectDB();

// Initialize Express
const app = express();

// Middleware - Simplified CORS configuration
app.use(cors());

// Parse JSON request bodies
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Add custom headers to bypass potential proxy issues
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  next();
});

// Log all requests for debugging
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);

  // Only log headers and body for non-OPTIONS requests
  if (req.method !== 'OPTIONS') {
    // Only log body for POST, PUT, PATCH requests
    if (['POST', 'PUT', 'PATCH'].includes(req.method) && req.body) {
      // Don't log passwords
      const sanitizedBody = { ...req.body };
      if (sanitizedBody.password) {
        sanitizedBody.password = '[REDACTED]';
      }
      console.log('Request Body:', JSON.stringify(sanitizedBody, null, 2));
    }
  }

  next();
});

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/users', require('./routes/users'));
app.use('/api/vehicles', require('./routes/vehicles'));
app.use('/api/tickets', require('./routes/tickets'));
app.use('/api/zones', require('./routes/zones'));
app.use('/api/notifications', require('./routes/notifications'));

// Default route
app.get('/', (req, res) => {
  res.send('ParkEz API is running');
});

// Test route - no authentication required
app.get('/api/test', (req, res) => {
  res.json({
    success: true,
    message: 'API test endpoint is working',
    timestamp: new Date().toISOString()
  });
});

// Health check route
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    mongodb: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'
  });
});

// Add a verify token route
app.get('/api/auth/verify', (req, res) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      success: false,
      message: 'No token provided'
    });
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Find the user by ID
    User.findById(decoded.id)
      .select('-password')
      .then(user => {
        if (!user) {
          return res.status(404).json({
            success: false,
            message: 'User not found'
          });
        }

        res.json({
          success: true,
          user
        });
      })
      .catch(err => {
        console.error('Error finding user:', err);
        res.status(500).json({
          success: false,
          message: 'Server error'
        });
      });
  } catch (err) {
    console.error('Token verification error:', err);
    res.status(401).json({
      success: false,
      message: 'Invalid token'
    });
  }
});

// Port configuration
const PORT = 5002; // Changed from 5000 to avoid conflicts with Control Center

// Start server
app.listen(PORT, '192.168.31.33', () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Server accessible at http://localhost:${PORT}`);
  console.log(`For mobile devices, use your computer's IP address: http://192.168.31.33:${PORT}`);
});
