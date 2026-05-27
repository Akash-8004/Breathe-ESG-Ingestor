import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/ingest',    icon: '📤', label: 'Ingest Data' },
  { to: '/review',    icon: '✅', label: 'Review Entries' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : 'U';

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar" id="app-sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">🌿</div>
          <h2>Breathe ESG</h2>
        </div>

        <nav className="sidebar-nav" id="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              id={`nav-${item.to.replace('/', '')}`}
              className={({ isActive }) =>
                `sidebar-link${isActive ? ' active' : ''}`
              }
            >
              <span className="sidebar-link-icon">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar" id="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.username || 'User'}</div>
              <div className="sidebar-user-role">Analyst</div>
            </div>
            <button
              className="sidebar-logout"
              id="sidebar-logout-btn"
              onClick={handleLogout}
              title="Sign out"
            >
              ⏻
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content area — child routes render here ── */}
      <div className="main-content">
        <Outlet />
      </div>
    </div>
  );
}
