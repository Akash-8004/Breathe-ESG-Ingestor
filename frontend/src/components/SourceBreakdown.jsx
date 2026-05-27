import React from 'react';

const SOURCE_COLORS = {
  SAP: '#00d4aa',
  sap: '#00d4aa',
  Utility: '#3b82f6',
  UTILITY: '#3b82f6',
  utility_bill: '#3b82f6',
  Travel: '#f59e0b',
  TRAVEL: '#f59e0b',
  travel: '#f59e0b',
  manual: '#a855f7',
};

export default function SourceBreakdown({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🗂️</div>
        <h3>No sources yet</h3>
        <p>Upload data to see source breakdown.</p>
      </div>
    );
  }

  const maxCount = Math.max(...data.map((d) => d.count || 0), 1);

  return (
    <div className="source-list" id="source-breakdown">
      {data.map((source) => {
        const color =
          SOURCE_COLORS[source.source_type] ||
          SOURCE_COLORS[source.name?.toLowerCase()] ||
          '#64748b';
        const pct = ((source.count || 0) / maxCount) * 100;

        return (
          <div
            className="source-item"
            key={source.source_type || source.name}
            id={`source-${source.source_type || source.name}`}
          >
            <span className="source-dot" style={{ background: color }} />
            <span className="source-name">
              {source.source_type || source.name}
            </span>
            <div className="source-bar-wrapper">
              <div
                className="source-bar"
                style={{ width: `${pct}%`, background: color }}
              />
            </div>
            <span className="source-count">{source.count ?? 0}</span>
          </div>
        );
      })}
    </div>
  );
}
