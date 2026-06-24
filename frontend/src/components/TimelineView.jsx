import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Trash2 } from 'lucide-react';
import { api } from '../services/api';

export default function TimelineView({ events = [], projects = [], onRefresh, loading = false }) {
  const [localEvents, setLocalEvents] = useState(events);

  useEffect(() => {
    setLocalEvents(events);
  }, [events]);

  const handleStatusChange = async (event, newStatus) => {
    const originalEvents = [...localEvents];
    setLocalEvents(prev => prev.map(e => e.id === event.id ? { ...e, status: newStatus } : e));
    try {
      await api.timeline.update(event.id, { status: newStatus });
      onRefresh();
    } catch (err) {
      setLocalEvents(originalEvents);
      alert('Failed to update event: ' + err.message);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const isPast = (dateStr) => {
    if (!dateStr) return false;
    return new Date(dateStr) < new Date();
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="card-title-bar">
          <div className="skeleton-pulse skeleton-title" style={{ width: '220px', height: '24px', margin: 0 }} />
        </div>
        <div className="glass-panel" style={{ padding: '32px' }}>
          <div className="timeline-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px' }}>
                <div style={{ width: '80%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div className="skeleton-pulse skeleton-text" style={{ width: '15%', height: '12px', margin: 0 }} />
                  <div className="skeleton-pulse skeleton-title" style={{ width: '50%', height: '18px', margin: 0 }} />
                  <div className="skeleton-pulse skeleton-text" style={{ width: '30%', height: '12px', margin: 0 }} />
                </div>
                <div className="skeleton-pulse skeleton-button" style={{ width: '80px', height: '32px', borderRadius: '6px' }} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar">
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Timeline & Milestones</h2>
      </div>

      <div className="glass-panel" style={{ padding: '32px' }}>
        {localEvents.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '48px 24px' }}>
            <Calendar size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '8px' }}>No timeline events</h3>
            <p style={{ fontSize: '0.85rem', maxWidth: '400px', margin: '0 auto' }}>
              Use the AI Command Panel to schedule project milestones and timeline events, or create them when setting up a new project.
            </p>
          </div>
        ) : (
          <div className="timeline-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {localEvents.map((event) => {
              const project = projects.find(p => p.id === event.project_id);
              const isCompleted = event.status === 'completed';
              const overdue = !isCompleted && isPast(event.event_date);

              return (
                <div 
                  key={event.id} 
                  className="glass-panel" 
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    padding: '16px 20px',
                    borderLeft: isCompleted ? '3px solid #34d399' : overdue ? '3px solid #f87171' : '3px solid var(--accent-primary)',
                    opacity: isCompleted ? 0.7 : 1,
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--accent-secondary)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>
                      {event.event_type}
                    </span>
                    <h3 style={{ 
                      fontSize: '1.05rem', 
                      margin: '4px 0', 
                      color: isCompleted ? 'var(--text-muted)' : 'inherit', 
                      textDecoration: isCompleted ? 'line-through' : 'none' 
                     }}>
                      {event.event_name}
                    </h3>
                    {event.notes && <p style={{ fontSize: '0.82rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>{event.notes}</p>}
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '4px' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                        {project?.title || 'Unknown Project'}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: overdue ? '#f87171' : 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: overdue ? 600 : 400 }}>
                        <Calendar size={11} /> {formatDate(event.event_date)}
                        {overdue && ' (overdue)'}
                      </span>
                    </div>
                  </div>

                  <div>
                    {isCompleted ? (
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', color: 'var(--text-secondary)', fontSize: '0.78rem' }}
                        onClick={() => handleStatusChange(event, 'pending')}
                      >
                        <CheckCircle2 size={14} style={{ color: '#34d399' }} /> Done
                      </button>
                    ) : (
                      <button
                        className="btn btn-primary"
                        style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                        onClick={() => handleStatusChange(event, 'completed')}
                      >
                        Mark Done
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
