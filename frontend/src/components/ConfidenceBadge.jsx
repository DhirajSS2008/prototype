import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function ConfidenceBadge({ score }) {
  const pct = Math.round((score || 0) * 100);

  let className = 'confidence-badge ';
  let Icon;

  if (pct >= 70) {
    className += 'confidence-high';
    Icon = ShieldCheck;
  } else if (pct >= 40) {
    className += 'confidence-medium';
    Icon = Shield;
  } else {
    className += 'confidence-low';
    Icon = ShieldAlert;
  }

  return (
    <span className={className}>
      <Icon size={12} />
      {pct}%
    </span>
  );
}
