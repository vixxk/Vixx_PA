import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Home,
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
  HelpCircle,
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
  ChevronUp,
  Search,
  Clock as ClockIcon,
  Bot
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

const DashboardSkeleton = () => (
  <div className="dashboard-grid">
    {/* Left Column */}
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Morning Brief Card skeleton */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="skeleton-pulse" style={{ height: '22px', width: '220px', borderRadius: '4px' }} />
          <div className="skeleton-pulse" style={{ height: '14px', width: '140px', borderRadius: '4px' }} />
        </div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="skeleton-pulse" style={{ height: '14px', width: '14px', borderRadius: '50%', flexShrink: 0 }} />
              <div className="skeleton-pulse" style={{ height: '14px', width: `${70 + (i * 5)}%`, borderRadius: '4px' }} />
            </div>
          ))}
        </div>
      </div>

      {/* Stats Bar skeleton */}
      <div className="stats-bar">
        {[1, 2, 3].map(i => (
          <div key={i} className="glass-panel stat-card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div className="skeleton-pulse" style={{ height: '12px', width: '60px', borderRadius: '3px' }} />
            <div className="skeleton-pulse" style={{ height: '26px', width: '100px', borderRadius: '4px' }} />
          </div>
        ))}
      </div>

      {/* Chat Interface skeleton */}
      <div className="glass-panel" style={{ padding: '20px', height: '360px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div className="skeleton-pulse" style={{ height: '24px', width: '24px', borderRadius: '50%' }} />
            <div className="skeleton-pulse" style={{ height: '16px', width: '100px', borderRadius: '4px' }} />
          </div>
          <div className="skeleton-pulse" style={{ height: '24px', width: '80px', borderRadius: '6px' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, padding: '16px 0', overflow: 'hidden' }}>
          <div style={{ alignSelf: 'flex-start', display: 'flex', gap: '8px', width: '70%' }}>
            <div className="skeleton-pulse" style={{ height: '32px', width: '100%', borderRadius: '12px 12px 12px 3px' }} />
          </div>
          <div style={{ alignSelf: 'flex-end', display: 'flex', gap: '8px', width: '50%' }}>
            <div className="skeleton-pulse" style={{ height: '32px', width: '100%', borderRadius: '12px 12px 3px 12px' }} />
          </div>
          <div style={{ alignSelf: 'flex-start', display: 'flex', gap: '8px', width: '60%' }}>
            <div className="skeleton-pulse" style={{ height: '32px', width: '100%', borderRadius: '12px 12px 12px 3px' }} />
          </div>
        </div>
        <div className="skeleton-pulse" style={{ height: '40px', width: '100%', borderRadius: '10px' }} />
      </div>
    </div>

    {/* Right Column */}
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Today's Focus Priorities skeleton */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div className="skeleton-pulse" style={{ height: '14px', width: '150px', borderRadius: '4px' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[1, 2, 3].map(i => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="skeleton-pulse" style={{ height: '14px', width: '14px', borderRadius: '4px', flexShrink: 0 }} />
              <div className="skeleton-pulse" style={{ height: '14px', width: '70%', borderRadius: '4px' }} />
              <div className="skeleton-pulse" style={{ height: '12px', width: '40px', borderRadius: '3px', marginLeft: 'auto' }} />
            </div>
          ))}
        </div>
      </div>

      {/* Active Workspace Projects skeleton */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div className="skeleton-pulse" style={{ height: '14px', width: '180px', borderRadius: '4px' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="skeleton-pulse" style={{ height: '24px', width: '24px', borderRadius: '6px', flexShrink: 0 }} />
              <div className="skeleton-pulse" style={{ height: '14px', width: '60%', borderRadius: '4px' }} />
              <div className="skeleton-pulse" style={{ height: '12px', width: '50px', borderRadius: '3px', marginLeft: 'auto' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [isRegister, setIsRegister] = useState(false);
  const [user, setUser] = useState(null);
  const [showHelpModal, setShowHelpModal] = useState(false);
  
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
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [paletteSearch, setPaletteSearch] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());

  const navigateTo = (tab) => {
    window.location.hash = tab === 'dashboard' ? '#/' : `#/${tab}`;
    setActiveTab(tab);
    setSelectedProjectId(null);
    setMobileMenuOpen(false);
    setShowCommandPalette(false);
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

  // System clock timer
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Keyboard shortcut listener for CMD+K / CTRL+K & Ctrl+Alt hotkeys
  useEffect(() => {
    const handleKeyDown = (e) => {
      // 1. Toggle Command Palette with CMD+K / CTRL+K
      if ((e.metaKey || e.ctrlKey) && (e.key.toLowerCase() === 'k' || e.code === 'KeyK')) {
        e.preventDefault();
        e.stopPropagation();
        setShowCommandPalette(prev => !prev);
        return;
      }
      if (e.key === 'Escape' || e.code === 'Escape') {
        setShowCommandPalette(false);
        return;
      }

      // 2. Handle Ctrl + Alt + key
      if (e.ctrlKey && e.altKey) {
        const key = e.key.toLowerCase();
        const code = e.code;
        let matchedTab = null;
        if (code === 'KeyH' || key === 'h') matchedTab = 'dashboard';
        else if (code === 'KeyP' || key === 'p') matchedTab = 'projects';
        else if (code === 'KeyB' || key === 'b') matchedTab = 'payments';
        else if (code === 'KeyR' || key === 'r') matchedTab = 'reports';
        else if (code === 'KeyA' || key === 'a') matchedTab = 'reminders';
        else if (code === 'KeyF' || key === 'f') matchedTab = 'files';
        else if (code === 'KeyI' || key === 'i') matchedTab = 'integrations';

        if (matchedTab) {
          e.preventDefault();
          e.stopPropagation();
          navigateTo(matchedTab);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true); // Use capturing phase
    return () => {
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, []);

  const [projects, setProjects] = useState([]);
  const [todos, setTodos] = useState([]);
  const [events, setEvents] = useState([]);
  const [payments, setPayments] = useState([]);
  const [sheetLinks, setSheetLinks] = useState({ payments_url: null });
  const [remindersCount, setRemindersCount] = useState(0);
  const [pendingThingsCount, setPendingThingsCount] = useState(0);
  const [loadingData, setLoadingData] = useState(true);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
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
      setHasLoadedOnce(true);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      try {
        const u = await api.auth.me();
        setUser(u);
        await fetchData();
      } catch (err) {
        try {
          await api.auth.login('vixx@example.com', 'password');
          const u = await api.auth.me();
          setUser(u);
          await fetchData();
        } catch (loginErr) {
          try {
            await api.auth.register('Vixx OS User', 'vixx@example.com', 'password');
            await api.auth.login('vixx@example.com', 'password');
            const u = await api.auth.me();
            setUser(u);
            await fetchData();
          } catch (regErr) {
            console.error("Auto-boot authentication failure:", regErr);
          }
        }
      }
    };
    initAuth();
  }, []);

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
    api.auth.logout();
    setIsAuthenticated(false);
    setProjects([]);
    setTodos([]);
    setEvents([]);
    setActiveTab('dashboard');
  };

  // Filter Command Palette Items
  const paletteCommands = [
    { label: 'Jump to Command Center (Vixx)', tab: 'dashboard', shortcut: 'Ctrl + Alt + H', icon: Home },
    { label: 'Jump to Projects Portfolio', tab: 'projects', shortcut: 'Ctrl + Alt + P', icon: Briefcase },
    { label: 'Jump to Payments Ledger', tab: 'payments', shortcut: 'Ctrl + Alt + B', icon: CreditCard },
    { label: 'Jump to PDF Reports Engine', tab: 'reports', shortcut: 'Ctrl + Alt + R', icon: FileText },
    { label: 'Jump to Scheduled Reminders', tab: 'reminders', shortcut: 'Ctrl + Alt + A', icon: Bell },
    { label: 'Jump to Secured Pending Files', tab: 'files', shortcut: 'Ctrl + Alt + F', icon: Paperclip },
    { label: 'Jump to System Integrations', tab: 'integrations', shortcut: 'Ctrl + Alt + I', icon: Link2 },
  ];

  const filteredCommands = paletteCommands.filter(cmd => 
    cmd.label.toLowerCase().includes(paletteSearch.toLowerCase())
  );

  const filteredProjectCommands = projects.filter(p => 
    p.title.toLowerCase().includes(paletteSearch.toLowerCase())
  );



  const handleToggleTodo = async (todo) => {
    try {
      const newStatus = todo.status === 'done' ? 'pending' : 'done';
      await api.todos.update(todo.id, { status: newStatus });
      fetchData();
      alert(`Task marked as ${newStatus}!`);
    } catch (err) {
      alert("Failed to update task: " + err.message);
    }
  };

  // Active projects outstanding calculation (Fix Mismatch Bug)
  const activeProjectIds = projects
    .filter(p => p.status !== 'completed' && p.status !== 'finished')
    .map(p => p.id);
  const activeProjectsBudget = projects
    .filter(p => p.status !== 'completed' && p.status !== 'finished')
    .reduce((sum, p) => sum + parseFloat(p.total_amount || 0), 0);
  const activeReceivedPayments = payments
    .filter(p => p.status === 'received' && activeProjectIds.includes(p.project_id))
    .reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
  const activeOutstanding = Math.max(0, activeProjectsBudget - activeReceivedPayments);

  return (
    <div className="app-container">
      <div className="blob-1 aurora-blob" />
      <div className="blob-2 aurora-blob" />
      {/* 1. Top OS Command Bar */}
      <header className="top-command-bar">
        <div className="top-bar-logo">
          <div 
            onClick={() => window.location.href = '/'}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
            title="Go to Homepage"
          >
            <img src="/bot icon.png" alt="Vixx" style={{ width: '30px', height: '30px', objectFit: 'contain', borderRadius: '6px' }} />
            <span className="top-bar-logo-text">Vixx</span>
          </div>
          <div 
            onClick={() => setShowHelpModal(true)}
            style={{ 
              background: 'linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)', 
              border: '1px solid #67e8f9', 
              color: '#000', 
              cursor: 'pointer', 
              padding: '4px 12px', 
              marginLeft: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '20px',
              transition: 'all 0.2s ease',
              boxShadow: '0 0 12px rgba(6, 182, 212, 0.5)',
              fontSize: '0.72rem',
              fontWeight: 800,
              letterSpacing: '0.02em',
              whiteSpace: 'nowrap'
            }}
            onMouseEnter={e => { 
              e.currentTarget.style.background = 'linear-gradient(135deg, #67e8f9 0%, #22d3ee 100%)'; 
              e.currentTarget.style.boxShadow = '0 0 18px rgba(6, 182, 212, 0.8)'; 
              e.currentTarget.style.transform = 'scale(1.04)'; 
            }}
            onMouseLeave={e => { 
              e.currentTarget.style.background = 'linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)'; 
              e.currentTarget.style.boxShadow = '0 0 12px rgba(6, 182, 212, 0.5)'; 
              e.currentTarget.style.transform = 'scale(1)'; 
            }}
            title="What can Vixx do?"
          >
            What can Vixx do?
          </div>
        </div>

        {/* Global CMD+K Search trigger pill */}
        <div className="top-bar-search-pill" onClick={() => setShowCommandPalette(true)}>
          <Search size={14} />
          <span>Search or trigger commands...</span>
          <span className="search-shortcut-label">⌘K</span>
        </div>

        <div className="top-bar-system-info">
          {/* Clock widget */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'monospace' }}>
            <ClockIcon size={14} color="var(--accent-primary)" />
            <span>{currentTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
          </div>

          <div style={{ width: '1px', height: '14px', background: 'rgba(255, 255, 255, 0.1)' }} />

          {/* Sync status */}
          {localStorage.getItem('google_token') ? (
            <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
              <CheckCircle size={12} /> Synced
            </span>
          ) : (
            <button 
              onClick={async () => {
                try {
                  const res = await api.sync.googleAuth();
                  if (res.url) window.location.href = res.url;
                } catch (e) {
                  alert("Google sync error: " + e.message);
                }
              }}
              style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', color: 'var(--text-secondary)', fontSize: '0.72rem', padding: '3px 8px', borderRadius: '6px', cursor: 'pointer' }}
            >
              Sync Calendar
            </button>
          )}

          <div style={{ width: '1px', height: '14px', background: 'rgba(255, 255, 255, 0.1)' }} />

          {/* User profile dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{user?.name || 'Developer'}</span>
          </div>
        </div>
      </header>

      {/* 2. Main Workspace Canvas */}
      <main className="main-content">
        {/* Render Back Button if nested inside a Project details view */}
        {selectedProjectId && (
          <div style={{ marginBottom: '4px' }}>
            <button 
              className="btn btn-secondary" 
              onClick={() => { window.location.hash = '#/projects'; }}
              style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: '8px' }}
            >
              <ArrowLeft size={14} /> Back to Portfolio
            </button>
          </div>
        )}

        {/* Tab content renderer */}
        {activeTab === 'dashboard' && (
          (loadingData && !hasLoadedOnce) ? (
            <DashboardSkeleton />
          ) : (
            <div className="dashboard-grid">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* Morning Brief Card */}
                <div className="glass-panel glow-panel-purple" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#fff' }}>
                      Welcome to Vixx Workspace Brief
                    </h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                      {currentTime.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                    </p>
                  </div>

                  <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Sparkles size={14} color="var(--accent-primary)" />
                      <span>Vixx Command Assistant is online. Try typing tasks, asking queries, or recording audio briefs below.</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Briefcase size={14} color="var(--accent-secondary)" />
                      <span>You have <strong>{projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length} active projects</strong> in development.</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <AlertCircle size={14} color="var(--accent-cyan)" />
                      <span>Outstanding pipeline balance: <strong style={{ color: '#fff' }}>₹{activeOutstanding.toLocaleString()}</strong> (from ₹{activeProjectsBudget.toLocaleString()} total active budgets).</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CheckCircle size={14} color="#34d399" />
                      <span>Google Calendar sync is functional. Current milestones are actively updating.</span>
                    </div>
                  </div>
                </div>

                {/* Dynamic stats row */}
                <DashboardStats 
                  projects={projects} 
                  todos={todos} 
                  events={events} 
                />
                
                {/* Main Vixx AI Chat console */}
                <ChatInterface 
                  projects={projects} 
                  todos={todos} 
                  payments={payments}
                  onRefreshData={fetchData} 
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* Today's Focus Priorities Checklist */}
                <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <h3 style={{ fontSize: '0.92rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                    Today's Focus Priorities
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {todos.filter(t => t.status !== 'done').length === 0 ? (
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>No pending tasks today. Nice job!</span>
                    ) : (
                      todos.filter(t => t.status !== 'done').slice(0, 3).map(todo => (
                        <div 
                          key={todo.id}
                          style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '4px 0' }}
                        >
                          <div 
                            onClick={() => handleToggleTodo(todo)}
                            style={{ 
                              cursor: 'pointer', 
                              width: '14px', 
                              height: '14px', 
                              borderRadius: '4px', 
                              border: todo.status === 'done' ? '1px solid var(--accent-primary)' : '1px solid rgba(255,255,255,0.25)', 
                              background: todo.status === 'done' ? 'var(--accent-primary)' : 'transparent',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0
                            }}
                          >
                            {todo.status === 'done' && (
                              <svg width="8" height="8" viewBox="0 0 8 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M1.5 4.5L3 6L6.5 2" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                              </svg>
                            )}
                          </div>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)', textDecoration: todo.status === 'done' ? 'line-through' : 'none' }}>
                            {todo.title}
                          </span>
                          <span className={`badge badge-${todo.priority || 'medium'}`} style={{ fontSize: '0.58rem', marginLeft: 'auto', padding: '1px 4px' }}>
                            {todo.priority || 'medium'}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Quick active projects navigation */}
                <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ fontSize: '0.92rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                      Active Workspace Projects
                    </h3>
                    <button 
                      onClick={fetchData} 
                      disabled={loadingData}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    >
                      <RotateCw size={14} className={loadingData ? 'animate-spin' : ''} />
                    </button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length === 0 ? (
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>No active projects found.</span>
                    ) : (
                      projects.filter(p => p.status !== 'completed' && p.status !== 'finished').map(proj => (
                        <div 
                          key={proj.id}
                          onClick={() => { window.location.hash = `#/projects/${proj.id}`; }}
                          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.04)', cursor: 'pointer', transition: 'all 0.2s' }}
                          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.2)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'; }}
                          onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.04)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'; }}
                        >
                          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{proj.title}</span>
                          <span className={`badge badge-${proj.status === 'developing' ? 'active' : 'planning'}`} style={{ fontSize: '0.62rem' }}>{proj.status}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Financial health and SVG Progress Charts */}
                <DashboardAnalytics projects={projects} payments={payments} />
              </div>
            </div>
          )
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

      {/* 3. Persistent Floating Desktop Dock */}
      <div className="floating-dock-container">
        <div className="floating-dock">
          {[
            { id: 'dashboard', name: 'Command Center', icon: Home },
            { id: 'projects', name: 'Projects Portfolio', icon: Briefcase },
            { id: 'payments', name: 'Payments & Ledger', icon: CreditCard },
            { id: 'reports', name: 'PDF Reports', icon: FileText },
            { id: 'reminders', name: 'Reminders Center', icon: Bell, count: remindersCount },
            { id: 'files', name: 'Pending Items', icon: Paperclip, count: pendingThingsCount },
            { id: 'integrations', name: 'Google Integration', icon: Link2 }
          ].map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <div 
                key={item.id}
                onClick={() => navigateTo(item.id)}
                className={`dock-item ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} />
                {isActive && <div className="dock-item-dot" />}
                {item.count > 0 && <span className="dock-badge">{item.count}</span>}
                <span className="dock-tooltip">{item.name}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. CMD+K / CTRL+K Command Palette Modal Overlay */}
      {showCommandPalette && (
        <div className="command-palette-overlay" onClick={() => setShowCommandPalette(false)}>
          <div className="command-palette" onClick={e => e.stopPropagation()}>
            <div className="command-palette-search">
              <Search size={18} color="var(--text-muted)" />
              <input 
                type="text" 
                className="command-palette-input" 
                placeholder="Search workspaces, triggers, and configurations..."
                value={paletteSearch}
                onChange={e => setPaletteSearch(e.target.value)}
                autoFocus
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px' }}>ESC</span>
            </div>

            <div className="command-palette-results">
              {/* Commands Section */}
              <div className="command-section-title">Navigation Triggers</div>
              {filteredCommands.length === 0 ? (
                <div style={{ padding: '8px 12px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>No matches found.</div>
              ) : (
                filteredCommands.map((cmd, idx) => {
                  const Icon = cmd.icon;
                  return (
                    <div 
                      key={idx}
                      className="command-item"
                      onClick={() => navigateTo(cmd.tab)}
                    >
                      <span className="command-item-label">
                        <Icon size={14} color="var(--accent-primary)" />
                        {cmd.label}
                      </span>
                      <span className="command-item-shortcut">{cmd.shortcut}</span>
                    </div>
                  );
                })
              )}

              {/* Active Projects Selection Section */}
              <div className="command-section-title" style={{ marginTop: '10px' }}>Active Projects</div>
              {filteredProjectCommands.length === 0 ? (
                <div style={{ padding: '8px 12px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>No projects matching query.</div>
              ) : (
                filteredProjectCommands.map((proj, idx) => (
                  <div 
                    key={idx}
                    className="command-item"
                    onClick={() => {
                      window.location.hash = `#/projects/${proj.id}`;
                      setShowCommandPalette(false);
                    }}
                  >
                    <span className="command-item-label">
                      <Briefcase size={14} color="var(--accent-secondary)" />
                      Open Workspace: {proj.title}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{proj.status}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification HUD */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast-card toast-${toast.type}`}>
            <div className="toast-content">
              {toast.type === 'success' && <CheckCircle size={14} className="toast-icon success" />}
              {toast.type === 'error' && <AlertCircle size={14} className="toast-icon error" />}
              {toast.type === 'info' && <Info size={14} className="toast-icon info" />}
              <span className="toast-message">{toast.message}</span>
            </div>
            <button 
              className="toast-close-btn" 
              onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
              title="Close toast"
            >
              <X size={12} />
            </button>
          </div>
        ))}
      </div>

      {/* Universal Modal Overlay */}
      {confirmConfig && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(5, 4, 9, 0.85)',
          backdropFilter: 'blur(16px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 99999
        }}>
          <div className="glass-panel" style={{
            width: '380px',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            boxShadow: '0 20px 48px rgba(0, 0, 0, 0.8), 0 0 30px rgba(239, 68, 68, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ef4444'
            }}>
              <AlertTriangle size={24} />
            </div>
            
            <div>
              <h4 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '6px', color: '#fff' }}>Confirm Destructive Action</h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
                {confirmConfig.message}
              </p>
            </div>
            
            <div style={{ display: 'flex', width: '100%', gap: '10px', marginTop: '4px' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setConfirmConfig(null)}
                style={{ flex: 1, padding: '9px', justifyContent: 'center' }}
              >
                Cancel
              </button>
              <button 
                className="btn" 
                onClick={() => {
                  try {
                    confirmConfig.onConfirm();
                  } catch (e) {
                    console.error(e);
                  }
                  setConfirmConfig(null);
                }}
                style={{ flex: 1, background: '#ef4444', borderColor: '#ef4444', color: 'white', padding: '9px', justifyContent: 'center' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Help / Capabilities Modal */}
      {showHelpModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(5, 4, 9, 0.85)',
          backdropFilter: 'blur(16px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 99999
        }} onClick={() => setShowHelpModal(false)}>
          <div className="glass-panel" style={{
            width: '420px',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 20px 48px rgba(0, 0, 0, 0.8), 0 0 30px rgba(139, 92, 246, 0.15)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Bot size={18} color="var(--accent-primary)" style={{ filter: 'drop-shadow(0 0 6px var(--accent-primary))' }} />
                <h4 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: '#fff' }}>What Vixx Can Do</h4>
              </div>
              <button 
                onClick={() => setShowHelpModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                title="Close"
              >
                <X size={18} />
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '4px' }}>
              {[
                "Send email reminders & SMS alerts",
                "Sync Google Calendar for schedules",
                "Robust project, operational, and financial transaction tracking",
                "Intelligent voice commands and transcription automation",
                "On-demand PDF summary and metrics report generation"
              ].map((capability, idx) => (
                <div key={idx} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: 'rgba(139, 92, 246, 0.15)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    color: 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    flexShrink: 0
                  }}>
                    {idx + 1}
                  </div>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: '1.4' }}>
                    {capability}
                  </span>
                </div>
              ))}
            </div>

            <button 
              className="btn btn-secondary" 
              onClick={() => setShowHelpModal(false)}
              style={{ width: '100%', padding: '10px', justifyContent: 'center', marginTop: '8px' }}
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
