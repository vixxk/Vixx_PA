import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Layers, 
  ShieldAlert, 
  FileText, 
  RefreshCw, 
  ExternalLink,
  Calendar,
  CheckCircle,
  Plus,
  GitBranch,
  Table,
  CheckSquare,
  CreditCard,
  Trash2,
  Upload,
  Paperclip,
  File,
  Square,
  Check,
  Pencil,
  X
} from 'lucide-react';
import { api, getFileUrl } from '../services/api';

export default function ProjectDetailWorkspace({ project, onBack, onRefresh }) {
  const [activeSubTab, setActiveSubTab] = useState('contracts_payments'); // board, risks, summary, sync, contracts_payments
  const [notepadText, setNotepadText] = useState(project.notepad || '');
  const [saveStatus, setSaveStatus] = useState(''); // '', 'saving', 'saved', 'error'

  useEffect(() => {
    setNotepadText(project.notepad || '');
  }, [project]);

  const handleSaveNotepad = async () => {
    setSaveStatus('saving');
    try {
      await api.projects.update(project.id, { notepad: notepadText });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus(''), 3000);
      onRefresh();
    } catch (err) {
      console.error(err);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(''), 4000);
    }
  };

  const [isEditingHeader, setIsEditingHeader] = useState(false);
  const [editedTitle, setEditedTitle] = useState(project.title);
  const [editedDescription, setEditedDescription] = useState(project.description || '');
  const [editedStatus, setEditedStatus] = useState(project.status || 'planning');

  useEffect(() => {
    setEditedTitle(project.title);
    setEditedDescription(project.description || '');
    setEditedStatus(project.status || 'planning');
  }, [project]);

  const handleSaveHeader = async () => {
    if (!editedTitle.trim()) {
      alert('Project title cannot be empty.');
      return;
    }
    try {
      await api.projects.update(project.id, { 
        title: editedTitle.trim(), 
        description: editedDescription.trim(),
        status: editedStatus
      });
      setIsEditingHeader(false);
      onRefresh();
    } catch (err) {
      alert('Failed to update project: ' + err.message);
    }
  };
  const [tasks, setTasks] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [payments, setPayments] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Contracts & Payments form states
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentType, setPaymentType] = useState('Advance');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [clientName, setClientName] = useState('');
  const [contractFile, setContractFile] = useState(null);
  const [contractNotes, setContractNotes] = useState('');

  // Pending Things form states
  const [pendingTitle, setPendingTitle] = useState('');
  const [pendingDescription, setPendingDescription] = useState('');
  const [attachmentFile, setAttachmentFile] = useState(null);
  
  // Sync Forms State
  const [googleToken, setGoogleToken] = useState(localStorage.getItem('google_token') || '');
  const [githubToken, setGithubToken] = useState(localStorage.getItem('github_token') || '');
  const [githubRepo, setGithubRepo] = useState(localStorage.getItem('github_repo') || '');
  const [syncStatus, setSyncStatus] = useState('');
  const [syncError, setSyncError] = useState('');

  // To-Do form states
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskPriority, setTaskPriority] = useState('medium');
  const [taskEstHours, setTaskEstHours] = useState('');
  const [todoFilter, setTodoFilter] = useState('all'); // all, pending, completed

  // Fetch project tasks, milestones, payments, contracts, and attachments
  const fetchProjectDetails = async () => {
    setLoading(true);
    try {
      const [todosList, timelineList, paymentsList, contractsList, pendingList] = await Promise.all([
        api.todos.list(project.id),
        api.timeline.list(project.id),
        api.payments.list(),
        api.contracts.list(),
        api.pendingThings.list()
      ]);
      setTasks(todosList);
      setMilestones(timelineList);
      setPayments(paymentsList.filter(p => p.project_id === project.id));
      setContracts(contractsList.filter(c => c.project_id === project.id));
      setAttachments(pendingList.filter(a => a.project_id === project.id));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectDetails();
  }, [project.id]);

  const handleStatusChange = async (todo, newStatus) => {
    const originalTasks = [...tasks];
    setTasks(prev => prev.map(t => t.id === todo.id ? { ...t, status: newStatus } : t));
    try {
      await api.todos.update(todo.id, { status: newStatus });
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setTasks(originalTasks);
      alert('Failed to update status: ' + err.message);
    }
  };

  const handleToggleTaskStatus = async (task) => {
    const newStatus = task.status === 'done' ? 'todo' : 'done';
    const originalTasks = [...tasks];
    setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: newStatus } : t));
    try {
      await api.todos.update(task.id, { status: newStatus });
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setTasks(originalTasks);
      alert('Failed to update task status: ' + err.message);
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;
    const originalTasks = [...tasks];
    const tempId = 'temp-' + Date.now();
    const tempTask = {
      id: tempId,
      project_id: project.id,
      title: taskTitle.trim(),
      description: taskDescription.trim(),
      priority: taskPriority,
      status: 'todo',
      estimated_hours: taskEstHours ? parseFloat(taskEstHours) : null,
      created_at: new Date().toISOString()
    };
    setTasks(prev => [...prev, tempTask]);
    setTaskTitle('');
    setTaskDescription('');
    setTaskPriority('medium');
    setTaskEstHours('');
    try {
      await api.todos.create({
        project_id: project.id,
        title: tempTask.title,
        description: tempTask.description,
        priority: tempTask.priority,
        status: 'todo',
        estimated_hours: tempTask.estimated_hours
      });
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setTasks(originalTasks);
      alert('Failed to create task: ' + err.message);
    }
  };

  const handleDeleteTask = async (id) => {
    window.showConfirm('Are you sure you want to delete this task?', async () => {
      const originalTasks = [...tasks];
      setTasks(prev => prev.filter(t => t.id !== id));
      try {
        await api.todos.delete(id);
        fetchProjectDetails();
        onRefresh();
      } catch (err) {
        setTasks(originalTasks);
        alert('Failed to delete task: ' + err.message);
      }
    });
  };

  const saveSyncSettings = () => {
    if (googleToken) localStorage.setItem('google_token', googleToken);
    if (githubToken) localStorage.setItem('github_token', githubToken);
    if (githubRepo) localStorage.setItem('github_repo', githubRepo);
    alert('Integration settings saved locally.');
  };

  const triggerGoogleAuth = async () => {
    try {
      const res = await api.sync.googleAuth();
      if (res.url) {
        window.location.href = res.url;
      }
    } catch (err) {
      alert('Google Auth initiation failed: ' + err.message);
    }
  };

  // Sync actions
  const syncToSheets = async () => {
    if (!googleToken) {
      setSyncError('Google Access Token is required. Authenticate or input it manually.');
      return;
    }
    setSyncStatus('Exporting project workspace to Google Sheets...');
    setSyncError('');
    try {
      const res = await api.sync.sheets(googleToken, project.id);
      setSyncStatus(`Successfully exported! Sheet URL: `);
      if (res.spreadsheet_url) {
        setSyncStatus(
          <span>
            Successfully exported!{' '}
            <a href={res.spreadsheet_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>
              View Google Sheet <ExternalLink size={12} style={{ display: 'inline' }} />
            </a>
          </span>
        );
      }
    } catch (err) {
      setSyncError(err.message || 'Sheets sync failed');
      setSyncStatus('');
    }
  };

  const syncToCalendar = async () => {
    if (!googleToken) {
      setSyncError('Google Access Token is required.');
      return;
    }
    setSyncStatus('Pushing milestones to Google Calendar...');
    setSyncError('');
    try {
      await api.sync.calendar(googleToken, project.id);
      setSyncStatus('Successfully synced project milestones with Google Calendar!');
    } catch (err) {
      setSyncError(err.message || 'Calendar sync failed');
      setSyncStatus('');
    }
  };

  const syncToGitHub = async () => {
    if (!githubToken || !githubRepo) {
      setSyncError('GitHub token and Repository path (owner/repo) are required.');
      return;
    }
    setSyncStatus('Creating Sprint tasks as GitHub issues...');
    setSyncError('');
    try {
      await api.sync.github(githubToken, githubRepo, project.id);
      setSyncStatus('Successfully created Sprint tasks on GitHub!');
    } catch (err) {
      setSyncError(err.message || 'GitHub sync failed');
      setSyncStatus('');
    }
  };



  const handleCreatePayment = async (e) => {
    e.preventDefault();
    if (!paymentAmount) return;
    const originalPayments = [...payments];
    const tempPayment = {
      id: 'temp-' + Date.now(),
      project_id: project.id,
      amount: parseFloat(paymentAmount),
      currency: 'INR',
      payment_type: paymentType,
      received_date: new Date().toISOString(),
      status: 'received',
      notes: paymentNotes
    };
    setPayments(prev => [...prev, tempPayment]);
    setPaymentAmount('');
    setPaymentNotes('');
    try {
      await api.payments.create({
        project_id: project.id,
        amount: tempPayment.amount,
        currency: 'INR',
        payment_type: tempPayment.payment_type,
        received_date: tempPayment.received_date,
        status: 'received',
        notes: tempPayment.notes
      });
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setPayments(originalPayments);
      alert('Failed to log payment: ' + err.message);
    }
  };

  const handleDeletePayment = async (id) => {
    window.showConfirm('Are you sure you want to delete this payment record?', async () => {
      const originalPayments = [...payments];
      setPayments(prev => prev.filter(p => p.id !== id));
      try {
        await api.payments.delete(id);
        fetchProjectDetails();
        onRefresh();
      } catch (err) {
        setPayments(originalPayments);
        alert('Failed to delete payment: ' + err.message);
      }
    });
  };

  const handleUploadContract = async (e) => {
    e.preventDefault();
    if (!clientName) {
      alert('Client Name is required');
      return;
    }
    const originalContracts = [...contracts];
    const tempContract = {
      id: 'temp-' + Date.now(),
      project_id: project.id,
      client_name: clientName,
      notes: contractNotes,
      received_date: new Date().toISOString(),
      contract_url: null
    };
    setContracts(prev => [...prev, tempContract]);
    setClientName('');
    setContractNotes('');
    setContractFile(null);
    const fileInput = document.getElementById('contract-file-input');
    if (fileInput) fileInput.value = '';

    const formData = new FormData();
    formData.append('project_id', project.id);
    formData.append('client_name', tempContract.client_name);
    formData.append('notes', tempContract.notes);
    formData.append('received_date', tempContract.received_date);
    if (contractFile) {
      formData.append('file', contractFile);
    }
    try {
      await api.contracts.create(formData);
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setContracts(originalContracts);
      alert('Failed to upload contract: ' + err.message);
    }
  };

  const handleDeleteContract = async (id) => {
    window.showConfirm('Are you sure you want to delete this contract?', async () => {
      const originalContracts = [...contracts];
      setContracts(prev => prev.filter(c => c.id !== id));
      try {
        await api.contracts.delete(id);
        fetchProjectDetails();
        onRefresh();
      } catch (err) {
        setContracts(originalContracts);
        alert('Failed to delete contract: ' + err.message);
      }
    });
  };

  const handleCreatePendingThing = async (e) => {
    e.preventDefault();
    if (!pendingTitle.trim()) {
      alert('Please enter a title');
      return;
    }
    const originalAttachments = [...attachments];
    const tempPending = {
      id: 'temp-' + Date.now(),
      project_id: project.id,
      title: pendingTitle,
      description: pendingDescription,
      is_completed: false,
      filename: attachmentFile ? attachmentFile.name : null,
      file_url: null,
      created_at: new Date().toISOString()
    };
    setAttachments(prev => [...prev, tempPending]);
    
    const formData = new FormData();
    formData.append('project_id', project.id);
    formData.append('title', pendingTitle);
    formData.append('description', pendingDescription);
    if (attachmentFile) {
      formData.append('file', attachmentFile);
    }

    setPendingTitle('');
    setPendingDescription('');
    setAttachmentFile(null);
    const fileInput = document.getElementById('pending-file-input');
    if (fileInput) fileInput.value = '';

    try {
      await api.pendingThings.create(formData);
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setAttachments(originalAttachments);
      alert('Failed to create pending item: ' + err.message);
    }
  };

  const handleTogglePendingThing = async (item) => {
    const originalAttachments = [...attachments];
    setAttachments(prev => prev.map(a => a.id === item.id ? { ...a, is_completed: !a.is_completed } : a));
    try {
      await api.pendingThings.update(item.id, { is_completed: !item.is_completed });
      fetchProjectDetails();
      onRefresh();
    } catch (err) {
      setAttachments(originalAttachments);
      alert('Failed to update pending item: ' + err.message);
    }
  };

  const handleDeletePendingThing = async (id) => {
    window.showConfirm('Are you sure you want to delete this pending item?', async () => {
      const originalAttachments = [...attachments];
      setAttachments(prev => prev.filter(a => a.id !== id));
      try {
        await api.pendingThings.delete(id);
        fetchProjectDetails();
        onRefresh();
      } catch (err) {
        setAttachments(originalAttachments);
        alert('Failed to delete pending item: ' + err.message);
      }
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', width: '100%' }}>
          {isEditingHeader ? (
            <div className="glass-panel" style={{ padding: '16px 20px', width: '100%', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', gap: '12px', width: '100%', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '240px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>Project Title</label>
                    <input
                      type="text"
                      className="input-field"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      style={{ fontSize: '1rem', padding: '8px 12px' }}
                      placeholder="Enter project title"
                    />
                  </div>
                  <div style={{ width: '160px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>Status</label>
                    <select
                      className="input-field"
                      value={editedStatus}
                      onChange={(e) => setEditedStatus(e.target.value)}
                      style={{ fontSize: '0.9rem', padding: '8px 12px', height: '38px' }}
                    >
                      <option value="planning">Planning</option>
                      <option value="developing">Developing</option>
                      <option value="finished">Finished</option>
                    </select>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <button 
                    onClick={handleSaveHeader} 
                    className="btn btn-primary"
                    style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Check size={16} /> Save
                  </button>
                  <button 
                    onClick={() => {
                      setIsEditingHeader(false);
                      setEditedTitle(project.title);
                      setEditedDescription(project.description || '');
                      setEditedStatus(project.status || 'planning');
                    }} 
                    className="btn btn-secondary"
                    style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <X size={16} /> Cancel
                  </button>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>Project Description</label>
                <input
                  type="text"
                  className="input-field"
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  style={{ fontSize: '0.9rem', padding: '8px 12px' }}
                  placeholder="Enter project description"
                />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', margin: 0 }}>
                  {project.title}
                  {project.total_amount !== undefined && project.total_amount !== null && (
                    <span className="badge badge-primary" style={{ fontSize: '0.8rem', padding: '4px 10px', background: 'rgba(139, 92, 246, 0.15)', color: '#a78bfa', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                      Value: {Number(project.total_amount).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}
                    </span>
                  )}
                  {(() => {
                    const status = (project.status || 'planning').toLowerCase();
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
                        fontSize: '0.8rem',
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
                  <button
                    onClick={() => setIsEditingHeader(true)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      padding: '4px',
                      borderRadius: '4px',
                      transition: 'all 0.2s',
                    }}
                    className="edit-header-btn"
                    title="Edit Details"
                  >
                    <Pencil size={14} />
                  </button>
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
                  {project.description || 'No description.'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="glass-panel" style={{ display: 'flex', padding: '6px', gap: '8px', borderRadius: '12px' }}>
        <button 
          className={`btn ${activeSubTab === 'board' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          onClick={() => setActiveSubTab('board')}
        >
          <CheckSquare size={16} /> To-Do List
        </button>
        <button 
          className={`btn ${activeSubTab === 'contracts_payments' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          onClick={() => setActiveSubTab('contracts_payments')}
        >
          <CreditCard size={16} /> Payments
        </button>
        <button 
          className={`btn ${activeSubTab === 'attachments' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          onClick={() => setActiveSubTab('attachments')}
        >
          <Paperclip size={16} /> Pending Things & Contracts
        </button>
        <button 
          className={`btn ${activeSubTab === 'notepad' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          onClick={() => setActiveSubTab('notepad')}
        >
          <FileText size={16} /> Notepad
        </button>
      </div>

      {/* Content panes */}
      {loading ? (
        activeSubTab === 'board' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
            {/* Skeletons for To-Do tasks column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="skeleton-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div className="skeleton-pulse skeleton-text" style={{ width: '40%', height: '14px', margin: 0 }} />
                  <div className="skeleton-pulse skeleton-text" style={{ width: '25%', height: '14px', margin: 0 }} />
                </div>
                <div className="skeleton-pulse skeleton-button" style={{ width: '100%', height: '8px', borderRadius: '4px' }} />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[1, 2, 3].map(i => (
                  <div key={i} className="skeleton-pulse skeleton-button" style={{ width: '80px', height: '28px', borderRadius: '4px' }} />
                ))}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[1, 2].map(i => (
                  <div key={i} className="skeleton-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div className="skeleton-pulse skeleton-button" style={{ width: '20px', height: '20px', borderRadius: '4px' }} />
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div className="skeleton-pulse skeleton-title" style={{ width: '60%', height: '16px', margin: 0 }} />
                      <div className="skeleton-pulse skeleton-text" style={{ width: '90%', height: '12px', margin: 0 }} />
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <div className="skeleton-pulse skeleton-button" style={{ width: '50px', height: '16px', borderRadius: '4px' }} />
                        <div className="skeleton-pulse skeleton-button" style={{ width: '30px', height: '16px', borderRadius: '4px' }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Form Column */}
            <div className="skeleton-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="skeleton-pulse skeleton-title" style={{ width: '40%', height: '18px' }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="skeleton-pulse skeleton-text" style={{ width: '30%', height: '12px' }} />
                <div className="skeleton-pulse skeleton-button" style={{ width: '100%', height: '36px', borderRadius: '6px' }} />
                <div className="skeleton-pulse skeleton-text" style={{ width: '30%', height: '12px' }} />
                <div className="skeleton-pulse skeleton-button" style={{ width: '100%', height: '70px', borderRadius: '6px' }} />
              </div>
            </div>
          </div>
        ) : activeSubTab === 'contracts_payments' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
            {/* Payments column skeleton */}
            <div className="skeleton-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="skeleton-pulse skeleton-title" style={{ width: '50%', height: '18px', margin: 0 }} />
                <div className="skeleton-pulse skeleton-button" style={{ width: '120px', height: '24px', borderRadius: '12px' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[1, 2].map(i => (
                  <div key={i} className="skeleton-card" style={{ padding: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '80%' }}>
                      <div className="skeleton-pulse skeleton-title" style={{ width: '60%', height: '14px', margin: 0 }} />
                      <div className="skeleton-pulse skeleton-text" style={{ width: '90%', height: '12px', margin: 0 }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Contracts column skeleton */}
            <div className="skeleton-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="skeleton-pulse skeleton-title" style={{ width: '60%', height: '18px', margin: 0 }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[1].map(i => (
                  <div key={i} className="skeleton-card" style={{ padding: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div className="skeleton-pulse skeleton-avatar" style={{ width: '24px', height: '24px' }} />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '70%' }}>
                      <div className="skeleton-pulse skeleton-title" style={{ width: '80%', height: '14px', margin: 0 }} />
                      <div className="skeleton-pulse skeleton-text" style={{ width: '50%', height: '12px', margin: 0 }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* attachments view skeleton */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="skeleton-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="skeleton-pulse skeleton-title" style={{ width: '40%', height: '18px', margin: 0 }} />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                {[1, 2, 3].map(i => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div className="skeleton-pulse skeleton-text" style={{ width: '50%', height: '12px' }} />
                    <div className="skeleton-pulse skeleton-button" style={{ width: '100%', height: '36px', borderRadius: '6px' }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      ) : (
        <>
          {activeSubTab === 'board' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
              
              {/* Left Column: Tasks List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {/* Stats & Progress bar */}
                <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Task Progress</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
                      {tasks.filter(t => t.status === 'done').length} / {tasks.length} Completed ({tasks.length > 0 ? Math.round((tasks.filter(t => t.status === 'done').length / tasks.length) * 100) : 0}%)
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${tasks.length > 0 ? (tasks.filter(t => t.status === 'done').length / tasks.length) * 100 : 0}%`, 
                      height: '100%', 
                      background: 'linear-gradient(to right, var(--accent-primary), var(--accent-secondary))',
                      transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
                    }} />
                  </div>
                </div>

                {/* Filter Bar */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  {['all', 'pending', 'completed'].map(filter => (
                    <button
                      key={filter}
                      className={`btn ${todoFilter === filter ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '6px 16px', fontSize: '0.8rem', textTransform: 'capitalize' }}
                      onClick={() => setTodoFilter(filter)}
                    >
                      {filter}
                    </button>
                  ))}
                </div>

                {/* Tasks List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {tasks.filter(t => {
                    if (todoFilter === 'pending') return t.status !== 'done';
                    if (todoFilter === 'completed') return t.status === 'done';
                    return true;
                  }).length === 0 ? (
                    <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No {todoFilter !== 'all' ? todoFilter : ''} tasks found.
                    </div>
                  ) : (
                    tasks.filter(t => {
                      if (todoFilter === 'pending') return t.status !== 'done';
                      if (todoFilter === 'completed') return t.status === 'done';
                      return true;
                    }).map(task => {
                      const isCompleted = task.status === 'done';
                      return (
                        <div 
                          key={task.id} 
                          className="glass-panel" 
                          style={{ 
                            padding: '16px', 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '16px', 
                            background: isCompleted ? 'rgba(255, 255, 255, 0.01)' : 'var(--bg-tertiary)',
                            opacity: isCompleted ? 0.7 : 1,
                            border: '1px solid rgba(255,255,255,0.05)',
                            transition: 'all var(--transition-fast)'
                          }}
                        >
                          {/* Custom Checkbox Toggle */}
                          <button 
                            type="button"
                            onClick={() => handleToggleTaskStatus(task)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              color: isCompleted ? '#10b981' : 'var(--text-muted)',
                              padding: 0,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0,
                              transition: 'color var(--transition-fast)'
                            }}
                          >
                            {isCompleted ? (
                              <CheckSquare size={20} style={{ color: '#10b981' }} />
                            ) : (
                              <Square size={20} />
                            )}
                          </button>

                          {/* Task Info */}
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <span style={{ 
                              fontSize: '0.9rem', 
                              fontWeight: 600, 
                              textDecoration: isCompleted ? 'line-through' : 'none',
                              color: isCompleted ? 'var(--text-muted)' : 'var(--text-primary)',
                              display: 'block',
                              marginBottom: '2px'
                            }}>
                              {task.title}
                            </span>
                            {task.description && (
                              <p style={{ 
                                fontSize: '0.8rem', 
                                color: isCompleted ? 'var(--text-muted)' : 'var(--text-secondary)',
                                margin: 0,
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis'
                              }}>
                                {task.description}
                              </p>
                            )}
                            
                            {/* Badges row */}
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '6px', flexWrap: 'wrap' }}>
                              <span className={`badge badge-${task.priority}`} style={{ fontSize: '0.65rem' }}>{task.priority}</span>
                              {task.estimated_hours && (
                                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{task.estimated_hours}h</span>
                              )}
                            </div>
                          </div>

                          {/* Status Selector & Delete Button */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
                            <select 
                              value={task.status} 
                              onChange={(e) => handleStatusChange(task, e.target.value)}
                              style={{ 
                                background: 'var(--bg-secondary)', 
                                color: 'var(--text-primary)', 
                                border: '1px solid var(--border-color)', 
                                borderRadius: '6px', 
                                fontSize: '0.75rem', 
                                padding: '4px 8px',
                                outline: 'none',
                                cursor: 'pointer'
                              }}
                            >
                              <option value="todo">Todo</option>
                              <option value="in_progress">In Progress</option>
                              <option value="review">Under Review</option>
                              <option value="done">Completed</option>
                            </select>

                            <button 
                              type="button"
                              className="btn" 
                              style={{ padding: '6px', background: 'transparent', color: '#f87171' }} 
                              onClick={() => handleDeleteTask(task.id)}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>

                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Right Column: Add Task Form */}
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Add New Task</h3>
                </div>

                <form onSubmit={handleCreateTask} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div className="form-group" style={{ marginBottom: '12px' }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Task Title</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      value={taskTitle} 
                      onChange={(e) => setTaskTitle(e.target.value)} 
                      placeholder="e.g. Build backend API endpoints" 
                      required 
                    />
                  </div>

                  <div className="form-group" style={{ marginBottom: '12px' }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Description</label>
                    <textarea 
                      className="input-field" 
                      value={taskDescription} 
                      onChange={(e) => setTaskDescription(e.target.value)} 
                      placeholder="Describe task requirements..." 
                      style={{ minHeight: '80px', fontFamily: 'inherit' }}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="form-group" style={{ marginBottom: '12px' }}>
                      <label className="form-label" style={{ fontSize: '0.75rem' }}>Priority</label>
                      <select 
                        className="input-field" 
                        value={taskPriority} 
                        onChange={(e) => setTaskPriority(e.target.value)}
                        style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>

                    <div className="form-group" style={{ marginBottom: '12px' }}>
                      <label className="form-label" style={{ fontSize: '0.75rem' }}>Est. Hours</label>
                      <input 
                        type="number" 
                        step="0.5"
                        className="input-field" 
                        value={taskEstHours} 
                        onChange={(e) => setTaskEstHours(e.target.value)} 
                        placeholder="e.g. 4.5" 
                      />
                    </div>
                  </div>

                  <button type="submit" className="btn btn-primary" style={{ marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                    <Plus size={14} /> Add Task
                  </button>
                </form>
              </div>

            </div>
          )}



          {activeSubTab === 'contracts_payments' && (() => {
            const totalVal = parseFloat(project.total_amount) || 0;
            const totalPaid = payments.reduce((sum, p) => sum + parseFloat(p.amount), 0);
            const remainingBal = Math.max(0, totalVal - totalPaid);
            const paidPct = totalVal > 0 ? Math.min(100, Math.round((totalPaid / totalVal) * 100)) : 0;
            const remainingPct = 100 - paidPct;

            return (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
                {/* Left Column: Visual Dashboard & Payments list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* Financial Overview Card */}
                  <div className="glass-panel" style={{ 
                    padding: '24px', 
                    background: 'linear-gradient(135deg, rgba(25, 22, 50, 0.7) 0%, rgba(18, 16, 33, 0.9) 100%)',
                    border: '1px solid rgba(139, 92, 246, 0.15)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '20px',
                    position: 'relative',
                    overflow: 'hidden'
                  }}>
                    {/* Glowing background highlights */}
                    <div style={{
                      position: 'absolute',
                      top: '-20%',
                      right: '-10%',
                      width: '180px',
                      height: '180px',
                      background: 'radial-gradient(circle, rgba(236, 72, 153, 0.15) 0%, transparent 70%)',
                      zIndex: 0,
                      pointerEvents: 'none'
                    }} />
                    <div style={{
                      position: 'absolute',
                      bottom: '-20%',
                      left: '-10%',
                      width: '180px',
                      height: '180px',
                      background: 'radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%)',
                      zIndex: 0,
                      pointerEvents: 'none'
                    }} />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 1 }}>
                      <h3 style={{ fontSize: '1.20rem', fontWeight: 600, margin: 0 }}>Project Financial Status</h3>
                      <span style={{ 
                        fontSize: '0.75rem', 
                        color: 'var(--text-secondary)',
                        background: 'rgba(255,255,255,0.06)',
                        padding: '4px 10px',
                        borderRadius: '20px'
                      }}>
                        {paidPct}% Collected
                      </span>
                    </div>

                    {/* Progress Bar Graphic */}
                    <div style={{ zIndex: 1 }}>
                      <div style={{ display: 'flex', height: '14px', background: 'var(--bg-primary)', borderRadius: '7px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)' }}>
                        {paidPct > 0 && (
                          <div style={{ 
                            width: `${paidPct}%`, 
                            background: 'linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)', 
                            height: '100%',
                            boxShadow: '0 0 12px var(--accent-glow)'
                          }} />
                        )}
                        {remainingPct > 0 && (
                          <div style={{ 
                            width: `${remainingPct}%`, 
                            background: 'rgba(255,255,255,0.03)', 
                            height: '100%' 
                          }} />
                        )}
                      </div>
                    </div>

                    {/* Metrics grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', zIndex: 1 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Project Value</span>
                        <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {totalVal.toLocaleString()} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>INR</span>
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', borderLeft: '1px solid rgba(255,255,255,0.08)', paddingLeft: '12px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Total Paid</span>
                        <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10b981' }}>
                          {totalPaid.toLocaleString()} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>INR</span>
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', borderLeft: '1px solid rgba(255,255,255,0.08)', paddingLeft: '12px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Remaining</span>
                        <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-secondary)' }}>
                          {remainingBal.toLocaleString()} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>INR</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Payments list panel */}
                  <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
                      <h3 style={{ fontSize: '1.20rem', fontWeight: 600 }}>Payments History</h3>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '320px', overflowY: 'auto', paddingRight: '4px' }}>
                      {payments.length === 0 ? (
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '32px' }}>No payments logged for this project yet.</p>
                      ) : (
                        payments.map((p) => (
                          <div key={p.id} style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center', 
                            padding: '16px', 
                            background: 'rgba(255, 255, 255, 0.02)', 
                            border: '1px solid rgba(255, 255, 255, 0.05)', 
                            borderRadius: '14px', 
                            transition: 'all 0.2s ease', 
                            cursor: 'default' 
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, minWidth: 0 }}>
                              <div style={{ 
                                width: '40px', 
                                height: '40px', 
                                borderRadius: '10px', 
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(236, 72, 153, 0.12) 100%)', 
                                border: '1px solid rgba(139, 92, 246, 0.2)',
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center', 
                                color: 'var(--accent-primary)',
                                flexShrink: 0
                              }}>
                                <CreditCard size={18} />
                              </div>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                  <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                    ₹{parseFloat(p.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                  </span>
                                  <span style={{ 
                                    fontSize: '0.65rem', 
                                    fontWeight: 600, 
                                    padding: '3px 8px', 
                                    borderRadius: '20px',
                                    background: p.payment_type === 'Advance' ? 'rgba(139, 92, 246, 0.15)' : p.payment_type === 'Final' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(251, 191, 36, 0.15)',
                                    color: p.payment_type === 'Advance' ? 'var(--accent-primary)' : p.payment_type === 'Final' ? '#34d399' : '#fbbf24',
                                    border: p.payment_type === 'Advance' ? '1px solid rgba(139, 92, 246, 0.3)' : p.payment_type === 'Final' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(251, 191, 36, 0.3)'
                                  }}>
                                    {p.payment_type}
                                  </span>
                                  <span style={{ 
                                    fontSize: '0.65rem', 
                                    fontWeight: 600, 
                                    padding: '3px 8px', 
                                    borderRadius: '20px',
                                    background: p.status === 'received' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(251, 191, 36, 0.1)',
                                    color: p.status === 'received' ? '#10b981' : '#f59e0b',
                                    border: p.status === 'received' ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(251, 191, 36, 0.2)'
                                  }}>
                                    {p.status === 'received' ? 'Completed' : 'Pending'}
                                  </span>
                                </div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <span>{p.received_date ? new Date(p.received_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Pending'}</span>
                                  {p.notes && (
                                    <>
                                      <span style={{ color: 'rgba(255,255,255,0.15)' }}>•</span>
                                      <span style={{ fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '240px' }} title={p.notes}>
                                        {p.notes}
                                      </span>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                            <button className="btn" style={{ padding: '8px', background: 'transparent', color: 'rgba(239, 68, 68, 0.6)', border: 'none', cursor: 'pointer' }} onClick={() => handleDeletePayment(p.id)}>
                              <Trash2 size={15} />
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Column: Log a Payment form */}
                <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
                    <h3 style={{ fontSize: '1.20rem', fontWeight: 600 }}>Log a Payment</h3>
                  </div>
                  <form onSubmit={handleCreatePayment} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>Amount (INR)</label>
                        <input 
                          type="number" 
                          className="input-field" 
                          value={paymentAmount} 
                          onChange={(e) => setPaymentAmount(e.target.value)} 
                          placeholder="e.g. 50000" 
                          required 
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>Payment Type</label>
                        <select 
                          className="input-field" 
                          value={paymentType} 
                          onChange={(e) => setPaymentType(e.target.value)}
                          style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                        >
                          <option value="Advance">Advance</option>
                          <option value="Partial">Partial</option>
                          <option value="Final">Final</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '0.75rem' }}>Notes / Reference</label>
                      <input 
                        type="text" 
                        className="input-field" 
                        value={paymentNotes} 
                        onChange={(e) => setPaymentNotes(e.target.value)} 
                        placeholder="e.g. Milestone 1 completion payment" 
                      />
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-end', display: 'flex', alignItems: 'center', gap: '6px', height: '40px' }}>
                      <Plus size={14} /> Log Payment
                    </button>
                  </form>
                </div>
              </div>
            );
          })()}

          {activeSubTab === 'attachments' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
              {/* Left Column: Pending Things */}
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
                  <h3 style={{ fontSize: '1.20rem', fontWeight: 600 }}>Pending Things & Credentials</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Track keys, credentials, files, or information that clients need to send, or any other pending actions.</p>
                </div>

                {/* List pending things */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '400px', overflowY: 'auto', padding: '4px' }}>
                  {attachments.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      No pending things tracked for this project yet.
                    </div>
                  ) : (
                    attachments.map((item) => (
                      <div 
                        key={item.id} 
                        style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center', 
                          padding: '14px 16px', 
                          background: item.is_completed ? 'rgba(255,255,255,0.01)' : 'rgba(255,255,255,0.02)', 
                          border: '1px solid rgba(255,255,255,0.05)', 
                          borderRadius: '12px',
                          opacity: item.is_completed ? 0.6 : 1,
                          transition: 'opacity 0.2s ease'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', minWidth: 0, flex: 1 }}>
                          <input 
                            type="checkbox" 
                            checked={item.is_completed} 
                            onChange={() => handleTogglePendingThing(item)}
                            style={{ marginTop: '4px', cursor: 'pointer', accentColor: 'var(--accent-primary)' }}
                          />
                          <div style={{ minWidth: 0, flex: 1 }}>
                            <div style={{ 
                              fontSize: '0.9rem', 
                              fontWeight: 600, 
                              textDecoration: item.is_completed ? 'line-through' : 'none',
                              color: item.is_completed ? 'var(--text-muted)' : 'var(--text-primary)'
                            }}>
                              {item.title}
                            </div>
                            {item.description && (
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                {item.description}
                              </div>
                            )}
                            {item.filename && item.file_url && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', padding: '6px 10px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', width: 'fit-content' }}>
                                <File size={14} style={{ color: 'var(--accent-primary)' }} />
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                                  {item.filename}
                                </span>
                                <a 
                                  href={getFileUrl(item.file_url)} 
                                  target="_blank" 
                                  rel="noreferrer" 
                                  style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', textDecoration: 'underline', marginLeft: '6px', display: 'flex', alignItems: 'center', gap: '2px' }}
                                >
                                  Download <ExternalLink size={8} />
                                </a>
                              </div>
                            )}
                          </div>
                        </div>
                        <button 
                          className="btn" 
                          style={{ padding: '6px', background: 'transparent', color: '#f87171', flexShrink: 0, marginLeft: '12px' }} 
                          onClick={() => handleDeletePendingThing(item.id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* Add pending thing form */}
                <form onSubmit={handleCreatePendingThing} style={{ display: 'flex', flexDirection: 'column', gap: '16px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '20px' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Add a Pending Item / Credential</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
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
                        placeholder="Add details (e.g. secret keys needed)"
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
                        id="pending-file-input"
                        className="input-field" 
                        onChange={(e) => setAttachmentFile(e.target.files[0])} 
                        style={{ padding: '6px' }}
                      />
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px', height: '40px' }}>
                      <Plus size={14} /> Add Pending Item
                    </button>
                  </div>
                </form>
              </div>

              {/* Right Column: Contracts panel */}
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '12px' }}>
                  <h3 style={{ fontSize: '1.20rem', fontWeight: 600 }}>Client Contracts & Documents</h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Upload service agreements, proposals, NDAs, or other official project documents.</p>
                </div>

                {/* List contracts */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '240px', overflowY: 'auto', paddingRight: '4px' }}>
                  {contracts.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '16px' }}>No contracts uploaded yet.</p>
                  ) : (
                    contracts.map((c) => (
                      <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <FileText size={18} style={{ color: 'var(--accent-primary)' }} />
                          <div>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{c.client_name}</div>
                            {c.contract_url ? (
                              <a href={getFileUrl(c.contract_url)} target="_blank" rel="noreferrer" style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', textDecoration: 'underline', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                View Signed PDF <ExternalLink size={10} />
                              </a>
                            ) : (
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Metadata only</span>
                            )}
                          </div>
                        </div>
                        <button className="btn" style={{ padding: '4px', background: 'transparent', color: '#f87171' }} onClick={() => handleDeleteContract(c.id)}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* Upload contract form */}
                <form onSubmit={handleUploadContract} style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '16px' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Upload a Contract / Document</h4>
                  <div className="form-group">
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Client / Partner Name</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      value={clientName} 
                      onChange={(e) => setClientName(e.target.value)} 
                      placeholder="e.g. Acme Corp Inc." 
                      required 
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Notes</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      value={contractNotes} 
                      onChange={(e) => setContractNotes(e.target.value)} 
                      placeholder="e.g. NDA and service level agreement" 
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Contract PDF File</label>
                    <input 
                      type="file" 
                      id="contract-file-input"
                      className="input-field" 
                      accept=".pdf"
                      onChange={(e) => setContractFile(e.target.files[0])} 
                      style={{ padding: '6px' }}
                    />
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-end', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Upload size={14} /> Upload Contract
                  </button>
                </form>
              </div>
            </div>
          )}

          {activeSubTab === 'notepad' && (
            <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                    <FileText size={20} style={{ color: 'var(--accent-primary)' }} />
                    Project Notepad
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
                    Write down notes, project briefs, task requirements, client details, or copy-paste useful snippets.
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {saveStatus === 'saving' && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <RefreshCw size={14} className="animate-spin" /> Saving...
                    </span>
                  )}
                  {saveStatus === 'saved' && (
                    <span style={{ fontSize: '0.85rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 500 }}>
                      <Check size={14} /> Saved!
                    </span>
                  )}
                  {saveStatus === 'error' && (
                    <span style={{ fontSize: '0.85rem', color: '#ef4444', fontWeight: 500 }}>
                      Failed to save notes.
                    </span>
                  )}
                  <button 
                    onClick={handleSaveNotepad} 
                    className="btn btn-primary"
                    disabled={saveStatus === 'saving'}
                    style={{ 
                      padding: '8px 20px', 
                      borderRadius: '8px', 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px', 
                      fontWeight: 600,
                      boxShadow: '0 4px 12px rgba(139, 92, 246, 0.2)'
                    }}
                  >
                    <Check size={16} /> Save Notes
                  </button>
                </div>
              </div>

              <div style={{ position: 'relative' }}>
                <textarea
                  className="input-field"
                  placeholder="Start typing your notes here..."
                  value={notepadText}
                  onChange={(e) => setNotepadText(e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: '450px',
                    fontFamily: 'Consolas, Monaco, "Courier New", Courier, monospace',
                    fontSize: '0.92rem',
                    lineHeight: '1.6',
                    padding: '20px',
                    background: 'var(--bg-secondary)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)',
                    resize: 'vertical',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'var(--accent-primary)';
                    e.target.style.boxShadow = '0 0 0 3px rgba(139, 92, 246, 0.15)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
