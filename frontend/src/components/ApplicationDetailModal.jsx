import React, { useState, useEffect } from 'react';
import {
  X,
  Upload,
  FileCheck,
  Download,
  Trash2,
  AlertTriangle,
  Check,
  Clock,
  ShieldCheck,
  Calendar,
  MapPin,
  Briefcase
} from 'lucide-react';
import { api } from '../api';

export default function ApplicationDetailModal({ application, isOpen, onClose, onRefresh }) {
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadType, setUploadType] = useState('identity_proof');
  const [fileToUpload, setFileToUpload] = useState(null);
  const [docError, setDocError] = useState('');
  const [cancelLoading, setCancelLoading] = useState(false);

  useEffect(() => {
    if (application?.id && isOpen) {
      loadDocuments();
    }
  }, [application?.id, isOpen]);

  if (!isOpen || !application) return null;

  async function loadDocuments() {
    setLoadingDocs(true);
    setDocError('');
    try {
      const data = await api.listApplicationDocuments(application.id);
      setDocuments(data);
    } catch (err) {
      console.error(err);
      setDocError('Failed to load application documents.');
    } finally {
      setLoadingDocs(false);
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!fileToUpload) return;
    setUploading(true);
    setDocError('');

    try {
      await api.uploadDocument(application.id, uploadType, fileToUpload);
      setFileToUpload(null);
      // Reset file input
      const fileInput = document.getElementById('doc-file-input');
      if (fileInput) fileInput.value = '';
      await loadDocuments();
      onRefresh();
    } catch (err) {
      console.error(err);
      setDocError(err.message || 'File upload failed (Max 5MB, PDF/JPEG/PNG only).');
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteDoc(docId) {
    if (!window.confirm('Delete this uploaded document?')) return;
    try {
      await api.deleteDocument(docId);
      await loadDocuments();
      onRefresh();
    } catch (err) {
      alert(err.message || 'Failed to delete document.');
    }
  }

  async function handleCancelApp() {
    if (!window.confirm('Are you sure you want to cancel this application?')) return;
    setCancelLoading(true);
    try {
      await api.cancelApplication(application.id);
      onRefresh();
      onClose();
    } catch (err) {
      alert(err.message || 'Failed to cancel application.');
    } finally {
      setCancelLoading(false);
    }
  }

  const formData = application.form_data || {};

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '780px' }}>
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="modal-title">Application #{application.application_number}</h2>
              <span className={`badge badge-${application.status.toLowerCase()}`}>
                {application.status.toUpperCase()}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Version {application.data_version} • Income Certificate Application
            </p>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Progress bar */}
        <div style={{ margin: '16px 0 24px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Progress: {application.current_step}</span>
            <span style={{ fontWeight: 700, color: '#818cf8' }}>{application.progress_percent}%</span>
          </div>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${application.progress_percent}%` }}></div>
          </div>
        </div>

        {/* Form Details Grid */}
        <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCheck size={18} color="#818cf8" />
            <span>Applicant Information</span>
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            fontSize: '0.88rem'
          }}>
            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>FULL NAME</span>
              <strong>{formData.full_name || 'N/A'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>CITIZENSHIP NO.</span>
              <strong>{formData.citizenship_number || 'N/A'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>DATE OF BIRTH</span>
              <span>{formData.date_of_birth || 'N/A'}</span>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>DISTRICT & WARD</span>
              <span>{formData.district}, Ward #{formData.ward_no}</span>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>ANNUAL INCOME</span>
              <strong style={{ color: '#34d399' }}>{formData.annual_income || 'N/A'}</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>PURPOSE</span>
              <span>{formData.purpose || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Attached Documents Section */}
        <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={18} color="#10b981" />
              <span>Attached Documents ({documents.length})</span>
            </h3>
          </div>

          {docError && (
            <div style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#fb7185',
              fontSize: '0.85rem',
              marginBottom: '16px'
            }}>
              {docError}
            </div>
          )}

          {/* List of documents */}
          {loadingDocs ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading attached documents...</p>
          ) : documents.length === 0 ? (
            <div style={{
              padding: '24px',
              textAlign: 'center',
              border: '1px dashed var(--border-light)',
              borderRadius: '12px',
              color: 'var(--text-muted)',
              fontSize: '0.85rem'
            }}>
              No documents attached yet. Upload identity proof or income verification below.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-light)'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <strong style={{ fontSize: '0.9rem' }}>{doc.safe_filename}</strong>
                      <span className="badge" style={{
                        background: 'rgba(99, 102, 241, 0.15)',
                        color: '#818cf8',
                        fontSize: '0.7rem'
                      }}>
                        {doc.document_type.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {(doc.file_size / 1024).toFixed(1)} KB • Verified
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <a
                      href={api.getDocumentDownloadUrl(doc.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary btn-sm"
                      title="Download file"
                    >
                      <Download size={14} />
                    </a>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteDoc(doc.id)}
                      title="Delete document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Upload Form */}
          <form onSubmit={handleUpload} style={{
            marginTop: '16px',
            padding: '16px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.25)',
            border: '1px solid var(--border-light)'
          }}>
            <h4 style={{ fontSize: '0.85rem', marginBottom: '12px', color: 'var(--text-muted)' }}>
              UPLOAD NEW VERIFICATION DOCUMENT
            </h4>

            <div className="form-row" style={{ alignItems: 'flex-end' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Document Category</label>
                <select
                  className="form-control"
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value)}
                >
                  <option value="identity_proof">Identity Proof (Aadhaar / Citizenship / Passport)</option>
                  <option value="address_proof">Address Proof (Electricity Bill / Ward Letter)</option>
                  <option value="income_proof">Income Proof (Salary Slip / Tax Return)</option>
                  <option value="photograph">Recent Passport Size Photograph</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Select File (PDF, PNG, JPG)</label>
                <input
                  id="doc-file-input"
                  type="file"
                  required
                  accept=".pdf,image/jpeg,image/png"
                  className="form-control"
                  onChange={(e) => setFileToUpload(e.target.files[0])}
                  style={{ padding: '8px' }}
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={uploading || !fileToUpload}
                style={{ height: '46px' }}
              >
                {uploading ? 'Uploading...' : (
                  <>
                    <Upload size={16} /> Upload
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Modal footer / cancellation */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderTop: '1px solid var(--border-light)',
          paddingTop: '20px'
        }}>
          {application.status !== 'cancelled' ? (
            <button
              className="btn btn-danger btn-sm"
              onClick={handleCancelApp}
              disabled={cancelLoading}
            >
              <AlertTriangle size={15} />
              <span>Cancel Application</span>
            </button>
          ) : (
            <span style={{ fontSize: '0.85rem', color: '#fb7185' }}>Application has been cancelled.</span>
          )}

          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
