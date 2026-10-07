import React from 'react';
import { 
  FileText, 
  PlusCircle, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  ArrowRight, 
  Sparkles,
  Zap,
  Award
} from 'lucide-react';

export default function DashboardView({ 
  applications, 
  user, 
  onOpenNewApp, 
  onOpenAuth, 
  onSelectApp, 
  setCurrentTab 
}) {
  const total = applications.length;
  const draftCount = applications.filter((a) => a.status === 'draft').length;
  const inProgress = applications.filter((a) => a.status === 'documents_pending' || a.status === 'under_government_review' || a.status === 'documents_under_review').length;
  const completed = applications.filter((a) => a.status === 'completed' || a.status === 'approved').length;

  return (
    <div>
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-tag">
            <Sparkles size={14} />
            <span>AI-Powered Citizen Assistance Portal</span>
          </div>

          <h1 className="hero-title">
            Simplifying Government Public Services for Everyone.
          </h1>

          <p className="hero-desc">
            Apply for income certificates, upload supporting documents safely with encryption,
            and monitor your status through our intelligent citizen portal.
          </p>

          <div className="hero-actions">
            {user ? (
              <button className="btn btn-primary btn-lg" onClick={onOpenNewApp}>
                <PlusCircle size={18} />
                <span>Start New Application</span>
              </button>
            ) : (
              <button className="btn btn-primary btn-lg" onClick={onOpenAuth}>
                <Zap size={18} color="#34d399" />
                <span>One-Click Demo Citizen Sign In</span>
              </button>
            )}

            <button 
              className="btn btn-secondary btn-lg"
              onClick={() => setCurrentTab('applications')}
            >
              <span>View All Applications</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon indigo">
            <FileText size={26} />
          </div>
          <div>
            <div className="stat-value">{total}</div>
            <div className="stat-label">Total Applications</div>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon amber">
            <Clock size={26} />
          </div>
          <div>
            <div className="stat-value">{inProgress + draftCount}</div>
            <div className="stat-label">Active / Pending Review</div>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon emerald">
            <CheckCircle2 size={26} />
          </div>
          <div>
            <div className="stat-value">{completed}</div>
            <div className="stat-label">Completed & Verified</div>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon cyan">
            <ShieldCheck size={26} />
          </div>
          <div>
            <div className="stat-value">100%</div>
            <div className="stat-label">Encrypted Document Vault</div>
          </div>
        </div>
      </div>

      {/* Available Public Services */}
      <div style={{ marginBottom: '36px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem' }}>Popular Citizen Services</h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Select a service below to start your application guided by e-SewaSathi
            </p>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px'
        }}>
          {/* Income Certificate Card */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: '#818cf8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Award size={22} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.1rem' }}>Income Certificate</h3>
                  <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>Active Online Service</span>
                </div>
              </div>

              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: 1.5 }}>
                Official municipal verification of household annual earnings for scholarships, banking, and university admissions.
              </p>
            </div>

            <button 
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={user ? onOpenNewApp : onOpenAuth}
            >
              <span>Apply Now</span>
              <ArrowRight size={16} />
            </button>
          </div>

          {/* Domicile Certificate Card */}
          <div className="glass-panel" style={{ padding: '24px', opacity: 0.85 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: 'rgba(6, 182, 212, 0.15)',
                color: '#22d3ee',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <ShieldCheck size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.1rem' }}>Local Domicile Proof</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>Phase 2 Rollout</span>
              </div>
            </div>

            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: 1.5 }}>
              Verification of permanent residency issued through local municipal ward offices.
            </p>

            <button className="btn btn-secondary" style={{ width: '100%', cursor: 'not-allowed' }} disabled>
              <span>Coming Soon</span>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Applications Preview */}
      {applications.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '1.25rem' }}>Recent Applications</h2>
            <button 
              className="btn btn-secondary btn-sm"
              onClick={() => setCurrentTab('applications')}
            >
              View All ({applications.length})
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {applications.slice(0, 3).map((app) => (
              <div 
                key={app.id}
                className="glass-panel"
                style={{
                  padding: '18px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer'
                }}
                onClick={() => onSelectApp(app)}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <strong style={{ fontSize: '0.95rem' }}>#{app.application_number}</strong>
                    <span className={`badge badge-${app.status.toLowerCase()}`}>
                      {app.status.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {app.form_data?.full_name || 'Draft applicant'} • {app.current_step}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#818cf8' }}>
                      {app.progress_percent}%
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {app.document_count} docs
                    </div>
                  </div>
                  <ArrowRight size={18} color="var(--text-muted)" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
