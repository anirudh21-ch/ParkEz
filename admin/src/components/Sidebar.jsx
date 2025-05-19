import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = ({ user, onLogout }) => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>ParkEz</h2>
        <p>Admin Panel</p>
      </div>
      
      <div className="sidebar-user">
        <div className="user-avatar">
          {user?.name?.charAt(0) || 'A'}
        </div>
        <div className="user-info">
          <p className="user-name">{user?.name || 'Admin'}</p>
          <p className="user-role">Super Admin</p>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <ul>
          <li className={isActive('/dashboard') ? 'active' : ''}>
            <Link to="/dashboard">
              <i className="material-icons">dashboard</i>
              Dashboard
            </Link>
          </li>
          <li className={isActive('/zone-requests') ? 'active' : ''}>
            <Link to="/zone-requests">
              <i className="material-icons">location_on</i>
              Zone Requests
            </Link>
          </li>
          <li className={isActive('/users') ? 'active' : ''}>
            <Link to="/users">
              <i className="material-icons">people</i>
              Users
            </Link>
          </li>
          <li className={isActive('/operators') ? 'active' : ''}>
            <Link to="/operators">
              <i className="material-icons">business</i>
              Operators
            </Link>
          </li>
        </ul>
      </nav>
      
      <div className="sidebar-footer">
        <button className="logout-button" onClick={onLogout}>
          <i className="material-icons">exit_to_app</i>
          Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
