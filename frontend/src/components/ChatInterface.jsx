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
  X
} from 'lucide-react';
import { api } from '../services/api';

export default function ChatInterface({ onRefreshData }) {
  // 1. Local Storage Persistent State
  const [conversations, setConversations] = useState(() => {
    try {
      const saved = localStorage.getItem('vixx_conversations');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.error("Error reading conversations from local storage:", e);
    }
    return [
      {
        id: 'default',
        title: 'New Chat',
        messages: [
          {
            id: 'welcome',
            sender: 'assistant',
            text: "Hi! I'm Vixx, your Personal Assistant. You can manage projects, schedule WhatsApp/email reminders (e.g. 'remind me to call John tomorrow at 10am'), log payments, or manage your to-do lists.",
            type: 'normal'
          }
        ],
        createdAt: new Date().toISOString()
      }
    ];
  });

  const [activeChatId, setActiveChatId] = useState(() => {
    const savedActive = localStorage.getItem('vixx_active_chat_id');
    if (savedActive) {
      return savedActive;
    }
    return 'default';
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedThoughts, setExpandedThoughts] = useState({});
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const editInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const [mobileRoomsDropdownOpen, setMobileRoomsDropdownOpen] = useState(false);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem('vixx_conversations', JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    localStorage.setItem('vixx_active_chat_id', activeChatId);
  }, [activeChatId]);

  // Ensure activeChatId is valid
  useEffect(() => {
    if (conversations.length > 0 && !conversations.some(c => c.id === activeChatId)) {
      setActiveChatId(conversations[0].id);
    }
  }, [conversations, activeChatId]);

  // Active conversation helper
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
      title: 'New Chat',
      messages: [
        {
          id: 'welcome',
          sender: 'assistant',
          text: "Hi! I'm Vixx, your Personal Assistant. You can manage projects, schedule WhatsApp/email reminders (e.g. 'remind me to call John tomorrow at 10am'), log payments, or manage your to-do lists.",
          type: 'normal'
        }
      ],
      createdAt: new Date().toISOString()
    };
    setConversations(prev => [newChat, ...prev]);
    setActiveChatId(newId);
  };

  const handleDeleteChat = (id) => {
    window.showConfirm("Are you sure you want to delete this conversation?", () => {
      setConversations(prev => {
        const filtered = prev.filter(c => c.id !== id);
        if (filtered.length === 0) {
          const newDefaultId = 'default_' + Date.now();
          setActiveChatId(newDefaultId);
          return [
            {
              id: newDefaultId,
              title: 'New Chat',
              messages: [
                {
                  id: 'welcome',
                  sender: 'assistant',
                  text: "Hi! I'm Vixx, your Personal Assistant. You can manage projects, schedule WhatsApp/email reminders (e.g. 'remind me to call John tomorrow at 10am'), log payments, or manage your to-do lists.",
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

  const handleStartRename = (e, conv) => {
    e.stopPropagation();
    setEditingChatId(conv.id);
    setEditingTitle(conv.title);
    setTimeout(() => editInputRef.current?.focus(), 50);
  };

  const handleSaveRename = () => {
    if (editingChatId && editingTitle.trim()) {
      setConversations(prev =>
        prev.map(c =>
          c.id === editingChatId ? { ...c, title: editingTitle.trim() } : c
        )
      );
    }
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleCancelRename = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleCopyChat = () => {
    const formattedText = messages
      .map(msg => {
        const prefix = msg.sender === 'assistant' ? 'AI' : 'User';
        return `${prefix}:\n${msg.text}`;
      })
      .join('\n\n');
    
    navigator.clipboard.writeText(formattedText)
      .then(() => { if (window.showToast) window.showToast('Conversation copied to clipboard', 'success'); })
      .catch(err => { if (window.showToast) window.showToast('Failed to copy: ' + err.message, 'error'); });
  };

  const renderFormattedText = (text) => {
    if (!text) return null;
    
    const formatBold = (str) => {
      const parts = str.split(/\*\*(.*?)\*\*/g);
      return parts.map((part, index) => {
        if (index % 2 === 1) {
          return <strong key={index} style={{ fontWeight: '700', color: 'inherit' }}>{part}</strong>;
        }
        return part;
      });
    };

    const parseLineContent = (str) => {
      if (!str) return null;
      
      const linkRegex = /\[(.*?)\]\((.*?)\)/;
      const match = str.match(linkRegex);
      
      if (match) {
        const label = match[1];
        const url = match[2];
        const before = str.substring(0, match.index);
        const after = str.substring(match.index + match[0].length);
        
        const cleanBefore = before.replace(/[📥\s\-\*•]+/g, '').trim();
        const cleanAfter = after.trim();
        const isPdf = url.toLowerCase().endsWith('.pdf') || url.includes('/uploads/');
        
        return (
          <div style={{ display: 'inline-flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start', margin: '4px 0' }}>
            {cleanBefore && <span style={{ display: 'block', fontSize: '0.92rem' }}>{formatBold(before)}</span>}
            {isPdf ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  marginTop: '4px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(124, 58, 237, 0.25)',
                  background: 'linear-gradient(135deg, var(--accent-primary) 0%, #7c3aed 100%)',
                  border: 'none',
                  color: 'white',
                  transition: 'transform 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
              >
                <Download size={14} /> {label}
              </a>
            ) : (
              <a href={url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>
                {label}
              </a>
            )}
            {cleanAfter && <span style={{ display: 'block', fontSize: '0.92rem' }}>{formatBold(after)}</span>}
          </div>
        );
      }
      
      return formatBold(str);
    };

    const normalizedText = text.replace(/ \/\/\/ /g, '\n').replace(/\/\/\//g, '\n');
    const lines = normalizedText.split('\n');

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {lines.map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) {
            return <div key={idx} style={{ height: '6px' }} />;
          }

          // Horizontal rule
          if (/^-{3,}$/.test(trimmed) || /^\*{3,}$/.test(trimmed) || /^_{3,}$/.test(trimmed)) {
            return <hr key={idx} style={{ border: 'none', borderTop: '1px solid rgba(255, 255, 255, 0.12)', margin: '8px 0' }} />;
          }

          if (trimmed.startsWith('###')) {
            return (
              <h4 key={idx} style={{ fontSize: '1.05rem', fontWeight: 600, marginTop: '12px', marginBottom: '4px', color: 'var(--text-primary)' }}>
                {parseLineContent(trimmed.substring(3).trim())}
              </h4>
            );
          }
          if (trimmed.startsWith('##')) {
            return (
              <h3 key={idx} style={{ fontSize: '1.15rem', fontWeight: 600, marginTop: '14px', marginBottom: '6px', color: 'var(--text-primary)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '4px' }}>
                {parseLineContent(trimmed.substring(2).trim())}
              </h3>
            );
          }
          if (trimmed.startsWith('#')) {
            return (
              <h2 key={idx} style={{ fontSize: '1.3rem', fontWeight: 700, marginTop: '16px', marginBottom: '8px', color: 'var(--text-primary)' }}>
                {parseLineContent(trimmed.substring(1).trim())}
              </h2>
            );
          }

          if (trimmed.startsWith('-') || (trimmed.startsWith('*') && !trimmed.startsWith('**'))) {
            return (
              <div key={idx} style={{ display: 'flex', gap: '8px', paddingLeft: '12px', fontSize: '0.9rem', lineHeight: '1.5', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--text-secondary)', marginTop: '2px', opacity: 0.8 }}>•</span>
                <span>{parseLineContent(trimmed.substring(1).trim())}</span>
              </div>
            );
          }

          return (
            <p key={idx} style={{ margin: 0, fontSize: '0.92rem', lineHeight: '1.5', color: 'inherit' }}>
              {parseLineContent(line)}
            </p>
          );
        })}
      </div>
    );
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (userText) => {
    setLoading(true);

    // Append user message AND optionally update title if it's "New Chat"
    setConversations(prevConvs => {
      return prevConvs.map(c => {
        if (c.id === activeChatId) {
          let newTitle = c.title;
          if (c.title === "New Chat") {
            newTitle = userText.length > 25 ? userText.substring(0, 22) + "..." : userText;
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
      // Process with LangGraph backend
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
            text: response.summary || "Action processed successfully.",
            type: 'success',
            reasoningSteps: response.reasoning_steps
          }
        ]);
        // Trigger dashboard stats/data refresh
        if (onRefreshData) onRefreshData();
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'assistant',
          text: `Error processing request: ${error.message || 'Config keys missing.'}`,
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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const lastMessage = messages[messages.length - 1];
  const isConfirmationActive = !loading && lastMessage && 
                               lastMessage.sender === 'assistant' && 
                               (lastMessage.text.includes('⚠️') || lastMessage.text.toLowerCase().includes('are you sure') || lastMessage.text.toLowerCase().includes('confirm to proceed'));

  return (
    <div className="glass-panel chat-container" style={{ display: 'flex', flexDirection: 'row', height: '600px', overflow: 'hidden' }}>
      
      {/* 2. Sleek Conversation Sidebar */}
      <div className="chat-sidebar" style={{
        width: '220px',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(10, 8, 19, 0.4)',
        height: '100%',
        flexShrink: 0
      }}>
        <button
          type="button"
          onClick={handleCreateNewChat}
          style={{
            margin: '16px',
            padding: '10px 14px',
            background: 'linear-gradient(135deg, var(--accent-primary) 0%, #7c3aed 100%)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            fontSize: '0.82rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(124, 58, 237, 0.2)',
            transition: 'transform 0.2s'
          }}
          onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
          onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <Plus size={14} />
          New Chat
        </button>
        
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 16px 8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {conversations.map(conv => {
            const isActive = conv.id === activeChatId;
            return (
              <div 
                key={conv.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                  border: isActive ? '1px solid rgba(139, 92, 246, 0.25)' : '1px solid transparent',
                  cursor: 'pointer',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  transition: 'all 0.2s'
                }} 
                onClick={() => setActiveChatId(conv.id)}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                {editingChatId === conv.id ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexGrow: 1, minWidth: 0 }}>
                    <input
                      ref={editInputRef}
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveRename();
                        if (e.key === 'Escape') handleCancelRename();
                        e.stopPropagation();
                      }}
                      onBlur={handleSaveRename}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        background: 'rgba(255, 255, 255, 0.08)',
                        border: '1px solid var(--accent-primary)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '0.82rem',
                        padding: '3px 6px',
                        outline: 'none',
                        width: '100%',
                        minWidth: 0,
                        fontFamily: 'inherit'
                      }}
                    />
                  </div>
                ) : (
                  <span 
                    style={{ 
                      fontSize: '0.82rem', 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis', 
                      whiteSpace: 'nowrap',
                      flexGrow: 1,
                      marginRight: '4px',
                      fontWeight: isActive ? 600 : 400
                    }}
                    onDoubleClick={(e) => handleStartRename(e, conv)}
                    title="Double-click to rename"
                  >
                    {conv.title}
                  </span>
                )}
                <div className="chat-item-actions" style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '2px',
                  opacity: isActive ? 1 : 0,
                  transition: 'opacity 0.2s',
                  flexShrink: 0
                }}>
                  {editingChatId !== conv.id && (
                    <button 
                      type="button"
                      onClick={(e) => handleStartRename(e, conv)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '4px',
                        transition: 'all 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.color = 'var(--accent-primary)'}
                      onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                      title="Rename Chat"
                    >
                      <Pencil size={12} />
                    </button>
                  )}
                  <button 
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChat(conv.id);
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '4px',
                      transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.color = '#f87171'}
                    onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                    title="Delete Chat"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Main Chat Pane */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        position: 'relative'
      }}>
        <div className="chat-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', paddingRight: '12px', paddingLeft: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="logo-icon" style={{ width: '28px', height: '28px', background: 'transparent', boxShadow: 'none', flexShrink: 0 }}>
              <img src="/bot icon.png" alt="Vixx" style={{ width: '100%', height: '100%', borderRadius: '6px', objectFit: 'contain' }} />
            </div>
            <div>
              <h3 className="chat-title-main" style={{ fontSize: '0.92rem', fontWeight: 600 }}>AI Command Center</h3>
              <p className="chat-subtitle-main" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Powered by Groq & LangGraph</p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Mobile Chat Selection Dropdown Trigger */}
            <div className="mobile-chat-dropdown-container" style={{ position: 'relative' }}>
              <button
                type="button"
                className="btn btn-secondary mobile-chat-select-btn"
                onClick={() => setMobileRoomsDropdownOpen(!mobileRoomsDropdownOpen)}
                style={{
                  display: 'none',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.75rem',
                  padding: '5px 8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  cursor: 'pointer'
                }}
              >
                <span style={{ maxWidth: '90px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {activeConv.title || 'Chat'}
                </span>
                <ChevronDown size={12} />
              </button>
              
              {/* Dropdown Panel */}
              {mobileRoomsDropdownOpen && (
                <div 
                  className="mobile-chat-rooms-popup glass-panel"
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: '8px',
                    width: '220px',
                    zIndex: 950,
                    background: 'rgba(12, 10, 24, 0.98)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '10px',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
                    padding: '8px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <button
                    type="button"
                    onClick={() => {
                      handleCreateNewChat();
                      setMobileRoomsDropdownOpen(false);
                    }}
                    style={{
                      padding: '7px 10px',
                      background: 'linear-gradient(135deg, var(--accent-primary) 0%, #7c3aed 100%)',
                      border: 'none',
                      borderRadius: '6px',
                      color: 'white',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                  >
                    <Plus size={12} /> New Chat
                  </button>
                  
                  <div style={{ height: '1px', background: 'rgba(255, 255, 255, 0.08)', margin: '2px 0' }} />
                  
                  <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    {conversations.map(conv => {
                      const isActive = conv.id === activeChatId;
                      return (
                        <div
                          key={conv.id}
                          onClick={() => {
                            setActiveChatId(conv.id);
                            setMobileRoomsDropdownOpen(false);
                          }}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '6px 8px',
                            borderRadius: '6px',
                            background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                            color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexGrow: 1, marginRight: '8px' }}>
                            {conv.title}
                          </span>
                          
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                const newTitle = prompt("Rename chat room to:", conv.title);
                                if (newTitle && newTitle.trim() !== "") {
                                  setConversations(prev => prev.map(c => c.id === conv.id ? { ...c, title: newTitle.trim() } : c));
                                }
                              }}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: 'rgba(255, 255, 255, 0.4)',
                                cursor: 'pointer',
                                padding: '2px',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title="Rename Chat"
                            >
                              <Pencil size={11} />
                            </button>
                            
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteChat(conv.id);
                                if (conv.id === activeChatId) {
                                  setMobileRoomsDropdownOpen(false);
                                }
                              }}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: 'rgba(255, 255, 255, 0.4)',
                                cursor: 'pointer',
                                padding: '2px',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title="Delete Chat"
                            >
                              <Trash2 size={11} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleCopyChat}
              className="btn btn-secondary copy-chat-btn"
              style={{ 
                fontSize: '0.72rem', 
                padding: '6px 10px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '4px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                cursor: 'pointer',
                borderRadius: '6px'
              }}
              title="Copy Conversation"
            >
              <Copy size={12} />
              <span className="copy-chat-btn-text">Copy Chat</span>
            </button>
          </div>
        </div>

        <div className="chat-messages" style={{ flex: 1, overflowY: 'auto' }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-bubble ${msg.sender} ${
                msg.type === 'clarification' ? 'clarification' : ''
              }`}
              style={{
                position: 'relative',
                ...(msg.type === 'error'
                  ? { background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)' }
                  : msg.type === 'success'
                  ? { background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid rgba(16, 185, 129, 0.25)', borderLeft: '3px solid #34d399' }
                  : {})
              }}
            >
              {/* Per-message copy button */}
              {msg.id !== 'welcome' && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(msg.text)
                      .then(() => {
                        if (window.showToast) window.showToast('Message copied to clipboard', 'success');
                      })
                      .catch(() => {
                        if (window.showToast) window.showToast('Failed to copy message', 'error');
                      });
                  }}
                  className="msg-copy-btn"
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '4px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: 0,
                    transition: 'all 0.2s'
                  }}
                  title="Copy message"
                >
                  <Copy size={12} />
                </button>
              )}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', flexDirection: 'column', width: '100%' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', width: '100%' }}>
                  {msg.type === 'clarification' && <AlertCircle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />}
                  {msg.type === 'success' && <CheckCircle2 size={16} style={{ marginTop: '2px', flexShrink: 0, color: '#34d399' }} />}
                  <div style={{ flexGrow: 1 }}>
                    {renderFormattedText(msg.text)}
                    {msg.missingFields && msg.missingFields.length > 0 && (
                      <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {msg.missingFields.map((field) => (
                          <span key={field} className="badge badge-critical" style={{ fontSize: '0.65rem' }}>
                            Missing: {field}
                          </span>
                        ))}
                      </div>
                    )}
                    {messages[messages.length - 1]?.id === msg.id && 
                     msg.sender === 'assistant' && 
                     (msg.text.includes('⚠️') || msg.text.toLowerCase().includes('are you sure') || msg.text.toLowerCase().includes('confirm to proceed')) && 
                     !loading && (
                      <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                        <button
                          type="button"
                          onClick={() => sendMessage('yes')}
                          className="btn btn-primary"
                          style={{ padding: '6px 16px', fontSize: '0.82rem', cursor: 'pointer', borderRadius: '6px' }}
                        >
                          Yes
                        </button>
                        <button
                          type="button"
                          onClick={() => sendMessage('no')}
                          className="btn btn-secondary"
                          style={{ padding: '6px 16px', fontSize: '0.82rem', cursor: 'pointer', borderRadius: '6px' }}
                        >
                          No
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Collapsible thought process */}
                {msg.reasoningSteps && msg.reasoningSteps.length > 0 && (
                  <div style={{ 
                    margin: '8px 0 0 0', 
                    background: 'rgba(255, 255, 255, 0.03)', 
                    border: '1px solid rgba(255, 255, 255, 0.06)', 
                    borderRadius: '8px', 
                    width: '100%',
                    overflow: 'hidden'
                  }}>
                    <button 
                      type="button"
                      onClick={() => setExpandedThoughts(prev => ({ ...prev, [msg.id]: !prev[msg.id] }))}
                      style={{ 
                        width: '100%', 
                        padding: '8px 12px', 
                        background: 'none', 
                        border: 'none', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between', 
                        fontSize: '0.78rem', 
                        color: 'var(--text-secondary)', 
                        cursor: 'pointer',
                        fontWeight: 500
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Brain size={13} color="var(--accent-primary)" style={{ animation: expandedThoughts[msg.id] ? 'none' : 'pulse 2s infinite' }} />
                        <span>{expandedThoughts[msg.id] ? 'Hide Vixx Thought Log' : 'Show Vixx Thought Log'}</span>
                      </div>
                      <span>{expandedThoughts[msg.id] ? '▲' : '▼'}</span>
                    </button>
                    
                    {expandedThoughts[msg.id] && (
                      <div style={{ 
                         padding: '10px 14px', 
                         borderTop: '1px solid rgba(255, 255, 255, 0.05)', 
                         display: 'flex', 
                         flexDirection: 'column', 
                         gap: '6px', 
                         maxHeight: '180px', 
                         overflowY: 'auto',
                         fontSize: '0.8rem',
                         fontFamily: 'Courier New, monospace',
                         color: 'rgba(255, 255, 255, 0.75)',
                         textAlign: 'left'
                      }}>
                        {msg.reasoningSteps.map((step, sIdx) => (
                          <div key={sIdx} style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
                            <span style={{ color: 'var(--accent-primary)' }}>➔</span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div className="logo-icon" style={{ width: '20px', height: '20px', background: 'transparent', boxShadow: 'none' }}>
                <img src="/bot icon.png" alt="Vixx" style={{ width: '100%', height: '100%', borderRadius: '4px', objectFit: 'contain' }} />
              </div>
              <span className="pulse-text">Vixx is processing...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Action Chips */}
        {!loading && !isConfirmationActive && (
          <div style={{ display: 'flex', gap: '8px', padding: '0 20px 10px 20px', overflowX: 'auto', whiteSpace: 'nowrap', width: '100%', scrollbarWidth: 'none' }}>
            {[
              { text: "Show dashboard stats", label: "📊 Show Stats" },
              { text: "List active projects", label: "💼 List Projects" },
              { text: "Show my to-do list", label: "✅ To-Do List" },
            ].map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => sendMessage(chip.text)}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  display: 'inline-flex',
                  alignItems: 'center',
                  flexShrink: 0
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
                  e.currentTarget.style.borderColor = 'var(--accent-primary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                }}
              >
                {chip.label}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSend} className="chat-input-container">
          <div className="chat-input-wrapper">
            <textarea
              className="chat-input"
              placeholder={isConfirmationActive ? "Please select Yes or No above..." : "Type a natural language command..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || isConfirmationActive}
              rows={1}
              style={{
                resize: 'none',
                overflowY: 'auto',
                minHeight: '20px',
                maxHeight: '120px',
                fontFamily: 'inherit',
                paddingTop: '10px',
                paddingBottom: '10px',
                opacity: isConfirmationActive ? 0.6 : 1
              }}
            />
            <button type="submit" className="btn btn-primary" style={{ padding: '8px 16px', alignSelf: 'flex-end', marginBottom: '4px' }} disabled={loading || isConfirmationActive}>
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
