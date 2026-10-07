import React, { useState } from 'react';
import { X, CheckCircle, ChevronRight, ChevronLeft, Award, FileText } from 'lucide-react';
import { api } from '../api';

export default function NewApplicationModal({ isOpen, onClose, onCreated }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    full_name: 'Aarav Sharma',
    date_of_birth: '1995-04-12',
    citizenship_number: '27-01-72-10842',
    address: 'Baneshwor, Ward No. 10',
    district: 'Kathmandu',
    municipality: 'Kathmandu Metropolitan',
    ward_no: '10',
    employment_status: 'Employed (Private Sector)',
    annual_income: '450000 NPR',
    purpose: 'Higher Education Scholarship & Bank Verification',
    preferred_language: 'en',
  });

  if (!isOpen) return null;

  function updateField(key, val) {
    setFormData((prev) => ({ ...prev, [key]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const app = await api.createApplication({
        service_type: 'income_certificate',
        form_data: formData,
        preferred_language: formData.preferred_language,
      });
      onCreated(app);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to submit application.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '680px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(16, 185, 129, 0.3) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff'
            }}>
              <Award size={22} />
            </div>
            <div>
              <h2 className="modal-title">New Service Application</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Government Income Certificate (आय प्रमाण-पत्र)
              </p>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Step indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px' }}>
          {[
            { num: 1, label: 'Personal' },
            { num: 2, label: 'Address' },
            { num: 3, label: 'Income & Purpose' },
          ].map((s) => (
            <div
              key={s.num}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '10px',
                background: step === s.num ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                border: step === s.num ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid var(--border-light)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.8rem',
                color: step === s.num ? '#ffffff' : 'var(--text-muted)',
                fontWeight: step === s.num ? 700 : 500,
              }}
            >
              <span style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: step === s.num ? '#6366f1' : 'rgba(255, 255, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                color: '#ffffff',
              }}>
                {s.num}
              </span>
              <span>{s.label}</span>
            </div>
          ))}
        </div>

        {error && (
          <div style={{
            padding: '12px',
            borderRadius: '10px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.85rem',
            marginBottom: '20px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <div style={{ animation: 'fadeIn 0.2s ease-out' }}>
              <div className="form-group">
                <label className="form-label">Full Name (As in Official ID)</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  value={formData.full_name}
                  onChange={(e) => updateField('full_name', e.target.value)}
                  placeholder="e.g. Aarav Sharma"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Date of Birth</label>
                  <input
                    type="date"
                    required
                    className="form-control"
                    value={formData.date_of_birth}
                    onChange={(e) => updateField('date_of_birth', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Citizenship / National ID No.</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={formData.citizenship_number}
                    onChange={(e) => updateField('citizenship_number', e.target.value)}
                    placeholder="27-01-72-10842"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Preferred Application Language</label>
                <select
                  className="form-control"
                  value={formData.preferred_language}
                  onChange={(e) => updateField('preferred_language', e.target.value)}
                >
                  <option value="en">English (Official Certificate)</option>
                  <option value="ne">Nepali (नेपाली)</option>
                  <option value="hi">Hindi (हिन्दी)</option>
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ animation: 'fadeIn 0.2s ease-out' }}>
              <div className="form-group">
                <label className="form-label">Permanent Residential Address</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  value={formData.address}
                  onChange={(e) => updateField('address', e.target.value)}
                  placeholder="Street / Tole / Landmark"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">District</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={formData.district}
                    onChange={(e) => updateField('district', e.target.value)}
                    placeholder="Kathmandu"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Municipality / Rural Municipality</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={formData.municipality}
                    onChange={(e) => updateField('municipality', e.target.value)}
                    placeholder="Kathmandu Metropolitan"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Ward No.</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={formData.ward_no}
                    onChange={(e) => updateField('ward_no', e.target.value)}
                    placeholder="10"
                  />
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div style={{ animation: 'fadeIn 0.2s ease-out' }}>
              <div className="form-group">
                <label className="form-label">Employment Status</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  value={formData.employment_status}
                  onChange={(e) => updateField('employment_status', e.target.value)}
                  placeholder="Employed / Business / Self-Employed"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Total Annual Household Income</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  value={formData.annual_income}
                  onChange={(e) => updateField('annual_income', e.target.value)}
                  placeholder="e.g. 450,000 NPR"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Purpose of Certificate</label>
                <textarea
                  rows={3}
                  required
                  className="form-control"
                  value={formData.purpose}
                  onChange={(e) => updateField('purpose', e.target.value)}
                  placeholder="e.g. Higher education scholarship, university admissions, or bank loan application"
                />
              </div>

              <div style={{
                padding: '14px',
                borderRadius: '12px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                fontSize: '0.85rem',
                color: 'var(--text-muted)'
              }}>
                <FileText size={20} color="#818cf8" style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>
                  After generating this draft, you can attach your verification documents (Identity proof, address proof, etc.) in the next step.
                </span>
              </div>
            </div>
          )}

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '28px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border-light)'
          }}>
            {step > 1 ? (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setStep((s) => s - 1)}
              >
                <ChevronLeft size={16} /> Back
              </button>
            ) : <div></div>}

            {step < 3 ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setStep((s) => s + 1)}
              >
                Next Step <ChevronRight size={16} />
              </button>
            ) : (
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Submitting to Portal...' : (
                  <>
                    <CheckCircle size={16} /> Create Application
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
