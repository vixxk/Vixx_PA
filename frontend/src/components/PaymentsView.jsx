import React, { useState, useEffect } from 'react';
import { Plus, Trash2, IndianRupee, Calendar, FileText, CheckCircle, AlertTriangle, Clock, TrendingUp } from 'lucide-react';
import { api } from '../services/api';

export default function PaymentsView({ projects = [], onRefresh }) {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [selectedFilterProjectId, setSelectedFilterProjectId] = useState('all');
  
  // Form state
  const [projectId, setProjectId] = useState('');
  const [amount, setAmount] = useState('');

  const [paymentType, setPaymentType] = useState('Advance');
  const [status, setStatus] = useState('pending');
  const [receivedDate, setReceivedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const data = await api.payments.list();
      setPayments(data || []);
    } catch (err) {
      console.error("Failed to fetch payments:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!projectId || !amount) {
      setError("Please select a project and enter an amount.");
      return;
    }

    setFormLoading(true);
    setError('');

    try {
      await api.payments.create({
        project_id: projectId,
        amount: parseFloat(amount),
        currency: 'INR',
        payment_type: paymentType,
        status,
        received_date: receivedDate ? new Date(receivedDate).toISOString() : null,
        notes: notes.trim() || null
      });

      // Clear Form
      setProjectId('');
      setAmount('');
      setReceivedDate('');
      setNotes('');
      setShowForm(false);
      
      // Refresh Data
      fetchPayments();
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.message || "Failed to log payment transaction");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (id) => {
    window.showConfirm("Are you sure you want to delete this payment record?", async () => {
      const originalPayments = [...payments];
      setPayments(prev => prev.filter(p => p.id !== id));
      try {
        await api.payments.delete(id);
        if (onRefresh) onRefresh();
      } catch (err) {
        setPayments(originalPayments);
        alert("Failed to delete payment record: " + err.message);
      }
    });
  };

  const getStatusIcon = (st) => {
    if (st === 'received') return <CheckCircle size={14} style={{ color: '#34d399' }} />;
    if (st === 'overdue') return <AlertTriangle size={14} style={{ color: '#f87171' }} />;
    return <Clock size={14} style={{ color: '#fbbf24' }} />;
  };

  // Aggregated financials
  const filteredPayments = selectedFilterProjectId === 'all'
    ? payments
    : payments.filter(p => p.project_id === selectedFilterProjectId);

  const totalReceived = filteredPayments
    .filter(p => p.status === 'received')
    .reduce((sum, p) => sum + parseFloat(p.amount), 0);

  const totalProjectsValue = selectedFilterProjectId === 'all'
    ? projects.reduce((sum, p) => sum + parseFloat(p.total_amount || 0), 0)
    : parseFloat(projects.find(p => p.id === selectedFilterProjectId)?.total_amount || 0);

  const pendingAmountToBeReceived = Math.max(0, totalProjectsValue - totalReceived);

  // Timeline Graph Calculations
  const chronologicalPayments = [...filteredPayments]
    .filter(p => p.status === 'received')
    .sort((a, b) => new Date(a.received_date || a.created_at) - new Date(b.received_date || b.created_at));

  let runningSum = 0;
  const dataPoints = chronologicalPayments.map(p => {
    runningSum += parseFloat(p.amount);
    return {
      id: p.id,
      date: new Date(p.received_date || p.created_at),
      amount: parseFloat(p.amount),
      cumulative: runningSum,
      project: projects.find(pr => pr.id === p.project_id)?.title || 'General Project',
      type: p.payment_type
    };
  });

  const chartPoints = [];
  if (dataPoints.length > 0) {
    const firstDate = new Date(dataPoints[0].date);
    const baselineDate = new Date(firstDate.getTime() - 15 * 24 * 60 * 60 * 1000);
    chartPoints.push({ date: baselineDate, cumulative: 0 });
    chartPoints.push(...dataPoints);
  }

  const maxCumulative = dataPoints.length > 0 ? dataPoints[dataPoints.length - 1].cumulative : 0;
  const minTime = chartPoints.length > 0 ? chartPoints[0].date.getTime() : 0;
  const maxTime = chartPoints.length > 0 ? chartPoints[chartPoints.length - 1].date.getTime() : 0;
  const timeDiff = maxTime - minTime || 1;

  const svgWidth = 620;
  const svgHeight = 300;
  const paddingX = 55;
  const paddingY = 35;

  const pointsWithCoords = chartPoints.map((p, idx) => {
    const x = paddingX + (timeDiff === 0 ? 0 : ((p.date.getTime() - minTime) / timeDiff) * (svgWidth - 2 * paddingX));
    const y = svgHeight - paddingY - (maxCumulative === 0 ? 0 : (p.cumulative / maxCumulative) * (svgHeight - 2 * paddingY));
    return { ...p, x, y };
  });

  // Smooth bezier curve path
  const smoothLine = (pts) => {
    if (pts.length < 2) return '';
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      const prev = pts[i - 1];
      const curr = pts[i];
      const cpx = (prev.x + curr.x) / 2;
      d += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
    }
    return d;
  };
  const linePath = smoothLine(pointsWithCoords);
  const areaPath = pointsWithCoords.length > 0 ? `${linePath} L ${pointsWithCoords[pointsWithCoords.length - 1].x} ${svgHeight - paddingY} L ${pointsWithCoords[0].x} ${svgHeight - paddingY} Z` : '';
  const yTicks = [0, 0.25, 0.5, 0.75, 1];

  const formatAxisAmount = (val) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}K`;
    return `₹${val}`;
  };

  const formatDate = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };



  return (
    <div className="payments-view-container" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card-title-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', width: '100%', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1 1 auto', minWidth: '160px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, whiteSpace: 'nowrap' }}>Filter Project:</span>
          <select 
            value={selectedFilterProjectId} 
            onChange={(e) => setSelectedFilterProjectId(e.target.value)}
            style={{ flex: '1 1 auto', minWidth: '100px', maxWidth: '220px', padding: '6px 10px', fontSize: '0.8rem' }}
          >
            <option value="all">All Projects</option>
            {projects.map(pr => (
              <option key={pr.id} value={pr.id}>{pr.title}</option>
            ))}
          </select>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)} style={{ flexShrink: 0, whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
          <Plus size={14} /> Log Payment
        </button>
      </div>

      {/* Aggregate Cards */}
      <div className="stats-bar" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
        {loading ? (
          [1, 2].map(i => (
            <div key={i} className="glass-panel stat-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="skeleton-pulse" style={{ width: '60%', height: '14px', borderRadius: '4px' }} />
              <div className="skeleton-pulse" style={{ width: '40%', height: '24px', borderRadius: '4px' }} />
            </div>
          ))
        ) : (
          <>
            <div className="glass-panel stat-card" style={{ borderLeft: '4px solid #34d399' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="stat-label">Total Revenue Earned</span>
                <CheckCircle size={20} color="#34d399" />
              </div>
              <span className="stat-value" style={{ color: '#34d399' }}>₹{Math.round(totalReceived).toLocaleString()}</span>
            </div>

            <div className="glass-panel stat-card" style={{ borderLeft: '4px solid #fbbf24' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="stat-label">Pending Amount to be Received</span>
                <Clock size={20} color="#fbbf24" />
              </div>
              <span className="stat-value" style={{ color: '#fbbf24' }}>₹{Math.round(pendingAmountToBeReceived).toLocaleString()}</span>
            </div>
          </>
        )}
      </div>

      {/* Revenue Growth Timeline Graph */}
      {!loading && (
        <div className="glass-panel" style={{ padding: '24px 20px', position: 'relative', background: 'linear-gradient(180deg, rgba(15, 12, 28, 0.8) 0%, rgba(15, 12, 28, 0.5) 100%)' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={16} color="var(--accent-primary)" />
            Revenue Growth Timeline
            {selectedFilterProjectId !== 'all' && (
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 400, marginLeft: '4px' }}>
                — {projects.find(p => p.id === selectedFilterProjectId)?.title}
              </span>
            )}
          </h3>
          {dataPoints.length === 0 ? (
            <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem', flexDirection: 'column', gap: '8px' }}>
              <TrendingUp size={32} color="rgba(255,255,255,0.08)" />
              No received payments to display on the timeline.
            </div>
          ) : (
            <div style={{ position: 'relative', width: '100%', height: '320px' }}>
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} width="100%" height="100%" style={{ overflow: 'visible' }}>
                <defs>
                  <linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.3"/>
                    <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.08"/>
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.0"/>
                  </linearGradient>
                  <linearGradient id="line-gradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#a78bfa"/>
                    <stop offset="50%" stopColor="#8b5cf6"/>
                    <stop offset="100%" stopColor="#c084fc"/>
                  </linearGradient>
                  <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="blur"/>
                    <feMerge>
                      <feMergeNode in="blur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                  <filter id="dot-glow">
                    <feGaussianBlur stdDeviation="4" result="blur"/>
                    <feMerge>
                      <feMergeNode in="blur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>

                {/* Grid Lines */}
                {yTicks.map((t, idx) => {
                  const yVal = svgHeight - paddingY - t * (svgHeight - 2 * paddingY);
                  return (
                    <g key={idx}>
                      <line x1={paddingX} y1={yVal} x2={svgWidth - paddingX} y2={yVal} stroke="rgba(255, 255, 255, 0.04)" strokeDasharray="3 6" />
                      <text x={paddingX - 10} y={yVal + 4} fill="rgba(255,255,255,0.4)" fontSize="13" fontWeight="500" textAnchor="end" fontFamily="'Inter', sans-serif">
                        {formatAxisAmount(Math.round(t * maxCumulative))}
                      </text>
                    </g>
                  );
                })}

                {/* X Axis Line */}
                <line x1={paddingX} y1={svgHeight - paddingY} x2={svgWidth - paddingX} y2={svgHeight - paddingY} stroke="rgba(255, 255, 255, 0.06)" />

                {/* Area Fill */}
                {areaPath && <path d={areaPath} fill="url(#area-gradient)" />}

                {/* Glow Line (behind) */}
                {linePath && <path d={linePath} fill="none" stroke="#8b5cf6" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" opacity="0.15" filter="url(#glow)" />}

                {/* Main Line Path */}
                {linePath && <path d={linePath} fill="none" stroke="url(#line-gradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />}

                {/* Vertical indicator lines on hover */}
                {hoveredPoint && hoveredPoint.id && (
                  <line x1={hoveredPoint.x} y1={hoveredPoint.y} x2={hoveredPoint.x} y2={svgHeight - paddingY} stroke="rgba(139, 92, 246, 0.3)" strokeWidth="1" strokeDasharray="4 3" />
                )}

                {/* Data Dots & X Labels */}
                {pointsWithCoords.map((p, idx) => (
                  <g key={idx}>
                    {idx > 0 && (
                      <>
                        {/* Outer glow circle */}
                        <circle cx={p.x} cy={p.y} r="10" fill="#8b5cf6" opacity={hoveredPoint?.id === p.id ? 0.2 : 0} style={{ transition: 'opacity 0.2s ease' }} />
                        <circle 
                          cx={p.x} 
                          cy={p.y} 
                          r={hoveredPoint?.id === p.id ? "5.5" : "4"} 
                          fill={hoveredPoint?.id === p.id ? '#8b5cf6' : '#0f0c1c'}
                          stroke={hoveredPoint?.id === p.id ? '#c084fc' : '#8b5cf6'}
                          strokeWidth={hoveredPoint?.id === p.id ? "2.5" : "2"} 
                          style={{ cursor: 'pointer', transition: 'all 0.2s ease' }} 
                          onMouseEnter={() => setHoveredPoint(p)} 
                          onMouseLeave={() => setHoveredPoint(null)} 
                        />
                      </>
                    )}
                    {/* X-axis date labels — show all if few points, otherwise first + last + alternating */}
                    {(idx === 0 || idx === pointsWithCoords.length - 1 || (pointsWithCoords.length < 10 && idx > 0)) && (
                      <text x={p.x} y={svgHeight - 10} fill="rgba(255,255,255,0.4)" fontSize="12.5" fontWeight="500" textAnchor="middle" fontFamily="'Inter', sans-serif">
                        {p.date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                      </text>
                    )}
                  </g>
                ))}
              </svg>

              {/* Hover Tooltip */}
              {hoveredPoint && hoveredPoint.amount && (
                <div style={{
                  position: 'absolute',
                  left: `${(hoveredPoint.x / svgWidth) * 100}%`,
                  top: `${(hoveredPoint.y / svgHeight) * 100 - 12}px`,
                  transform: 'translate(-50%, -100%)',
                  background: 'rgba(10, 8, 22, 0.96)',
                  border: '1px solid rgba(139, 92, 246, 0.4)',
                  borderRadius: '10px',
                  padding: '10px 14px',
                  fontSize: '0.82rem',
                  color: 'var(--text-primary)',
                  zIndex: 10,
                  pointerEvents: 'none',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.6), 0 0 20px rgba(139, 92, 246, 0.1)',
                  whiteSpace: 'nowrap',
                  backdropFilter: 'blur(12px)'
                }}>
                  <div style={{ fontWeight: 600, marginBottom: '4px', fontSize: '0.85rem' }}>{hoveredPoint.project}</div>
                  <div style={{ color: '#a78bfa', fontWeight: 700, fontSize: '1rem' }}>+₹{hoveredPoint.amount.toLocaleString()}</div>
                  <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: '0.75rem', marginTop: '4px' }}>
                    Total: ₹{hoveredPoint.cumulative.toLocaleString()} · {formatDate(hoveredPoint.date)}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Log Payment Form */}
      {showForm && (
        <form className="glass-panel" onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Log Payment Milestone</h3>
          
          {error && <p style={{ color: '#f87171', fontSize: '0.85rem' }}>{error}</p>}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Associated Project</label>
              <select className="input-field" value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
                <option value="">-- Select Project --</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Payment Milestone Type</label>
              <select className="input-field" value={paymentType} onChange={(e) => setPaymentType(e.target.value)}>
                <option value="Advance">Advance Payment</option>
                <option value="Partial">Milestone Release</option>
                <option value="Final">Final Release</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Amount</label>
              <input type="number" step="0.01" className="input-field" placeholder="10000" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </div>

          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Status</label>
              <select className="input-field" value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="pending">Pending</option>
                <option value="received">Received</option>
                <option value="overdue">Overdue</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Received Date (Optional)</label>
              <input type="date" className="input-field" value={receivedDate} onChange={(e) => setReceivedDate(e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Transaction Notes</label>
            <textarea className="input-field" style={{ minHeight: '60px', fontFamily: 'inherit' }} placeholder="Invoice reference or milestone details..." value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? 'Logging...' : 'Log Transaction'}
            </button>
          </div>
        </form>
      )}

      {/* Transaction Timeline */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Transactions Log</h3>
        </div>
        
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[1, 2, 3].map(i => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', width: '60%' }}>
                  <div className="skeleton-pulse" style={{ width: '36px', height: '36px', borderRadius: '8px' }} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '80%' }}>
                    <div className="skeleton-pulse" style={{ width: '50%', height: '14px', borderRadius: '4px' }} />
                    <div className="skeleton-pulse" style={{ width: '70%', height: '12px', borderRadius: '4px' }} />
                  </div>
                </div>
                <div className="skeleton-pulse" style={{ width: '80px', height: '24px', borderRadius: '12px' }} />
              </div>
            ))}
          </div>
        ) : filteredPayments.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '24px' }}>
            {selectedFilterProjectId === 'all' ? 'No payments logged yet.' : 'No payments logged for this project.'}
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredPayments.map(p => {
              const associatedProject = projects.find(pr => pr.id === p.project_id);
              const projectTitle = associatedProject ? associatedProject.title : 'General Project';

              return (
                <div key={p.id} className="glass-panel list-item" style={{ 
                  padding: '16px 20px', 
                  borderRadius: '16px', 
                  background: 'var(--glass-bg)', 
                  border: '1px solid var(--glass-border)',
                  backdropFilter: 'var(--glass-blur)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, minWidth: 0 }}>
                    <div style={{ 
                      width: '42px', 
                      height: '42px', 
                      borderRadius: '12px', 
                      background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)', 
                      border: '1px solid rgba(139, 92, 246, 0.25)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      color: 'var(--accent-primary)',
                      flexShrink: 0
                    }}>
                      <IndianRupee size={18} />
                    </div>
                    
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          ₹{Math.round(parseFloat(p.amount)).toLocaleString()}
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
                          background: p.status === 'received' ? 'rgba(16, 185, 129, 0.1)' : p.status === 'overdue' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(251, 191, 36, 0.1)',
                          color: p.status === 'received' ? '#10b981' : p.status === 'overdue' ? '#f87171' : '#fbbf24',
                          border: p.status === 'received' ? '1px solid rgba(16, 185, 129, 0.2)' : p.status === 'overdue' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(251, 191, 36, 0.2)'
                        }}>
                          {p.status.toUpperCase()}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{projectTitle}</span>
                        <span style={{ color: 'rgba(255,255,255,0.15)' }}>•</span>
                        <span>{formatDate(p.received_date || p.created_at)}</span>
                        {p.notes && (
                          <>
                            <span style={{ color: 'rgba(255,255,255,0.15)' }}>•</span>
                            <span style={{ fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '300px' }} title={p.notes}>
                              {p.notes}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <button className="btn" style={{ padding: '8px', background: 'transparent', color: 'rgba(239, 68, 68, 0.6)', border: 'none', cursor: 'pointer', marginLeft: '12px' }} onClick={() => handleDelete(p.id)}>
                    <Trash2 size={15} />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
