import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import client from '../api/client';
import EmissionTable from '../components/EmissionTable';

export default function ReviewPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  // Filters
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [scope, setScope] = useState(searchParams.get('scope') || '');
  const [dateFrom, setDateFrom] = useState(searchParams.get('date_from') || '');
  const [dateTo, setDateTo] = useState(searchParams.get('date_to') || '');

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (status) params.status = status;
      if (scope) params.scope = scope;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const runId = searchParams.get('run_id');
      if (runId) params.run_id = runId;

      const res = await client.get('/emission-entries/', { params });
      const data = Array.isArray(res.data) ? res.data : res.data.results || [];
      setEntries(data);
    } catch (err) {
      console.error('Failed to load entries:', err);
    } finally {
      setLoading(false);
    }
  }, [status, scope, dateFrom, dateTo, searchParams]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  // Update URL params on filter change
  useEffect(() => {
    const params = {};
    if (status) params.status = status;
    if (scope) params.scope = scope;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    const runId = searchParams.get('run_id');
    if (runId) params.run_id = runId;
    setSearchParams(params, { replace: true });
  }, [status, scope, dateFrom, dateTo]);

  // Actions
  const handleApprove = async (id) => {
    setActionLoading(id);
    try {
      await client.post(`/emission-entries/${id}/approve/`);
      setEntries((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: 'APPROVED' } : e))
      );
    } catch (err) {
      console.error('Approve failed:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleFlag = async (id, reason) => {
    setActionLoading(id);
    try {
      await client.post(`/emission-entries/${id}/flag/`, { reason });
      setEntries((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: 'FLAGGED' } : e))
      );
    } catch (err) {
      console.error('Flag failed:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id) => {
    setActionLoading(id);
    try {
      await client.post(`/emission-entries/${id}/reject/`);
      setEntries((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: 'REJECTED' } : e))
      );
    } catch (err) {
      console.error('Reject failed:', err);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="page-enter">
      <header className="page-header" id="review-header">
        <div>
          <h1>Review Entries</h1>
          <p className="page-header-sub">
            {entries.length} entries {status ? `• ${status}` : ''}
          </p>
        </div>
      </header>

      <div className="page-body">
        {/* ── Filters ── */}
        <div className="filters-bar" id="review-filters">
          <div className="filter-group">
            <label htmlFor="filter-status">Status</label>
            <select
              id="filter-status"
              className="filter-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="FLAGGED">Flagged</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-scope">Scope</label>
            <select
              id="filter-scope"
              className="filter-select"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
            >
              <option value="">All</option>
              <option value="SCOPE_1">Scope 1</option>
              <option value="SCOPE_2">Scope 2</option>
              <option value="SCOPE_3">Scope 3</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="filter-date-from">From</label>
            <input
              id="filter-date-from"
              className="filter-input"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="filter-date-to">To</label>
            <input
              id="filter-date-to"
              className="filter-input"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>

        {/* ── Table ── */}
        {loading ? (
          <div className="loading-center">
            <div className="spinner spinner--lg" />
            <span>Loading entries…</span>
          </div>
        ) : (
          <div className="card">
            <div className="card-body" style={{ padding: 0 }}>
              <EmissionTable
                entries={entries}
                onApprove={handleApprove}
                onFlag={handleFlag}
                onReject={handleReject}
                actionLoading={actionLoading}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
