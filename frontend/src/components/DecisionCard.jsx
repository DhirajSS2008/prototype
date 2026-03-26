import {
  CheckCircle2,
  AlertTriangle,
  XOctagon,
  Calendar,
  ArrowRight,
  Mail,
  CreditCard,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useState } from 'react';

const DECISION_CONFIG = {
  APPROVE: {
    className: 'decision-approve',
    icon: CheckCircle2,
    iconColor: 'var(--color-approve)',
    label: 'Affordable',
    labelColor: 'var(--color-approve)',
  },
  DEFER: {
    className: 'decision-defer',
    icon: AlertTriangle,
    iconColor: 'var(--color-defer)',
    label: 'Conditional — Defer Recommended',
    labelColor: 'var(--color-defer)',
  },
  CRITICAL: {
    className: 'decision-critical',
    icon: XOctagon,
    iconColor: 'var(--color-critical)',
    label: 'Critical Conflict',
    labelColor: 'var(--color-critical)',
  },
};

export default function DecisionCard({ result, onAction }) {
  const [showDetails, setShowDetails] = useState(false);
  const [showEmail, setShowEmail] = useState(false);

  if (!result) return null;

  const config = DECISION_CONFIG[result.decision] || DECISION_CONFIG.DEFER;
  const Icon = config.icon;

  return (
    <div className={`decision-card animate-fade-in ${config.className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Icon size={24} style={{ color: config.iconColor }} />
            {result.decision === 'CRITICAL' && (
              <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full pulse-critical"
                style={{ background: 'var(--color-critical)' }} />
            )}
          </div>
          <div>
            <p className="text-sm font-bold" style={{ color: config.labelColor }}>
              {config.label}
            </p>
            <p className="text-xs" style={{ color: 'var(--color-on-surface-variant)' }}>
              {result.expense_name} • ₹{result.expense_amount?.toLocaleString()}
            </p>
          </div>
        </div>
        <span
          className="text-xs px-2 py-1 rounded-full font-semibold"
          style={{
            background: 'var(--color-primary-container)',
            color: 'var(--color-primary)',
          }}
        >
          {result.priority_tier} Priority
        </span>
      </div>

      {/* Claude Explanation */}
      {result.claude_explanation && (
        <div
          className="rounded-lg p-3 mb-4 text-sm leading-relaxed"
          style={{ background: 'var(--color-surface-container)', color: 'var(--color-on-surface)' }}
        >
          {result.claude_explanation}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <p className="text-label mb-1">Current Balance</p>
          <p className="text-sm font-bold" style={{ color: 'var(--color-on-surface)' }}>
            ₹{result.current_balance?.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-label mb-1">Projected</p>
          <p className="text-sm font-bold" style={{
            color: result.projected_balance_at_date < 0
              ? 'var(--color-critical)'
              : 'var(--color-on-surface)',
          }}>
            ₹{result.projected_balance_at_date?.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-label mb-1">Burn Rate</p>
          <p className="text-sm font-bold" style={{ color: 'var(--color-on-surface)' }}>
            ₹{result.monthly_burn_rate?.toLocaleString()}/mo
          </p>
        </div>
      </div>

      {/* Deferral Info */}
      {result.decision === 'DEFER' && result.deferral_days && (
        <div
          className="flex items-center gap-2 rounded-lg p-3 mb-4"
          style={{ background: 'rgba(245, 158, 11, 0.08)' }}
        >
          <Calendar size={16} style={{ color: 'var(--color-defer)' }} />
          <span className="text-sm" style={{ color: 'var(--color-defer)' }}>
            Recommended deferral: <strong>{result.deferral_days} days</strong>
            {result.recommended_date && <> (until {result.recommended_date})</>}
          </span>
        </div>
      )}

      {/* Alternative Paths for CRITICAL */}
      {result.decision === 'CRITICAL' && result.alternative_paths?.length > 0 && (
        <div className="space-y-2 mb-4">
          <p className="text-label">Alternative Options</p>
          {result.alternative_paths.map((path, idx) => (
            <button
              key={idx}
              className="w-full text-left rounded-lg p-3 transition-all hover:scale-[1.01]"
              style={{
                background: 'var(--color-surface-container)',
                border: '1px solid var(--color-outline-variant)',
              }}
              onClick={() => {
                if (path.path_type === 'defer_obligation') setShowEmail(!showEmail);
                if (onAction) onAction(path);
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                {path.path_type === 'defer_obligation' ? (
                  <Mail size={14} style={{ color: 'var(--color-defer)' }} />
                ) : (
                  <CreditCard size={14} style={{ color: 'var(--color-primary)' }} />
                )}
                <span className="text-sm font-medium" style={{ color: 'var(--color-on-surface)' }}>
                  {path.path_type === 'defer_obligation' ? 'Negotiate Deferral' : 'Short-Term Borrowing'}
                </span>
                <ArrowRight size={12} className="ml-auto" style={{ color: 'var(--color-on-surface-variant)' }} />
              </div>
              <p className="text-xs" style={{ color: 'var(--color-on-surface-variant)' }}>
                {path.description}
              </p>
              {path.borrowing_amount && (
                <div className="flex gap-4 mt-2 text-xs">
                  <span>Amount: <strong>₹{path.borrowing_amount.toLocaleString()}</strong></span>
                  <span>Cost: <strong>₹{path.borrowing_cost?.toLocaleString()}</strong></span>
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Negotiation Email */}
      {showEmail && result.negotiation_email && (
        <div className="animate-fade-in rounded-lg p-3 mb-4"
          style={{ background: 'var(--color-surface-container)' }}>
          <p className="text-label mb-2">Draft Negotiation Email</p>
          <pre className="text-xs whitespace-pre-wrap" style={{ color: 'var(--color-on-surface-variant)' }}>
            {result.negotiation_email}
          </pre>
          <button className="btn btn-secondary text-xs mt-2" onClick={() => {
            navigator.clipboard.writeText(result.negotiation_email);
          }}>
            Copy to Clipboard
          </button>
        </div>
      )}

      {/* Toggle Details */}
      <button
        className="flex items-center gap-1 text-xs mt-2"
        style={{ color: 'var(--color-primary)' }}
        onClick={() => setShowDetails(!showDetails)}
      >
        {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {showDetails ? 'Hide' : 'Show'} Details
      </button>

      {showDetails && (
        <div className="mt-3 text-xs space-y-1 animate-fade-in"
          style={{ color: 'var(--color-on-surface-variant)' }}>
          <p>Reason Code: <strong>{result.reason_code}</strong></p>
          <p>Category: <strong>{result.expense_category}</strong></p>
          <p>Forecast Points: <strong>{result.forecast_data?.length || 0}</strong></p>
        </div>
      )}
    </div>
  );
}
