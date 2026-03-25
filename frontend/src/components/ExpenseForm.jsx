import { useState } from 'react';
import { checkAffordability } from '../api/client';
import { CircleDollarSign, Calendar, Tag, Send, Loader2 } from 'lucide-react';

const CATEGORIES = [
  'Health & Medical', 'Legal & Compliance', 'Critical Operations', 'Tax & Government',
  'Equipment & Tools', 'Travel & Transport', 'Vendor Advances', 'Marketing',
  'Rent & Lease', 'Loan EMI', 'Supplier Payments', 'Office Supplies',
  'Subscriptions', 'Upgrades', 'Discretionary', 'Entertainment', 'Other',
];

export default function ExpenseForm({ onResult }) {
  const [form, setForm] = useState({
    name: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    category: 'Other',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.amount) return;

    setLoading(true);
    setError('');

    try {
      const res = await checkAffordability({
        name: form.name,
        amount: parseFloat(form.amount),
        date: new Date(form.date).toISOString(),
        category: form.category,
      });
      if (onResult) onResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run affordability check');
    } finally {
      setLoading(false);
    }
  };

  const update = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-headline text-base font-semibold flex items-center gap-2">
        <CircleDollarSign size={18} style={{ color: 'var(--color-primary)' }} />
        Check New Expense
      </h3>

      {/* Name */}
      <div>
        <label className="text-label block mb-1.5">Expense Name</label>
        <input
          type="text"
          className="input-field"
          placeholder="e.g., New laptop for design team"
          value={form.name}
          onChange={(e) => update('name', e.target.value)}
          required
        />
      </div>

      {/* Amount & Date Row */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-label block mb-1.5">Amount (₹)</label>
          <div className="relative">
            <span
              className="absolute left-3 top-1/2 -translate-y-1/2 text-sm"
              style={{ color: 'var(--color-on-surface-variant)' }}
            >
              ₹
            </span>
            <input
              type="number"
              className="input-field pl-7"
              placeholder="0.00"
              min="1"
              step="0.01"
              value={form.amount}
              onChange={(e) => update('amount', e.target.value)}
              required
            />
          </div>
        </div>
        <div>
          <label className="text-label block mb-1.5">Date</label>
          <input
            type="date"
            className="input-field"
            value={form.date}
            onChange={(e) => update('date', e.target.value)}
            required
          />
        </div>
      </div>

      {/* Category */}
      <div>
        <label className="text-label block mb-1.5">Category</label>
        <select
          className="input-field"
          value={form.category}
          onChange={(e) => update('category', e.target.value)}
        >
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <p className="text-xs" style={{ color: 'var(--color-critical)' }}>{error}</p>
      )}

      {/* Submit */}
      <button
        type="submit"
        className="btn btn-primary w-full justify-center"
        disabled={loading || !form.name || !form.amount}
        style={{ opacity: loading ? 0.7 : 1 }}
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Send size={16} />
            Check Affordability
          </>
        )}
      </button>
    </form>
  );
}
