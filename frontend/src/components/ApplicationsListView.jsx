import React, { useState } from 'react';
import { Search, PlusCircle, FileText, ArrowRight, Filter, Calendar } from 'lucide-react';

export default function ApplicationsListView({ 
  applications, 
  user, 
  onSelectApp, 
  onOpenNewApp, 
  onOpenAuth 
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const filtered = applications.filter((app) => {
    const matchesSearch = 
      app.application_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (app.form_data?.full_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (app.form_data?.district || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = 
      filterStatus === 'ALL' || 
      app.status.toUpperCase() === filterStatus.toUpperCase();

    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      {/* Top Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
        marginBottom: '28px'
      }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', marginBottom: '4px' }}>My Applications</h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Track progress, submit documents, and review municipal submissions.
          </p>
        </div>

        {user ? (
          <button className="btn btn-primary" onClick={onOpenNewApp}>
            <PlusCircle size={17} />
            <span>New Application</span>
          </button>
        ) : (
          <button className="btn btn-primary" onClick={onOpenAuth}>
            <span>Sign In to Apply</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{
        padding: '16px 20px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Search Input */}
        <div style={{
          position: 'relative',
          flex: '1',
          minWidth: '240px'
        }}>
          <Search size={18} color="var(--text-dim)" style={{
            position: 'absolute',
            left: '14px',
            top: '50%',
            transform: 'translateY(-50%)'
          }} />
          <input
            type="text"
            className="form-control"
            placeholder="Search by ID, name, or district..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ paddingLeft: '42px', margin: 0 }}
          />
        </div>

        {/* Status Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflowX: 'auto', padding: '4px 0' }}>
          {['ALL', 'DRAFT', 'DOCUMENTS_PENDING', 'SUBMITTED', 'CANCELLED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              style={{
                padding: '6px 14px',
                borderRadius: '9999px',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: 'none',
                background: filterStatus === st ? '#6366f1' : 'rgba(255, 255, 255, 0.06)',
                color: filterStatus === st ? '#ffffff' : 'var(--text-muted)',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap'
              }}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Applications Cards Grid */}
      {filtered.length === 0 ? (
        <div className="glass-panel" style={{
          padding: '60px 24px',
          textAlign: 'center',
          borderRadius: '16px'
        }}>
          <FileText size={48} color="var(--text-dim)" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>No Applications Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto 24px' }}>
            {searchTerm 
              ? 'No records matched your search query. Try searching for something else.'
              : 'You have not submitted any government service applications yet.'}
          </p>
          {user && (
            <button className="btn btn-primary" onClick={onOpenNewApp}>
              <PlusCircle size={16} />
              <span>Create First Application</span>
            </button>
          )}
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '20px'
        }}>
          {filtered.map((app) => (
            <div
              key={app.id}
              className="glass-panel"
              style={{
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                cursor: 'pointer'
              }}
              onClick={() => onSelectApp(app)}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <span className={`badge badge-${app.status.toLowerCase()}`}>
                    {app.status.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    Ver. {app.data_version}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.15rem', marginBottom: '4px' }}>
                  #{app.application_number}
                </h3>

                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                  {app.form_data?.full_name || 'Draft Citizen'} • {app.form_data?.district || 'Kathmandu'}
                </p>

                {/* Progress bar */}
                <div style={{ margin: '12px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-dim)' }}>{app.current_step}</span>
                    <span style={{ fontWeight: 700, color: '#818cf8' }}>{app.progress_percent}%</span>
                  </div>
                  <div className="progress-bar-container" style={{ margin: 0 }}>
                    <div className="progress-bar-fill" style={{ width: `${app.progress_percent}%` }}></div>
                  </div>
                </div>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderTop: '1px solid var(--border-light)',
                paddingTop: '16px',
                marginTop: '16px'
              }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                  {app.document_count} Documents Attached
                </span>

                <button className="btn btn-secondary btn-sm" onClick={(e) => {
                  e.stopPropagation();
                  onSelectApp(app);
                }}>
                  <span>Details</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
