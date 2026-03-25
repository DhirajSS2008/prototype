import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { User, LogOut, ChevronDown, RefreshCw } from 'lucide-react';
import AccountSwitcher from './AccountSwitcher';

export default function UserProfile() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [showSwitcher, setShowSwitcher] = useState(false);
  const ref = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  if (!user) return null;

  const initials = user.email
    .split('@')[0]
    .slice(0, 2)
    .toUpperCase();

  return (
    <>
      <div className="profile-wrapper" ref={ref}>
        <button
          className="profile-trigger"
          onClick={() => setOpen(!open)}
          aria-label="User profile menu"
        >
          <div className="profile-avatar">{initials}</div>
          <ChevronDown
            size={14}
            className={`profile-chevron ${open ? 'profile-chevron-open' : ''}`}
          />
        </button>

        {open && (
          <div className="profile-dropdown animate-fade-in">
            {/* User Info */}
            <div className="profile-info">
              <div className="profile-avatar-lg">{initials}</div>
              <div>
                <p className="profile-email">{user.email}</p>
                <p className="text-label" style={{ fontSize: '0.625rem' }}>
                  {user.created_at
                    ? `Joined ${new Date(user.created_at).toLocaleDateString()}`
                    : 'LiquiSense User'}
                </p>
              </div>
            </div>

            <div className="profile-divider" />

            {/* Switch User */}
            <button
              className="profile-menu-item"
              onClick={() => {
                setOpen(false);
                setShowSwitcher(true);
              }}
            >
              <RefreshCw size={15} />
              Switch User
            </button>

            {/* Logout */}
            <button
              className="profile-menu-item profile-menu-item-danger"
              onClick={() => {
                setOpen(false);
                logout();
              }}
            >
              <LogOut size={15} />
              Log Out
            </button>
          </div>
        )}
      </div>

      {/* Account Switcher Modal */}
      {showSwitcher && (
        <AccountSwitcher onClose={() => setShowSwitcher(false)} />
      )}
    </>
  );
}
