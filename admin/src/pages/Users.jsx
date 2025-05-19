import './Users.css';

const Users = () => {
  return (
    <div className="users-page">
      <div className="page-header">
        <h1>Users Management</h1>
        <p>Manage platform users and their vehicles</p>
      </div>
      
      <div className="placeholder-content">
        <div className="placeholder-icon">
          <i className="material-icons">people</i>
        </div>
        <h2>Users Management</h2>
        <p>This page will allow administrators to:</p>
        <ul>
          <li>View all registered users</li>
          <li>See user details including registered vehicles</li>
          <li>Manage user accounts (activate/deactivate)</li>
          <li>View user parking history</li>
        </ul>
        <p className="placeholder-note">This feature will be implemented in the next phase.</p>
      </div>
    </div>
  );
};

export default Users;
