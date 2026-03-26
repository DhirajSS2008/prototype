import { useState, useEffect } from 'react';
import { History as HistoryIcon, Trash2, AlertTriangle, X } from 'lucide-react';
import { fetchAffordabilityHistory, clearAllHistory } from '../api/client';
import DecisionCard from '../components/DecisionCard';

export default function HistoryPage() {
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCheck, setSelectedCheck] = useState(null);
  const [filter, setFilter] = useState('ALL');
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await fetchAffordabilityHistory({ limit: 50 });
      setChecks(res.data.checks || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    setClearing(true);
    try {
      await clearAllHistory();
      setChecks([]);
      setSelectedCheck(null);
      setClearSuccess(true);
      setShowClearModal(false);
      setTimeout(() => setClearSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to clear history:', err);
      alert('Failed to clear history. Please try again.');
    } finally {
      setClearing(false);
    }
  };

  const filtered = filter === 'ALL' ? checks : checks.filter((c) => c.decision === filter);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-headline text-2xl font-bold flex items-center gap-3">
            <HistoryIcon size={24} style={{ color: 'var(--color-primary)' }} />
            Affordability History
          </h2>
          <p className="text-sm mt-1" style={{ color: 'var(--color-on-surface-variant)' }}>
            Review past affordability checks and decisions
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Filters */}
          <div className="flex gap-2">
            {['ALL', 'APPROVE', 'DEFER', 'CRITICAL'].map((f) => (
              <button
                key={f}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${
                  filter === f ? 'active-filter' : ''
                }`}
                style={{
                  background: filter === f ? 'rgba(163, 166, 255, 0.15)' : 'var(--color-surface-container)',
                  color: filter === f ? 'var(--color-primary)' : 'var(--color-on-surface-variant)',
                }}
                onClick={() => setFilter(f)}
              >
                {f === 'ALL' ? 'All' : f.charAt(0) + f.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          {/* Clear All Button */}
          {checks.length > 0 && (
            <button
              className="btn btn-clear-history"
              onClick={() => setShowClearModal(true)}
              title="Clear all history"
            >
              <Trash2 size={15} />
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Success Toast */}
      {clearSuccess && (
        <div className="clear-success-toast animate-fade-in">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          All history cleared successfully
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-20 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* List */}
          <div className="space-y-2">
            {filtered.length === 0 && (
              <div className="text-center py-12 text-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
                {checks.length === 0 ? 'No history yet. Run an affordability check to get started.' : 'No checks found for this filter.'}
              </div>
            )}
            {filtered.map((check) => {
              const color =
                check.decision === 'APPROVE'
                  ? 'var(--color-approve)'
                  : check.decision === 'CRITICAL'
                  ? 'var(--color-critical)'
                  : 'var(--color-defer)';

              return (
                <button
                  key={check.id}
                  className="w-full text-left p-4 rounded-xl transition-all hover:scale-[1.005]"
                  style={{
                    background:
                      selectedCheck?.id === check.id
                        ? 'var(--color-surface-high)'
                        : 'var(--color-surface-container)',
                    border:
                      selectedCheck?.id === check.id
                        ? '1px solid rgba(163, 166, 255, 0.2)'
                        : '1px solid transparent',
                  }}
                  onClick={() => setSelectedCheck(check)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{check.expense_name}</p>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--color-on-surface-variant)' }}>
                        {check.expense_category} • {new Date(check.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right ml-3">
                      <p className="text-sm font-bold">₹{check.expense_amount?.toLocaleString()}</p>
                      <p
                        className="text-[10px] font-bold uppercase tracking-wider"
                        style={{ color }}
                      >
                        {check.decision}
                      </p>
                    </div>
                  </div>
                  {check.claude_explanation && (
                    <p
                      className="text-xs mt-2 line-clamp-2"
                      style={{ color: 'var(--color-on-surface-variant)' }}
                    >
                      {check.claude_explanation}
                    </p>
                  )}
                </button>
              );
            })}
          </div>

          {/* Detail Panel */}
          <div className="lg:sticky lg:top-6 self-start">
            {selectedCheck ? (
              <DecisionCard result={selectedCheck} />
            ) : (
              <div
                className="card-glass flex items-center justify-center h-60 text-sm"
                style={{ color: 'var(--color-on-surface-variant)' }}
              >
                Select a check to view details
              </div>
            )}
          </div>
        </div>
      )}

      {/* Clear Confirmation Modal */}
      {showClearModal && (
        <div className="modal-overlay" onClick={() => !clearing && setShowClearModal(false)}>
          <div
            className="modal-content animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              className="modal-close"
              onClick={() => !clearing && setShowClearModal(false)}
              disabled={clearing}
            >
              <X size={18} />
            </button>

            {/* Warning Icon */}
            <div className="modal-icon-wrapper">
              <AlertTriangle size={28} />
            </div>

            <h3 className="text-headline text-lg font-bold text-center mt-4">
              Clear All History?
            </h3>

            <p className="text-sm text-center mt-2" style={{ color: 'var(--color-on-surface-variant)' }}>
              This will permanently delete <strong>all transactions</strong>, <strong>affordability checks</strong>, and <strong>cash balance snapshots</strong>. This action cannot be undone.
            </p>

            <div className="modal-actions">
              <button
                className="btn btn-secondary flex-1"
                onClick={() => setShowClearModal(false)}
                disabled={clearing}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger flex-1"
                onClick={handleClearAll}
                disabled={clearing}
              >
                {clearing ? (
                  <>
                    <span className="btn-spinner" />
                    Clearing...
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    Yes, Clear Everything
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
