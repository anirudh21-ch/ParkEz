import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { authAPI } from './api/api';
import './App.css';

// Auth Components
import Login from './pages/Login';

// Admin Components
import Dashboard from './pages/Dashboard';
import ZoneRequests from './pages/ZoneRequests';
import Users from './pages/Users';
import Operators from './pages/Operators';
import Sidebar from './components/Sidebar';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('token');

    if (token) {
      // Try to verify the token with the server
      const verifyToken = async () => {
        try {
          const response = await authAPI.verifyToken();
          if (response.data && response.data.user) {
            setUser(response.data.user);
            setIsAuthenticated(true);
          } else {
            // If verification fails, remove the token
            localStorage.removeItem('token');
          }
        } catch (error) {
          console.error('Token verification failed:', error);
          localStorage.removeItem('token');

          // For demo purposes only, if the token is 'demo-admin-token', automatically log in
          if (token === 'demo-admin-token') {
            const demoAdminUser = {
              _id: 'admin-demo-id',
              name: 'Admin User',
              email: 'admin@parkez.com',
              role: 'admin'
            };
            setUser(demoAdminUser);
            setIsAuthenticated(true);
          }
        } finally {
          setLoading(false);
        }
      };

      verifyToken();
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    // Remove token from localStorage
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <Router>
      <div className="app">
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading...</p>
          </div>
        ) : isAuthenticated ? (
          <div className="app-container">
            <Sidebar user={user} onLogout={handleLogout} />
            <div className="content">
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/zone-requests" element={<ZoneRequests />} />
                <Route path="/users" element={<Users />} />
                <Route path="/operators" element={<Operators />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          </div>
        ) : (
          <Routes>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        )}
      </div>
    </Router>
  )
}

export default App
