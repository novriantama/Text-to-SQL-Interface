import React from 'react';
import { History, Clock, ChevronRight, RefreshCw, AlertCircle } from 'lucide-react';

export default function HistorySidebar({ history, onSelectHistoryItem, onRefreshHistory, isLoading }) {
  return (
    <aside className="glass-panel" style={{ padding: '1.25rem', height: 'fit-content' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <History size={18} color="var(--accent-primary)" />
          Query History
        </h3>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
          onClick={onRefreshHistory}
          disabled={isLoading}
          title="Refresh History"
        >
          <RefreshCw size={12} />
        </button>
      </div>

      {!history || history.length === 0 ? (
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem 0' }}>
          No past queries recorded for this session.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '600px', overflowY: 'auto', paddingRight: '0.2rem' }}>
          {history.map((item, idx) => {
            const confPct = Math.round((item.confidence_score || 0) * 100);
            const confColor = confPct >= 80 ? 'var(--success)' : confPct >= 60 ? 'var(--warning)' : 'var(--danger)';

            return (
              <div
                key={idx}
                className="glass-card"
                style={{ cursor: 'pointer', padding: '0.75rem' }}
                onClick={() => onSelectHistoryItem(item)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.88rem', fontWeight: '600', color: 'var(--text-primary)', lineClamp: 2, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.question}
                  </span>
                  <ChevronRight size={16} color="var(--text-muted)" style={{ flexShrink: 0, marginTop: '2px' }} />
                </div>

                <div style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', background: '#0d1117', padding: '0.3rem 0.5rem', borderRadius: 'var(--radius-sm)', marginBottom: '0.5rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.generated_sql}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Clock size={12} /> {item.execution_time_ms}ms • {item.rows_returned} rows
                  </span>

                  <span style={{ color: confColor, fontWeight: '700', background: `${confColor}15`, padding: '0.1rem 0.4rem', borderRadius: '4px', border: `1px solid ${confColor}40` }}>
                    {confPct}%
                  </span>
                </div>

                {item.warnings && item.warnings.length > 0 && (
                  <div style={{ marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <AlertCircle size={12} /> {item.warnings.length} warning(s)
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}
