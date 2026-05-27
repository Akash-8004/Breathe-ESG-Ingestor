import React from 'react';

const CARD_CONFIG = [
  { key: 'total',    label: 'Total Entries',       icon: '📦', variant: 'total' },
  { key: 'pending',  label: 'Pending Review',      icon: '⏳', variant: 'pending' },
  { key: 'approved', label: 'Approved',            icon: '✅', variant: 'approved' },
  { key: 'flagged',  label: 'Flagged / Rejected',  icon: '⚠️', variant: 'flagged' },
];

export default function SummaryCards({ data }) {
  return (
    <div className="summary-grid" id="summary-cards">
      {CARD_CONFIG.map(({ key, label, icon, variant }) => (
        <div
          key={key}
          className={`summary-card summary-card--${variant}`}
          id={`summary-card-${key}`}
        >
          <div className="summary-card-icon">{icon}</div>
          <div className="summary-card-value">
            {data?.[key] ?? '—'}
          </div>
          <div className="summary-card-label">{label}</div>
        </div>
      ))}
    </div>
  );
}
