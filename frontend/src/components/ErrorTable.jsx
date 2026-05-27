import React from 'react';

export default function ErrorTable({ errors }) {
  if (!errors || errors.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">✅</div>
        <h3>No errors</h3>
        <p>All rows were processed successfully.</p>
      </div>
    );
  }

  return (
    <div className="data-table-wrapper" id="error-table-wrapper">
      <table className="data-table" id="error-table">
        <thead>
          <tr>
            <th>Row</th>
            <th>Field</th>
            <th>Error</th>
            <th>Raw Value</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((err, idx) => (
            <tr key={idx} id={`error-row-${idx}`}>
              <td>{err.row_number ?? idx + 1}</td>
              <td>{err.field || '—'}</td>
              <td style={{ color: 'var(--status-rejected)' }}>
                {err.error || err.message || '—'}
              </td>
              <td className="text-muted" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {err.raw_value != null ? String(err.raw_value) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
