import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  AlertCircle, 
  CheckCircle2, 
  Brain, 
  ChevronDown, 
  ChevronUp, 
  Copy, 
  Download,
  Plus,
  Trash2,
  Pencil,
  Check,
  X,
  Mic,
  Square,
  Paperclip,
  Calendar,
  CreditCard,
  Folder,
  User,
  Clock,
  ArrowRight,
  TrendingUp,
  Volume2,
  Menu
} from 'lucide-react';
import { api } from '../services/api';

export default function ChatInterface({ projects = [], todos = [], payments = [], onRefreshData }) {
  // 1. Local Storage Persistent State
  const [conversations, setConversations] = useState(() => {
    try {
      const saved = localStorage.getItem('vixx_conversations');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const activeHasMessages = parsed.filter(c => c.messages.length > 1 || c.title !== 'New Chat');
          if (activeHasMessages.length > 0) return activeHasMessages;
          return parsed;
        }
      }
    } catch (e) {
      console.error("Error reading conversations:", e);
    }
    return [
      {
        id: 'default',
        title: 'System Boot Chat',
        messages: [
          {
            id: 'welcome',
            sender: 'assistant',
            text: "Welcome to Vixx Workspace. I am your resident AI agent. Ask me to draft proposals, schedule WhatsApp rules (e.g. 'schedule alert for payments'), track financials, or prioritize active sprint checklists.",
            type: 'normal'
          }
        ],
        createdAt: new Date().toISOString()
      }
    ];
  });

  const [activeChatId, setActiveChatId] = useState(() => {
    const savedActive = localStorage.getItem('vixx_active_chat_id');
    return savedActive || 'default';
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedThoughts, setExpandedThoughts] = useState({});
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const editInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const chatMessagesRef = useRef(null);
  
  // Selected Project Context state (Default to 'all' projects)
  const [selectedContextId, setSelectedContextId] = useState('all');
  
  // Custom dropdown and sidebar toggle states
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const [copiedMessageId, setCopiedMessageId] = useState(null);
  const [chatCopied, setChatCopied] = useState(false);

  const handleCopyText = (text, msgId) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(msgId);
    setTimeout(() => {
      setCopiedMessageId(null);
    }, 2000);
  };

  const handleCopyWholeChat = () => {
    if (!messages || messages.length === 0) return;
    const textTranscript = messages.map(msg => {
      const senderName = msg.sender === 'user' ? 'User' : 'Vixx';
      return `${senderName}: ${msg.text}`;
    }).join('\n\n');
    
    navigator.clipboard.writeText(textTranscript);
    setChatCopied(true);
    setTimeout(() => {
      setChatCopied(false);
    }, 2000);
  };

  // Voice Mode interface state
  const [voiceModeActive, setVoiceModeActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem('vixx_conversations', JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    localStorage.setItem('vixx_active_chat_id', activeChatId);
  }, [activeChatId]);

  // Handle click outside custom dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load sessions from database on mount
  useEffect(() => {
    const fetchDbSessions = async () => {
      try {
        const dbSessions = await api.ai.listSessions();
        if (Array.isArray(dbSessions) && dbSessions.length > 0) {
          setConversations(dbSessions);
          const savedActive = localStorage.getItem('vixx_active_chat_id');
          if (savedActive && dbSessions.some(c => c.id === savedActive)) {
            setActiveChatId(savedActive);
          } else {
            setActiveChatId(dbSessions[0].id);
          }
        }
      } catch (err) {
        console.error("Error fetching sessions from database:", err);
      }
    };
    fetchDbSessions();
  }, []);

  // Set default project context
  useEffect(() => {
    if (!selectedContextId) {
      setSelectedContextId('all');
    }
  }, [selectedContextId]);

  const activeConv = conversations.find(c => c.id === activeChatId) || conversations[0] || { messages: [] };
  const messages = activeConv.messages;

  const setMessages = (updateFn) => {
    setConversations(prevConvs => {
      return prevConvs.map(c => {
        if (c.id === activeChatId) {
          const newMsgs = typeof updateFn === 'function' ? updateFn(c.messages) : updateFn;
          return { ...c, messages: newMsgs };
        }
        return c;
      });
    });
  };

  const handleCreateNewChat = () => {
    const newId = 'chat_' + Date.now();
    const newChat = {
      id: newId,
      title: 'New Session',
      messages: [
        {
          id: 'welcome',
          sender: 'assistant',
          text: "Vixx AI memory ready. Ask me to list invoices, track schedules, or prioritize backlog sprints.",
          type: 'normal'
        }
      ],
      createdAt: new Date().toISOString()
    };
    setConversations(prev => [newChat, ...prev]);
    setActiveChatId(newId);
  };

  const handleDeleteChat = (id) => {
    window.showConfirm("Delete this workspace conversation history?", async () => {
      try {
        await api.ai.deleteSession(id);
      } catch (err) {
        console.error("Error deleting session in DB:", err);
      }

      setConversations(prev => {
        const filtered = prev.filter(c => c.id !== id);
        if (filtered.length === 0) {
          const newDefaultId = 'default_' + Date.now();
          setActiveChatId(newDefaultId);
          return [
            {
              id: newDefaultId,
              title: 'New Session',
              messages: [
                {
                  id: 'welcome',
                  sender: 'assistant',
                  text: "Vixx AI memory ready. Ask me to list invoices, track schedules, or prioritize backlog sprints.",
                  type: 'normal'
                }
              ],
              createdAt: new Date().toISOString()
            }
          ];
        }
        if (activeChatId === id) {
          setActiveChatId(filtered[0].id);
        }
        return filtered;
      });
    });
  };

  const handleSaveRename = async () => {
    if (editingChatId && editingTitle.trim()) {
      const newTitle = editingTitle.trim();
      try {
        await api.ai.renameSession(editingChatId, newTitle);
      } catch (err) {
        console.error("Error renaming session in DB:", err);
      }

      setConversations(prev =>
        prev.map(c =>
          c.id === editingChatId ? { ...c, title: newTitle } : c
        )
      );
    }
    setEditingChatId(null);
    setEditingTitle('');
  };

  const toggleThoughts = (msgId) => {
    setExpandedThoughts(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  const scrollToBottom = () => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTo({
        top: chatMessagesRef.current.scrollHeight,
        behavior: 'smooth'
      });
    } else {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
    const timer = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timer);
  }, [messages, loading, expandedThoughts]);

  const sendMessage = async (userText) => {
    setLoading(true);
    setConversations(prevConvs => {
      return prevConvs.map(c => {
        if (c.id === activeChatId) {
          let newTitle = c.title;
          if (c.title === "New Session" || c.title === "New Chat") {
            newTitle = userText.length > 20 ? userText.substring(0, 18) + "..." : userText;
            api.ai.renameSession(c.id, newTitle).catch(e => console.error("Auto-rename failed in DB:", e));
          }
          return {
            ...c,
            title: newTitle,
            messages: [
              ...c.messages,
              { id: Date.now().toString(), sender: 'user', text: userText }
            ]
          };
        }
        return c;
      });
    });

    try {
      const googleToken = localStorage.getItem('google_token');
      const response = await api.ai.process(userText, googleToken, activeChatId);
      const responseMsgId = (Date.now() + 1).toString();
      
      if (response.needs_clarification) {
        setMessages((prev) => [
          ...prev,
          {
            id: responseMsgId,
            sender: 'assistant',
            text: response.clarification_message,
            type: 'clarification',
            missingFields: response.missing_fields,
            reasoningSteps: response.reasoning_steps
          }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: responseMsgId,
            sender: 'assistant',
            text: response.summary || "Action executed successfully.",
            type: 'success',
            reasoningSteps: response.reasoning_steps
          }
        ]);
        if (onRefreshData) onRefreshData();
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'assistant',
          text: `Configuration issue: ${error.message || 'Check your keys.'}`,
          type: 'error'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput('');
    await sendMessage(userText);
  };

  // Voice recording handlers
  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        setLoading(true);
        if (window.showToast) window.showToast('AI Transcribing...', 'info');
        
        try {
          const res = await api.ai.transcribe(audioBlob);
          if (res && res.text) {
            setInput(res.text);
            setVoiceModeActive(false);
            if (window.showToast) window.showToast('Voice transcribed!', 'success');
          } else {
            if (window.showToast) window.showToast('Speech not clear.', 'error');
          }
        } catch (err) {
          if (window.showToast) window.showToast(err.message, 'error');
        } finally {
          setLoading(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      timerRef.current = setInterval(() => setRecordingDuration(prev => prev + 1), 1000);
    } catch (e) {
      alert("Microphone connection failed.");
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // Checklist handler
  const handleToggleTask = async (task) => {
    try {
      const nextStatus = task.status === 'done' ? 'pending' : 'done';
      await api.todos.update(task.id, { status: nextStatus });
      if (onRefreshData) onRefreshData();
    } catch (e) {
      alert("Failed to toggle: " + e.message);
    }
  };

  const isAllContext = selectedContextId === 'all';

  // Selected project details (handle 'all' context dynamically)
  const activeProjContext = isAllContext
    ? {
        title: 'All Workspaces',
        client_name: `${projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length} Active`,
        total_amount: projects.filter(p => p.status !== 'completed' && p.status !== 'finished').reduce((sum, p) => sum + parseFloat(p.total_amount || 0), 0),
        status: 'active'
      }
    : (projects.find(p => p.id === selectedContextId) || null);

  // Filter tasks & payments for the right side context
  const activeProjTasks = isAllContext
    ? todos.filter(t => t.status !== 'done').slice(0, 4)
    : (activeProjContext ? todos.filter(t => t.project_id === activeProjContext.id && t.status !== 'done').slice(0, 4) : []);

  const activeProjPayments = isAllContext
    ? payments.slice(0, 3)
    : (activeProjContext ? payments.filter(p => p.project_id === activeProjContext.id).slice(0, 3) : []);

  const formatAmount = (val) => {
    return parseFloat(val || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
  };

  const renderInlineFormatting = (str) => {
    if (!str) return '';
    const regex = /(\*\*.*?\*\*|`.*?`)/g;
    const parts = str.split(regex);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={idx} style={{ fontWeight: '700', color: '#fff' }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={idx} style={{ 
            background: 'rgba(255,255,255,0.06)', 
            padding: '2px 6px', 
            borderRadius: '4px', 
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            color: '#f43f5e',
            border: '1px solid rgba(255,255,255,0.04)'
          }}>
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  const renderFormattedText = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, lineIdx) => {
      // Parse markdown links (e.g. [Label](url)) and render as high-fidelity buttons
      const match = line.match(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/);
      if (match) {
        const label = match[1];
        const url = match[2];
        const isDownload = label.toLowerCase().includes('download') || url.toLowerCase().endsWith('.pdf');
        
        return (
          <div key={lineIdx} style={{ margin: '12px 0' }}>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                textDecoration: 'none',
                fontWeight: 600,
                fontSize: '0.82rem',
                background: isDownload ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
                color: '#fff',
                borderRadius: '8px',
                transition: 'all 0.2s ease',
                boxShadow: isDownload ? '0 4px 15px rgba(16, 185, 129, 0.2)' : '0 4px 15px rgba(139, 92, 246, 0.2)',
                cursor: 'pointer',
                border: 'none'
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.filter = 'brightness(1.1)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.filter = 'none';
              }}
            >
              <Download size={14} />
              <span>{label}</span>
            </a>
          </div>
        );
      }

      if (line.startsWith('### ')) {
        return (
          <h3 key={lineIdx} style={{ 
            fontSize: '1rem', 
            fontWeight: '600', 
            color: '#fff', 
            margin: '12px 0 6px 0',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            paddingBottom: '4px'
          }}>
            {renderInlineFormatting(line.substring(4))}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={lineIdx} style={{ 
            fontSize: '1.15rem', 
            fontWeight: '600', 
            color: '#fff', 
            margin: '16px 0 8px 0',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            paddingBottom: '4px'
          }}>
            {renderInlineFormatting(line.substring(3))}
          </h2>
        );
      }
      if (line.startsWith('# ')) {
        return (
          <h1 key={lineIdx} style={{ 
            fontSize: '1.3rem', 
            fontWeight: '700', 
            color: '#fff', 
            margin: '20px 0 10px 0' 
          }}>
            {renderInlineFormatting(line.substring(2))}
          </h1>
        );
      }
      if (line.trim().startsWith('- ')) {
        return (
          <div key={lineIdx} style={{ 
            display: 'flex', 
            alignItems: 'flex-start', 
            gap: '8px', 
            margin: '4px 0 4px 12px',
            fontSize: '0.86rem',
            color: 'var(--text-secondary)'
          }}>
            <span style={{ color: 'var(--accent-primary)', fontSize: '1rem', lineHeight: '1.2' }}>•</span>
            <div style={{ flex: 1 }}>{renderInlineFormatting(line.trim().substring(2))}</div>
          </div>
        );
      }
      if (line.trim() === '') {
        return <div key={lineIdx} style={{ height: '8px' }} />;
      }
      return (
        <p key={lineIdx} style={{ 
          margin: '0 0 6px 0', 
          fontSize: '0.86rem', 
          color: 'var(--text-secondary)',
          lineHeight: '1.5'
        }}>
          {renderInlineFormatting(line)}
        </p>
      );
    });
  };

  return (
    <div className="glass-panel" style={{ 
      display: 'grid', 
      gridTemplateColumns: sidebarOpen ? '240px 1fr 280px' : '1fr 280px', 
      height: '620px', 
      overflow: 'hidden', 
      background: '#13131a',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      boxShadow: '0 30px 80px rgba(0,0,0,0.9)'
    }}>
      <style>{`
        .ai-workspace-sidebar {
          border-right: 1px solid rgba(255,255,255,0.03);
          background: #171720;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .ai-workspace-chat {
          display: flex;
          flex-direction: column;
          height: 100%;
          min-height: 0;
          position: relative;
          background: #0e0e13;
        }
        .ai-workspace-context {
          border-left: 1px solid rgba(255,255,255,0.03);
          background: #171720;
          padding: 20px 16px;
          display: flex;
          flex-direction: column;
          gap: 20px;
          overflow-y: auto;
        }
        .whisper-orb-container {
          position: absolute;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(9, 9, 11, 0.95);
          z-index: 10;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 20px;
        }
        .voice-pulse-orb {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          background: radial-gradient(circle, var(--accent-primary) 0%, var(--accent-secondary) 100%);
          box-shadow: 0 0 40px rgba(139, 92, 246, 0.6);
          animation: recordPulse 2s infinite ease-in-out;
        }
        .suggestion-prompt-card {
          padding: 12px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.04);
          border-radius: 10px;
          font-size: 0.76rem;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: left;
        }
        .suggestion-prompt-card:hover {
          background: rgba(255, 255, 255, 0.04);
          border-color: rgba(139, 92, 246, 0.3);
          color: #fff;
          transform: translateY(-2px);
        }
        .timeline-step {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.72rem;
          font-family: monospace;
          color: var(--text-muted);
        }
        .timeline-step.completed {
          color: var(--accent-cyan);
        }
        .timeline-step.active {
          color: #fff;
          animation: pulse 1.2s infinite;
        }
        .memory-sessions-list::-webkit-scrollbar {
          width: 5px !important;
          display: block !important;
        }
        .memory-sessions-list::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.01) !important;
        }
        .memory-sessions-list::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.12) !important;
          border-radius: 4px !important;
        }
        .memory-sessions-list::-webkit-scrollbar-thumb:hover {
          background: var(--accent-primary) !important;
        }
      `}</style>

      {/* COLUMN 1: Pinned Sessions & History Drawer */}
      {sidebarOpen && (
        <div className="ai-workspace-sidebar">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Memory Session</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button 
                onClick={handleCreateNewChat}
                style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                title="Start new chat workspace"
              >
                <Plus size={15} />
              </button>
              <button
                onClick={() => setSidebarOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                title="Hide sidebar history"
              >
                <X size={15} />
              </button>
            </div>
          </div>

          <div className="memory-sessions-list" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {conversations.map(c => {
              const isActive = c.id === activeChatId;
              const isEditing = editingChatId === c.id;
              return (
                <div 
                  key={c.id}
                  onClick={() => !isEditing && setActiveChatId(c.id)}
                  style={{
                    padding: '10px',
                    borderRadius: '8px',
                    background: isActive ? 'rgba(255,255,255,0.03)' : 'transparent',
                    border: isActive ? '1px solid rgba(255,255,255,0.05)' : '1px solid transparent',
                    cursor: isEditing ? 'default' : 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.8rem',
                    color: isActive ? '#fff' : 'var(--text-secondary)',
                    transition: 'all 0.15s'
                  }}
                >
                  {isEditing ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', width: '100%' }} onClick={e => e.stopPropagation()}>
                      <input 
                        type="text"
                        value={editingTitle}
                        onChange={e => setEditingTitle(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter') handleSaveRename();
                          if (e.key === 'Escape') { setEditingChatId(null); setEditingTitle(''); }
                        }}
                        onBlur={handleSaveRename}
                        autoFocus
                        style={{
                          background: 'rgba(255,255,255,0.06)',
                          border: '1px solid var(--accent-primary)',
                          borderRadius: '4px',
                          color: '#fff',
                          fontSize: '0.75rem',
                          padding: '4px 6px',
                          width: '100%',
                          outline: 'none'
                        }}
                      />
                    </div>
                  ) : (
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis', flex: 1 }}>
                        <Sparkles size={12} color={isActive ? 'var(--accent-primary)' : 'var(--text-muted)'} />
                        <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{c.title}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }} onClick={e => e.stopPropagation()}>
                        <button 
                          onClick={(e) => { e.stopPropagation(); setEditingChatId(c.id); setEditingTitle(c.title); }}
                          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                          title="Rename session"
                          onMouseEnter={e => e.currentTarget.style.color = '#fff'}
                          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                        >
                          <Pencil size={11} />
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleDeleteChat(c.id); }}
                          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                          title="Delete session"
                          onMouseEnter={e => e.currentTarget.style.color = '#ef4444'}
                          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                        >
                          <Trash2 size={11} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            <Brain size={12} color="var(--accent-primary)" />
            <span>Workspace context active</span>
          </div>
        </div>
      )}

      {/* COLUMN 2: Message Workspace & Floating Composer */}
      <div className="ai-workspace-chat">
        
        {/* Floating Voice Mode Orb Overlay */}
        {voiceModeActive && (
          <div className="whisper-orb-container">
            <h3 style={{ fontSize: '1rem', color: '#fff' }}>Futuristic Whisper Mode</h3>
            <div className="voice-pulse-orb" />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {isRecording ? `Listening... ${recordingDuration}s` : 'Processing transcription...'}
            </span>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              {isRecording ? (
                <button className="btn" onClick={stopVoiceRecording} style={{ background: '#ef4444', color: '#fff' }}>
                  <Square size={14} /> Stop & Transcribe
                </button>
              ) : (
                <button className="btn btn-primary" onClick={startVoiceRecording}>
                  <Mic size={14} /> Start Speak
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setVoiceModeActive(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Minimal Chat Header */}
        <div style={{
          padding: '12px 18px',
          borderBottom: '1px solid rgba(255,255,255,0.03)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(9, 9, 11, 0.1)',
          zIndex: 40
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: '6px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginRight: '8px',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'; e.currentTarget.style.color = '#fff'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                title="Show history sidebar"
              >
                <Menu size={14} />
                <span style={{ fontSize: '0.72rem' }}>History</span>
              </button>
            )}
            <div>
              <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>Active AI Model</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fff', fontSize: '0.82rem', fontWeight: 600 }}>
                <Brain size={12} color="var(--accent-cyan)" />
                <span>Vixx-Groq-Llama3</span>
              </div>
            </div>
          </div>

          {/* Header controls: Copy Chat & Dropdown Workspace Context */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              onClick={handleCopyWholeChat}
              disabled={!messages || messages.length === 0}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '8px',
                color: chatCopied ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                fontSize: '0.72rem',
                padding: '6px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                cursor: (!messages || messages.length === 0) ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                height: '30px',
                opacity: (!messages || messages.length === 0) ? 0.5 : 1
              }}
              onMouseEnter={e => { 
                if (messages && messages.length > 0) {
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)'; 
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'; 
                }
              }}
              onMouseLeave={e => { 
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)'; 
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; 
              }}
              title="Copy entire conversation to clipboard"
            >
              {chatCopied ? (
                <>
                  <Check size={12} color="var(--accent-cyan)" />
                  <span>Copied Chat!</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
                  <span>Copy Chat</span>
                </>
              )}
            </button>

            {/* Enhanced custom dropdown UI */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', position: 'relative' }} ref={dropdownRef}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Workspace:</span>
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '0.75rem',
                  padding: '6px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  outline: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  minWidth: '130px',
                  justifyContent: 'space-between',
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)'
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)'; e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; }}
              >
                <span style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100px' }}>
                  {selectedContextId === 'all' ? 'All Workspaces' : (projects.find(p => p.id === selectedContextId)?.title || 'Select Project')}
                </span>
                <ChevronDown size={12} style={{ transition: 'transform 0.2s', transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0)' }} />
              </button>

              {dropdownOpen && (
                <div style={{
                  position: 'absolute',
                  top: 'calc(100% + 6px)',
                  right: 0,
                  width: '180px',
                  background: 'rgba(20, 20, 26, 0.98)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '10px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.5), 0 0 15px rgba(139,92,246,0.05)',
                  zIndex: 100,
                  padding: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  backdropFilter: 'blur(12px)'
                }}>
                  <button
                    type="button"
                    onClick={() => { setSelectedContextId('all'); setDropdownOpen(false); }}
                    style={{
                      background: selectedContextId === 'all' ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                      border: 'none',
                      borderRadius: '6px',
                      color: selectedContextId === 'all' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      fontSize: '0.75rem',
                      padding: '8px 10px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      width: '100%',
                      transition: 'all 0.15s',
                      fontWeight: selectedContextId === 'all' ? 600 : 400
                    }}
                    onMouseEnter={e => { if (selectedContextId !== 'all') { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.color = '#fff'; } }}
                    onMouseLeave={e => { if (selectedContextId !== 'all') { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
                  >
                    <span>All Workspaces</span>
                    {selectedContextId === 'all' && <Check size={12} />}
                  </button>

                  {projects.map(p => {
                    const isSelected = selectedContextId === p.id;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => { setSelectedContextId(p.id); setDropdownOpen(false); }}
                        style={{
                          background: isSelected ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                          border: 'none',
                          borderRadius: '6px',
                          color: isSelected ? 'var(--accent-primary)' : 'var(--text-secondary)',
                          fontSize: '0.75rem',
                          padding: '8px 10px',
                          textAlign: 'left',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          width: '100%',
                          transition: 'all 0.15s',
                          fontWeight: isSelected ? 600 : 400
                        }}
                        onMouseEnter={e => { if (!isSelected) { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.color = '#fff'; } }}
                        onMouseLeave={e => { if (!isSelected) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
                      >
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '130px' }}>{p.title}</span>
                        {isSelected && <Check size={12} />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Messages Stream */}
        <div className="chat-messages" ref={chatMessagesRef} style={{ flex: 1, padding: '20px 24px', overflowY: 'auto', minHeight: 0 }}>
          {messages.map((msg, mIdx) => {
            const isUser = msg.sender === 'user';
            return (
              <div 
                key={msg.id || mIdx}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                  marginBottom: '20px',
                  width: '100%'
                }}
              >
                {isUser ? (
                  /* User Pill design */
                  <div style={{
                    padding: '10px 16px',
                    borderRadius: '16px 16px 2px 16px',
                    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(99, 102, 241, 0.18) 100%)',
                    border: '1px solid rgba(139, 92, 246, 0.4)',
                    color: '#fff',
                    fontSize: '0.85rem',
                    maxWidth: '80%',
                    boxShadow: '0 4px 15px rgba(139, 92, 246, 0.1)',
                    lineHeight: '1.4'
                  }}>
                    {msg.text}
                  </div>
                ) : (
                  /* Assistant inline content blocks (Card Bubble) */
                  <div style={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: '12px', 
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    borderLeft: '3px solid var(--accent-primary)',
                    borderRadius: '12px',
                    padding: '16px',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Sparkles size={14} color="var(--accent-primary)" />
                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Vixx</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleCopyText(msg.text, msg.id || mIdx)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: copiedMessageId === (msg.id || mIdx) ? 'var(--accent-cyan)' : 'var(--text-muted)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '0.7rem',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          transition: 'all 0.25s'
                        }}
                        onMouseEnter={e => { e.currentTarget.style.color = '#fff'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                        onMouseLeave={e => { e.currentTarget.style.color = copiedMessageId === (msg.id || mIdx) ? 'var(--accent-cyan)' : 'var(--text-muted)'; e.currentTarget.style.background = 'none'; }}
                        title="Copy message to clipboard"
                      >
                        {copiedMessageId === (msg.id || mIdx) ? (
                          <>
                            <Check size={12} color="var(--accent-cyan)" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={12} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>

                    <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                      {renderFormattedText(msg.text)}
                    </div>

                    {/* Collapsible reasoning timeline */}
                    {msg.reasoningSteps && msg.reasoningSteps.length > 0 && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', padding: '10px 14px', borderRadius: '8px' }}>
                        <div 
                          onClick={() => toggleThoughts(msg.id || mIdx)}
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Brain size={12} color="var(--accent-primary)" />
                            <span>Thinking Timeline</span>
                          </div>
                          {expandedThoughts[msg.id || mIdx] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        </div>
                        {expandedThoughts[msg.id || mIdx] && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '6px' }}>
                            {msg.reasoningSteps.map((step, sIdx) => (
                              <div key={sIdx} className="timeline-step completed">
                                <span>[✓] {step}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {/* Reasoning particle loader while thinking */}
          {loading && (
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '12px', 
              width: '100%', 
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderLeft: '3px solid var(--accent-primary)',
              borderRadius: '12px',
              padding: '16px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
              marginBottom: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} color="var(--accent-primary)" />
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>AI Agent Thinking</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div className="timeline-step active">
                  <span className="pulse-text">[→] Compiling workspace variables...</span>
                </div>
                <div className="timeline-step">
                  <span>[ ] Validating database ledger records...</span>
                </div>
                <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-primary)', animation: 'pulse 1s infinite' }} />
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-primary)', animation: 'pulse 1s infinite 0.2s' }} />
                  <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-primary)', animation: 'pulse 1s infinite 0.4s' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Prompts Section (Shown when input is empty and chat is brand new) */}
        {!input.trim() && !loading && messages.length <= 1 && (
          <div style={{ padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '14px' }}>
            {[
              { text: 'Estimate budget details for active projects', label: 'Estimates' },
              { text: 'List today priorities task backlog', label: 'Priorities' },
              { text: 'Summarize financial collections outstanding', label: 'Invoices' },
              { text: 'Create email follower reminder rule', label: 'Automations' }
            ].map((p, idx) => (
              <div 
                key={idx} 
                className="suggestion-prompt-card"
                onClick={() => setInput(p.text)}
              >
                <div style={{ fontWeight: 600, color: '#fff', marginBottom: '2px', fontSize: '0.74rem' }}>{p.label}</div>
                <div>{p.text}</div>
              </div>
            ))}
          </div>
        )}

        {/* Composer container */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid rgba(255,255,255,0.03)',
          background: 'rgba(9, 9, 11, 0.15)'
        }}>
          <form onSubmit={handleSend} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '12px',
            padding: '8px 12px'
          }}>

            <input 
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask Jarvis to log bills, create checklist, or design rules..."
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#fff',
                fontSize: '0.85rem'
              }}
            />

            {/* Voice Mode Activation */}
            <button 
              type="button"
              onClick={() => { setVoiceModeActive(true); startVoiceRecording(); }}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              title="Voice Whisper mode"
            >
              <Mic size={16} />
            </button>

            <button 
              type="submit"
              disabled={loading || !input.trim()}
              style={{
                background: 'none',
                border: 'none',
                color: input.trim() ? 'var(--accent-primary)' : 'var(--text-muted)',
                cursor: input.trim() ? 'pointer' : 'default',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>

      {/* COLUMN 3: Live Database Context Panel */}
      <div className="ai-workspace-context">
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Project Context</span>
          {activeProjContext ? (
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff' }}>{activeProjContext.title}</h4>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                <span>{isAllContext ? 'Projects:' : 'Client:'} {activeProjContext.client_name || 'N/A'}</span>
                <span className="badge badge-active" style={{ fontSize: '0.6rem', padding: '1px 5px' }}>{activeProjContext.status}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                <span>Budget: {formatAmount(activeProjContext.total_amount)}</span>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>No active project context selected.</div>
          )}
        </div>

        <div style={{ height: '1px', background: 'rgba(255,255,255,0.04)' }} />

        {/* Active Checklist (Todos) */}
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Pending Sprint Tasks</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
            {activeProjTasks.length === 0 ? (
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>All sprint tasks completed!</span>
            ) : (
              activeProjTasks.map(task => (
                <div key={task.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input 
                    type="checkbox"
                    checked={task.status === 'done'}
                    onChange={() => handleToggleTask(task)}
                    style={{ cursor: 'pointer', accentColor: 'var(--accent-primary)', width: '13px', height: '13px' }}
                  />
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                    {task.title}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div style={{ height: '1px', background: 'rgba(255,255,255,0.04)' }} />

        {/* Payments ledger */}
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Financial Invoices</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
            {activeProjPayments.length === 0 ? (
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>No payment logs recorded.</span>
            ) : (
              activeProjPayments.map(p => (
                <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.76rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{p.payment_type}</span>
                  <span style={{ 
                    fontWeight: 700, 
                    color: p.status === 'received' ? '#34d399' : '#fbbf24' 
                  }}>
                    {formatAmount(p.amount)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div style={{ height: '1px', background: 'rgba(255,255,255,0.04)' }} />

        {/* Quick action triggers */}
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Quick Integrations</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
            <button 
              onClick={() => setInput(`generate todo report for projects in navy theme`)}
              className="btn btn-secondary" 
              style={{ padding: '6px', fontSize: '0.72rem', justifyContent: 'flex-start', width: '100%' }}
            >
              Compile PDF Report
            </button>
            <button 
              onClick={() => alert("Google Calendar sync triggers automatically on schedule.")}
              className="btn btn-secondary" 
              style={{ padding: '6px', fontSize: '0.72rem', justifyContent: 'flex-start', width: '100%' }}
            >
              Trigger Sync Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
