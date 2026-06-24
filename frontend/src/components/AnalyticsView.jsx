import React, { useState, useEffect } from 'react';
import { Sparkles, IndianRupee, CheckCircle2, TrendingUp, AlertTriangle, ShieldAlert, Award } from 'lucide-react';
import { api } from '../services/api';

export default function AnalyticsView() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const data = await api.analytics.get();
      setStats(data);
    } catch (err) {
      console.error("Failed to load analytics dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="card-title-bar">
          <div>
            <div className="skeleton-pulse" style={{ width: '250px', height: '24px', borderRadius: '4px' }} />
            <div className="skeleton-pulse" style={{ width: '400px', height: '14px', borderRadius: '4px', marginTop: '8px' }} />
          </div>
        </div>

        {/* Grid of Key Statistics Skeletons */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="glass-panel stat-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="skeleton-pulse" style={{ width: '60%', height: '14px', borderRadius: '4px' }} />
              <div className="skeleton-pulse" style={{ width: '40%', height: '24px', borderRadius: '4px' }} />
            </div>
          ))}
        </div>

        {/* Project Health Index Skeleton */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div className="skeleton-pulse" style={{ width: '200px', height: '18px', borderRadius: '4px', marginBottom: '16px' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[1, 2].map(i => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '50%' }}>
                  <div className="skeleton-pulse" style={{ width: '70%', height: '16px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse" style={{ width: '40%', height: '12px', borderRadius: '4px' }} />
                </div>
                <div className="skeleton-pulse" style={{ width: '50px', height: '24px', borderRadius: '4px' }} />
              </div>
            ))}
          </div>
        </div>

        {/* Workload Distribution Skeleton */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div className="skeleton-pulse" style={{ width: '180px', height: '18px', borderRadius: '4px', marginBottom: '16px' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {[1, 2].map(i => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div className="skeleton-pulse" style={{ width: '30%', height: '14px', borderRadius: '4px' }} />
                  <div className="skeleton-pulse" style={{ width: '15%', height: '14px', borderRadius: '4px' }} />
                </div>
                <div className="skeleton-pulse" style={{ width: '100%', height: '8px', borderRadius: '4px' }} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!stats || stats.projects?.total === 0) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        No analytics data available. Start by creating projects and logging tasks/payments to visualize metrics.
      </div>
    );
  }

  const fin = stats.financials || {};
  const prod = stats.productivity || {};
  const health = stats.project_health || {};
  const workload = stats.workload || {};

  const getHealthEmoji = (status) => {
    if (status === 'Healthy') return '🟢';
    if (status === 'At Risk') return '🟡';
    return '🔴';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar">
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Command Center Analytics</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            A comprehensive overview of your freelance workload, velocity, and finances.
          </p>
        </div>
      </div>

      {/* Grid of Key Statistics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-panel stat-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Total Earnings</span>
            <IndianRupee size={18} color="#34d399" />
          </div>
          <span className="stat-value" style={{ color: '#34d399', fontSize: '1.6rem' }}>
            ₹{fin.total_earned?.toLocaleString()}
          </span>
        </div>

        <div className="glass-panel stat-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Pending Invoices</span>
            <TrendingUp size={18} color="#fbbf24" />
          </div>
          <span className="stat-value" style={{ color: '#fbbf24', fontSize: '1.6rem' }}>
            ₹{fin.total_pending?.toLocaleString()}
          </span>
        </div>

        <div className="glass-panel stat-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Overdue Bills</span>
            <AlertTriangle size={18} color="#f87171" />
          </div>
          <span className="stat-value" style={{ color: '#f87171', fontSize: '1.6rem' }}>
            ₹{fin.total_overdue?.toLocaleString()}
          </span>
        </div>

        <div className="glass-panel stat-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Task Completion Rate</span>
            <CheckCircle2 size={18} color="var(--accent-primary)" />
          </div>
          <span className="stat-value" style={{ color: 'var(--accent-primary)', fontSize: '1.6rem' }}>
            {prod.completion_rate}%
          </span>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
            {prod.completed_tasks} / {prod.total_tasks} tasks resolved
          </p>
        </div>
      </div>

      {/* Project Health Index */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🩺 Project Health & Risk Index
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {Object.entries(health).map(([projTitle, hInfo]) => (
            <div key={projTitle} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px' }}>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>{getHealthEmoji(hInfo.status)}</span> {projTitle}
                </h4>
                <div style={{ display: 'flex', gap: '12px', fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  <span>Blockers: <strong style={{ color: hInfo.blockers_count > 0 ? '#f87171' : 'inherit' }}>{hInfo.blockers_count}</strong></span>
                  <span>Overdue Tasks: <strong style={{ color: hInfo.overdue_tasks > 0 ? '#f87171' : 'inherit' }}>{hInfo.overdue_tasks}</strong></span>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, color: hInfo.score >= 80 ? '#34d399' : hInfo.score >= 50 ? '#fbbf24' : '#f87171' }}>
                  {hInfo.score}/100
                </span>
                <span className="badge" style={{
                  fontSize: '0.65rem',
                  background: hInfo.status === 'Healthy' ? 'rgba(16,185,129,0.1)' : hInfo.status === 'At Risk' ? 'rgba(251,191,36,0.1)' : 'rgba(239,68,68,0.1)',
                  color: hInfo.status === 'Healthy' ? '#34d399' : hInfo.status === 'At Risk' ? '#fbbf24' : '#f87171',
                  border: 'none'
                }}>
                  {hInfo.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Workload Distribution */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '16px' }}>💼 Active Tasks Workload</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {Object.entries(workload).map(([projTitle, taskCount]) => {
            const maxTasks = Math.max(...Object.values(workload), 1);
            const percent = Math.min(100, Math.round((taskCount / maxTasks) * 100));
            return (
              <div key={projTitle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 500 }}>{projTitle}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{taskCount} active tasks</span>
                </div>
                <div style={{ height: '8px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${percent}%`, background: 'var(--accent-primary)', borderRadius: '4px', transition: 'width 0.5s ease-out' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
