import React, { useState, useEffect } from 'react';
import {
  FileText,
  Palette,
  Calendar,
  Download,
  RefreshCw,
  FileCheck,
  Briefcase,
  CreditCard,
  Clock,
  TrendingUp,
  AlertCircle,
  Check,
  CheckSquare
} from 'lucide-react';
import { api } from '../services/api';

export default function ReportsEngineView({ projects = [] }) {
  const [reportType, setReportType] = useState('todo');
  const [theme, setTheme] = useState('navy');
  const [selectedProjectIds, setSelectedProjectIds] = useState([]);
  const [sinceDate, setSinceDate] = useState('');
  const [customFilename, setCustomFilename] = useState('');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

  // Initialize selectedProjectIds to all projects on load or when projects change
  useEffect(() => {
    if (projects.length > 0 && selectedProjectIds.length === 0) {
      setSelectedProjectIds(projects.map(p => p.id));
    }
  }, [projects]);

  const reportTypes = [
    { id: 'notepad', name: 'Project Notepad', icon: FileText, desc: 'AI-formatted compilation of raw project notes and briefs.' },
    { id: 'todo', name: 'To-Do List', icon: CheckSquare, desc: 'Detailed task list backlog showing priorities, statuses, and hours.' },
    { id: 'payments', name: 'Payments Ledger', icon: CreditCard, desc: 'Full financial log of transaction records, amounts, and statuses.' }
  ];

  const themes = [
    { id: 'navy', color: '#1e3a8a', name: 'Classic Navy' },
    { id: 'teal', color: '#0d9488', name: 'Modern Teal' },
    { id: 'emerald', color: '#059669', name: 'Vibrant Emerald' },
    { id: 'charcoal', color: '#374151', name: 'Sleek Charcoal' },
    { id: 'ruby', color: '#be123c', name: 'Deep Ruby' },
    { id: 'dark', color: '#0f172a', name: 'Premium Dark' }
  ];

  const handleToggleProject = (id) => {
    setSelectedProjectIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(item => item !== id);
      } else {
        return [...prev, id];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedProjectIds.length === projects.length) {
      setSelectedProjectIds([]);
    } else {
      setSelectedProjectIds(projects.map(p => p.id));
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setPdfUrl(null);

    // Build command for AI router
    let projectTitle = '';
    if (selectedProjectIds.length > 0) {
      if (selectedProjectIds.length === projects.length) {
        projectTitle = 'for all projects';
      } else {
        const titles = projects
          .filter(p => selectedProjectIds.includes(p.id))
          .map(p => `"${p.title}"`)
          .join(', ');
        projectTitle = `for projects ${titles}`;
      }
    } else {
      projectTitle = 'for all projects';
    }

    let nameFilter = '';
    if (customFilename.trim()) {
      nameFilter = `named "${customFilename.trim()}"`;
    }

    const command = `generate ${reportType} report ${projectTitle} in ${theme} theme ${nameFilter}`.trim();

    try {
      const res = await api.ai.process(command);
      setResult(res.summary);

      // Extract PDF url from markdown "[Download Project Overview PDF](url)"
      const match = res.summary?.match(/\((https?:\/\/[^\/]+\/uploads\/.*?\.pdf)\)/);
      if (match && match[1]) {
        setPdfUrl(match[1]);
      }
    } catch (err) {
      setResult(`Failed to generate report: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="reports-view-container" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px', alignItems: 'stretch' }}>
        {/* Form Configurator */}
        <form className="glass-panel" onSubmit={handleGenerate} style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px', borderRadius: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 4px 0' }}>Configure Document</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>Select document parameters and compilation parameters</p>
          </div>

          {/* Report Type Grid */}
          <div className="form-group">
            <label className="form-label" style={{ marginBottom: '10px' }}>Report Type</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
              {reportTypes.map(t => {
                const IconComponent = t.icon;
                const isSelected = reportType === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setReportType(t.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '14px',
                      background: isSelected ? 'rgba(139, 92, 246, 0.08)' : 'rgba(255, 255, 255, 0.01)',
                      border: isSelected ? '1px solid var(--accent-primary)' : '1px solid rgba(255, 255, 255, 0.05)',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.25s ease',
                      boxShadow: isSelected ? '0 0 15px rgba(139, 92, 246, 0.15)' : 'none',
                    }}
                    className="report-type-card"
                  >
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '8px',
                      background: isSelected ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: isSelected ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      flexShrink: 0,
                      transition: 'all 0.25s'
                    }}>
                      <IconComponent size={16} />
                    </div>
                    <div>
                      <span style={{ fontSize: '0.88rem', fontWeight: 600, color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)', display: 'block' }}>{t.name}</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '2px', display: 'block', lineHeight: '1.3' }}>{t.desc}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
            {/* Project Context */}
            <div className="form-group" style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label" style={{ margin: 0 }}>Filter Projects</label>
                {projects.length > 0 && (
                  <button
                    type="button"
                    onClick={handleSelectAll}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-primary)',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      transition: 'background 0.2s',
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                  >
                    {selectedProjectIds.length === projects.length ? 'Deselect All' : 'Select All'}
                  </button>
                )}
              </div>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                padding: '4px 0',
              }}>
                {projects.length === 0 ? (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>No projects available</span>
                ) : (
                  projects.map(p => {
                    const isChecked = selectedProjectIds.includes(p.id);
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => handleToggleProject(p.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 14px',
                          borderRadius: '20px',
                          fontSize: '0.8rem',
                          fontWeight: 500,
                          cursor: 'pointer',
                          background: isChecked 
                            ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%)' 
                            : 'rgba(255, 255, 255, 0.02)',
                          border: isChecked 
                            ? '1px solid rgba(139, 92, 246, 0.5)' 
                            : '1px solid rgba(255, 255, 255, 0.08)',
                          color: isChecked ? '#fff' : 'var(--text-secondary)',
                          boxShadow: isChecked ? '0 0 10px rgba(139, 92, 246, 0.1)' : 'none',
                          transition: 'all 0.2s ease',
                          userSelect: 'none',
                        }}
                        onMouseEnter={e => {
                          if (!isChecked) {
                            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                          }
                        }}
                        onMouseLeave={e => {
                          if (!isChecked) {
                            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                          }
                        }}
                      >
                        <div style={{
                          width: '14px',
                          height: '14px',
                          borderRadius: '50%',
                          border: isChecked ? 'none' : '1px solid rgba(255, 255, 255, 0.3)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: isChecked ? 'var(--accent-primary)' : 'transparent',
                          color: '#fff',
                          flexShrink: 0,
                          transition: 'all 0.2s'
                        }}>
                          {isChecked && <Check size={8} strokeWidth={4} />}
                        </div>
                        {p.title}
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            {/* Theme Palette */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Styling Theme</label>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', height: '42px' }}>
                {themes.map(t => {
                  const isSelected = theme === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTheme(t.id)}
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        background: t.color,
                        border: isSelected ? '2px solid #fff' : '2px solid rgba(255,255,255,0.1)',
                        cursor: 'pointer',
                        boxShadow: isSelected ? `0 0 12px ${t.color}` : 'none',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        padding: 0
                      }}
                      title={t.name}
                    >
                      {isSelected && <Check size={12} strokeWidth={3} />}
                    </button>
                  );
                })}
            </div>
          </div>
        </div>

        <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Custom File Name (Optional)</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Q2_Client_Brief"
              value={customFilename}
              onChange={(e) => setCustomFilename(e.target.value)}
              style={{ width: '100%', boxSizing: 'border-box' }}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{
              padding: '14px',
              fontSize: '0.95rem',
              marginTop: '10px',
              justifyContent: 'center',
              boxShadow: (loading || selectedProjectIds.length === 0) ? 'none' : '0 8px 24px rgba(139, 92, 246, 0.25)',
              opacity: (loading || selectedProjectIds.length === 0) ? 0.5 : 1,
              cursor: (loading || selectedProjectIds.length === 0) ? 'not-allowed' : 'pointer'
            }}
            disabled={loading || selectedProjectIds.length === 0}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <RefreshCw className="spin" size={18} /> Compiling PDF Engine...
              </span>
            ) : (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={18} /> Compile PDF Document
              </span>
            )}
          </button>
        </form>

        {/* Live Compilation Outcome */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', flexGrow: 1, minHeight: '400px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            {loading ? (
              <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px', padding: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                  <div className="skeleton-pulse" style={{ width: '160px', height: '22px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse" style={{ width: '50px', height: '14px', borderRadius: '4px' }} />
                </div>
                <div className="skeleton-pulse" style={{ width: '100%', height: '100px', borderRadius: '12px' }} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div className="skeleton-pulse" style={{ width: '92%', height: '14px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse" style={{ width: '96%', height: '14px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse" style={{ width: '60%', height: '14px', borderRadius: '4px' }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', width: '100%', marginTop: '16px' }}>
                  <div className="skeleton-pulse" style={{ width: '160px', height: '40px', borderRadius: '20px' }} />
                </div>
              </div>
            ) : pdfUrl ? (
              <div style={{ textAlign: 'center', width: '100%', padding: '20px 0' }}>
                <div style={{
                  width: '72px',
                  height: '72px',
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px auto',
                  color: '#34d399',
                  boxShadow: '0 0 25px rgba(16, 185, 129, 0.15)'
                }}>
                  <FileCheck size={36} />
                </div>
                <h4 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>PDF Document Compiled</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '28px', maxWidth: '320px', margin: '0 auto 28px auto', lineHeight: '1.5' }}>
                  The PDF report has been generated successfully with the configuration specified.
                </p>
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '12px 28px',
                    textDecoration: 'none',
                    fontWeight: 600,
                    boxShadow: '0 8px 24px rgba(16, 185, 129, 0.25)',
                    background: '#10b981',
                    borderColor: '#10b981'
                  }}
                >
                  <Download size={16} /> Download PDF
                </a>
              </div>
            ) : result ? (
              <div style={{ width: '100%', display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' }}>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Response Log</h4>
                <div style={{
                  background: 'rgba(10, 6, 22, 0.4)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  padding: '16px',
                  borderRadius: '12px',
                  fontSize: '0.82rem',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'SFMono-Regular, Consolas, Monaco, monospace',
                  overflowY: 'auto',
                  maxHeight: '320px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.5'
                }}>
                  {result}
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '40px 0' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px auto',
                  color: 'var(--text-secondary)'
                }}>
                  <FileText size={28} style={{ opacity: 0.4 }} />
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>No Document Active</h4>
                <p style={{ fontSize: '0.8rem', maxWidth: '280px', margin: '0 auto', lineHeight: '1.5' }}>
                  Select report configurations on the left and click Compile to construct your document.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
