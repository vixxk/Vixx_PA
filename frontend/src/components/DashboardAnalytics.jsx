import React, { useState, useMemo } from 'react';
import { CreditCard, CheckCircle2, Clock, TrendingUp, ChevronRight, AlertCircle } from 'lucide-react';

// Tailored vibrant dark-mode palettes
const COMPLETED_COLORS = [
  '#10b981', // Emerald
  '#6366f1', // Indigo
  '#06b6d4', // Cyan
  '#a855f7', // Purple
  '#3b82f6', // Blue
  '#ec4899', // Pink
  '#14b8a6', // Teal
  '#f59e0b', // Amber
];

const REMAINING_COLORS = [
  '#f59e0b', // Amber
  '#ec4899', // Pink / Rose
  '#8b5cf6', // Violet
  '#06b6d4', // Cyan
  '#f97316', // Orange
  '#3b82f6', // Blue
  '#10b981', // Emerald
  '#e11d48', // Crimson
];

// Helper formatting functions
const formatAmount = (val) => {
  if (!val || isNaN(val)) return '₹0';
  if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
  if (val >= 1000) return `₹${(val / 1000).toFixed(0)}K`;
  return `₹${Math.round(val)}`;
};

export default function DashboardAnalytics({ projects = [], payments = [] }) {
  const [hoveredCompletedId, setHoveredCompletedId] = useState(null);
  const [hoveredRemainingId, setHoveredRemainingId] = useState(null);

  // 1. Compute project-wise completed payments
  const completedData = useMemo(() => {
    // Map of projId -> sum received
    const projReceivedMap = {};
    payments.forEach(p => {
      const isReceived = p.status === 'received' || p.status === 'completed' || p.status === 'paid';
      if (isReceived) {
        const amt = parseFloat(p.amount || 0);
        if (amt > 0) {
          projReceivedMap[p.project_id] = (projReceivedMap[p.project_id] || 0) + amt;
        }
      }
    });

    const projectLookup = new Map(projects.map(p => [p.id, p]));
    const list = [];
    let otherSum = 0;

    Object.entries(projReceivedMap).forEach(([projId, amount]) => {
      const proj = projectLookup.get(projId);
      if (proj) {
        list.push({
          id: proj.id,
          title: proj.title,
          amount,
          status: proj.status
        });
      } else {
        otherSum += amount;
      }
    });

    if (otherSum > 0) {
      list.push({
        id: 'other',
        title: 'Other',
        amount: otherSum,
        status: 'completed'
      });
    }

    // Sort descending by amount
    list.sort((a, b) => b.amount - a.amount);
    const total = list.reduce((sum, item) => sum + item.amount, 0);

    // SVG parameters
    const radius = 45;
    const circumference = 2 * Math.PI * radius; // ~282.74
    let accumulated = 0;

    const slices = list.map((item, index) => {
      const pct = total > 0 ? (item.amount / total) * 100 : 0;
      const dash = (pct / 100) * circumference;
      const offset = -accumulated;
      accumulated += dash;
      return {
        ...item,
        color: COMPLETED_COLORS[index % COMPLETED_COLORS.length],
        pct,
        dash,
        offset
      };
    });

    return { list: slices, total, radius, circumference };
  }, [projects, payments]);

  // 2. Compute project-wise remaining payments
  const remainingData = useMemo(() => {
    // Map of projId -> sum received
    const projReceivedMap = {};
    payments.forEach(p => {
      const isReceived = p.status === 'received' || p.status === 'completed' || p.status === 'paid';
      if (isReceived) {
        const amt = parseFloat(p.amount || 0);
        projReceivedMap[p.project_id] = (projReceivedMap[p.project_id] || 0) + amt;
      }
    });

    const list = [];
    projects.forEach(proj => {
      const budget = parseFloat(proj.total_amount || 0);
      const received = projReceivedMap[proj.id] || 0;
      const remaining = Math.max(0, budget - received);
      if (remaining > 0) {
        list.push({
          id: proj.id,
          title: proj.title,
          amount: remaining,
          budget,
          received,
          status: proj.status
        });
      }
    });

    // Sort descending by remaining amount
    list.sort((a, b) => b.amount - a.amount);
    const total = list.reduce((sum, item) => sum + item.amount, 0);

    // SVG parameters
    const radius = 45;
    const circumference = 2 * Math.PI * radius; // ~282.74
    let accumulated = 0;

    const slices = list.map((item, index) => {
      const pct = total > 0 ? (item.amount / total) * 100 : 0;
      const dash = (pct / 100) * circumference;
      const offset = -accumulated;
      accumulated += dash;
      return {
        ...item,
        color: REMAINING_COLORS[index % REMAINING_COLORS.length],
        pct,
        dash,
        offset
      };
    });

    return { list: slices, total, radius, circumference };
  }, [projects, payments]);

  // Overall financial summary
  const totalCompleted = completedData.total;
  const totalRemaining = remainingData.total;
  const grandTotal = totalCompleted + totalRemaining;
  const collectionRate = grandTotal > 0 ? Math.round((totalCompleted / grandTotal) * 100) : 0;

  // Top project progress bars (top 3 with budget)
  const topProjects = useMemo(() => {
    const projReceivedMap = {};
    payments.forEach(p => {
      const isReceived = p.status === 'received' || p.status === 'completed' || p.status === 'paid';
      if (isReceived) {
        const amt = parseFloat(p.amount || 0);
        projReceivedMap[p.project_id] = (projReceivedMap[p.project_id] || 0) + amt;
      }
    });

    return projects
      .map(proj => {
        const budget = parseFloat(proj.total_amount || 0);
        const received = projReceivedMap[proj.id] || 0;
        const pct = budget > 0 ? Math.min(100, (received / budget) * 100) : 0;
        return {
          id: proj.id,
          title: proj.title,
          budget,
          received,
          pct,
          status: proj.status
        };
      })
      .filter(p => p.budget > 0)
      .sort((a, b) => b.budget - a.budget)
      .slice(0, 3);
  }, [projects, payments]);

  // Active slice details for hover states
  const activeCompletedSlice = completedData.list.find(s => s.id === hoveredCompletedId);
  const activeRemainingSlice = remainingData.list.find(s => s.id === hoveredRemainingId);

  return (
    <div className="dashboard-analytics-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
      {/* ── Financial Health Overview Card ── */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {/* Card Header & Global Metrics */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', margin: 0 }}>
            <CreditCard size={16} color="var(--accent-primary)" />
            Financial Health
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              fontSize: '0.72rem',
              fontWeight: 600,
              padding: '3px 9px',
              borderRadius: '9999px',
              background: 'rgba(16, 185, 129, 0.12)',
              color: '#34d399',
              border: '1px solid rgba(16, 185, 129, 0.25)'
            }}>
              {collectionRate}% Collected
            </span>
          </div>
        </div>

        {/* Global Summary Pills */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div style={{
            padding: '10px 12px',
            background: 'rgba(16, 185, 129, 0.05)',
            border: '1px solid rgba(16, 185, 129, 0.15)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px'
          }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
              Total Completed
            </span>
            <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#10b981' }}>
              ₹{Math.round(totalCompleted).toLocaleString()}
            </span>
          </div>

          <div style={{
            padding: '10px 12px',
            background: 'rgba(245, 158, 11, 0.05)',
            border: '1px solid rgba(245, 158, 11, 0.15)',
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px'
          }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b' }} />
              Total Remaining
            </span>
            <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f59e0b' }}>
              ₹{Math.round(totalRemaining).toLocaleString()}
            </span>
          </div>
        </div>

        {/* ── Two Donut Charts Grid ── */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          alignItems: 'start'
        }}>
          
          {/* ──── Donut Chart 1: Project-wise Payment Completed ──── */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.04)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={13} color="#10b981" />
                Payment Completed
              </span>
              <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 600, background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '6px' }}>
                {completedData.list.length} {completedData.list.length === 1 ? 'proj' : 'projs'}
              </span>
            </div>

            {completedData.total === 0 ? (
              <div style={{ height: '150px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <AlertCircle size={20} opacity={0.4} />
                No payments completed yet.
              </div>
            ) : (
              <>
                {/* Donut SVG Graphic */}
                <div style={{ position: 'relative', width: '130px', height: '130px', margin: '0 auto', flexShrink: 0 }}>
                  <svg viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%', overflow: 'visible' }}>
                    <defs>
                      <filter id="glow-completed" x="-30%" y="-30%" width="160%" height="160%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feMerge>
                          <feMergeNode in="blur" />
                          <feMergeNode in="SourceGraphic" />
                        </feMerge>
                      </filter>
                    </defs>

                    {/* Empty track circle */}
                    <circle cx="60" cy="60" r={completedData.radius} fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth={11} />

                    {/* Slices */}
                    {completedData.list.map(slice => {
                      const isHovered = hoveredCompletedId === slice.id;
                      return (
                        <circle
                          key={slice.id}
                          cx="60"
                          cy="60"
                          r={completedData.radius}
                          fill="none"
                          stroke={slice.color}
                          strokeWidth={isHovered ? 15 : 11}
                          strokeDasharray={`${slice.dash} ${completedData.circumference - slice.dash}`}
                          strokeDashoffset={slice.offset}
                          strokeLinecap="butt"
                          filter={isHovered ? 'url(#glow-completed)' : 'none'}
                          style={{
                            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                            opacity: hoveredCompletedId && !isHovered ? 0.35 : 1,
                            cursor: 'pointer'
                          }}
                          onMouseEnter={() => setHoveredCompletedId(slice.id)}
                          onMouseLeave={() => setHoveredCompletedId(null)}
                        />
                      );
                    })}
                  </svg>

                  {/* Donut Center Info */}
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                    pointerEvents: 'none',
                    width: '80px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      fontSize: '0.62rem',
                      color: 'var(--text-muted)',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '75px'
                    }}>
                      {activeCompletedSlice ? activeCompletedSlice.title : 'Total Paid'}
                    </div>
                    <div style={{
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      color: activeCompletedSlice ? activeCompletedSlice.color : '#10b981',
                      lineHeight: '1.2',
                      marginTop: '2px',
                      transition: 'color 0.2s ease'
                    }}>
                      {activeCompletedSlice ? formatAmount(activeCompletedSlice.amount) : formatAmount(completedData.total)}
                    </div>
                    <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: '1px' }}>
                      {activeCompletedSlice ? `${Math.round(activeCompletedSlice.pct)}%` : '100%'}
                    </div>
                  </div>
                </div>

                {/* Project-wise Completed Breakdown List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {completedData.list.map(slice => {
                    const isHovered = hoveredCompletedId === slice.id;
                    return (
                      <div
                        key={slice.id}
                        onClick={() => {
                          if (slice.id !== 'other') {
                            window.location.hash = `#/projects/${slice.id}`;
                          }
                        }}
                        onMouseEnter={() => setHoveredCompletedId(slice.id)}
                        onMouseLeave={() => setHoveredCompletedId(null)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '5px 8px',
                          borderRadius: '8px',
                          background: isHovered ? 'rgba(255, 255, 255, 0.06)' : 'transparent',
                          cursor: slice.id !== 'other' ? 'pointer' : 'default',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', overflow: 'hidden', minWidth: 0 }}>
                          <span style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            background: slice.color,
                            flexShrink: 0,
                            boxShadow: isHovered ? `0 0 8px ${slice.color}` : 'none'
                          }} />
                          <span style={{
                            fontSize: '0.74rem',
                            color: isHovered ? '#fff' : 'var(--text-primary)',
                            fontWeight: isHovered ? 600 : 400,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}>
                            {slice.title}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                          <span style={{ fontSize: '0.74rem', fontWeight: 600, color: isHovered ? slice.color : 'var(--text-secondary)' }}>
                            ₹{Math.round(slice.amount).toLocaleString()}
                          </span>
                          <span style={{ fontSize: '0.64rem', color: 'var(--text-muted)', minWidth: '24px', textAlign: 'right' }}>
                            {Math.round(slice.pct)}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* ──── Donut Chart 2: Project-wise Payment Remaining ──── */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.04)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={13} color="#f59e0b" />
                Payment Remaining
              </span>
              <span style={{ fontSize: '0.7rem', color: '#f59e0b', fontWeight: 600, background: 'rgba(245, 158, 11, 0.1)', padding: '2px 6px', borderRadius: '6px' }}>
                {remainingData.list.length} {remainingData.list.length === 1 ? 'proj' : 'projs'}
              </span>
            </div>

            {remainingData.total === 0 ? (
              <div style={{ height: '150px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={24} color="#10b981" />
                <span>All projects fully settled!</span>
                <span style={{ fontSize: '0.68rem', color: '#34d399' }}>₹0 outstanding balance</span>
              </div>
            ) : (
              <>
                {/* Donut SVG Graphic */}
                <div style={{ position: 'relative', width: '130px', height: '130px', margin: '0 auto', flexShrink: 0 }}>
                  <svg viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%', overflow: 'visible' }}>
                    <defs>
                      <filter id="glow-remaining" x="-30%" y="-30%" width="160%" height="160%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feMerge>
                          <feMergeNode in="blur" />
                          <feMergeNode in="SourceGraphic" />
                        </feMerge>
                      </filter>
                    </defs>

                    {/* Empty track circle */}
                    <circle cx="60" cy="60" r={remainingData.radius} fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth={11} />

                    {/* Slices */}
                    {remainingData.list.map(slice => {
                      const isHovered = hoveredRemainingId === slice.id;
                      return (
                        <circle
                          key={slice.id}
                          cx="60"
                          cy="60"
                          r={remainingData.radius}
                          fill="none"
                          stroke={slice.color}
                          strokeWidth={isHovered ? 15 : 11}
                          strokeDasharray={`${slice.dash} ${remainingData.circumference - slice.dash}`}
                          strokeDashoffset={slice.offset}
                          strokeLinecap="butt"
                          filter={isHovered ? 'url(#glow-remaining)' : 'none'}
                          style={{
                            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                            opacity: hoveredRemainingId && !isHovered ? 0.35 : 1,
                            cursor: 'pointer'
                          }}
                          onMouseEnter={() => setHoveredRemainingId(slice.id)}
                          onMouseLeave={() => setHoveredRemainingId(null)}
                        />
                      );
                    })}
                  </svg>

                  {/* Donut Center Info */}
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                    pointerEvents: 'none',
                    width: '80px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      fontSize: '0.62rem',
                      color: 'var(--text-muted)',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '75px'
                    }}>
                      {activeRemainingSlice ? activeRemainingSlice.title : 'Outstanding'}
                    </div>
                    <div style={{
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      color: activeRemainingSlice ? activeRemainingSlice.color : '#f59e0b',
                      lineHeight: '1.2',
                      marginTop: '2px',
                      transition: 'color 0.2s ease'
                    }}>
                      {activeRemainingSlice ? formatAmount(activeRemainingSlice.amount) : formatAmount(remainingData.total)}
                    </div>
                    <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: '1px' }}>
                      {activeRemainingSlice ? `${Math.round(activeRemainingSlice.pct)}%` : '100%'}
                    </div>
                  </div>
                </div>

                {/* Project-wise Remaining Breakdown List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {remainingData.list.map(slice => {
                    const isHovered = hoveredRemainingId === slice.id;
                    return (
                      <div
                        key={slice.id}
                        onClick={() => {
                          window.location.hash = `#/projects/${slice.id}`;
                        }}
                        onMouseEnter={() => setHoveredRemainingId(slice.id)}
                        onMouseLeave={() => setHoveredRemainingId(null)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '5px 8px',
                          borderRadius: '8px',
                          background: isHovered ? 'rgba(255, 255, 255, 0.06)' : 'transparent',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', overflow: 'hidden', minWidth: 0 }}>
                          <span style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            background: slice.color,
                            flexShrink: 0,
                            boxShadow: isHovered ? `0 0 8px ${slice.color}` : 'none'
                          }} />
                          <span style={{
                            fontSize: '0.74rem',
                            color: isHovered ? '#fff' : 'var(--text-primary)',
                            fontWeight: isHovered ? 600 : 400,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}>
                            {slice.title}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                          <span style={{ fontSize: '0.74rem', fontWeight: 600, color: isHovered ? slice.color : 'var(--text-secondary)' }}>
                            ₹{Math.round(slice.amount).toLocaleString()}
                          </span>
                          <span style={{ fontSize: '0.64rem', color: 'var(--text-muted)', minWidth: '24px', textAlign: 'right' }}>
                            {Math.round(slice.pct)}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

        </div>
      </div>

      {/* ── Top Project Budgets Progress Section ── */}
      {topProjects.length > 0 && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', margin: 0 }}>
            <TrendingUp size={15} color="var(--accent-secondary)" />
            Top Project Budgets
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {topProjects.map(proj => (
              <div 
                key={proj.id} 
                onClick={() => {
                  window.location.hash = `#/projects/${proj.id}`;
                }}
                style={{ display: 'flex', flexDirection: 'column', gap: '6px', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px' }}>
                    {proj.title}
                  </span>
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                    ₹{Math.round(proj.received).toLocaleString()} <span style={{ color: 'var(--text-muted)' }}>/ {formatAmount(proj.budget)}</span>
                  </span>
                </div>
                
                {/* Horizontal Progress Bar */}
                <div style={{ width: '100%', height: '7px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
                  <div style={{
                    width: `${proj.pct}%`,
                    height: '100%',
                    background: proj.pct >= 100 
                      ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)' 
                      : 'linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
                    borderRadius: '4px',
                    transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
                  }} />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                  <span>Settled: {Math.round(proj.pct)}%</span>
                  <span style={{ display: 'flex', alignItems: 'center', color: 'var(--accent-primary)' }}>
                    Details <ChevronRight size={10} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
