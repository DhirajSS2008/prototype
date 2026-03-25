import { CheckCircle2, AlertTriangle, XOctagon, Clock } from 'lucide-react';

const icons = {
  APPROVE: CheckCircle2,
  DEFER: AlertTriangle,
  CRITICAL: XOctagon,
};

const colors = {
  APPROVE: 'var(--color-approve)',
  DEFER: 'var(--color-defer)',
  CRITICAL: 'var(--color-critical)',
};

export default function AffordabilityHistory({ checks = [] }) {
  if (checks.length === 0) {
    return (
      <div className="text-center py-8 text-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
        <Clock size={32} className="mx-auto mb-3 opacity-40" />
        No affordability checks yet. Use the form above to run your first check.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {checks.map((check) => {
        const Icon = icons[check.decision] || AlertTriangle;
        const color = colors[check.decision] || 'var(--color-on-surface-variant)';

        return (
          <div
            key={check.id}
            className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.005]"
            style={{ background: 'var(--color-surface-container)' }}
          >
            <Icon size={18} style={{ color }} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--color-on-surface)' }}>
                {check.expense_name}
              </p>
              <p className="text-xs" style={{ color: 'var(--color-on-surface-variant)' }}>
                {check.expense_category} • {new Date(check.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-sm font-bold" style={{ color }}>
                ₹{check.expense_amount?.toLocaleString()}
              </p>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
                {check.decision}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
