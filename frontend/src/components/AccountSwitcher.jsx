import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { X, UserPlus, Trash2, ArrowRight, Check } from 'lucide-react';

export default function AccountSwitcher({ onClose }) {
  const { user, accounts, switchToAccount, removeAccount, login } = useAuth();
  const [addMode, setAddMode] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAddAccount = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to sign in');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitch = async (acctEmail) => {
    if (acctEmail === user?.email) return;
    await switchToAccount(acctEmail);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content animate-fade-in"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '480px' }}
      >
        <button className="modal-close" onClick={onClose}>
          <X size={18} />
        </button>

        <h3
          className="text-headline text-lg font-semibold"
          style={{ marginBottom: '1.25rem' }}
        >
          Switch Account
        </h3>

        {/* Account List */}
        <div className="switcher-list">
          {accounts.map((acct) => (
            <button
              key={acct.email}
              className={`switcher-account ${acct.email === user?.email ? 'switcher-active' : ''}`}
              onClick={() => handleSwitch(acct.email)}
            >
              <div className="switcher-avatar">
                {acct.email.split('@')[0].slice(0, 2).toUpperCase()}
              </div>
              <div className="switcher-email">{acct.email}</div>
              {acct.email === user?.email && (
                <Check size={16} style={{ color: 'var(--color-approve)', marginLeft: 'auto' }} />
              )}
              <button
                className="switcher-remove"
                onClick={(e) => {
                  e.stopPropagation();
                  removeAccount(acct.email);
                }}
                title="Remove account"
              >
                <Trash2 size={14} />
              </button>
            </button>
          ))}
        </div>

        {/* Add Account */}
        {!addMode ? (
          <button
            className="switcher-add-btn"
            onClick={() => setAddMode(true)}
          >
            <UserPlus size={16} />
            Add another account
          </button>
        ) : (
          <form onSubmit={handleAddAccount} className="switcher-add-form animate-fade-in">
            <input
              type="email"
              className="input-field"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
            <input
              type="password"
              className="input-field"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
            {error && <p className="login-error">{error}</p>}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setAddMode(false)}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{ flex: 1 }}
              >
                {loading ? <div className="btn-spinner" /> : <>Sign In <ArrowRight size={14} /></>}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
