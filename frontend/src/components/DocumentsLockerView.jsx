import React, { useState, useEffect } from 'react';
import { FolderLock, Download, Trash2, ShieldCheck, FileCheck, HardDrive } from 'lucide-react';
import { api } from '../api';

export default function DocumentsLockerView({ applications, onSelectApp }) {
  const [allDocs, setAllDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAllDocuments() {
      setLoading(true);
      const combined = [];
      for (const app of applications) {
        try {
          const docs = await api.listApplicationDocuments(app.id);
          for (const d of docs) {
            combined.push({
              ...d,
              applicationNumber: app.application_number,
              applicationStatus: app.status,
            });
          }
        } catch {
          // ignore individual fetch errors
        }
      }
      setAllDocs(combined);
      setLoading(false);
    }

    if (applications.length > 0) {
      fetchAllDocuments();
    } else {
      setLoading(false);
    }
  }, [applications]);

  const totalBytes = allDocs.reduce((acc, d) => acc + (d.file_size || 0), 0);

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
        marginBottom: '28px'
      }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', marginBottom: '4px' }}>Citizen Document Locker</h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Securely stored proofs encrypted at-rest and validated by municipal standards.
          </p>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '8px 16px',
          borderRadius: '9999px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#34d399',
          fontSize: '0.85rem',
          fontWeight: 600
        }}>
          <HardDrive size={16} />
          <span>{(totalBytes / 1024).toFixed(1)} KB Used / 5 MB Max</span>
        </div>
      </div>

      {loading ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Retrieving encrypted documents from vault...
        </div>
      ) : allDocs.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center' }}>
          <FolderLock size={48} color="var(--text-dim)" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Your Vault is Empty</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto' }}>
            No documents have been uploaded yet. Open an application to attach your Identity Proof, Address Proof, or Income Slips.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {allDocs.map((doc) => (
            <div key={doc.id} className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span className="badge" style={{
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: '#818cf8',
                  fontSize: '0.72rem'
                }}>
                  {doc.document_type.replace('_', ' ').toUpperCase()}
                </span>
                <span style={{ fontSize: '0.75rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} /> Verified
                </span>
              </div>

              <h4 style={{ fontSize: '0.95rem', marginBottom: '6px', wordBreak: 'break-all' }}>
                {doc.safe_filename}
              </h4>

              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                Linked to #{doc.applicationNumber} • {(doc.file_size / 1024).toFixed(1)} KB
              </p>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderTop: '1px solid var(--border-light)',
                paddingTop: '12px'
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  {doc.mime_type}
                </span>

                <a
                  href={api.getDocumentDownloadUrl(doc.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-primary btn-sm"
                  style={{ textDecoration: 'none' }}
                >
                  <Download size={14} /> Download
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
