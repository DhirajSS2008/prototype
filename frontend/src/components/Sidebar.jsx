import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  History,
  Menu,
  X,
  Wallet,
  TrendingUp,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import { clearAllHistory } from '../api/client';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload Documents' },
  { to: '/history', icon: History, label: 'Check History' },
];

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetting, setResetting] = useState(false);

  const handleReset = async () => {
    setResetting(true);
    try {
      await clearAllHistory();
      setShowResetModal(false);
      // Reload the page to refresh all data
      window.location.reload();
    } catch (err) {
      console.error('Failed to reset data:', err);
      alert('Failed to reset data. Please try again.');
      setResetting(false);
    }
  };

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="fixed top-4 left-4 z-50 p-2 rounded-xl md:hidden"
        style={{ background: 'var(--color-surface-container)' }}
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10 px-2">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dim))',
            }}
          >
            <Wallet size={20} style={{ color: 'var(--color-on-primary)' }} />
          </div>
          <div>
            <h1 className="text-headline text-lg font-bold" style={{ color: 'var(--color-on-surface)' }}>
              LiquiSense
            </h1>
            <p className="text-xs" style={{ color: 'var(--color-on-surface-variant)' }}>
              Smart Finance
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive ? 'nav-active' : 'nav-item'
                }`
              }
              style={({ isActive }) => ({
                background: isActive ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                color: isActive ? 'var(--color-primary)' : 'var(--color-on-surface-variant)',
              })}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Reset Button */}
        <button
          className="reset-btn"
          onClick={() => setShowResetModal(true)}
        >
          <Trash2 size={16} />
          Reset All Data
        </button>

        {/* Bottom section */}
        <div
          className="rounded-xl p-4 mt-3"
          style={{ background: 'var(--color-surface-container)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={16} style={{ color: 'var(--color-tertiary)' }} />
            <span className="text-label">Pro Tip</span>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-on-surface-variant)' }}>
            Upload bank statements regularly for better affordability predictions.
          </p>
        </div>
      </aside>

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="reset-modal-overlay" onClick={() => !resetting && setShowResetModal(false)}>
          <div className="reset-modal" onClick={(e) => e.stopPropagation()}>
            <div className="reset-modal-icon">
              <AlertTriangle size={28} />
            </div>
            <h3 className="reset-modal-title">Reset All Data?</h3>
            <p className="reset-modal-desc">
              This will <strong>permanently delete</strong> all your transactions,
              affordability checks, balance history, and uploaded files.
              This action cannot be undone.
            </p>
            <div className="reset-modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowResetModal(false)}
                disabled={resetting}
              >
                Cancel
              </button>
              <button
                className="reset-modal-confirm"
                onClick={handleReset}
                disabled={resetting}
              >
                {resetting ? (
                  <>
                    <span className="reset-spinner" />
                    Resetting…
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    Reset All Data
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
