import React, { useState } from 'react';
import { CreditCard, CheckCircle, Clock, TrendingUp, ChevronRight } from 'lucide-react';

export default function DashboardAnalytics({ projects = [], payments = [] }) {
  const [activeSegment, setActiveSegment] = useState(null); // 'received', 'pending', or null

  // 1. Calculate aggregated financial metrics
  const activeProjectIds = projects
    .filter(p => p.status !== 'completed' && p.status !== 'finished')
    .map(p => p.id);

  const totalBudget = projects
    .filter(p => p.status !== 'completed' && p.status !== 'finished')
    .reduce((sum, p) => sum + parseFloat(p.total_amount || 0), 0);

  const totalReceived = payments
    .filter(p => p.status === 'received' && activeProjectIds.includes(p.project_id))
    .reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);

  // Pending amount is budget minus received (min 0)
  const totalPending = Math.max(0, totalBudget - totalReceived);
  
  // Percentages
  const overallTotal = totalReceived + totalPending;
  const receivedPct = overallTotal > 0 ? (totalReceived / overallTotal) * 100 : 0;
  const pendingPct = overallTotal > 0 ? (totalPending / overallTotal) * 100 : 0;

  // Donut SVG parameters
  const radius = 50;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius; // ~314.16

  // Received stroke calculations
  const receivedDash = (receivedPct / 100) * circumference;
  const receivedOffset = 0;

  // Pending stroke calculations
  const pendingDash = (pendingPct / 100) * circumference;
  const pendingOffset = -receivedDash;

  // 2. Compute project progress bars (top 3 projects by budget)
  const activeProjectsList = projects
    .filter(p => p.status !== 'completed' && p.status !== 'finished')
    .map(proj => {
      const projReceived = payments
        .filter(p => p.project_id === proj.id && p.status === 'received')
        .reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
      const budget = parseFloat(proj.total_amount || 0);
      const pct = budget > 0 ? Math.min(100, (projReceived / budget) * 100) : 0;
      return {
        id: proj.id,
        title: proj.title,
        budget,
        received: projReceived,
        pct
      };
    })
    .sort((a, b) => b.budget - a.budget)
    .slice(0, 3);

  // Helper formatting functions
  const formatAmount = (val) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}K`;
    return `₹${val}`;
  };

  return (
    <div className="dashboard-analytics-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
      {/* ── Financial Donut Card ── */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
          <CreditCard size={15} color="var(--accent-primary)" />
          Financial Health
        </h3>

        {overallTotal === 0 ? (
          <div style={{ height: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            No financial projects or budget logged.
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '24px', flexWrap: 'wrap' }}>
            {/* Donut Graphic */}
            <div style={{ position: 'relative', width: '130px', height: '130px', flexShrink: 0, margin: '0 auto' }}>
              <svg viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)', overflow: 'visible', width: '100%', height: '100%' }}>
                <defs>
                  <filter id="donut-glow-green">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                  <filter id="donut-glow-yellow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>

                {/* Empty track circle */}
                <circle cx="60" cy="60" r={radius} fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth={strokeWidth} />

                {/* Received Slice */}
                {receivedPct > 0 && (
                  <circle
                    cx="60"
                    cy="60"
                    r={radius}
                    fill="none"
                    stroke="#10b981"
                    strokeWidth={activeSegment === 'received' ? strokeWidth + 2 : strokeWidth}
                    strokeDasharray={`${receivedDash} ${circumference - receivedDash}`}
                    strokeDashoffset={receivedOffset}
                    strokeLinecap="round"
                    filter={activeSegment === 'received' ? 'url(#donut-glow-green)' : 'none'}
                    style={{ transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', cursor: 'pointer' }}
                    onMouseEnter={() => setActiveSegment('received')}
                    onMouseLeave={() => setActiveSegment(null)}
                  />
                )}

                {/* Pending Slice */}
                {pendingPct > 0 && (
                  <circle
                    cx="60"
                    cy="60"
                    r={radius}
                    fill="none"
                    stroke="#fbbf24"
                    strokeWidth={activeSegment === 'pending' ? strokeWidth + 2 : strokeWidth}
                    strokeDasharray={`${pendingDash} ${circumference - pendingDash}`}
                    strokeDashoffset={pendingOffset}
                    strokeLinecap="round"
                    filter={activeSegment === 'pending' ? 'url(#donut-glow-yellow)' : 'none'}
                    style={{ transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', cursor: 'pointer' }}
                    onMouseEnter={() => setActiveSegment('pending')}
                    onMouseLeave={() => setActiveSegment(null)}
                  />
                )}
              </svg>

              {/* Center Info Text overlay */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                pointerEvents: 'none'
              }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {activeSegment === 'received' ? 'Received' : activeSegment === 'pending' ? 'Pending' : 'Total'}
                </div>
                <div style={{
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  color: activeSegment === 'received' ? '#10b981' : activeSegment === 'pending' ? '#fbbf24' : '#fff',
                  marginTop: '1px',
                  transition: 'color 0.2s ease'
                }}>
                  {activeSegment === 'received' 
                    ? `${Math.round(receivedPct)}%` 
                    : activeSegment === 'pending' 
                      ? `${Math.round(pendingPct)}%` 
                      : formatAmount(overallTotal)
                  }
                </div>
              </div>
            </div>

            {/* Labels and values side */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, minWidth: '120px' }}>
              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px', 
                  padding: '6px 8px', 
                  borderRadius: '8px', 
                  background: activeSegment === 'received' ? 'rgba(16, 185, 129, 0.06)' : 'transparent',
                  transition: 'background 0.2s ease',
                  cursor: 'pointer'
                }}
                onMouseEnter={() => setActiveSegment('received')}
                onMouseLeave={() => setActiveSegment(null)}
              >
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Collected</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#10b981' }}>₹{Math.round(totalReceived).toLocaleString()}</span>
                </div>
              </div>

              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px', 
                  padding: '6px 8px', 
                  borderRadius: '8px', 
                  background: activeSegment === 'pending' ? 'rgba(251, 191, 36, 0.06)' : 'transparent',
                  transition: 'background 0.2s ease',
                  cursor: 'pointer'
                }}
                onMouseEnter={() => setActiveSegment('pending')}
                onMouseLeave={() => setActiveSegment(null)}
              >
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fbbf24' }} />
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Outstanding</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fbbf24' }}>₹{Math.round(totalPending).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Project Value Bar Progress list ── */}
      {activeProjectsList.length > 0 && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
            <TrendingUp size={15} color="var(--accent-secondary)" />
            Top Project Budgets
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {activeProjectsList.map(proj => (
              <div 
                key={proj.id} 
                onClick={() => {
                  window.location.hash = `#/projects/${proj.id}`;
                }}
                style={{ display: 'flex', flexDirection: 'column', gap: '6px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px' }}>{proj.title}</span>
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                    ₹{Math.round(proj.received).toLocaleString()} <span style={{ color: 'var(--text-muted)' }}>/ {formatAmount(proj.budget)}</span>
                  </span>
                </div>
                
                {/* Horizontal Progress Bar */}
                <div style={{ width: '100%', height: '7px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
                  <div style={{
                    width: `${proj.pct}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
                    borderRadius: '4px',
                    transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
                  }} />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                  <span>Collection: {Math.round(proj.pct)}%</span>
                  <span style={{ display: 'flex', alignItems: 'center', color: 'var(--accent-primary)' }}>Details <ChevronRight size={10} /></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
