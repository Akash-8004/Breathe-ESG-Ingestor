import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const COLORS = ['#00d4aa', '#10b981', '#06b6d4'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: '#1a1d27',
        border: '1px solid rgba(148,163,184,0.18)',
        borderRadius: 8,
        padding: '10px 14px',
        fontSize: '0.8125rem',
      }}
    >
      <p style={{ fontWeight: 600, marginBottom: 4 }}>{label}</p>
      <p style={{ color: '#00d4aa' }}>
        {payload[0].value.toLocaleString()} tCO₂e
      </p>
    </div>
  );
};

export default function ScopeChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📊</div>
        <h3>No scope data</h3>
        <p>Scope breakdown will appear once data is ingested.</p>
      </div>
    );
  }

  return (
    <div className="chart-container" id="scope-chart">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
          <XAxis
            dataKey="scope"
            tick={{ fill: '#94a3b8', fontSize: 13 }}
            axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v.toLocaleString()}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,212,170,0.06)' }} />
          <Bar dataKey="total_emissions" radius={[6, 6, 0, 0]} maxBarSize={60}>
            {data.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
