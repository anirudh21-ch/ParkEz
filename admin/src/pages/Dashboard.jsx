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

    // Set up interval to refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);

    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Always use dynamic data for admin dashboard
      try {
        // Fetch zone data
        const zonesResponse = await fetch('http://192.168.137.131:5002/api/zones');
        const zonesData = await zonesResponse.json();

        // Fetch operators data
        const operatorsResponse = await fetch('http://192.168.137.131:5002/api/operators');
        const operatorsData = await operatorsResponse.json();

        // Fetch users data
        const usersResponse = await fetch('http://192.168.137.131:5002/api/users');
        const usersData = await usersResponse.json();

        // Fetch tickets data
        const ticketsResponse = await fetch('http://192.168.137.131:5002/api/tickets');
        const ticketsData = await ticketsResponse.json();

        // Calculate revenue from tickets
        const revenue = ticketsData.data
          ? ticketsData.data.reduce((total, ticket) => {
              return total + (ticket.amount || 0);
            }, 0)
          : 0;

        // Count pending zone requests
        const pendingRequests = zonesData.data
          ? zonesData.data.filter(zone => zone.status === 'pending').length
          : 0;

        // Count active tickets
        const activeTickets = ticketsData.data
          ? ticketsData.data.filter(ticket => ticket.status === 'active').length
          : 0;

        // Set the stats
        setStats({
          users: usersData.data ? usersData.data.length : 0,
          operators: operatorsData.data ? operatorsData.data.length : 0,
          zones: zonesData.data ? zonesData.data.length : 0,
          activeTickets,
          pendingRequests,
          revenue
        });

        // Fetch recent activities
        const activitiesResponse = await fetch('http://192.168.137.131:5002/api/activities');
        const activitiesData = await activitiesResponse.json();

        if (activitiesData.data && activitiesData.data.length > 0) {
          setActivities(activitiesData.data);
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
