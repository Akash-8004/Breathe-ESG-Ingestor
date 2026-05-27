import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import ErrorTable from '../components/ErrorTable';

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

export default function RunDetailPage() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [rawRecords, setRawRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function fetchRun() {
      setLoading(true);
      setError('');
      try {
        const [runRes, rawRes] = await Promise.all([
          client.get(`/ingestion-runs/${id}/`),
          client.get(`/ingestion-runs/${id}/raw-records/`).catch(() => ({ data: [] })),
        ]);
        if (!cancelled) {
          setRun(runRes.data);
          const records = Array.isArray(rawRes.data)
            ? rawRes.data
            : rawRes.data.results || [];
          setRawRecords(records);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Failed to load run details.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchRun();
    return () => { cancelled = true; };
  }, [id]);

  if (loading) {
    return (
      <>
        <header className="page-header">
          <div>
            <h1>Run Detail</h1>
            <p className="page-header-sub">Loading…</p>
          </div>
        </header>
        <div className="page-body">
          <div className="loading-center">
            <div className="spinner spinner--lg" />
            <span>Loading run details…</span>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <header className="page-header">
          <div>
            <h1>Run Detail</h1>
          </div>
        </header>
        <div className="page-body">
          <div className="upload-result upload-result--error">
            <h4>Error</h4>
            <p>{error}</p>
          </div>
        </div>
      </>
    );
  }

  const errorRows = rawRecords.filter((r) => r.error || r.errors);

  return (
    <div className="page-enter">
      <header className="page-header" id="run-detail-header">
        <div>
          <h1>Run #{run.id}</h1>
          <p className="page-header-sub">
            {run.source_name || 'Ingestion run details'}
          </p>
        </div>
        <span className={`badge badge--${(run.status || 'processing').toLowerCase()}`}>
          {run.status || 'processing'}
        </span>
      </header>

      <div className="page-body">
        {/* ── Metadata Grid ── */}
        <div className="run-meta-grid" id="run-meta-grid">
          <div className="run-meta-item">
            <div className="run-meta-label">Source Type</div>
            <div className="run-meta-value">{run.source_type || '—'}</div>
          </div>
          <div className="run-meta-item">
            <div className="run-meta-label">Source Name</div>
            <div className="run-meta-value">{run.source_name || '—'}</div>
          </div>
          <div className="run-meta-item">
            <div className="run-meta-label">Created</div>
            <div className="run-meta-value">{formatDateTime(run.triggered_at)}</div>
          </div>
          <div className="run-meta-item">
            <div className="run-meta-label">Completed</div>
            <div className="run-meta-value">{formatDateTime(run.completed_at)}</div>
          </div>
          <div className="run-meta-item">
            <div className="run-meta-label">Total Rows</div>
            <div className="run-meta-value">{run.row_count ?? rawRecords.length}</div>
          </div>
          <div className="run-meta-item">
            <div className="run-meta-label">Success Rows</div>
            <div className="run-meta-value">{run.row_count != null && run.error_count != null ? run.row_count - run.error_count : '—'}</div>
          </div>
          <div className="run-meta-item">
            <div className="run-meta-label">Error Rows</div>
            <div className="run-meta-value" style={{ color: errorRows.length > 0 ? 'var(--status-rejected)' : 'inherit' }}>
              {run.error_count ?? errorRows.length}
            </div>
          </div>
        </div>

        {/* ── Link to Emission Entries ── */}
        <div className="mb-lg">
          <Link
            to={`/review?run_id=${run.id}`}
            className="btn btn-outline"
            id="view-entries-btn"
          >
            View Emission Entries →
          </Link>
        </div>

        {/* ── Error Rows ── */}
        <div className="card">
          <div className="card-header">
            <h3>Error Rows</h3>
            <span className="text-sm text-muted">{errorRows.length} errors</span>
          </div>
          <div className="card-body">
            <ErrorTable errors={errorRows} />
          </div>
        </div>
      </div>
    </div>
  );
}
