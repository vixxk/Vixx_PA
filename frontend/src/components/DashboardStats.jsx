import React from 'react';
import { Briefcase, CheckSquare, Calendar } from 'lucide-react';

export default function DashboardStats({ projects = [], todos = [], events = [] }) {
  const activeProjects = projects.filter(p => p.status !== 'completed' && p.status !== 'finished').length;
  const pendingTodos = todos.filter(t => t.status !== 'done').length;
  const completedEvents = events.filter(e => e.status === 'completed').length;

  return (
    <div className="stats-bar">
      <div className="glass-panel stat-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="stat-label">Active Projects</span>
          <Briefcase size={20} color="var(--accent-primary)" />
        </div>
        <span className="stat-value">{activeProjects}</span>
      </div>

      <div className="glass-panel stat-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="stat-label">Pending Tasks</span>
          <CheckSquare size={20} color="var(--accent-secondary)" />
        </div>
        <span className="stat-value">{pendingTodos}</span>
      </div>

      <div className="glass-panel stat-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="stat-label">Timeline Checkpoints</span>
          <Calendar size={20} color="#34d399" />
        </div>
        <span className="stat-value">{events.length}</span>
      </div>
    </div>
  );
}
