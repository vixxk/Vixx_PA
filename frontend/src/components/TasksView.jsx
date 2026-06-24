import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Check, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function TasksView({ todos = [], projects = [], onRefresh }) {
  const [localTodos, setLocalTodos] = useState(todos);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [projectId, setProjectId] = useState(projects[0]?.id || '');
  const [estimatedHours, setEstimatedHours] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLocalTodos(todos);
  }, [todos]);

  useEffect(() => {
    if (projects.length > 0 && !projectId) {
      setProjectId(projects[0].id);
    }
  }, [projects]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !projectId) return;

    setLoading(true);
    setError('');

    const originalTodos = [...localTodos];
    const tempId = 'temp-' + Date.now();
    const tempTodo = {
      id: tempId,
      project_id: projectId,
      title: title.trim(),
      description: description.trim(),
      priority,
      status: 'todo',
      estimated_hours: estimatedHours ? parseFloat(estimatedHours) : null,
      created_at: new Date().toISOString()
    };

    setLocalTodos(prev => [...prev, tempTodo]);
    setTitle('');
    setDescription('');
    setEstimatedHours('');
    setShowForm(false);

    try {
      await api.todos.create({
        project_id: tempTodo.project_id,
        title: tempTodo.title,
        description: tempTodo.description,
        priority: tempTodo.priority,
        status: 'todo',
        estimated_hours: tempTodo.estimated_hours
      });
      onRefresh();
    } catch (err) {
      setLocalTodos(originalTodos);
      setError(err.message || 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (todo, newStatus) => {
    const originalTodos = [...localTodos];
    setLocalTodos(prev => prev.map(t => t.id === todo.id ? { ...t, status: newStatus } : t));
    try {
      await api.todos.update(todo.id, { status: newStatus });
      onRefresh();
    } catch (err) {
      setLocalTodos(originalTodos);
      alert('Failed to update status: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    window.showConfirm('Are you sure you want to delete this task?', async () => {
      const originalTodos = [...localTodos];
      setLocalTodos(prev => prev.filter(t => t.id !== id));
      try {
        await api.todos.delete(id);
        onRefresh();
      } catch (err) {
        setLocalTodos(originalTodos);
        alert('Failed to delete task: ' + err.message);
      }
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar">
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Engineering Tasks</h2>
        {projects.length > 0 && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> New Task
          </button>
        )}
      </div>

      {showForm && (
        <form className="glass-panel" onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Create New Task</h3>
          
          {error && (
            <div style={{ color: '#f87171', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Associate Project</label>
            <select className="input-field" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
              <option value="">Select a project...</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Task Title</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Build backend API endpoints"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="input-field"
              placeholder="Describe requirements..."
              style={{ minHeight: '80px', fontFamily: 'inherit' }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Priority</label>
              <select className="input-field" value={priority} onChange={(e) => setPriority(e.target.value)}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Estimated Hours</label>
              <input
                type="number"
                step="0.5"
                className="input-field"
                placeholder="e.g. 4.5"
                value={estimatedHours}
                onChange={(e) => setEstimatedHours(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      )}

      <div className="list-container">
        {localTodos.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No tasks found. Use the AI command panel or add a task manually.
          </div>
        ) : (
          localTodos.map((todo) => {
            const project = projects.find(p => p.id === todo.project_id);
            return (
              <div key={todo.id} className="glass-panel list-item">
                <div>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '4px', textDecoration: todo.status === 'done' ? 'line-through' : 'none', color: todo.status === 'done' ? 'var(--text-muted)' : 'inherit' }}>
                    {todo.title}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>{todo.description || 'No description.'}</p>
                  <div className="item-meta">
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                      {project?.title || 'Unknown Project'}
                    </span>
                    <span className={`badge badge-${todo.priority}`}>{todo.priority}</span>
                    {todo.estimated_hours && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Est: {todo.estimated_hours}h
                      </span>
                    )}
                    {todo.status !== 'done' ? (
                      <button className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: '0.7rem' }} onClick={() => handleStatusChange(todo, 'done')}>
                        Complete
                      </button>
                    ) : (
                      <span className="badge badge-completed" style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                        <Check size={10} /> Done
                      </span>
                    )}
                  </div>
                </div>
                <button className="btn btn-secondary" style={{ padding: '8px', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.2)' }} onClick={() => handleDelete(todo.id)}>
                  <Trash2 size={16} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
