import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { zonesAPI, ticketsAPI } from '../api/api';
import './ZoneDetails.css';

const ZoneDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [zone, setZone] = useState(null);
  const [stats, setStats] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchZoneDetails();
  }, [id]);

  const fetchZoneDetails = async () => {
    setLoading(true);
    try {
      // Fetch zone stats
      const response = await zonesAPI.getZoneStats(id);

      if (response.data && response.data.data) {
        setZone(response.data.data.zone);
        setStats(response.data.data.stats);
        setRecentTickets(response.data.data.recentTickets);
      } else {
        // Fallback: fetch zone details and tickets separately
        const zoneResponse = await zonesAPI.getZoneById(id);
        if (zoneResponse.data && zoneResponse.data.data) {
          setZone(zoneResponse.data.data);
        }
      }

      setError(null);
    } catch (error) {
      console.error('Error fetching zone details:', error);
      setError('Failed to fetch zone details');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(amount);
  };

  const handleStatusChange = async (status) => {
    try {
      setLoading(true);

      if (status === 'approved') {
        await zonesAPI.approveZone(id);
      } else if (status === 'rejected') {
        await zonesAPI.rejectZone(id);
      }

      // Refresh zone details
      fetchZoneDetails();

    } catch (error) {
      console.error(`Error ${status === 'approved' ? 'approving' : 'rejecting'} zone:`, error);
      setError(`Failed to ${status === 'approved' ? 'approve' : 'reject'} zone`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="zone-details-page">
        <div className="loading">Loading zone details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="zone-details-page">
        <div className="error-message">
          {error}
          <button className="retry-button" onClick={fetchZoneDetails}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!zone) {
    return (
      <div className="zone-details-page">
        <div className="error-message">Zone not found</div>
        <button className="back-button" onClick={() => navigate(-1)}>
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="zone-details-page">
      <div className="page-header">
        <div className="header-left">
          <button className="back-button" onClick={() => navigate(-1)}>
            <i className="material-icons">arrow_back</i>
          </button>
          <div>
            <h1>{zone.name}</h1>
            <p>{zone.address}</p>
          </div>
        </div>
        <div className="header-right">
          <span className={`status-badge ${zone.status}`}>
            {zone.status.charAt(0).toUpperCase() + zone.status.slice(1)}
          </span>
          {zone.status === 'pending' && (
            <div className="action-buttons">
              <button
                className="reject-button"
                onClick={() => handleStatusChange('rejected')}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Reject'}
              </button>
              <button
                className="approve-button"
                onClick={() => handleStatusChange('approved')}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Approve'}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="zone-details-content">
        <div className="zone-info-section">
          <h2>Zone Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Operator</span>
              <span className="info-value">{zone.operator?.name || 'Unknown'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Hourly Rate</span>
              <span className="info-value">{formatCurrency(zone.hourlyRate)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Total Slots</span>
              <span className="info-value">{zone.totalSlots}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Available Slots</span>
              <span className="info-value">{zone.availableSlots}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Created At</span>
              <span className="info-value">{formatDate(zone.createdAt)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Last Updated</span>
              <span className="info-value">{formatDate(zone.updatedAt)}</span>
            </div>
          </div>
        </div>

        {stats && (
          <div className="zone-stats-section">
            <h2>Zone Statistics</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{stats.activeTickets}</div>
                <div className="stat-label">Active Tickets</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.totalTickets}</div>
                <div className="stat-label">Total Tickets</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.completedTickets}</div>
                <div className="stat-label">Completed Tickets</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{formatCurrency(stats.totalRevenue)}</div>
                <div className="stat-label">Total Revenue</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.occupancyRate.toFixed(1)}%</div>
                <div className="stat-label">Occupancy Rate</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.availableSlots} / {stats.totalSlots}</div>
                <div className="stat-label">Available Slots</div>
              </div>
            </div>
          </div>
        )}

        {recentTickets && recentTickets.length > 0 && (
          <div className="recent-tickets-section">
            <h2>Recent Tickets</h2>
            <div className="tickets-table-container">
              <table className="tickets-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Vehicle</th>
                    <th>Entry Time</th>
                    <th>Exit Time</th>
                    <th>Status</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTickets.map(ticket => (
                    <tr key={ticket._id}>
                      <td>{ticket._id.substring(0, 8)}...</td>
                      <td>{ticket.user?.name || 'Unknown'}</td>
                      <td>{ticket.vehicle?.vehicleNumber || 'Unknown'}</td>
                      <td>{formatDate(ticket.entryTime)}</td>
                      <td>{ticket.exitTime ? formatDate(ticket.exitTime) : '-'}</td>
                      <td>
                        <span className={`status-badge ${ticket.status}`}>
                          {ticket.status.charAt(0).toUpperCase() + ticket.status.slice(1)}
                        </span>
                      </td>
                      <td>{ticket.amount ? formatCurrency(ticket.amount) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ZoneDetails;
