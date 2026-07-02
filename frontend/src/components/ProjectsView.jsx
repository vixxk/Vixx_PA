import React, { useState, useEffect } from 'react';
import { Plus, Trash2, ArrowRight, AlertCircle, Briefcase } from 'lucide-react';
import { api } from '../services/api';
import ProjectDetailWorkspace from './ProjectDetailWorkspace';

export default function ProjectsView({ 
  projects = [], 
  onRefresh, 
  loading = false,
  selectedProject,
  setSelectedProject
}) {
  const [localProjects, setLocalProjects] = useState(projects);
  
  useEffect(() => {
    setLocalProjects(projects);
  }, [projects]);

  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    setFormLoading(true);
    setError('');

    try {
      await api.projects.create({
        title,
        description,
        status: 'planning',
        total_amount: totalAmount ? parseFloat(totalAmount) : 0.0
      });
      setTitle('');
      setDescription('');
      setTotalAmount('');
      setShowForm(false);
      onRefresh();
    } catch (err) {
      setError(err.message || 'Failed to create project');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (id) => {
    window.showConfirm('Are you sure you want to delete this project?', async () => {
      // Optimistic UI Update: immediately hide the deleted project
      setLocalProjects(prev => prev.filter(p => p.id !== id));
      
      try {
        await api.projects.delete(id);
        if (selectedProject?.id === id) {
          setSelectedProject(null);
        }
        onRefresh();
      } catch (err) {
        // Rollback on failure
        setLocalProjects(projects);
        alert('Failed to delete project: ' + err.message);
      }
    });
  };

  if (selectedProject) {
    return (
      <ProjectDetailWorkspace 
        project={selectedProject} 
        onBack={() => setSelectedProject(null)} 
        onRefresh={onRefresh} 
      />
    );
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="card-title-bar" style={{ justifyContent: 'space-between' }}>
          <div className="skeleton-pulse skeleton-title" style={{ width: '220px', height: '24px', margin: 0 }} />
          <div className="skeleton-pulse skeleton-button" style={{ width: '130px', height: '38px', borderRadius: '8px' }} />
        </div>
        <div className="list-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ width: '80%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div className="skeleton-pulse skeleton-title" style={{ width: '40%', height: '18px', margin: 0 }} />
                <div className="skeleton-pulse skeleton-text" style={{ width: '90%', height: '12px', margin: 0 }} />
                <div className="skeleton-pulse skeleton-text" style={{ width: '30%', height: '12px', margin: 0 }} />
              </div>
              <div className="skeleton-pulse skeleton-button" style={{ width: '38px', height: '38px', borderRadius: '8px' }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="projects-view-container" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar" style={{ justifyContent: 'flex-end' }}>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> New Project
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <form className="glass-panel modal-card" onClick={e => e.stopPropagation()} onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#fff', marginBottom: '8px' }}>Create New Project</h3>
            
            {error && (
              <div style={{ color: '#f87171', display: 'flex', gap: '8px', alignItems: 'center', fontSize: '0.85rem' }}>
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Project Title</label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. Project Apollo"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea
                className="input-field"
                placeholder="Describe the scope..."
                style={{ minHeight: '80px', fontFamily: 'inherit' }}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Total Amount (INR)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="input-field"
                placeholder="e.g. 50000"
                value={totalAmount}
                onChange={(e) => setTotalAmount(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '12px' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '24px'
      }}>
        {localProjects.length === 0 ? (
          <div className="glass-panel" style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No projects found. Use the AI command panel or click "New Project" to start.
          </div>
        ) : (
          localProjects.map((proj) => (
            <div 
              key={proj.id} 
              className="glass-panel project-card-hover" 
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '24px',
                borderRadius: '16px',
                minHeight: '200px',
                cursor: 'pointer',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease',
                position: 'relative',
                overflow: 'hidden',
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'var(--glass-blur)'
              }}
              onClick={() => setSelectedProject(proj)}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 12px 30px rgba(0, 0, 0, 0.3), 0 0 1px 1px var(--accent-primary)';
                e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.borderColor = 'var(--glass-border)';
              }}
            >
              <div>
                {/* Header Row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '8px',
                    background: 'rgba(139, 92, 246, 0.15)',
                    border: '1px solid rgba(139, 92, 246, 0.25)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-primary)'
                  }}>
                    <Briefcase size={18} />
                  </div>
                  
                  {/* Status Badge */}
                  {(() => {
                    const status = (proj.status || 'planning').toLowerCase();
                    let color = '#60a5fa';
                    let bg = 'rgba(96, 165, 250, 0.15)';
                    let border = '1px solid rgba(96, 165, 250, 0.25)';
                    
                    if (status === 'developing') {
                      color = '#fbbf24';
                      bg = 'rgba(251, 191, 36, 0.15)';
                      border = '1px solid rgba(251, 191, 36, 0.25)';
                    } else if (status === 'finished' || status === 'completed') {
                      color = '#34d399';
                      bg = 'rgba(52, 211, 153, 0.15)';
                      border = '1px solid rgba(52, 211, 153, 0.25)';
                    }
                    return (
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        padding: '4px 10px',
                        borderRadius: '9999px',
                        background: bg,
                        color: color,
                        border: border
                      }}>
                        {status}
                      </span>
                    );
                  })()}
                </div>

                {/* Title */}
                <h3 style={{
                  fontSize: '1.25rem',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  {proj.title}
                </h3>

                {/* Description with Clamp */}
                <p style={{
                  fontSize: '0.88rem',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.45',
                  marginBottom: '20px',
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {proj.description || 'No description provided.'}
                </p>
              </div>

              {/* Card Footer */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                paddingTop: '14px',
                marginTop: 'auto'
              }}>
                {/* Value display */}
                {proj.total_amount !== undefined && proj.total_amount !== null ? (
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Value</span>
                    <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {Number(proj.total_amount).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}
                    </span>
                  </div>
                ) : (
                  <div />
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button 
                    className="btn btn-secondary"
                    style={{
                      padding: '8px',
                      color: 'var(--text-muted)',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '8px',
                      transition: 'all 0.2s'
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedProject(proj);
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = 'var(--text-primary)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = 'var(--text-muted)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                    }}
                    title="Open Workspace"
                  >
                    <ArrowRight size={15} />
                  </button>

                  <button 
                    className="btn btn-secondary" 
                    style={{
                      padding: '8px',
                      color: '#ef4444',
                      borderColor: 'rgba(239, 68, 68, 0.15)',
                      background: 'rgba(239, 68, 68, 0.02)',
                      borderRadius: '8px',
                      transition: 'all 0.2s'
                    }} 
                    onClick={(e) => { e.stopPropagation(); handleDelete(proj.id); }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                      e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(239, 68, 68, 0.02)';
                      e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.15)';
                    }}
                    title="Delete Project"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
