import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import './Layout.css';

const Layout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-brand">
          <Link to="/">Comma Connect</Link>
        </div>

        <div className="nav-menu">
          <Link to="/" className="nav-link">Dashboard</Link>
          <Link to="/devices" className="nav-link">Devices</Link>
          <Link to="/routes" className="nav-link">Routes</Link>
          <Link to="/settings" className="nav-link">Settings</Link>
        </div>

        <div className="nav-user">
          <span>{user?.email}</span>
          <button onClick={handleLogout} className="btn btn-secondary">
            Logout
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
