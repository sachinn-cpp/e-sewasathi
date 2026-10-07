import React, { useState } from 'react';
import { X, LogIn, UserPlus, Zap, AlertCircle } from 'lucide-react';
import { api } from '../api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form states
  const [email, setEmail] = useState('citizen.demo@example.com');
  const [password, setPassword] = useState('Password123!');
  const [confirmPassword, setConfirmPassword] = useState('Password123!');
  const [name, setName] = useState('Aarav Sharma');
  const [phone, setPhone] = useState('+9779812345678');
  const [language, setLanguage] = useState('en');

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await api.login(email, password);
      } else {
        await api.register({
          name,
          email,
          phone,
          password,
          confirm_password: confirmPassword,
          preferred_language: language,
        });
        // Auto-login after registration
        await api.login(email, password);
      }
      onAuthSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickDemo() {
    setError('');
    setLoading(true);
    const demoEmail = 'citizen.demo@example.com';
    const demoPass = 'Password123!';

    try {
      // First try to login with demo credentials
      await api.login(demoEmail, demoPass);
      onAuthSuccess();
      onClose();
    } catch {
      // If not yet registered, register demo citizen first
      try {
        await api.register({
          name: 'Aarav Sharma',
          email: demoEmail,
          phone: '+9779812345678',
          password: demoPass,
          confirm_password: demoPass,
          preferred_language: 'en',
        });
        await api.login(demoEmail, demoPass);
        onAuthSuccess();
        onClose();
      } catch (regErr) {
        setError(regErr.message || 'Quick demo setup failed.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '440px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'rgba(99, 102, 241, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8'
            }}>
              {isLogin ? <LogIn size={18} /> : <UserPlus size={18} />}
            </div>
            <h2 className="modal-title">{isLogin ? 'Sign In to e-SewaSathi' : 'Citizen Registration'}</h2>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px',
            borderRadius: '10px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.85rem',
            marginBottom: '20px'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Quick Demo Button */}
        <button
          type="button"
          onClick={handleQuickDemo}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            color: '#ffffff',
            fontWeight: 600,
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            cursor: 'pointer',
            marginBottom: '24px'
          }}
        >
          <Zap size={16} color="#34d399" />
          <span>One-Click Quick Demo Login</span>
        </button>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '20px',
          color: 'var(--text-dim)',
          fontSize: '0.8rem'
        }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }}></div>
          <span>OR ENTER CREDENTIALS</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }}></div>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Aarav Sharma"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone Number</label>
                <input
                  type="tel"
                  required
                  className="form-control"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+9779812345678"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Preferred Language</label>
                <select
                  className="form-control"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="ne">Nepali (नेपाली)</option>
                  <option value="hi">Hindi (हिन्दी)</option>
                </select>
              </div>
            </>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              required
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="citizen@example.com"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              required
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                required
                className="form-control"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {isLogin ? (
            <>
              Don't have an account?{' '}
              <span
                style={{ color: '#818cf8', fontWeight: 600, cursor: 'pointer' }}
                onClick={() => { setIsLogin(false); setError(''); }}
              >
                Register here
              </span>
            </>
          ) : (
            <>
              Already registered?{' '}
              <span
                style={{ color: '#818cf8', fontWeight: 600, cursor: 'pointer' }}
                onClick={() => { setIsLogin(true); setError(''); }}
              >
                Sign In
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
