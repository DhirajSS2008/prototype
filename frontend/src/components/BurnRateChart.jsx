import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = [
  '#4F46E5', '#7C3AED', '#DB2777', '#059669', '#D97706',
  '#DC2626', '#6366F1', '#8B5CF6', '#EC4899', '#10B981',
  '#F59E0B', '#EF4444', '#3B82F6', '#6B7280',
];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs"
      style={{
        background: 'var(--color-surface-bright)',
        border: '1px solid var(--color-outline-variant)',
        color: 'var(--color-on-surface)',
      }}
    >
      <p className="font-medium">{name}</p>
      <p style={{ color: 'var(--color-primary)' }}>₹{value.toLocaleString()}/mo</p>
    </div>
  );
};

const CustomLegend = ({ payload }) => (
  <div className="flex flex-wrap gap-x-4 gap-y-1 justify-center mt-2">
    {payload?.map((entry, idx) => (
      <div key={idx} className="flex items-center gap-1.5 text-xs">
        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: entry.color }} />
        <span style={{ color: 'var(--color-on-surface-variant)' }}>{entry.value}</span>
      </div>
    ))}
  </div>
);

export default function BurnRateChart({ data = {} }) {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name,
    value: value.avg_monthly || 0,
  })).filter(d => d.value > 0)
    .sort((a, b) => b.value - a.value);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-60 text-sm" 
        style={{ color: 'var(--color-on-surface-variant)' }}>
        No spending data yet. Upload bank statements to see your burn rate.
      </div>
    );
  }

  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
            animationBegin={0}
            animationDuration={800}
          >
            {chartData.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} stroke="none" />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Center label */}
      <div className="text-center -mt-44 pointer-events-none relative z-10">
        <p className="text-label">Monthly Burn</p>
        <p className="text-display text-2xl" style={{ color: 'var(--color-on-surface)' }}>
          ₹{total.toLocaleString()}
        </p>
      </div>
      <div className="h-20" />
    </div>
  );
}
