import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';

export default function ConfidenceBreakdown({ confidence, guardrailsPassed, warnings }) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!confidence) return null;

  const overallPct = Math.round((confidence.overall_score || 0) * 100);
  const isHigh = overallPct >= 80;
  const isMedium = overallPct >= 60 && overallPct < 80;

  const badgeBg = isHigh ? 'var(--success-bg)' : isMedium ? 'var(--warning-bg)' : 'var(--danger-bg)';
  const badgeColor = isHigh ? 'var(--success)' : isMedium ? 'var(--warning)' : 'var(--danger)';
  const badgeLabel = isHigh ? 'High Confidence' : isMedium ? 'Medium Confidence' : 'Low Confidence';

  const signals = [
    { name: 'SQL Syntax & Safety', score: confidence.syntax_validity, weight: '20%' },
    { name: 'Back-Translation Alignment', score: confidence.back_translation_match, weight: '25%' },
    { name: 'Result Sanity Checks', score: confidence.result_sanity_score, weight: '20%' },
    { name: 'Multi-Query Consensus', score: confidence.multi_query_consensus, weight: '20%' },
    { name: 'Schema Coverage', score: confidence.schema_coverage, weight: '15%' },
  ];

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: badgeBg, border: `1px solid ${badgeColor}`, color: badgeColor, padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '700', fontSize: '1.2rem' }}>
            <ShieldCheck size={22} />
            <span>{overallPct}%</span>
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: '600', color: badgeColor }}>
              {badgeLabel}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Composite verification score across 5 validation signals
            </div>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => setIsExpanded(!isExpanded)}
          style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
        >
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          {isExpanded ? 'Hide Signal Breakdown' : 'Show Signal Breakdown'}
        </button>
      </div>

      {warnings && warnings.length > 0 && (
        <div style={{ marginTop: '1rem', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 'var(--radius-sm)', padding: '0.75rem 1rem' }}>
          {warnings.map((warn, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', fontSize: '0.83rem', color: 'var(--warning)', margin: '0.2rem 0' }}>
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>{warn}</span>
            </div>
          ))}
        </div>
      )}

      {isExpanded && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          {signals.map((sig, idx) => {
            const pct = Math.round((sig.score || 0) * 100);
            const sigColor = pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';
            return (
              <div key={idx} className="glass-card" style={{ padding: '0.75rem 0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                  <span>{sig.name}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Weight {sig.weight}</span>
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: sigColor, marginBottom: '0.4rem' }}>
                  {pct}%
                </div>
                <div style={{ background: 'rgba(255,255,255,0.1)', height: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ background: sigColor, width: `${pct}%`, height: '100%', transition: 'width 0.3s ease' }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
