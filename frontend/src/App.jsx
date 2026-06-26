import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Briefcase, 
  Bell, 
  Calendar, 
  LogOut, 
  Mail, 
  Lock, 
  User as UserIcon, 
  AlertCircle, 
  CheckCircle,
  Info,
  X,
  Paperclip,
  Table,
  ExternalLink,
  Link2,
  CreditCard,
  Users,
  TrendingUp,
  FileText,
  RotateCw,
  AlertTriangle,
  Menu,
  ArrowLeft,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { api } from './services/api';
import ChatInterface from './components/ChatInterface';
import DashboardStats from './components/DashboardStats';
import ProjectsView from './components/ProjectsView';
import RemindersView from './components/RemindersView';
import FilesView from './components/FilesView';
import IntegrationsView from './components/IntegrationsView';
import PaymentsView from './components/PaymentsView';
import ReportsEngineView from './components/ReportsEngineView';
import DashboardAnalytics from './components/DashboardAnalytics';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [isRegister, setIsRegister] = useState(false);
  const [user, setUser] = useState(null);
  
  // Auth Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // App Data State
  const [activeTab, setActiveTab] = useState(() => {
    const hash = window.location.hash.replace('#/', '');
    if (hash.startsWith('projects/')) return 'projects';
    return ['projects', 'payments', 'reports', 'reminders', 'files', 'integrations'].includes(hash) ? hash : 'dashboard';
  });

  const [selectedProjectId, setSelectedProjectId] = useState(() => {
    const hash = window.location.hash.replace('#/', '');
    if (hash.startsWith('projects/')) {
      return hash.replace('projects/', '');
    }
    return null;
  });

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigateTo = (tab) => {
    window.location.hash = tab === 'dashboard' ? '#/' : `#/${tab}`;
    setMobileMenuOpen(false);
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#/', '');
      if (hash.startsWith('projects/')) {
        const projectId = hash.replace('projects/', '');
        setActiveTab('projects');
        setSelectedProjectId(projectId);
      } else {
        const tab = ['projects', 'payments', 'reports', 'reminders', 'files', 'integrations'].includes(hash) ? hash : 'dashboard';
        setActiveTab(tab);
        setSelectedProjectId(null);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const [projects, setProjects] = useState([]);
  const [todos, setTodos] = useState([]);
  const [events, setEvents] = useState([]);
  const [payments, setPayments] = useState([]);
  const [sheetLinks, setSheetLinks] = useState({ payments_url: null });
  const [remindersCount, setRemindersCount] = useState(0);
  const [pendingThingsCount, setPendingThingsCount] = useState(0);
  const [loadingData, setLoadingData] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [confirmConfig, setConfirmConfig] = useState(null);

  useEffect(() => {
    window.showConfirm = (message, onConfirm) => {
      setConfirmConfig({ message, onConfirm });
    };
    return () => {
      delete window.showConfirm;
    };
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      const proj = projects.find(p => p.id === selectedProjectId);
      if (proj) {
        setSelectedProject(proj);
      }
    } else {
      setSelectedProject(null);
    }
  }, [projects, selectedProjectId]);

  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [mobileProjectsOpen, setMobileProjectsOpen] = useState(false);
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const [toasts, setToasts] = useState([]);

  const showToast = React.useCallback((message, type = 'info') => {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  }, []);

  useEffect(() => {
    window.showToast = showToast;
    window.alert = (msg) => {
      if (!msg) return;
      const msgStr = typeof msg === 'object' ? JSON.stringify(msg) : String(msg);
      const isError = msgStr.toLowerCase().includes('fail') || msgStr.toLowerCase().includes('error') || msgStr.toLowerCase().includes('invalid') || msgStr.toLowerCase().includes('required');
      showToast(msgStr, isError ? 'error' : 'success');
    };
  }, [showToast]);

  // Fetch all user data
  const fetchData = async () => {
    if (!isAuthenticated) return;
    setLoadingData(true);
    try {
      const [projList, todoList, eventList, links, reminderList, pendingList, paymentList] = await Promise.all([
        api.projects.list().catch(err => { console.error("Error listing projects:", err); return []; }),
        api.todos.list().catch(err => { console.error("Error listing todos:", err); return []; }),
        api.timeline.list().catch(err => { console.error("Error listing timeline:", err); return []; }),
        api.sync.getSheetsLinks().catch(() => ({ payments_url: null })),
        api.reminders.list().catch(() => []),
        api.pendingThings.list().catch(() => []),
        api.payments.list().catch(err => { console.error("Error listing payments:", err); return []; })
      ]);
      setProjects(projList || []);
      setTodos(todoList || []);
      setEvents(eventList || []);
      setSheetLinks(links || { payments_url: null });
      setRemindersCount(reminderList ? reminderList.filter(r => r.status === 'pending').length : 0);
      setPendingThingsCount(pendingList ? pendingList.filter(p => !p.is_completed).length : 0);
      setPayments(paymentList || []);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      // Get current user profile
      api.auth.me()
        .then(setUser)
        .catch(() => {
          api.auth.logout();
          setIsAuthenticated(false);
        });
      fetchData();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const googleToken = params.get('google_token');
    const oauthError = params.get('error');
    
    if (googleToken) {
      localStorage.setItem('google_token', googleToken);
      window.history.replaceState({}, document.title, window.location.pathname);
      navigateTo('dashboard');
      fetchData();
      alert('Google account successfully linked!');
    } else if (oauthError) {
      window.history.replaceState({}, document.title, window.location.pathname);
      alert('Google authentication failed: ' + oauthError);
    }
  }, []);

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);

    try {
      if (isRegister) {
        await api.auth.register(name, email, password);
        // Automatically login
        await api.auth.login(email, password);
      } else {
        await api.auth.login(email, password);
      }
      setIsAuthenticated(true);
      setName('');
      setEmail('');
      setPassword('');
    } catch (err) {
      setAuthError(err.message || 'Authentication failed');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setProjects([]);
    setTodos([]);
    setEvents([]);
    setActiveTab('dashboard');
  };

  return (
    <div className="app-container">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div className="mobile-sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Persistent Sidebar */}
      <aside className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="logo-container">
          <div className="logo-icon" style={{ background: 'transparent', boxShadow: 'none' }}>
            <img src="/bot icon.png" alt="Vixx" style={{ width: '100%', height: '100%', borderRadius: '8px', objectFit: 'contain' }} />
          </div>
          <span className="logo-text">Vixx</span>
        </div>

        <nav className="nav-links">
          <div className="sidebar-group-label">Core Assistant</div>
          <a 
            className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => navigateTo('dashboard')}
          >
            <Sparkles size={18} />
            Command Center
          </a>
          <a 
            className={`nav-link ${activeTab === 'files' ? 'active' : ''}`}
            onClick={() => navigateTo('files')}
          >
            <Paperclip size={18} />
            <span>Pending Things</span>
            {pendingThingsCount > 0 && <span className="nav-badge" style={{ marginLeft: 'auto', background: '#f87171', color: 'white', fontSize: '0.7rem', padding: '2px 6px', borderRadius: '10px', fontWeight: 600 }}>{pendingThingsCount}</span>}
          </a>
          <a 
            className={`nav-link ${activeTab === 'reminders' ? 'active' : ''}`}
            onClick={() => navigateTo('reminders')}
          >
            <Bell size={18} />
            <span>Reminders</span>
            {remindersCount > 0 && <span className="nav-badge" style={{ marginLeft: 'auto', background: 'var(--accent-primary)', color: 'white', fontSize: '0.7rem', padding: '2px 6px', borderRadius: '10px', fontWeight: 600 }}>{remindersCount}</span>}
          </a>

          <div className="sidebar-divider" />
          <div className="sidebar-group-label">Work & Portfolio</div>
          <a 
            className={`nav-link ${activeTab === 'projects' ? 'active' : ''}`}
            onClick={() => {
              navigateTo('projects');
            }}
          >
            <Briefcase size={18} />
            Projects
          </a>
          <a 
            className={`nav-link ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => navigateTo('reports')}
          >
            <FileText size={18} />
            Reports Engine
          </a>

          <div className="sidebar-divider" />
          <div className="sidebar-group-label">Financials</div>
          <a 
            className={`nav-link ${activeTab === 'payments' ? 'active' : ''}`}
            onClick={() => navigateTo('payments')}
          >
            <CreditCard size={18} />
            Payments & Billings
          </a>

          <div className="sidebar-divider" />
          <div className="sidebar-group-label">System</div>
          <a 
            className={`nav-link ${activeTab === 'integrations' ? 'active' : ''}`}
            onClick={() => navigateTo('integrations')}
          >
            <Link2 size={18} />
            Integrations
          </a>
        </nav>
      </aside>

      {/* Main Content Pane */}
      <main className="main-content">
        <header className="top-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {(activeTab !== 'dashboard' || selectedProjectId) && (
              <button 
                className="mobile-header-btn back-btn" 
                onClick={() => {
                  if (selectedProjectId) {
                    window.location.hash = '#/projects';
                  } else {
                    window.location.hash = '#/';
                  }
                }}
              >
                <ArrowLeft size={20} />
              </button>
            )}
            
            <h1 className="page-title">
              {activeTab === 'dashboard' && 'AI Command Center'}
              {activeTab === 'projects' && 'Projects Portfolio'}
              {activeTab === 'payments' && 'Payments & Billings'}
              {activeTab === 'reports' && 'PDF Reports & Billings Engine'}
              {activeTab === 'reminders' && 'Reminders & Alerts'}
              {activeTab === 'timeline' && 'Timeline & Milestones'}
              {activeTab === 'files' && 'Workspace Pending Things'}
              {activeTab === 'integrations' && 'Integrations'}
            </h1>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button 
              className="mobile-header-btn hamburger-btn" 
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu size={20} />
            </button>
            {!localStorage.getItem('google_token') && (
              <button
                onClick={async () => {
                  try {
                    const res = await api.sync.googleAuth();
                    if (res.url) window.location.href = res.url;
                  } catch (e) {
                    alert("Failed to initiate Google Link: " + e.message);
                  }
                }}
                className="btn btn-primary"
                style={{ fontSize: '0.8rem', padding: '8px 14px', cursor: 'pointer' }}
              >
                Link Google Account
              </button>
            )}
          </div>
        </header>

        {activeTab === 'dashboard' && isMobile && (
          <div className="mobile-dashboard-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%' }}>
            {/* Active Projects Dropdown Popup */}
            <div className="mobile-projects-dropdown-wrapper" style={{ width: '100%', position: 'relative', zIndex: 850 }}>
              <button
                type="button"
                onClick={() => setMobileProjectsOpen(!mobileProjectsOpen)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: 'rgba(18, 16, 33, 0.85)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '10px',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  backdropFilter: 'blur(10px)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Briefcase size={14} color="var(--accent-primary)" />
                  <span>Active Projects ({projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length})</span>
                </div>
                {mobileProjectsOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {mobileProjectsOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    marginTop: '6px',
                    background: 'rgba(12, 10, 24, 0.98)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '10px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                    padding: '6px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    maxHeight: '180px',
                    overflowY: 'auto',
                    backdropFilter: 'blur(20px)'
                  }}
                >
                  {projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length === 0 ? (
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', padding: '8px', textAlign: 'center' }}>No active projects found.</p>
                  ) : (
                    projects.filter(p => p.status !== 'completed' && p.status !== 'finished').map(p => (
                      <div
                        key={p.id}
                        onClick={() => {
                          window.location.hash = `#/projects/${p.id}`;
                          setMobileProjectsOpen(false);
                        }}
                        style={{
                          padding: '8px 10px',
                          background: 'rgba(255, 255, 255, 0.02)',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          color: 'var(--text-primary)',
                          fontSize: '0.78rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <span style={{ fontWeight: 500 }}>{p.title}</span>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{p.status || 'Active'}</span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Chat interface in the middle */}
            <ChatInterface onRefreshData={fetchData} />

            {/* Dashboard Analytics charts */}
            <DashboardAnalytics projects={projects} payments={payments} />

            {/* Stats Cards at the bottom */}
            <DashboardStats 
              projects={projects} 
              todos={todos} 
              events={events} 
            />
          </div>
        )}

        {activeTab === 'dashboard' && !isMobile && (
          <div className="dashboard-grid">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              <DashboardStats 
                projects={projects} 
                todos={todos} 
                events={events} 
              />
              <ChatInterface onRefreshData={fetchData} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', height: 'fit-content' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0 }}>Active Projects</h3>
                  <button
                    onClick={() => fetchData()}
                    disabled={loadingData}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '6px',
                      borderRadius: '50%',
                      transition: 'all 0.2s',
                    }}
                    className="refresh-btn"
                    title="Refresh Projects"
                  >
                    <RotateCw 
                      size={16} 
                      className={loadingData ? 'animate-spin' : ''} 
                      style={{ transition: 'transform 0.2s' }}
                    />
                  </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {loadingData ? (
                    [1, 2, 3].map(i => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                        <div className="skeleton-pulse" style={{ width: '55%', height: '14px', borderRadius: '4px' }} />
                        <div className="skeleton-pulse" style={{ width: '25%', height: '14px', borderRadius: '4px' }} />
                      </div>
                    ))
                  ) : projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length === 0 ? (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No active projects found.</p>
                  ) : (
                    projects.filter(p => p.status !== 'completed' && p.status !== 'finished').slice(0, 5).map(p => (
                      <div 
                        key={p.id} 
                        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: '8px', cursor: 'pointer' }}
                        onClick={() => {
                          window.location.hash = `#/projects/${p.id}`;
                        }}
                      >
                        <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{p.title}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Dashboard Analytics charts */}
              <DashboardAnalytics projects={projects} payments={payments} />
            </div>
          </div>
        )}

        {activeTab === 'projects' && (
          <ProjectsView 
            projects={projects} 
            onRefresh={fetchData} 
            loading={loadingData}
            selectedProject={selectedProject}
            setSelectedProject={(proj) => {
              if (proj) {
                window.location.hash = `#/projects/${proj.id}`;
              } else {
                window.location.hash = '#/projects';
              }
            }}
          />
        )}

        {activeTab === 'payments' && (
          <PaymentsView 
            projects={projects} 
            onRefresh={fetchData} 
          />
        )}

        {activeTab === 'reports' && (
          <ReportsEngineView 
            projects={projects} 
          />
        )}

        {activeTab === 'reminders' && (
          <RemindersView 
            onRefresh={fetchData} 
          />
        )}



        {activeTab === 'files' && (
          <FilesView 
            projects={projects} 
            onRefresh={fetchData} 
          />
        )}

        {activeTab === 'integrations' && (
          <IntegrationsView 
            sheetLinks={sheetLinks} 
            onRefresh={fetchData} 
            loading={loadingData}
          />
        )}
      </main>

      {/* Toast Notification Side UI */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast-card toast-${toast.type}`}>
            <div className="toast-content">
              {toast.type === 'success' && <CheckCircle size={16} className="toast-icon success" />}
              {toast.type === 'error' && <AlertCircle size={16} className="toast-icon error" />}
              {toast.type === 'info' && <Info size={16} className="toast-icon info" />}
              <span className="toast-message">{toast.message}</span>
            </div>
            <button 
              className="toast-close-btn" 
              onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
              title="Close"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Global Custom Confirm Modal */}
      {confirmConfig && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(10, 6, 22, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 99999
        }}>
          <div className="glass-panel" style={{
            width: '400px',
            padding: '28px',
            borderRadius: '16px',
            border: '1px solid rgba(139, 92, 246, 0.25)',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(139, 92, 246, 0.15)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: '20px'
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ef4444'
            }}>
              <AlertTriangle size={28} />
            </div>
            
            <div>
              <h4 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>Are you sure?</h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                {confirmConfig.message}
              </p>
            </div>
            
            <div style={{ display: 'flex', width: '100%', gap: '12px', marginTop: '4px' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setConfirmConfig(null)}
                style={{ flex: 1, padding: '10px', justifyContent: 'center', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={() => {
                  try {
                    confirmConfig.onConfirm();
                  } catch (e) {
                    console.error(e);
                  }
                  setConfirmConfig(null);
                }}
                style={{ flex: 1, background: '#ef4444', borderColor: '#ef4444', color: 'white', padding: '10px', justifyContent: 'center', cursor: 'pointer' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
