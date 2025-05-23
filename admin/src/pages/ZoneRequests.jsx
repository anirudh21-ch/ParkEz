import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { zonesAPI } from '../api/api';
import './ZoneRequests.css';

const ZoneRequests = () => {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchZoneRequests();
  }, []);

  const fetchZoneRequests = async () => {
    setLoading(true);
    try {
      // Try to fetch real data from API
      try {
        // Use the getPendingZones endpoint to get only pending requests
        const response = await zonesAPI.getPendingZones();
        if (response.data && response.data.data && response.data.data.length > 0) {
          setRequests(response.data.data);
        } else {
          // If no pending zones, try to get zones with pending status
          const pendingResponse = await zonesAPI.getZonesByStatus('pending');
          if (pendingResponse.data && pendingResponse.data.data && pendingResponse.data.data.length > 0) {
            setRequests(pendingResponse.data.data);
          } else {
            setRequests([]);
          }
        }
      } catch (apiError) {
        console.error('API Error:', apiError);
        // If API fails, try fallback to get all zones and filter pending ones
        try {
          const allZonesResponse = await zonesAPI.getZones();
          if (allZonesResponse.data && allZonesResponse.data.data) {
            const pendingZones = allZonesResponse.data.data.filter(zone => zone.status === 'pending');
            setRequests(pendingZones);
          } else {
            setRequests([]);
          }
        } catch (fallbackError) {
          console.error('Fallback API Error:', fallbackError);
          setRequests([]);
        }
      }

      setError(null);
    } catch (error) {
      console.error('Error fetching zone requests:', error);
      setError('Failed to fetch zone requests');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      setLoading(true);

      try {
        // Try to call the real API
        await zonesAPI.approveZone(id);

        // Update the local state
        setRequests(requests.map(request =>
          request._id === id ? { ...request, status: 'approved' } : request
        ));

        // Show success message
        alert('Zone request approved successfully!');
      } catch (apiError) {
        console.error('API Error:', apiError);
        setError('Failed to approve zone request: API error');
      }
    } catch (error) {
      console.error('Error approving zone request:', error);
      setError('Failed to approve zone request');
    } finally {
      setLoading(false);
      setModalOpen(false);
    }
  };

  const handleReject = async (id) => {
    try {
      setLoading(true);

      try {
        // Try to call the real API
        await zonesAPI.rejectZone(id);

        // Update the local state
        setRequests(requests.map(request =>
          request._id === id ? { ...request, status: 'rejected' } : request
        ));

        // Show success message
        alert('Zone request rejected successfully!');
      } catch (apiError) {
        console.error('API Error:', apiError);
        setError('Failed to reject zone request: API error');
      }
    } catch (error) {
      console.error('Error rejecting zone request:', error);
      setError('Failed to reject zone request');
    } finally {
      setLoading(false);
      setModalOpen(false);
    }
  };

  const openModal = (request) => {
    setSelectedRequest(request);
    setModalOpen(true);
  };

  const viewZoneDetails = (zoneId) => {
    navigate(`/zone-details/${zoneId}`);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="zone-requests">
      <div className="page-header">
        <h1>Zone Requests</h1>
        <p>Manage parking zone requests from operators</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button className="retry-button" onClick={fetchZoneRequests}>
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading zone requests...</div>
      ) : (
        <div className="requests-table-container">
          <table className="requests-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Zone Name</th>
                <th>Operator</th>
                <th>Total Slots</th>
                <th>Hourly Rate</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.length > 0 ? (
                requests.map(request => (
                  <tr key={request._id}>
                    <td>{request._id.substring(0, 8)}...</td>
                    <td>{request.name}</td>
                    <td>{request.operator.name}</td>
                    <td>{request.totalSlots}</td>
                    <td>₹{request.hourlyRate.toFixed(2)}</td>
                    <td>
                      <span className={`status-badge ${request.status}`}>
                        {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                      </span>
                    </td>
                    <td>{formatDate(request.createdAt)}</td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="view-button"
                          onClick={() => viewZoneDetails(request._id)}
                        >
                          View Details
                        </button>
                        {request.status === 'pending' && (
                          <button
                            className="modal-button"
                            onClick={() => openModal(request)}
                          >
                            Quick Actions
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="no-data">No zone requests found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && selectedRequest && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>Zone Request Details</h2>
              <button className="close-button" onClick={() => setModalOpen(false)}>
                <i className="material-icons">close</i>
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">Zone ID:</span>
                <span className="detail-value">{selectedRequest._id}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Zone Name:</span>
                <span className="detail-value">{selectedRequest.name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Address:</span>
                <span className="detail-value">{selectedRequest.address}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Operator:</span>
                <span className="detail-value">{selectedRequest.operator.name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Email:</span>
                <span className="detail-value">{selectedRequest.operator.email}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Phone:</span>
                <span className="detail-value">{selectedRequest.operator.phone}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Total Slots:</span>
                <span className="detail-value">{selectedRequest.totalSlots}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Available Slots:</span>
                <span className="detail-value">{selectedRequest.availableSlots}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Hourly Rate:</span>
                <span className="detail-value">₹{selectedRequest.hourlyRate.toFixed(2)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Status:</span>
                <span className="detail-value">
                  <span className={`status-badge ${selectedRequest.status}`}>
                    {selectedRequest.status.charAt(0).toUpperCase() + selectedRequest.status.slice(1)}
                  </span>
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Created At:</span>
                <span className="detail-value">{formatDate(selectedRequest.createdAt)}</span>
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="reject-button"
                onClick={() => handleReject(selectedRequest._id)}
                disabled={loading || selectedRequest.status !== 'pending'}
              >
                {loading ? 'Processing...' : 'Reject'}
              </button>
              <button
                className="approve-button"
                onClick={() => handleApprove(selectedRequest._id)}
                disabled={loading || selectedRequest.status !== 'pending'}
              >
                {loading ? 'Processing...' : 'Approve'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ZoneRequests;
