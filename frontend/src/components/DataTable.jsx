import React, { useState, useMemo } from 'react';
import { Table, ArrowUpDown, ArrowUp, ArrowDown, Download, Search, FileText } from 'lucide-react';

export default function DataTable({ results, explainPlan }) {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc'); // 'asc' or 'desc'
  const [searchTerm, setSearchTerm] = useState('');
  const [showExplain, setShowExplain] = useState(false);

  if (!results || !results.data || results.data.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Table size={32} style={{ marginBottom: '0.5rem', opacity: 0.5 }} />
        <p>No results returned or query executed without output.</p>
      </div>
    );
  }

  const columns = results.columns && results.columns.length > 0 ? results.columns : Object.keys(results.data[0]);

  const handleSort = (col) => {
    if (sortColumn === col) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col);
      setSortDirection('asc');
    }
  };

  const filteredData = useMemo(() => {
    let data = [...results.data];

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      data = data.filter((row) =>
        Object.values(row).some((val) => val != null && String(val).toLowerCase().includes(term))
      );
    }

    if (sortColumn) {
      data.sort((a, b) => {
        const valA = a[sortColumn];
        const valB = b[sortColumn];
        if (valA === valB) return 0;
        if (valA == null) return 1;
        if (valB == null) return -1;
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortDirection === 'asc' ? valA - valB : valB - valA;
        }
        return sortDirection === 'asc'
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
    }

    return data;
  }, [results.data, searchTerm, sortColumn, sortDirection]);

  const exportCsv = () => {
    const header = columns.join(',');
    const rows = filteredData.map((row) =>
      columns.map((col) => {
        const val = row[col];
        if (val == null) return '""';
        return `"${String(val).replace(/"/g, '""')}"`;
      }).join(',')
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [header, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `query_results_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Table size={18} color="var(--accent-primary)" />
            Execution Results
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
              ({filteredData.length} of {results.rows_returned} rows • {results.execution_time_ms}ms)
            </span>
          </h3>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '0.6rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              className="input-field"
              style={{ paddingLeft: '2rem', paddingRight: '0.6rem', paddingTop: '0.35rem', paddingBottom: '0.35rem', fontSize: '0.8rem', width: '180px' }}
              placeholder="Filter results..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {explainPlan && (
            <button
              type="button"
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
              onClick={() => setShowExplain(!showExplain)}
            >
              <FileText size={14} /> EXPLAIN Plan
            </button>
          )}

          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
            onClick={exportCsv}
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {showExplain && explainPlan && (
        <div style={{ marginBottom: '1rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.8rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
            Database EXPLAIN Execution Plan
          </div>
          <pre className="code-box" style={{ fontSize: '0.78rem', maxHeight: '180px' }}>
            {explainPlan}
          </pre>
        </div>
      )}

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} onClick={() => handleSort(col)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span>{col}</span>
                    {sortColumn === col ? (
                      sortDirection === 'asc' ? <ArrowUp size={14} color="var(--accent-primary)" /> : <ArrowDown size={14} color="var(--accent-primary)" />
                    ) : (
                      <ArrowUpDown size={12} color="var(--text-muted)" style={{ opacity: 0.4 }} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.map((row, rowIdx) => (
              <tr key={rowIdx}>
                {columns.map((col) => (
                  <td key={col}>
                    {row[col] === null ? (
                      <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>NULL</span>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
