import React, { useState } from 'react';
import client from '../api/client';
import EntryDetail from './EntryDetail';

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function EmissionTable({
  entries,
  onApprove,
  onFlag,
  onReject,
  actionLoading,
}) {
  const [expandedId, setExpandedId] = useState(null);
  const [detailData, setDetailData] = useState({});  // cache: { id: detailObj }
  const [detailLoading, setDetailLoading] = useState(null);
  const [flagModal, setFlagModal] = useState(null);
  const [flagReason, setFlagReason] = useState('');

  const toggleExpand = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);

    // Fetch detail if not already cached
    if (!detailData[id]) {
      setDetailLoading(id);
      try {
        const res = await client.get(`/emission-entries/${id}/`);
        setDetailData((prev) => ({ ...prev, [id]: res.data }));
      } catch (err) {
        console.error('Failed to fetch entry detail:', err);
      } finally {
        setDetailLoading(null);
      }
    }
  };

  const handleFlag = () => {
    if (flagModal && flagReason.trim()) {
      onFlag(flagModal, flagReason.trim());
      setFlagModal(null);
      setFlagReason('');
    }
  };

  if (!entries || entries.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <h3>No entries found</h3>
        <p>Adjust your filters or upload data to see emission entries.</p>
      </div>
    );
  }

  return (
    <>
      <div className="data-table-wrapper" id="emission-table-wrapper">
        <table className="data-table" id="emission-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}></th>
              <th>Date</th>
              <th>Source</th>
              <th>Scope</th>
              <th>Category</th>
              <th>CO₂e (tonnes)</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <React.Fragment key={entry.id}>
                <tr id={`entry-row-${entry.id}`}>
                  <td>
                    <button
                      className="btn-icon"
                      onClick={() => toggleExpand(entry.id)}
                      id={`expand-btn-${entry.id}`}
                      title={expandedId === entry.id ? 'Collapse' : 'Expand'}
                    >
                      {expandedId === entry.id ? '▾' : '▸'}
                    </button>
                  </td>
                  <td>{formatDate(entry.activity_date)}</td>
                  <td>{entry.source_type || '—'}</td>
                  <td>{entry.scope || '—'}</td>
                  <td>{entry.category || '—'}</td>
                  <td style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                    {entry.quantity_normalized != null
                      ? (Number(entry.quantity_normalized) / 1000).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })
                      : '—'}
                  </td>
                  <td>
                    <span className={`badge badge--${(entry.status || 'pending').toLowerCase()}`}>
                      {entry.status || 'pending'}
                    </span>
                  </td>
                  <td>
                    <div className="action-btns">
                      <button
                        className="btn btn-sm btn-approve"
                        disabled={actionLoading === entry.id || entry.status === 'APPROVED'}
                        onClick={() => onApprove(entry.id)}
                        id={`approve-btn-${entry.id}`}
                        title="Approve"
                      >
                        ✓
                      </button>
                      <button
                        className="btn btn-sm btn-flag"
                        disabled={actionLoading === entry.id}
                        onClick={() => setFlagModal(entry.id)}
                        id={`flag-btn-${entry.id}`}
                        title="Flag"
                      >
                        ⚑
                      </button>
                      <button
                        className="btn btn-sm btn-reject"
                        disabled={actionLoading === entry.id || entry.status === 'REJECTED'}
                        onClick={() => onReject(entry.id)}
                        id={`reject-btn-${entry.id}`}
                        title="Reject"
                      >
                        ✕
                      </button>
                    </div>
                  </td>
                </tr>

                {expandedId === entry.id && (
                  <tr className="expand-row" id={`expand-row-${entry.id}`}>
                    <td colSpan={8}>
                      {detailLoading === entry.id ? (
                        <div className="loading-center" style={{ padding: '1.5rem' }}>
                          <div className="spinner" />
                          <span>Loading details…</span>
                        </div>
                      ) : (
                        <EntryDetail entry={detailData[entry.id] || entry} />
                      )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Flag reason modal ── */}
      {flagModal && (
        <div className="modal-overlay" id="flag-modal-overlay" onClick={() => setFlagModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} id="flag-modal">
            <h3>Flag Entry #{flagModal}</h3>
            <textarea
              placeholder="Enter reason for flagging…"
              value={flagReason}
              onChange={(e) => setFlagReason(e.target.value)}
              id="flag-reason-input"
              autoFocus
            />
            <div className="modal-actions">
              <button
                className="btn btn-outline btn-sm"
                onClick={() => {
                  setFlagModal(null);
                  setFlagReason('');
                }}
                id="flag-cancel-btn"
              >
                Cancel
              </button>
              <button
                className="btn btn-flag btn-sm"
                disabled={!flagReason.trim()}
                onClick={handleFlag}
                id="flag-submit-btn"
              >
                Submit Flag
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
