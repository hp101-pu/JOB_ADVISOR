import React from "react";

const PdfIcon = ({ size = 40 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);

const ResumeUpload = ({ uploadedFile, resumeMeta, isLoadingResume, onUpload, onRemove, onOpenResume, onDelete }) => {
  const triggerFilePicker = () => document.getElementById("resume-file").click();

  return (
    <div className="resume-column">
      <div className="resume-card">
        <div className="resume-card-header">
          <h3>Upload Resume</h3>
        </div>

        {/* Hidden file input — always present */}
        <input
          id="resume-file"
          type="file"
          accept=".pdf"
          onChange={onUpload}
          style={{ display: "none" }}
        />

        {isLoadingResume ? (
          /* ---- Loading state ---- */
          <div className="upload-area upload-area--loading">
            <p className="upload-hint">Loading saved resume…</p>
          </div>

        ) : uploadedFile ? (
          /* ---- New file selected (not yet uploaded) ---- */
          <>
            <div className="file-info">
              <div className="file-icon-container"><PdfIcon /></div>
              <div className="file-details">
                <p className="file-name">{uploadedFile.name}</p>
                <p className="file-size">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <button onClick={onRemove} className="btn-remove" title="Remove file">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <button onClick={triggerFilePicker} className="btn-replace">Replace File</button>
          </>

        ) : resumeMeta ? (
          /* ---- Saved resume exists ---- */
          <>
            <div className="saved-resume-display">
              <div className="saved-resume-icon">
                <PdfIcon size={48} />
              </div>
              <div className="saved-resume-details">
                <p className="saved-resume-name">{resumeMeta.filename}</p>
                <p className="saved-resume-sub">Saved resume</p>
              </div>
              <button onClick={onOpenResume} className="btn-open-pdf" title="Open PDF">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
                Open
              </button>
            </div>
            <div className="upload-action-row">
              <button onClick={triggerFilePicker} className="btn-replace btn-replace--flex">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Replace
              </button>
              <button onClick={onDelete} className="btn-delete-resume">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                  <path d="M10 11v6M14 11v6" />
                  <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                </svg>
                Delete
              </button>
            </div>
          </>

        ) : (
          /* ---- No resume yet ---- */
          <div className="upload-area">
            <label htmlFor="resume-file" className="upload-label">
              <div className="upload-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p className="upload-text">Click to upload your resume</p>
              <p className="upload-hint">PDF format only • Maximum 5MB</p>
            </label>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeUpload;