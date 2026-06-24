import React, { useState } from 'react';
import { Table, ExternalLink, Link2, Calendar, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function IntegrationsView({ sheetLinks = { payments_url: null, todos_url: null }, onRefresh, loading = false }) {
  const [localLoading, setLocalLoading] = useState(false);
  const hasGoogleToken = !!localStorage.getItem('google_token');

  const handleLinkGoogle = async () => {
    setLocalLoading(true);
    try {
      const res = await api.sync.googleAuth();
      if (res.url) {
        window.location.href = res.url;
      }
    } catch (err) {
      alert("Failed to initiate Google Link: " + err.message);
    } finally {
      setLocalLoading(false);
    }
  };

  const handleDisconnectGoogle = () => {
    window.showConfirm("Are you sure you want to disconnect your Google Account? This will stop real-time Calendar synchronization.", () => {
      localStorage.removeItem('google_token');
      onRefresh();
    });
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px', margin: '0 auto' }}>
        <div className="skeleton-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '70%' }}>
              <div className="skeleton-pulse skeleton-avatar" style={{ width: '40px', height: '40px' }} />
              <div style={{ width: '80%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div className="skeleton-pulse skeleton-title" style={{ width: '60%', height: '18px', margin: 0 }} />
                <div className="skeleton-pulse skeleton-text" style={{ width: '85%', height: '12px', margin: 0 }} />
              </div>
            </div>
            <div className="skeleton-pulse skeleton-button" style={{ width: '90px', height: '24px', borderRadius: '4px' }} />
          </div>
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="skeleton-pulse skeleton-text" style={{ width: '60%', height: '14px', margin: 0 }} />
            <div className="skeleton-pulse skeleton-button" style={{ width: '150px', height: '36px', borderRadius: '8px' }} />
          </div>
        </div>
        <div className="skeleton-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div className="skeleton-pulse skeleton-avatar" style={{ width: '36px', height: '36px', borderRadius: '8px' }} />
          <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="skeleton-pulse skeleton-title" style={{ width: '30%', height: '16px', margin: 0 }} />
            <div className="skeleton-pulse skeleton-text" style={{ width: '75%', height: '12px', margin: 0 }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px', margin: '0 auto' }}>
      
      {/* Connection Status Card */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              borderRadius: '50%', 
              background: 'rgba(66, 133, 244, 0.1)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center' 
            }}>
              <Link2 size={22} color="#4285F4" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>Google Integration Status</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                Manage Google Calendar integrations.
              </p>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {hasGoogleToken ? (
              <span className="badge badge-active" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
                <CheckCircle2 size={12} /> Connected
              </span>
            ) : (
              <span className="badge badge-planning" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
                <AlertCircle size={12} /> Not Linked
              </span>
            )}
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            {hasGoogleToken 
              ? "Your account is authorized. Real-time changes to your tasks and milestones are automatically synced with Google Calendar."
              : "Authorize Vixx to read and write your Google Calendar events."
            }
          </div>
          <div>
            {hasGoogleToken ? (
              <button 
                onClick={handleDisconnectGoogle} 
                className="btn btn-secondary" 
                style={{ color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.2)' }}
              >
                Disconnect Account
              </button>
            ) : (
              <button 
                onClick={handleLinkGoogle} 
                className="btn btn-primary"
                disabled={localLoading}
              >
                {localLoading ? 'Initiating...' : 'Link Google Account'}
              </button>
            )}
          </div>
        </div>
      </div>



      {/* Calendar Integration Section */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ 
          width: '36px', 
          height: '36px', 
          borderRadius: '8px', 
          background: 'rgba(59, 130, 246, 0.1)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center'
        }}>
          <Calendar size={20} color="#3b82f6" />
        </div>
        <div style={{ flexGrow: 1 }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Google Calendar Sync</h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
            Whenever you create or update tasks or timeline events, they will automatically sync to your connected Google Calendar.
          </p>
        </div>
      </div>

    </div>
  );
}
