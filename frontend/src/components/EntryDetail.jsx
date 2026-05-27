import React from 'react';

function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function EntryDetail({ entry }) {
  const auditTrail = entry.audit_trail || entry.history || [];

  return (
    <div className="expand-content" id={`entry-detail-${entry.id}`}>
      {/* ── Fields ── */}
      <div className="expand-section">
        <h4>Entry Details</h4>
        <div className="entry-detail-grid">
          <div className="entry-field">
            <span className="entry-field-label">ID</span>
            <span className="entry-field-value">{entry.id}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Date</span>
            <span className="entry-field-value">{formatDateTime(entry.activity_date)}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Source Type</span>
            <span className="entry-field-value">{entry.source_type || '—'}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Scope</span>
            <span className="entry-field-value">{entry.scope || '—'}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Category</span>
            <span className="entry-field-value">{entry.category || '—'}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Original Quantity</span>
            <span className="entry-field-value">{entry.quantity ?? '—'} {entry.unit || ''}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Emission Factor</span>
            <span className="entry-field-value">{entry.emission_factor ?? '—'}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">Factor Source</span>
            <span className="entry-field-value" style={{ fontSize: '0.75rem' }}>{entry.emission_factor_source || '—'}</span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">CO₂e (kgCO2e)</span>
            <span className="entry-field-value" style={{ fontWeight: 700, color: 'var(--accent)' }}>
              {entry.quantity_normalized != null ? Number(entry.quantity_normalized).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
            </span>
          </div>
          <div className="entry-field">
            <span className="entry-field-label">CO₂e (tonnes)</span>
            <span className="entry-field-value" style={{ fontWeight: 700 }}>
              {entry.quantity_normalized != null ? (Number(entry.quantity_normalized) / 1000).toFixed(4) : '—'}
            </span>
          </div>
          {entry.facility_code && (
            <div className="entry-field">
              <span className="entry-field-label">Facility</span>
              <span className="entry-field-value">{entry.facility_code}</span>
            </div>
          )}
          {entry.location && (
            <div className="entry-field">
              <span className="entry-field-label">Location</span>
              <span className="entry-field-value">{entry.location}</span>
            </div>
          )}
          {entry.cost != null && (
            <div className="entry-field">
              <span className="entry-field-label">Cost</span>
              <span className="entry-field-value">{entry.cost_currency || ''} {Number(entry.cost).toLocaleString()}</span>
            </div>
          )}
          {entry.flagged_reason && (
            <div className="entry-field" style={{ gridColumn: '1 / -1' }}>
              <span className="entry-field-label">⚠️ Flagged Reason</span>
              <span className="entry-field-value" style={{ color: 'var(--status-flagged, #f59e0b)' }}>{entry.flagged_reason}</span>
            </div>
          )}
        </div>

        {/* Calculation breakdown */}
        {entry.quantity != null && entry.emission_factor != null && (
          <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(0,212,170,0.06)', borderRadius: '8px', fontSize: '0.8125rem' }}>
            <strong>Calculation:</strong>{' '}
            {Number(entry.quantity).toLocaleString()} {entry.unit || ''} × {entry.emission_factor} kgCO2e/{entry.unit || 'unit'} ={' '}
            <strong>{entry.quantity_normalized != null ? Number(entry.quantity_normalized).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'} kgCO2e</strong>
          </div>
        )}
      </div>

      {/* ── Raw Payload ── */}
      {entry.raw_payload && (
        <div className="expand-section">
          <h4>Raw Payload</h4>
          <pre className="raw-payload" id={`raw-payload-${entry.id}`}>
            {typeof entry.raw_payload === 'string'
              ? entry.raw_payload
              : JSON.stringify(entry.raw_payload, null, 2)}
          </pre>
        </div>
      )}

      {/* ── Audit Trail ── */}
      {auditTrail.length > 0 && (
        <div className="expand-section">
          <h4>Audit Trail</h4>
          <div className="audit-trail" id={`audit-trail-${entry.id}`}>
            {auditTrail.map((event, idx) => (
              <div className="audit-entry" key={idx}>
                <span className="audit-time">{formatDateTime(event.timestamp)}</span>
                <span className="audit-action">
                  <span className={`badge badge--${(event.action || '').toLowerCase()}`}>
                    {event.action}
                  </span>
                </span>
                <span className="text-sm text-muted" style={{ flex: 1 }}>
                  {event.actor_name && <strong>{event.actor_name}</strong>}
                  {event.notes && ` — ${event.notes}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
