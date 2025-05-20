const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

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

// Create proxy middleware
const apiProxy = createProxyMiddleware({
  target: 'http://localhost:5000',
  changeOrigin: true,
  pathRewrite: {
    '^/proxy': ''
  },
  onProxyRes: (proxyRes, req, res) => {
    proxyRes.headers['Access-Control-Allow-Origin'] = '*';
  }
});

// Use proxy for all requests
app.use('/proxy', apiProxy);

// Default route
app.get('/', (req, res) => {
  res.send('Proxy server is running');
});

// Start server on a different port
const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`);
});
