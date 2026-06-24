import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Mail, Phone, Briefcase, Award, AlertCircle, Edit, Save, X } from 'lucide-react';
import { api } from '../services/api';

export default function ClientsView() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  // Form State
  const [name, setName] = useState('');
  const [company, setCompany] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [priorityScore, setPriorityScore] = useState(70);
  const [error, setError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  // Edit State
  const [editName, setEditName] = useState('');
  const [editCompany, setEditCompany] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editPhone, setEditPhone] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [editScore, setEditScore] = useState(70);

  const fetchClients = async () => {
    setLoading(true);
    try {
      const data = await api.clients.list();
      setClients(data || []);
    } catch (err) {
      console.error("Failed to fetch clients:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setFormLoading(true);
    setError('');

    try {
      await api.clients.create({
        name: name.trim(),
        company: company.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
        notes: notes.trim() || null,
        priority_score: parseInt(priorityScore)
      });

      // Clear Form
      setName('');
      setCompany('');
      setEmail('');
      setPhone('');
      setNotes('');
      setPriorityScore(70);
      setShowForm(false);
      
      fetchClients();
    } catch (err) {
      setError(err.message || "Failed to add client profile");
    } finally {
      setFormLoading(false);
    }
  };

  const handleStartEdit = (client) => {
    setEditingId(client.id);
    setEditName(client.name);
    setEditCompany(client.company || '');
    setEditEmail(client.email || '');
    setEditPhone(client.phone || '');
    setEditNotes(client.notes || '');
    setEditScore(client.priority_score || 70);
  };

  const handleSaveEdit = async (id) => {
    try {
      await api.clients.update(id, {
        name: editName.trim(),
        company: editCompany.trim() || null,
        email: editEmail.trim() || null,
        phone: editPhone.trim() || null,
        notes: editNotes.trim() || null,
        priority_score: parseInt(editScore)
      });
      setEditingId(null);
      fetchClients();
    } catch (err) {
      alert("Failed to update client: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    window.showConfirm("Are you sure you want to delete this client? All associations will be set to null.", async () => {
      const originalClients = [...clients];
      setClients(prev => prev.filter(c => c.id !== id));
      try {
        await api.clients.delete(id);
      } catch (err) {
        setClients(originalClients);
        alert("Failed to delete client: " + err.message);
      }
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar">
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Clients Directory</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Store client profiles, manage communication details, and prioritize client accounts.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> Add Client
        </button>
      </div>

      {/* New Client Form */}
      {showForm && (
        <form className="glass-panel" onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>New Client Profile</h3>
          
          {error && <p style={{ color: '#f87171', fontSize: '0.85rem' }}>{error}</p>}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Client Name</label>
              <input type="text" className="input-field" placeholder="e.g. Jane Doe" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>

            <div className="form-group">
              <label className="form-label">Company Name</label>
              <input type="text" className="input-field" placeholder="e.g. Acme Corporation" value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input type="email" className="input-field" placeholder="jane@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input type="text" className="input-field" placeholder="+1-555-0199" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Client Priority Score</span>
              <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>{priorityScore}/100</span>
            </label>
            <input type="range" min="0" max="100" className="input-field" style={{ padding: 0, height: '6px', cursor: 'pointer' }} value={priorityScore} onChange={(e) => setPriorityScore(e.target.value)} />
          </div>

          <div className="form-group">
            <label className="form-label">Client Notes</label>
            <textarea className="input-field" style={{ minHeight: '60px', fontFamily: 'inherit' }} placeholder="Rates, requirements, or communication preferences..." value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? 'Adding...' : 'Save Client'}
            </button>
          </div>
        </form>
      )}

      {/* Clients list */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
        {loading ? (
          [1, 2, 3].map(i => (
            <div key={i} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '70%' }}>
                  <div className="skeleton-pulse" style={{ width: '80%', height: '16px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse" style={{ width: '50%', height: '12px', borderRadius: '4px' }} />
                </div>
                <div className="skeleton-pulse" style={{ width: '40px', height: '14px', borderRadius: '4px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', margin: '4px 0' }}>
                <div className="skeleton-pulse" style={{ width: '60%', height: '12px', borderRadius: '4px' }} />
                <div className="skeleton-pulse" style={{ width: '40%', height: '12px', borderRadius: '4px' }} />
              </div>
              <div className="skeleton-pulse" style={{ width: '100%', height: '40px', borderRadius: '6px' }} />
            </div>
          ))
        ) : clients.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', gridColumn: '1 / -1', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No clients registered yet. Keep details clean by creating client records.
          </div>
        ) : (
          clients.map(c => (
            <div key={c.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px', position: 'relative' }}>
              {editingId === c.id ? (
                // Editing mode
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <input type="text" className="input-field" value={editName} onChange={(e) => setEditName(e.target.value)} placeholder="Name" />
                  <input type="text" className="input-field" value={editCompany} onChange={(e) => setEditCompany(e.target.value)} placeholder="Company" />
                  <input type="email" className="input-field" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} placeholder="Email" />
                  <input type="text" className="input-field" value={editPhone} onChange={(e) => setEditPhone(e.target.value)} placeholder="Phone" />
                  
                  <div className="form-group">
                    <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span>Priority Score:</span>
                      <span>{editScore}/100</span>
                    </label>
                    <input type="range" min="0" max="100" value={editScore} onChange={(e) => setEditScore(e.target.value)} />
                  </div>

                  <textarea className="input-field" style={{ minHeight: '50px', fontSize: '0.8rem' }} value={editNotes} onChange={(e) => setEditNotes(e.target.value)} placeholder="Notes" />
                  
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '6px' }}>
                    <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={() => setEditingId(null)}><X size={12} /> Cancel</button>
                    <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={() => handleSaveEdit(c.id)}><Save size={12} /> Save</button>
                  </div>
                </div>
              ) : (
                // Standard mode
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>{c.name}</h3>
                      {c.company && <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '2px 0 0 0', display: 'flex', alignItems: 'center', gap: '4px' }}><Briefcase size={12} /> {c.company}</p>}
                    </div>
                    
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn" style={{ padding: '4px', background: 'transparent', color: 'var(--text-secondary)' }} onClick={() => handleStartEdit(c)}>
                        <Edit size={14} />
                      </button>
                      <button className="btn" style={{ padding: '4px', background: 'transparent', color: '#f87171' }} onClick={() => handleDelete(c.id)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '4px 0' }}>
                    {c.email && <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Mail size={12} /> {c.email}</span>}
                    {c.phone && <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Phone size={12} /> {c.phone}</span>}
                  </div>

                  {c.notes && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', padding: '8px 10px', borderRadius: '6px', margin: 0 }}>
                      {c.notes}
                    </p>
                  )}

                  <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Award size={12} color="var(--accent-primary)" /> Priority Score
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{c.priority_score}/100</span>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
