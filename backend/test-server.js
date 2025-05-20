const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '.env') });

// Create a simple Express server
const app = express();

// Enable CORS
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept']
}));

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

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Log all requests
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  if (req.body && Object.keys(req.body).length > 0) {
    const sanitizedBody = { ...req.body };
    if (sanitizedBody.password) {
      sanitizedBody.password = '[REDACTED]';
    }
    console.log('Request Body:', sanitizedBody);
  }
  next();
});

// Default route
app.get('/', (req, res) => {
  res.json({
    success: true,
    message: 'Test server is running',
    timestamp: new Date().toISOString()
  });
});

// Health check route
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    env: {
      NODE_ENV: process.env.NODE_ENV,
      PORT: process.env.PORT,
      MONGO_URI: process.env.MONGO_URI ? 'Set' : 'Not set',
      JWT_SECRET: process.env.JWT_SECRET ? 'Set' : 'Not set',
      JWT_EXPIRE: process.env.JWT_EXPIRE
    }
  });
});

// Test routes
app.get('/test', (req, res) => {
  res.json({
    success: true,
    message: 'Test endpoint is working',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/test', (req, res) => {
  res.json({
    success: true,
    message: 'API test endpoint is working',
    timestamp: new Date().toISOString()
  });
});

// Auth routes
app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;

  console.log('Login attempt:', { email, password: '[REDACTED]' });

  if (!email || !password) {
    return res.status(400).json({
      success: false,
      message: 'Please provide email and password'
    });
  }

  res.json({
    success: true,
    message: 'Login successful',
    token: 'test-jwt-token-' + Date.now(),
    user: {
      id: '123',
      name: 'Test User',
      email: email || 'test@example.com',
      role: 'user',
      phone: '1234567890'
    }
  });
});

app.post('/api/auth/register', (req, res) => {
  const userData = req.body;

  console.log('Registration attempt:', userData);

  if (!userData.email || !userData.password || !userData.name) {
    return res.status(400).json({
      success: false,
      message: 'Please provide name, email and password'
    });
  }

  res.status(201).json({
    success: true,
    message: 'Registration successful',
    token: 'test-jwt-token-' + Date.now(),
    user: {
      id: '456',
      name: userData.name || 'New User',
      email: userData.email || 'newuser@example.com',
      role: userData.role || 'user',
      phone: userData.phone || '1234567890'
    }
  });
});

app.get('/api/auth/verify', (req, res) => {
  const authHeader = req.headers.authorization;

  console.log('Token verification attempt:', authHeader);

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      success: false,
      message: 'No token provided'
    });
  }

  res.json({
    success: true,
    user: {
      id: '123',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      phone: '1234567890'
    }
  });
});

// Mock API endpoints
app.get('/api/tickets/active', (req, res) => {
  res.json({
    success: true,
    tickets: []
  });
});

app.get('/api/zones', (req, res) => {
  res.json({
    success: true,
    zones: [
      {
        id: '1',
        name: 'Zone A',
        description: 'Main Campus',
        hourlyRate: 2.5,
        location: {
          latitude: 37.7749,
          longitude: -122.4194
        }
      },
      {
        id: '2',
        name: 'Zone B',
        description: 'Downtown',
        hourlyRate: 3.5,
        location: {
          latitude: 37.7749,
          longitude: -122.4194
        }
      }
    ]
  });
});

app.get('/api/activity', (req, res) => {
  res.json({
    success: true,
    activities: []
  });
});

// Start server on port 5001 (different from main server)
const PORT = 5001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Test server running on port ${PORT}`);
  console.log(`Server accessible at http://localhost:${PORT}`);
  console.log(`For mobile devices, use your computer's IP address: http://192.168.31.244:${PORT}`);
});
