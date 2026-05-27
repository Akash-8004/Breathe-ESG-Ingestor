import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';
import FileUploadTab from '../components/FileUploadTab';

const TABS = [
  { key: 'sap',          label: 'SAP' },
  { key: 'utility_bill', label: 'Utility Bill' },
  { key: 'travel',       label: 'Travel' },
];

// Map frontend tab keys to backend source_type enum values
const SOURCE_TYPE_MAP = {
  sap: 'SAP',
  utility_bill: 'UTILITY',
  travel: 'TRAVEL',
};

export default function IngestPage() {
  const [activeTab, setActiveTab] = useState('sap');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async (file, sourceType) => {
    setUploading(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('source_type', SOURCE_TYPE_MAP[sourceType] || sourceType);

      const res = await client.post('/ingestion-runs/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setResult({
        success: true,
        data: res.data,
        message: `File "${file.name}" uploaded successfully! Run #${res.data.id} created.`,
      });
    } catch (err) {
      setResult({
        success: false,
        message:
          err.response?.data?.detail ||
          err.response?.data?.error ||
          'Upload failed. Please check the file and try again.',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-enter">
      <header className="page-header" id="ingest-header">
        <div>
          <h1>Ingest Data</h1>
          <p className="page-header-sub">Upload emission data files for processing</p>
        </div>
      </header>

      <div className="page-body">
        <div className="card">
          <div className="card-body">
            {/* ── Tabs ── */}
            <div className="tab-bar" id="ingest-tab-bar">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  className={`tab-btn${activeTab === tab.key ? ' active' : ''}`}
                  onClick={() => {
                    setActiveTab(tab.key);
                    setResult(null);
                  }}
                  id={`tab-btn-${tab.key}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* ── Upload Zone ── */}
            <FileUploadTab
              sourceType={activeTab}
              onUpload={handleUpload}
              uploading={uploading}
            />

            {/* ── Result ── */}
            {result && (
              <div
                className={`upload-result ${
                  result.success ? 'upload-result--success' : 'upload-result--error'
                }`}
                id="upload-result"
              >
                <h4>{result.success ? '✅ Success' : '❌ Error'}</h4>
                <p>{result.message}</p>
                {result.success && result.data?.id && (
                  <p className="mt-md">
                    <Link to={`/runs/${result.data.id}`} className="table-link">
                      View Run Details →
                    </Link>
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
