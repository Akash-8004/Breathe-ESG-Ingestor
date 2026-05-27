import React, { useEffect, useState } from 'react';
import client from '../api/client';
import SummaryCards from '../components/SummaryCards';
import ScopeChart from '../components/ScopeChart';
import SourceBreakdown from '../components/SourceBreakdown';
import RecentRuns from '../components/RecentRuns';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      try {
        const [summaryRes, runsRes] = await Promise.all([
          client.get('/dashboard/summary/'),
          client.get('/ingestion-runs/'),
        ]);
        if (!cancelled) {
          setSummary(summaryRes.data);
          const runData = Array.isArray(runsRes.data)
            ? runsRes.data
            : runsRes.data.results || [];
          setRuns(runData);
        }
      } catch (err) {
        console.error('Dashboard fetch error:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <>
        <header className="page-header">
          <div>
            <h1>Dashboard</h1>
            <p className="page-header-sub">Emission data overview</p>
          </div>
        </header>
        <div className="page-body">
          <div className="loading-center">
            <div className="spinner spinner--lg" />
            <span>Loading dashboard…</span>
          </div>
        </div>
      </>
    );
  }

  const cards = {
    total: summary?.total_entries ?? 0,
    pending: summary?.pending_count ?? 0,
    approved: summary?.approved_count ?? 0,
    flagged: (summary?.flagged_count ?? 0) + (summary?.rejected_count ?? 0),
  };

  // Transform flat scope totals into the array format ScopeChart expects
  const scopeData = [];
  if (summary?.scope_1_total > 0) scopeData.push({ scope: 'Scope 1', total_emissions: parseFloat(summary.scope_1_total) });
  if (summary?.scope_2_total > 0) scopeData.push({ scope: 'Scope 2', total_emissions: parseFloat(summary.scope_2_total) });
  if (summary?.scope_3_total > 0) scopeData.push({ scope: 'Scope 3', total_emissions: parseFloat(summary.scope_3_total) });

  // Transform flat source counts into the array format SourceBreakdown expects
  const sourceData = [];
  if (summary?.sap_count > 0) sourceData.push({ source_type: 'SAP', count: summary.sap_count });
  if (summary?.utility_count > 0) sourceData.push({ source_type: 'Utility', count: summary.utility_count });
  if (summary?.travel_count > 0) sourceData.push({ source_type: 'Travel', count: summary.travel_count });

  const recentRuns = runs.slice(0, 8);

  return (
    <div className="page-enter">
      <header className="page-header" id="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-header-sub">Emission data overview</p>
        </div>
      </header>

      <div className="page-body">
        <SummaryCards data={cards} />

        <div className="dashboard-grid">
          <div className="card">
            <div className="card-header">
              <h3>Emissions by Scope</h3>
            </div>
            <div className="card-body">
              <ScopeChart data={scopeData} />
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3>Source Breakdown</h3>
            </div>
            <div className="card-body">
              <SourceBreakdown data={sourceData} />
            </div>
          </div>
        </div>

        <div className="dashboard-grid dashboard-grid--full">
          <div className="card">
            <div className="card-header">
              <h3>Recent Ingestion Runs</h3>
            </div>
            <div className="card-body">
              <RecentRuns runs={recentRuns} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
