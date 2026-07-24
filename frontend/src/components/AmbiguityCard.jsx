import React from 'react';
import { HelpCircle, ArrowRight } from 'lucide-react';

export default function AmbiguityCard({ options, onSelectOption }) {
  if (!options || options.length === 0) return null;

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem', borderLeft: '4px solid var(--warning)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
        <HelpCircle size={22} color="var(--warning)" />
        <h3 style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--warning)' }}>
          Ambiguous Question Detected — Clarification Required
        </h3>
      </div>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Your question can be interpreted in multiple valid business contexts. Please select your desired interpretation:
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
        {options.map((opt, idx) => (
          <div key={idx} className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: '700', fontSize: '0.95rem', color: 'var(--accent-primary)' }}>
                  Interpretation {idx + 1}: {opt.label}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                {opt.description}
              </p>
              <div className="code-box" style={{ fontSize: '0.8rem', padding: '0.6rem', marginBottom: '0.75rem' }}>
                {opt.example_sql}
              </div>
            </div>

            <button
              type="button"
              className="btn btn-secondary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => onSelectOption(opt.example_sql, opt.description)}
            >
              Execute {opt.label} <ArrowRight size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
