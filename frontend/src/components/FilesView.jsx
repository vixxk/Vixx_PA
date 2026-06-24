import React, { useState, useEffect } from 'react';
import { Trash2, File, Upload, ExternalLink, Paperclip, FolderOpen, ChevronDown, ChevronRight, Plus, Check } from 'lucide-react';
import { api, getFileUrl } from '../services/api';

export default function FilesView({ projects = [], onRefresh }) {
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedProjects, setExpandedProjects] = useState({});
  
  // Form state
  const [projectId, setProjectId] = useState(projects[0]?.id || '');
  const [pendingTitle, setPendingTitle] = useState('');
  const [pendingDescription, setPendingDescription] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const fetchAttachments = async () => {
    setLoading(true);
    try {
      const list = await api.pendingThings.list();
      setAttachments(list);
    } catch (err) {
      console.error('Failed to load pending things:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttachments();
  }, []);

  useEffect(() => {
    if (projects.length > 0 && !projectId) {
      setProjectId(projects[0].id);
    }
    // Auto-expand projects
    const expanded = {};
    projects.forEach(p => {
      expanded[p.id] = true; // Default all expanded
    });
    setExpandedProjects(expanded);
  }, [projects]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!pendingTitle.trim() || !projectId) {
      alert('Please enter a title and select a project.');
      return;
    }

    setUploading(true);
    const originalAttachments = [...attachments];
    const tempPending = {
      id: 'temp-' + Date.now(),
      project_id: projectId,
      title: pendingTitle,
      description: pendingDescription,
      is_completed: false,
      filename: file ? file.name : null,
      file_url: null,
      created_at: new Date().toISOString()
    };

    setAttachments(prev => [...prev, tempPending]);
    
    // Cache current file reference and reset form
    const uploadFile = file;
    setPendingTitle('');
    setPendingDescription('');
    setFile(null);
    const fileInput = document.getElementById('files-view-input');
    if (fileInput) fileInput.value = '';

    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('title', tempPending.title);
    formData.append('description', tempPending.description);
    if (uploadFile) {
      formData.append('file', uploadFile);
    }

    try {
      await api.pendingThings.create(formData);
      fetchAttachments();
      if (onRefresh) onRefresh();
    } catch (err) {
      setAttachments(originalAttachments);
      alert('Failed to add pending thing: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleToggle = async (item) => {
    const originalAttachments = [...attachments];
    setAttachments(prev => prev.map(a => a.id === item.id ? { ...a, is_completed: !a.is_completed } : a));
    try {
      await api.pendingThings.update(item.id, { is_completed: !item.is_completed });
      fetchAttachments();
      if (onRefresh) onRefresh();
    } catch (err) {
      setAttachments(originalAttachments);
      alert('Failed to update pending item: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    window.showConfirm('Are you sure you want to delete this pending item?', async () => {
      const originalAttachments = [...attachments];
      setAttachments(prev => prev.filter(att => att.id !== id));
      try {
        await api.pendingThings.delete(id);
        fetchAttachments();
        if (onRefresh) onRefresh();
      } catch (err) {
        setAttachments(originalAttachments);
        alert('Failed to delete pending item: ' + err.message);
      }
    });
  };

  const toggleProject = (projId) => {
    setExpandedProjects(prev => ({ ...prev, [projId]: !prev[projId] }));
  };

  // Group pending things by project
  const itemsByProject = {};
  attachments.forEach(att => {
    if (!itemsByProject[att.project_id]) {
      itemsByProject[att.project_id] = [];
    }
    itemsByProject[att.project_id].push(att);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>Workspace Pending Things & Contracts</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Track API keys, client documents, credentials, or custom information needed for each project.</p>
      </div>

      {/* Creation Panel */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        {projects.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Create a project first to track pending items.</p>
        ) : (
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0 }}>Add a Pending Item / Credential</h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
              <div className="form-group">
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Project Folder</label>
                <select 
                  className="input-field" 
                  value={projectId} 
                  onChange={(e) => setProjectId(e.target.value)}
                  required
                >
                  {projects.map(proj => (
                    <option key={proj.id} value={proj.id}>{proj.title}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Title (e.g. Stripe API Keys) *</label>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="What is pending?"
                  value={pendingTitle}
                  onChange={(e) => setPendingTitle(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Description (optional)</label>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Add details..."
                  value={pendingDescription}
                  onChange={(e) => setPendingDescription(e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div className="form-group" style={{ flex: 1, minWidth: '240px' }}>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Attach File (optional)</label>
                <input 
                  type="file" 
                  id="files-view-input"
                  className="input-field" 
                  onChange={(e) => setFile(e.target.files[0])} 
                  style={{ padding: '6px' }}
                />
              </div>

              <button 
                type="submit" 
                className="btn btn-primary" 
                style={{ display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap', height: '40px' }}
                disabled={uploading}
              >
                <Plus size={16} /> {uploading ? 'Adding...' : 'Add Pending Item'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Project Folders */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[1, 2].map((i) => (
            <div key={i} className="skeleton-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="skeleton-pulse skeleton-button" style={{ width: '16px', height: '16px', borderRadius: '4px' }} />
              <div className="skeleton-pulse skeleton-avatar" style={{ width: '18px', height: '18px' }} />
              <div className="skeleton-pulse skeleton-title" style={{ width: '35%', height: '16px', margin: 0 }} />
              <div className="skeleton-pulse skeleton-button" style={{ width: '50px', height: '18px', borderRadius: '12px', marginLeft: 'auto' }} />
            </div>
          ))}
        </div>
      ) : projects.length === 0 ? null : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {projects.map(proj => {
            const projItems = itemsByProject[proj.id] || [];
            const isExpanded = expandedProjects[proj.id];
            
            return (
              <div key={proj.id} className="glass-panel" style={{ overflow: 'hidden' }}>
                {/* Folder Header */}
                <button
                  type="button"
                  onClick={() => toggleProject(proj.id)}
                  style={{
                    width: '100%',
                    padding: '16px 20px',
                    background: 'none',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    cursor: 'pointer',
                    color: 'var(--text-primary)',
                  }}
                >
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <FolderOpen size={18} style={{ color: '#fbbf24' }} />
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, flex: 1, textAlign: 'left' }}>{proj.title}</span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', background: 'var(--bg-tertiary)', padding: '2px 8px', borderRadius: '12px' }}>
                    {projItems.length} item{projItems.length !== 1 ? 's' : ''}
                  </span>
                </button>

                {/* Folder Contents */}
                {isExpanded && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', padding: '12px 20px' }}>
                    {projItems.length === 0 ? (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', padding: '8px 0', textAlign: 'center' }}>
                        No pending things in this project folder.
                      </p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {projItems.map(item => (
                          <div
                            key={item.id}
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              padding: '10px 12px',
                              background: item.is_completed ? 'rgba(255,255,255,0.01)' : 'rgba(255,255,255,0.02)',
                              borderRadius: '6px',
                              border: '1px solid rgba(255,255,255,0.04)',
                              opacity: item.is_completed ? 0.6 : 1,
                              transition: 'opacity 0.2s ease'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', minWidth: 0, flex: 1 }}>
                              <input 
                                type="checkbox"
                                checked={item.is_completed}
                                onChange={() => handleToggle(item)}
                                style={{ marginTop: '3px', cursor: 'pointer', accentColor: 'var(--accent-primary)' }}
                              />
                              <div style={{ minWidth: 0, flex: 1 }}>
                                <div style={{ 
                                  fontSize: '0.85rem', 
                                  fontWeight: 500, 
                                  textDecoration: item.is_completed ? 'line-through' : 'none',
                                  color: item.is_completed ? 'var(--text-muted)' : 'var(--text-primary)'
                                }}>
                                  {item.title}
                                </div>
                                {item.description && (
                                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                    {item.description}
                                  </div>
                                )}
                                {item.filename && item.file_url && (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                                    <File size={12} style={{ color: 'var(--accent-primary)' }} />
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                                      {item.filename}
                                    </span>
                                    <a 
                                      href={getFileUrl(item.file_url)} 
                                      target="_blank" 
                                      rel="noreferrer" 
                                      style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', textDecoration: 'underline' }}
                                    >
                                      Download
                                    </a>
                                  </div>
                                )}
                              </div>
                            </div>
                            <button 
                              className="btn" 
                              style={{ padding: '6px', background: 'transparent', color: '#f87171' }} 
                              onClick={() => handleDelete(item.id)}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* No projects empty state */}
      {!loading && projects.length === 0 && attachments.length === 0 && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <FolderOpen size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '8px' }}>No project folders yet</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Create a project first, then track credentials and pending client requirements.
          </p>
        </div>
      )}
    </div>
  );
}
