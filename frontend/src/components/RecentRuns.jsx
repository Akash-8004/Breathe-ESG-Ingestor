import React from 'react';
import { Link } from 'react-router-dom';

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const SOURCE_ICONS = {
  SAP: '🏭',
  UTILITY: '⚡',
  TRAVEL: '✈️',
};

export default function RecentRuns({ runs }) {
  if (!runs || runs.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📂</div>
        <h3>No runs yet</h3>
        <p>Ingested files will appear here.</p>
      </div>
    );
  }

  return (
    <div className="recent-runs-list" id="recent-runs">
      {runs.map((run) => (
        <Link
          key={run.id}
          to={`/runs/${run.id}`}
          className="recent-run-item"
          id={`run-item-${run.id}`}
        >
          <div className="recent-run-icon">
            {SOURCE_ICONS[run.source_type] || '📄'}
          </div>
          <div className="recent-run-info">
            <div className="recent-run-name">
              {run.source_name || `Run #${run.id}`}
            </div>
            <div className="recent-run-time">{formatDate(run.triggered_at || run.created_at)}</div>
          </div>
          <span className={`badge badge--${(run.status || 'processing').toLowerCase()}`}>
            {run.status || 'processing'}
          </span>
        </Link>
      ))}
    </div>
  );
}
