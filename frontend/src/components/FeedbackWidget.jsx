import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send, CheckCircle2, MessageSquare } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function FeedbackWidget({ question, generatedSql }) {
  const [feedbackStatus, setFeedbackStatus] = useState(null);
  const [showIncorrectForm, setShowIncorrectForm] = useState(false);
  const [comments, setComments] = useState('');
  const [suggestedSql, setSuggestedSql] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState('');

  const submitFeedback = async (isCorrect, commentText = comments, sqlText = suggestedSql) => {
    setFeedbackStatus('submitting');
    try {
      const res = await fetch(`${API_BASE_URL}/v1/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          generated_sql: generatedSql,
          is_correct: isCorrect,
          comments: commentText || null,
          suggested_sql: sqlText || null
        })
      });

      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await res.text();
        throw new Error(`Server returned non-JSON response (${res.status}): ${text.slice(0, 100)}...`);
      }

      const data = await res.json();
      if (res.ok) {
        setFeedbackStatus(isCorrect ? 'submitted_correct' : 'submitted_incorrect');
        setFeedbackMsg(data.message || 'Feedback recorded successfully.');
      } else {
        setFeedbackStatus(null);
        alert('Failed to submit feedback.');
      }
    } catch (err) {
      setFeedbackStatus(null);
      alert(`Feedback submission error: ${err.message}`);
    }
  };

  if (feedbackStatus === 'submitted_correct' || feedbackStatus === 'submitted_incorrect') {
    return (
      <div className="glass-card" style={{ padding: '0.8rem 1rem', marginTop: '1rem', border: '1px solid var(--success-bg)', background: 'var(--success-bg)', display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.88rem', color: 'var(--success)' }}>
        <CheckCircle2 size={18} />
        <span>{feedbackMsg}</span>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ marginTop: '1.25rem', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ fontSize: '0.88rem', fontWeight: '600', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <MessageSquare size={16} color="var(--accent-primary)" />
          <span>Was this SQL query output correct? (Flywheel Feedback)</span>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', borderColor: 'rgba(16, 185, 129, 0.4)', color: '#34d399' }}
            onClick={() => submitFeedback(true)}
            disabled={feedbackStatus === 'submitting'}
          >
            <ThumbsUp size={14} /> Correct (Add to Few-Shot)
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', borderColor: 'rgba(239, 68, 68, 0.4)', color: '#f87171' }}
            onClick={() => setShowIncorrectForm(!showIncorrectForm)}
            disabled={feedbackStatus === 'submitting'}
          >
            <ThumbsDown size={14} /> Incorrect (Add to Eval Suite)
          </button>
        </div>
      </div>

      {showIncorrectForm && (
        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            Help us improve our evaluation dataset by describing why this query was incorrect:
          </div>

          <textarea
            className="input-field"
            style={{ fontSize: '0.82rem', minHeight: '60px', marginBottom: '0.5rem' }}
            placeholder="Comments (e.g. JOIN condition missed completed status filter)..."
            value={comments}
            onChange={(e) => setComments(e.target.value)}
          />

          <input
            type="text"
            className="input-field"
            style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', marginBottom: '0.75rem' }}
            placeholder="Suggested Correct SQL (optional)..."
            value={suggestedSql}
            onChange={(e) => setSuggestedSql(e.target.value)}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-primary"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}
              onClick={() => submitFeedback(false)}
              disabled={feedbackStatus === 'submitting'}
            >
              <Send size={14} /> Submit Incorrect Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
