import React, { useState, useEffect } from 'react';
import { Code, Edit3, Copy, Check, Play, GitBranch } from 'lucide-react';

export default function SqlViewer({ generatedSql, explanation, alternativeSql, alternativeExplanation, onExecuteCustomSql, isLoading }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedSql, setEditedSql] = useState(generatedSql || '');
  const [activeTab, setActiveTab] = useState('primary');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setEditedSql(generatedSql || '');
  }, [generatedSql]);

  const handleCopy = (textToCopy) => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunCustom = () => {
    if (editedSql.trim() && onExecuteCustomSql) {
      onExecuteCustomSql(editedSql);
    }
  };

  const highlightSql = (sql) => {
    if (!sql) return '';
    const keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT', 'JOIN', 'LEFT JOIN', 'INNER JOIN', 'ON', 'AS', 'SUM', 'COUNT', 'AVG', 'MIN', 'MAX', 'HAVING', 'AND', 'OR', 'NOT', 'IN', 'WITH'];
    let formatted = sql;

    keywords.forEach((kw) => {
      const regex = new RegExp(`\\b(${kw})\\b`, 'gi');
      formatted = formatted.replace(regex, `<span class="code-keyword">$1</span>`);
    });

    return formatted;
  };

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', padding: '0.2rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <button
              type="button"
              onClick={() => setActiveTab('primary')}
              style={{
                background: activeTab === 'primary' ? 'var(--accent-primary)' : 'transparent',
                color: activeTab === 'primary' ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                padding: '0.3rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <Code size={14} /> Primary SQL
            </button>

            {alternativeSql && alternativeSql !== generatedSql && (
              <button
                type="button"
                onClick={() => setActiveTab('alternative')}
                style={{
                  background: activeTab === 'alternative' ? 'var(--accent-primary)' : 'transparent',
                  color: activeTab === 'alternative' ? '#ffffff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '0.3rem 0.8rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem'
                }}
              >
                <GitBranch size={14} /> Alternative Formulation
              </button>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
            onClick={() => handleCopy(activeTab === 'primary' ? (isEditing ? editedSql : generatedSql) : alternativeSql)}
          >
            {copied ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy SQL'}
          </button>

          {activeTab === 'primary' && (
            <button
              type="button"
              className={`btn ${isEditing ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
              onClick={() => setIsEditing(!isEditing)}
            >
              <Edit3 size={14} />
              {isEditing ? 'View Highlighting' : 'Edit SQL (Power Mode)'}
            </button>
          )}
        </div>
      </div>

      {activeTab === 'primary' ? (
        <>
          {isEditing ? (
            <div>
              <textarea
                className="input-field"
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.9rem',
                  minHeight: '120px',
                  lineHeight: '1.5',
                  marginBottom: '0.75rem'
                }}
                value={editedSql}
                onChange={(e) => setEditedSql(e.target.value)}
                placeholder="Edit SQL query manually..."
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleRunCustom}
                  disabled={isLoading || !editedSql.trim()}
                >
                  <Play size={16} /> Execute Modified SQL
                </button>
              </div>
            </div>
          ) : (
            <pre
              className="code-box"
              dangerouslySetInnerHTML={{ __html: highlightSql(generatedSql) }}
            />
          )}

          {explanation && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Natural Explanation: </strong> {explanation}
            </div>
          )}
        </>
      ) : (
        <>
          <pre
            className="code-box"
            dangerouslySetInnerHTML={{ __html: highlightSql(alternativeSql) }}
          />
          {alternativeExplanation && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Alternative Strategy: </strong> {alternativeExplanation}
            </div>
          )}
        </>
      )}
    </div>
  );
}
