import React, { useRef, useState } from 'react';

function formatBytes(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUploadTab({ sourceType, onUpload, uploading }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragover, setDragover] = useState(false);

  const handleFiles = (files) => {
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragover(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragover(true);
  };

  const handleDragLeave = () => setDragover(false);

  const handleSubmit = () => {
    if (file && onUpload) {
      onUpload(file, sourceType);
    }
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div id={`upload-tab-${sourceType}`}>
      <div
        className={`upload-zone${dragover ? ' dragover' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        id={`upload-zone-${sourceType}`}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json"
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(e.target.files)}
          id={`file-input-${sourceType}`}
        />
        <div className="upload-zone-icon">📁</div>
        <div className="upload-zone-text">
          Drop your <strong>{sourceType.replace('_', ' ')}</strong> file here, or click to browse
        </div>
        <div className="upload-zone-hint">
          Supports CSV, XLSX, XLS, JSON
        </div>
      </div>

      {file && (
        <div className="upload-file-info" id={`file-info-${sourceType}`}>
          <span className="upload-file-icon">📄</span>
          <span className="upload-file-name">{file.name}</span>
          <span className="upload-file-size">{formatBytes(file.size)}</span>
          <button className="btn-icon" onClick={clearFile} title="Remove" id={`clear-file-${sourceType}`}>
            ✕
          </button>
        </div>
      )}

      <div className="upload-actions">
        <button
          className="btn btn-primary"
          disabled={!file || uploading}
          onClick={handleSubmit}
          id={`upload-submit-${sourceType}`}
        >
          {uploading && <span className="spinner" />}
          {uploading ? 'Uploading…' : 'Upload & Ingest'}
        </button>
      </div>
    </div>
  );
}
