import axios from 'axios';

// Use the correct port for the backend server
const API_URL = 'http://192.168.1.6:5002/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  verifyToken: () => api.get('/auth/verify')
};

// Users API
export const usersAPI = {
  getUsers: () => api.get('/users'),
  getUserCount: () => api.get('/users/count'),
  getOperatorCount: () => api.get('/users/operators/count')
};

// Zones API
export const zonesAPI = {
  getZones: () => api.get('/zones'),
  getZoneCount: () => api.get('/zones/count'),
  getPendingZones: () => api.get('/zones/pending'),
  getPendingZoneCount: () => api.get('/zones/pending/count'),
  approveZone: (zoneId) => api.put(`/zones/${zoneId}/approve`),
  rejectZone: (zoneId) => api.put(`/zones/${zoneId}/reject`)
};

// Tickets API
export const ticketsAPI = {
  getTickets: () => api.get('/tickets'),
  getActiveTicketCount: () => api.get('/tickets/active/count'),
  getRevenueTotal: () => api.get('/tickets/revenue')
};

// Activity API
export const activityAPI = {
  getRecentActivity: () => api.get('/notifications/recent')
};

// Dashboard API
export const dashboardAPI = {
  getStats: async () => {
    try {
      const [
        usersCount,
        operatorsCount,
        zonesCount,
        activeTicketsCount,
        pendingRequestsCount,
        revenue
      ] = await Promise.all([
        usersAPI.getUserCount(),
        usersAPI.getOperatorCount(),
        zonesAPI.getZoneCount(),
        ticketsAPI.getActiveTicketCount(),
        zonesAPI.getPendingZoneCount(),
        ticketsAPI.getRevenueTotal()
      ]);

      return {
        users: usersCount.data.count || 0,
        operators: operatorsCount.data.count || 0,
        zones: zonesCount.data.count || 0,
        activeTickets: activeTicketsCount.data.count || 0,
        pendingRequests: pendingRequestsCount.data.count || 0,
        revenue: revenue.data.total || 0
      };
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  }
};

export default api;
