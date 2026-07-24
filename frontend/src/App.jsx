import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import QueryInput from './components/QueryInput';
import AmbiguityCard from './components/AmbiguityCard';
import ConfidenceBreakdown from './components/ConfidenceBreakdown';
import SqlViewer from './components/SqlViewer';
import DataTable from './components/DataTable';
import FeedbackWidget from './components/FeedbackWidget';
import HistorySidebar from './components/HistorySidebar';
import { API_BASE_URL } from './config';

export default function App() {
  const [sessionId, setSessionId] = useState('default_session');
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [history, setHistory] = useState([]);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchHistory = useCallback(async (sid = sessionId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/v1/history?session_id=${encodeURIComponent(sid)}`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Error fetching session history:', err);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchHistory(sessionId);
  }, [sessionId, fetchHistory]);

  const handleSubmitQuery = async (queryText = question) => {
    if (!queryText.trim()) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE_URL}/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: queryText, session_id: sessionId })
      });

      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await res.text();
        throw new Error(`Server returned non-JSON response (${res.status}): ${text.slice(0, 100)}...`);
      }

      const data = await res.json();

      if (!res.ok) {
        if (data.detail && data.detail.message) {
          setErrorMsg(data.detail.message);
        } else {
          setErrorMsg('Failed to process text-to-SQL query.');
        }
        setResponse(null);
      } else {
        setResponse(data);
        fetchHistory(sessionId);
      }
    } catch (err) {
      setErrorMsg(`Network or server error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteCustomSql = async (customSql) => {
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE_URL}/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: `[Custom SQL]: ${customSql}`, session_id: sessionId })
      });

      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await res.text();
        throw new Error(`Server returned non-JSON response (${res.status}): ${text.slice(0, 100)}...`);
      }

      const data = await res.json();

      if (!res.ok) {
        if (data.detail && data.detail.message) {
          setErrorMsg(data.detail.message);
        } else {
          setErrorMsg('Failed to execute custom SQL statement.');
        }
      } else {
        setResponse(data);
        fetchHistory(sessionId);
      }
    } catch (err) {
      setErrorMsg(`Error executing custom SQL: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistoryItem = (item) => {
    setQuestion(item.question);
    setResponse({
      question: item.question,
      generated_sql: item.generated_sql,
      explanation: item.explanation,
      results: {
        data: [],
        columns: [],
        rows_returned: item.rows_returned,
        execution_time_ms: item.execution_time_ms
      },
      confidence: {
        overall_score: item.confidence_score,
        syntax_validity: 1.0,
        back_translation_match: item.confidence_score,
        result_sanity_score: 1.0,
        multi_query_consensus: 1.0,
        schema_coverage: 1.0,
        is_high_confidence: () => item.confidence_score >= 0.8
      },
      guardrails_passed: item.guardrails_passed,
      warnings: item.warnings || []
    });
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      <Header sessionId={sessionId} onSessionChange={setSessionId} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
        <main>
          <QueryInput
            question={question}
            setQuestion={setQuestion}
            onSubmit={() => handleSubmitQuery()}
            isLoading={isLoading}
          />

          {errorMsg && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', borderLeft: '4px solid var(--danger)', color: 'var(--danger)' }}>
              <strong>Error executing request: </strong> {errorMsg}
            </div>
          )}

          {response && (
            <>
              {response.clarification_needed ? (
                <AmbiguityCard
                  options={response.clarification_options}
                  onSelectOption={(sql, desc) => {
                    handleSubmitQuery(`Execute specific interpretation: ${desc}`);
                  }}
                />
              ) : (
                <>
                  <ConfidenceBreakdown
                    confidence={response.confidence}
                    guardrailsPassed={response.guardrails_passed}
                    warnings={response.warnings}
                  />

                  <SqlViewer
                    generatedSql={response.generated_sql}
                    explanation={response.explanation}
                    alternativeSql={response.alternative_sql}
                    alternativeExplanation={response.alternative_explanation}
                    onExecuteCustomSql={handleExecuteCustomSql}
                    isLoading={isLoading}
                  />

                  <DataTable
                    results={response.results}
                    explainPlan={response.results ? response.results.explain_plan : null}
                  />

                  <FeedbackWidget
                    question={response.question}
                    generatedSql={response.generated_sql}
                  />
                </>
              )}
            </>
          )}
        </main>

        <HistorySidebar
          history={history}
          onSelectHistoryItem={handleSelectHistoryItem}
          onRefreshHistory={() => fetchHistory(sessionId)}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
