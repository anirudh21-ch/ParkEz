import { useState, useEffect } from 'react';
import { dashboardAPI, activityAPI } from '../api/api';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    users: 0,
    operators: 0,
    zones: 0,
    activeTickets: 0,
    pendingRequests: 0,
    revenue: 0
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Try to fetch real data from API
      try {
        const statsData = await dashboardAPI.getStats();
        setStats(statsData);

        const activitiesResponse = await activityAPI.getRecentActivity();
        if (activitiesResponse.data && activitiesResponse.data.length > 0) {
          setActivities(activitiesResponse.data);
        } else {
          setActivities([]);
        }
      } catch (apiError) {
        console.error('API Error:', apiError);
        // If API fails, set empty data
        setStats({
          users: 0,
          operators: 0,
          zones: 0,
          activeTickets: 0,
          pendingRequests: 0,
          revenue: 0
        });
        setActivities([]);
      }

      setError(null);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const DashboardCard = ({ title, value, icon, color }) => (
    <div className="dashboard-card">
      <div className="card-icon" style={{ backgroundColor: color }}>
        <i className="material-icons">{icon}</i>
      </div>
      <div className="card-content">
        <h3>{title}</h3>
        <p className="card-value">{value}</p>
      </div>
    </div>
  );

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of ParkEz platform</p>
      </div>

      {loading ? (
        <div className="loading">Loading dashboard data...</div>
      ) : (
        <div className="dashboard-grid">
          <DashboardCard
            title="Total Users"
            value={stats.users}
            icon="people"
            color="#3498db"
          />
          <DashboardCard
            title="Operators"
            value={stats.operators}
            icon="business"
            color="#2ecc71"
          />
          <DashboardCard
            title="Parking Zones"
            value={stats.zones}
            icon="location_on"
            color="#9b59b6"
          />
          <DashboardCard
            title="Active Tickets"
            value={stats.activeTickets}
            icon="local_parking"
            color="#e74c3c"
          />
          <DashboardCard
            title="Pending Requests"
            value={stats.pendingRequests}
            icon="hourglass_empty"
            color="#f39c12"
          />
          <DashboardCard
            title="Revenue (INR)"
            value={`₹${stats.revenue}`}
            icon="attach_money"
            color="#1abc9c"
          />
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
          <button className="retry-button" onClick={fetchDashboardData}>
            Retry
          </button>
        </div>
      )}

      <div className="recent-activity">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          {activities.length > 0 ? (
            activities.map((activity, index) => {
              // Determine icon and color based on activity type
              let icon = 'info';
              let color = '#3498db';

              if (activity.type === 'user_registration') {
                icon = 'person_add';
                color = '#3498db';
              } else if (activity.type === 'zone_approval') {
                icon = 'check_circle';
                color = '#2ecc71';
              } else if (activity.type === 'zone_rejection') {
                icon = 'cancel';
                color = '#e74c3c';
              } else if (activity.type === 'ticket_creation') {
                icon = 'local_parking';
                color = '#f39c12';
              } else if (activity.type === 'ticket_checkout') {
                icon = 'exit_to_app';
                color = '#9b59b6';
              }

              return (
                <div className="activity-item" key={activity._id || index}>
                  <div className="activity-icon" style={{ backgroundColor: color }}>
                    <i className="material-icons">{icon}</i>
                  </div>
                  <div className="activity-details">
                    <p className="activity-text">{activity.description}</p>
                    <p className="activity-time">{new Date(activity.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="no-activity">
              <p>No recent activity found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
