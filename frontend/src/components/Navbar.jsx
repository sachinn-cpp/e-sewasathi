import React from 'react';
import { 
  FileText, 
  Home, 
  PlusCircle, 
  FolderLock, 
  User, 
  LogOut, 
  Activity, 
  Sparkles 
} from 'lucide-react';

export default function Navbar({ 
  currentTab, 
  setCurrentTab, 
  user, 
  onOpenAuth, 
  onLogout, 
  onNewApp, 
  health 
}) {
  return (
    <header className="navbar">
      <div className="nav-brand" onClick={() => setCurrentTab('dashboard')}>
        <div className="brand-icon">
          <Sparkles size={20} />
        </div>
        <div>
          <span className="brand-title">e-SewaSathi</span>
          <span className="brand-badge" style={{ marginLeft: '8px' }}>AI Citizen Companion</span>
        </div>
      </div>

      <nav className="nav-links">
        <button 
          className={`nav-link-btn ${currentTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setCurrentTab('dashboard')}
        >
          <Home size={16} />
          <span>Dashboard</span>
        </button>
        <button 
          className={`nav-link-btn ${currentTab === 'applications' ? 'active' : ''}`}
          onClick={() => setCurrentTab('applications')}
        >
          <FileText size={16} />
          <span>Applications</span>
        </button>
        <button 
          className={`nav-link-btn ${currentTab === 'documents' ? 'active' : ''}`}
          onClick={() => setCurrentTab('documents')}
        >
          <FolderLock size={16} />
          <span>Doc Locker</span>
        </button>
      </nav>

      <div className="nav-right">
        <div className="status-pill" title="Connected to FastAPI Backend (127.0.0.1:8000)">
          <div className="status-dot"></div>
          <span>{health ? 'API Online' : 'Connecting...'}</span>
        </div>

        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button 
              className="btn btn-primary btn-sm"
              onClick={onNewApp}
            >
              <PlusCircle size={15} />
              <span>Apply</span>
            </button>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'rgba(255, 255, 255, 0.06)',
              borderRadius: '9999px',
              fontSize: '0.85rem'
            }}>
              <User size={15} color="#818cf8" />
              <span style={{ fontWeight: 600 }}>{user.name || user.email.split('@')[0]}</span>
            </div>
            <button 
              className="btn btn-secondary btn-sm" 
              onClick={onLogout}
              title="Logout"
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={onOpenAuth}>
            <User size={15} />
            <span>Sign In / Demo</span>
          </button>
        )}
      </div>
    </header>
  );
}
