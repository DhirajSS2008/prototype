import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs"
      style={{
        background: 'var(--color-surface-bright)',
        border: '1px solid var(--color-outline-variant)',
        color: 'var(--color-on-surface)',
      }}
    >
      <p className="font-medium mb-1">{label}</p>
      <p>
        Balance:{' '}
        <strong style={{
          color: point?.projected_balance < 0
            ? 'var(--color-critical)'
            : 'var(--color-primary)',
        }}>
          ₹{point?.projected_balance?.toLocaleString()}
        </strong>
      </p>
      {point?.has_obligation && (
        <p style={{ color: 'var(--color-defer)' }} className="mt-1">
          ⚡ {point.obligation_name}: ₹{point.obligation_amount?.toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default function CashFlowChart({ data = [], currentBalance = 0 }) {
  const chartData = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    projected_balance: d.projected_balance,
  }));

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-60 text-sm"
        style={{ color: 'var(--color-on-surface-variant)' }}>
        No forecast data. Add transactions to see your projected cash flow.
      </div>
    );
  }

  const minBalance = Math.min(...chartData.map(d => d.projected_balance));
  const maxBalance = Math.max(...chartData.map(d => d.projected_balance));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4F46E5" stopOpacity={0.2} />
            <stop offset="100%" stopColor="#4F46E5" stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id="dangerGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#DC2626" stopOpacity={0.2} />
            <stop offset="100%" stopColor="#DC2626" stopOpacity={0.02} />
          </linearGradient>
        </defs>

        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(70, 70, 93, 0.2)"
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tick={{ fill: '#6B7280', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: '#aaa8c3', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
          domain={[Math.min(minBalance * 1.1, 0), maxBalance * 1.1]}
        />
        <Tooltip content={<CustomTooltip />} />

        {/* Zero reference line */}
        {minBalance < 0 && (
          <ReferenceLine
            y={0}
            stroke="var(--color-critical)"
            strokeDasharray="4 4"
            strokeOpacity={0.6}
          />
        )}

        <Area
          type="monotone"
          dataKey="projected_balance"
          stroke="#4F46E5"
          strokeWidth={2}
          fill="url(#balanceGradient)"
          dot={false}
          activeDot={{
            r: 5,
            fill: '#4F46E5',
            stroke: '#FFFFFF',
            strokeWidth: 2,
          }}
        />

        {/* Obligation markers */}
        {chartData
          .filter(d => d.has_obligation)
          .map((d, i) => (
            <ReferenceLine
              key={i}
              x={d.date}
              stroke="var(--color-defer)"
              strokeDasharray="2 2"
              strokeOpacity={0.4}
            />
          ))
        }
      </AreaChart>
    </ResponsiveContainer>
  );
}
