import React from 'react';
import { Database, ShieldCheck, Cpu } from 'lucide-react';

export default function Header({ sessionId, onSessionChange }) {
  return (
    <header className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ background: 'var(--accent-gradient)', padding: '0.6rem', borderRadius: 'var(--radius-md)', display: 'flex' }}>
          <Database size={24} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: '700', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            Enterprise Text-to-SQL Interface
            <span style={{ fontSize: '0.7rem', background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', padding: '0.2rem 0.5rem', borderRadius: '12px', border: '1px solid rgba(59, 130, 246, 0.4)' }}>
              v1.0 Guardrails
            </span>
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Schema-aware SQL generation with read-only sandboxing & 5-signal hallucination detection
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'rgba(16, 185, 129, 0.1)', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <ShieldCheck size={16} color="#10b981" />
          <span>Sandbox Active</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Cpu size={16} color="var(--text-muted)" />
          <input
            type="text"
            className="input-field"
            style={{ padding: '0.35rem 0.6rem', fontSize: '0.8rem', width: '150px' }}
            value={sessionId}
            onChange={(e) => onSessionChange(e.target.value)}
            placeholder="Session ID"
            title="Session ID for query history"
          />
        </div>
      </div>
    </header>
  );
}
