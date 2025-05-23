import { useState } from 'react';
import { authAPI } from '../api/api';
import './Login.css';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Always use a single admin login for admin@parkez.com
      if (email === 'admin@parkez.com' && password === 'admin123') {
        // Create an admin user
        const adminUser = {
          _id: 'admin-id',
          name: 'Admin User',
          email: 'admin@parkez.com',
          role: 'admin'
        };

        // Store token in localStorage
        localStorage.setItem('token', 'admin-token');

        // Call the onLogin callback with the admin user data
        onLogin(adminUser);
        return;
      }

      // Try to call the real API for non-demo credentials
      try {
        const response = await authAPI.login({ email, password });

        if (response.data && response.data.token) {
          // Store the token in localStorage
          localStorage.setItem('token', response.data.token);

          // Call the onLogin callback with the user data
          onLogin(response.data.user);
          return;
        }
      } catch (apiError) {
        console.error('API Login error:', apiError);
        setError('Invalid credentials. Use admin@parkez.com / admin123');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h2>ParkEz</h2>
          <p>Admin Panel</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@parkez.com"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="admin123"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="login-footer">
          <div className="demo-credentials">
            <h3>Demo Credentials</h3>
            <p><strong>Email:</strong> admin@parkez.com</p>
            <p><strong>Password:</strong> admin123</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
