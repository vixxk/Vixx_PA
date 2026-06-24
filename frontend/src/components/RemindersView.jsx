import React, { useState, useEffect } from 'react';
import { Bell, Plus, Trash2, Clock, Calendar, MessageSquare, Mail, X, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../services/api';

export default function RemindersView({ onRefresh }) {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [remindDate, setRemindDate] = useState('');
  const [remindTime, setRemindTime] = useState('');
  const [channel, setChannel] = useState('whatsapp');
  const [formLoading, setFormLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchReminders = async () => {
    setLoading(true);
    try {
      const list = await api.reminders.list();
      setReminders(list);
    } catch (err) {
      console.error('Failed to load reminders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !remindDate || !remindTime) return;
    setFormLoading(true);
    setError('');

    const originalReminders = [...reminders];
    const localDateTimeStr = `${remindDate}T${remindTime}`;
    const remindAtISO = new Date(localDateTimeStr).toISOString();

    const tempReminder = {
      id: 'temp-' + Date.now(),
      title: title.trim(),
      description: description.trim() || null,
      remind_at: remindAtISO,
      channel,
      status: 'pending'
    };

    setReminders(prev => [...prev, tempReminder]);
    setTitle('');
    setDescription('');
    setRemindDate('');
    setRemindTime('');
    setChannel('whatsapp');
    setShowForm(false);

    try {
      await api.reminders.create({
        title: tempReminder.title,
        description: tempReminder.description,
        remind_at: tempReminder.remind_at,
        channel: tempReminder.channel
      });
      fetchReminders();
      if (onRefresh) onRefresh();
    } catch (err) {
      setReminders(originalReminders);
      setError(err.message || 'Failed to create reminder');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (id) => {
    window.showConfirm("Are you sure you want to delete this reminder?", async () => {
      const originalReminders = [...reminders];
      setReminders(prev => prev.filter(r => r.id !== id));
      try {
        await api.reminders.delete(id);
        fetchReminders();
        if (onRefresh) onRefresh();
      } catch (err) {
        setReminders(originalReminders);
        alert('Failed to delete reminder: ' + err.message);
      }
    });
  };

  const handleClearAll = async () => {
    window.showConfirm('Cancel all active reminders?', async () => {
      const originalReminders = [...reminders];
      setReminders(prev => prev.filter(r => r.status !== 'pending'));
      try {
        await api.reminders.clear();
        fetchReminders();
        if (onRefresh) onRefresh();
      } catch (err) {
        setReminders(originalReminders);
        alert('Failed to clear reminders: ' + err.message);
      }
    });
  };

  const getChannelIcon = (ch) => {
    if (ch === 'whatsapp') return <MessageSquare size={14} style={{ color: '#25D366' }} />;
    if (ch === 'email') return <Mail size={14} style={{ color: '#60a5fa' }} />;
    return <><MessageSquare size={14} style={{ color: '#25D366' }} /><Mail size={14} style={{ color: '#60a5fa' }} /></>;
  };

  const getStatusBadge = (status) => {
    if (status === 'sent') return <span className="badge" style={{ background: 'rgba(16,185,129,0.15)', color: '#34d399', fontSize: '0.68rem' }}><CheckCircle2 size={10} /> Sent</span>;
    if (status === 'failed') return <span className="badge" style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171', fontSize: '0.68rem' }}><XCircle size={10} /> Failed</span>;
    if (status === 'cancelled') return <span className="badge" style={{ background: 'rgba(156,163,175,0.15)', color: '#9ca3af', fontSize: '0.68rem' }}><X size={10} /> Cancelled</span>;
    return <span className="badge" style={{ background: 'rgba(251,191,36,0.15)', color: '#fbbf24', fontSize: '0.68rem' }}><Clock size={10} /> Pending</span>;
  };

  const pending = reminders.filter(r => r.status === 'pending');
  const past = reminders.filter(r => r.status !== 'pending');

  const formatTime = (iso) => {
    if (!iso) return 'N/A';
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  };

  const isOverdue = (iso) => {
    if (!iso) return false;
    return new Date(iso) < new Date();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar">
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Reminders & Alerts</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Manage scheduled WhatsApp & email reminders. Vixx sends them automatically.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {pending.length > 0 && (
            <button className="btn btn-secondary" onClick={handleClearAll} style={{ fontSize: '0.78rem', padding: '8px 14px' }}>
              Cancel All
            </button>
          )}
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Plus size={16} /> New Reminder
          </button>
        </div>
      </div>

      {/* Create Reminder Form */}
      {showForm && (
        <form className="glass-panel" onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bell size={18} style={{ color: 'var(--accent-primary)' }} /> Schedule a Reminder
          </h3>

          {error && (
            <div style={{ color: '#f87171', display: 'flex', gap: '8px', alignItems: 'center', fontSize: '0.85rem' }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">What to remind you about</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Review website launch, Pay server bills"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Extra details (optional)</label>
            <textarea
              className="input-field"
              placeholder="Any additional notes..."
              style={{ minHeight: '60px', fontFamily: 'inherit' }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">When to remind</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '12px' }}>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <Calendar 
                    size={16} 
                    style={{ 
                      position: 'absolute', 
                      left: '12px', 
                      color: 'var(--text-muted)', 
                      pointerEvents: 'none' 
                    }} 
                  />
                  <input
                    type="date"
                    className="input-field"
                    style={{ paddingLeft: '36px' }}
                    value={remindDate}
                    onChange={(e) => setRemindDate(e.target.value)}
                    required
                  />
                </div>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <Clock 
                    size={16} 
                    style={{ 
                      position: 'absolute', 
                      left: '12px', 
                      color: 'var(--text-muted)', 
                      pointerEvents: 'none' 
                    }} 
                  />
                  <input
                    type="time"
                    className="input-field"
                    style={{ paddingLeft: '36px' }}
                    value={remindTime}
                    onChange={(e) => setRemindTime(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Send via</label>
              <select className="input-field" value={channel} onChange={(e) => setChannel(e.target.value)}>
                <option value="whatsapp">📱 WhatsApp</option>
                <option value="email">📧 Email</option>
                <option value="both">📱📧 Both</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? 'Setting...' : 'Set Reminder'}
            </button>
          </div>
        </form>
      )}

      {/* Active Reminders */}
      {pending.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} style={{ color: '#fbbf24' }} /> Upcoming Reminders ({pending.length})
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {pending.map(r => {
              const isOvd = isOverdue(r.remind_at);
              const chanColor = r.channel === 'whatsapp' ? '#25D366' : r.channel === 'email' ? '#60a5fa' : 'var(--accent-primary)';
              const chanGrad = r.channel === 'whatsapp' 
                ? 'linear-gradient(135deg, rgba(37, 211, 102, 0.12) 0%, rgba(16, 185, 129, 0.12) 100%)' 
                : r.channel === 'email'
                ? 'linear-gradient(135deg, rgba(96, 165, 250, 0.12) 0%, rgba(59, 130, 246, 0.12) 100%)'
                : 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(236, 72, 153, 0.12) 100%)';
              const chanBorder = r.channel === 'whatsapp' 
                ? '1px solid rgba(37, 211, 102, 0.25)' 
                : r.channel === 'email'
                ? '1px solid rgba(96, 165, 250, 0.25)'
                : '1px solid rgba(139, 92, 246, 0.25)';

              return (
                <div
                  key={r.id}
                  className="glass-panel"
                  style={{
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    borderRadius: '14px',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    borderLeft: `4px solid ${isOvd ? '#f87171' : chanColor}`,
                    background: 'rgba(255, 255, 255, 0.01)',
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.2)',
                    transition: 'all 0.25s ease',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'none';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.01)';
                  }}
                >
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', minWidth: 0, flex: 1 }}>
                      <div style={{ 
                        width: '36px', 
                        height: '36px', 
                        borderRadius: '10px', 
                        background: chanGrad, 
                        border: chanBorder,
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        color: chanColor,
                        flexShrink: 0
                      }}>
                        {getChannelIcon(r.channel)}
                      </div>
                      <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.title}>
                        {r.title}
                      </h4>
                    </div>
                    <button
                      className="btn"
                      style={{ padding: '6px', background: 'transparent', color: 'rgba(248, 113, 113, 0.7)', border: 'none', cursor: 'pointer', transition: 'color 0.2s' }}
                      onClick={() => handleDelete(r.id)}
                      title="Cancel reminder"
                      onMouseEnter={(e) => e.currentTarget.style.color = '#f87171'}
                      onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(248, 113, 113, 0.7)'}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>

                  {r.description && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: '1.5', minHeight: '38px' }}>
                      {r.description}
                    </p>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginTop: 'auto', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.03)' }}>
                    <span style={{ 
                      fontSize: '0.75rem', 
                      color: isOvd ? '#f87171' : 'var(--text-primary)', 
                      background: isOvd ? 'rgba(248, 113, 113, 0.1)' : 'rgba(255,255,255,0.03)',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '5px', 
                      fontWeight: 600,
                      border: isOvd ? '1px solid rgba(248, 113, 113, 0.2)' : '1px solid rgba(255,255,255,0.05)'
                    }}>
                      <Clock size={12} /> {formatTime(r.remind_at)}
                    </span>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {getStatusBadge(r.status)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Past / Sent / Failed Reminders */}
      {past.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px', color: 'var(--text-secondary)' }}>
            Execution History ({past.length})
          </h3>
          <div className="glass-panel" style={{ padding: '0px', overflow: 'hidden', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '14px' }}>
            <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
              {past.map((r, idx) => (
                <div
                  key={r.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '14px 20px',
                    borderBottom: idx === past.length - 1 ? 'none' : '1px solid rgba(255, 255, 255, 0.04)',
                    background: 'rgba(255, 255, 255, 0.005)',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.005)'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: 1 }}>
                    <div style={{ 
                      width: '28px', 
                      height: '28px', 
                      borderRadius: '8px', 
                      background: 'rgba(255,255,255,0.03)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: 'var(--text-secondary)'
                    }}>
                      {getChannelIcon(r.channel)}
                    </div>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.title}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexShrink: 0 }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{formatTime(r.remind_at)}</span>
                    {getStatusBadge(r.status)}
                    <button
                      className="btn"
                      style={{ padding: '6px', background: 'transparent', color: 'rgba(255,255,255,0.2)', border: 'none', cursor: 'pointer', transition: 'color 0.2s' }}
                      onClick={() => handleDelete(r.id)}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#f87171'}
                      onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.2)'}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && reminders.length === 0 && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <Bell size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '8px' }}>No reminders yet</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '400px', margin: '0 auto' }}>
            Schedule reminders and Vixx will send you WhatsApp or email notifications at the right time.
          </p>
          <button className="btn btn-primary" onClick={() => setShowForm(true)} style={{ marginTop: '20px' }}>
            <Plus size={16} /> Create Your First Reminder
          </button>
        </div>
      )}

      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="skeleton-pulse skeleton-title" style={{ width: '180px', height: '18px' }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="skeleton-pulse skeleton-title" style={{ width: '60%', height: '16px', margin: 0 }} />
                  <div className="skeleton-pulse skeleton-button" style={{ width: '24px', height: '24px', borderRadius: '4px' }} />
                </div>
                <div className="skeleton-pulse skeleton-text" style={{ width: '90%', height: '12px', margin: 0 }} />
                <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                  <div className="skeleton-pulse skeleton-button" style={{ width: '110px', height: '20px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse skeleton-button" style={{ width: '80px', height: '20px', borderRadius: '4px' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
