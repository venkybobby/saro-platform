import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export default function MVP2Audit() {
  const [tab, setTab] = useState('run')
  const [form, setForm] = useState({ model_name: '', model_version: '1.0', use_case: '', jurisdiction: 'EU', risk_category: 'medium' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [audits, setAudits] = useState([])
  const [matrix, setMatrix] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listAudits().then(setAudits).catch(() => {})
    api.complianceMatrix('EU').then(setMatrix).catch(() => {})
  }, [])

  const handleAudit = async () => {
    if (!form.model_name || !form.use_case) { setError('Model name and use case are required'); return }
    setLoading(true); setError(null)
    try {
      const res = await api.runAudit(form)
      setResult(res)
      setAudits(a => [res, ...a])
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const riskBadge = (risk) => {
    const map = { critical: 'badge-red', high: 'badge-red', medium: 'badge-amber', low: 'badge-green' }
    return map[risk] || 'badge-gray'
  }

  const statusBadge = (status) => {
    const map = { compliant: 'badge-green', non_compliant: 'badge-red', pending: 'badge-amber', review: 'badge-cyan' }
    return map[status] || 'badge-gray'
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">AI Model Audit</h1>
          <p className="page-subtitle">Run compliance audits, assess regulatory risk, and get actionable remediation plans</p>
        </div>
        <span className="mvp-tag mvp2-tag">◉ MVP2</span>
      </div>

      <div className="tabs">
        {['run', 'history', 'matrix'].map(t => (
          <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'run' ? '▶ Run Audit' : t === 'history' ? '📋 Audit History' : '📊 Compliance Matrix'}
          </div>
        ))}
      </div>

      {tab === 'run' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Audit Configuration</span></div>
            {error && <div style={{ background: 'var(--accent-red-dim)', color: 'var(--accent-red)', border: '1px solid rgba(255,61,106,0.3)', borderRadius: 6, padding: '10px 14px', marginBottom: 16, fontSize: 13 }}>{error}</div>}
            <div className="grid-2" style={{ marginBottom: 0 }}>
              <div className="form-group">
                <label className="form-label">Model Name</label>
                <input className="form-input" placeholder="CreditScorer-v2" value={form.model_name} onChange={e => setForm(f => ({ ...f, model_name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Version</label>
                <input className="form-input" placeholder="2.1.0" value={form.model_version} onChange={e => setForm(f => ({ ...f, model_version: e.target.value }))} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Use Case / Domain</label>
              <input className="form-input" placeholder="healthcare, finance, hr, fraud detection..." value={form.use_case} onChange={e => setForm(f => ({ ...f, use_case: e.target.value }))} />
            </div>
            <div className="grid-2" style={{ marginBottom: 0 }}>
              <div className="form-group">
                <label className="form-label">Jurisdiction</label>
                <select className="form-select" value={form.jurisdiction} onChange={e => setForm(f => ({ ...f, jurisdiction: e.target.value }))}>
                  {['EU', 'US', 'UK', 'APAC'].map(j => <option key={j}>{j}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Risk Category</label>
                <select className="form-select" value={form.risk_category} onChange={e => setForm(f => ({ ...f, risk_category: e.target.value }))}>
                  {['low', 'medium', 'high', 'critical'].map(r => <option key={r}>{r}</option>)}
                </select>
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleAudit} disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
              {loading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Running audit...</> : '◉ Run Compliance Audit'}
            </button>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Audit Results</span></div>
            {result ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600 }}>{result.model_name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>{result.audit_id}</div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                      <span className={`badge ${riskBadge(result.overall_risk)}`}>{result.overall_risk} risk</span>
                      <span className={`badge ${statusBadge(result.status)}`}>{result.status.replace('_', ' ')}</span>
                    </div>
                  </div>
                  <div className="score-ring">
                    <div className="score-ring-value" style={{ color: result.compliance_score >= 0.8 ? 'var(--accent-green)' : result.compliance_score >= 0.6 ? 'var(--accent-amber)' : 'var(--accent-red)' }}>
                      {(result.compliance_score * 100).toFixed(0)}%
                    </div>
                    <div className="score-ring-label">Compliance</div>
                  </div>
                </div>

                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Findings ({result.findings.length})</div>
                  {result.findings.map((f, i) => (
                    <div key={i} style={{ display: 'flex', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                      <span className={`badge ${f.severity === 'critical' || f.severity === 'high' ? 'badge-red' : f.severity === 'medium' ? 'badge-amber' : 'badge-gray'}`} style={{ flexShrink: 0 }}>{f.severity}</span>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{f.category}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{f.finding}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Recommendations</div>
                  {result.recommendations.slice(0, 3).map((r, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '5px 0', fontSize: 12, color: 'var(--text-secondary)' }}>
                      <span style={{ color: 'var(--accent-cyan)', flexShrink: 0 }}>→</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">◉</div>
                <div className="empty-state-text">Configure and run an audit to see results</div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Audit History</span>
            <span className="badge badge-cyan">{audits.length} audits</span>
          </div>
          {audits.length > 0 ? (
            <table className="data-table">
              <thead><tr><th>Audit ID</th><th>Model</th><th>Risk</th><th>Score</th><th>Status</th><th>Date</th></tr></thead>
              <tbody>
                {audits.map((a, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{a.audit_id}</td>
                    <td style={{ color: 'var(--text-primary)' }}>{a.model_name}</td>
                    <td><span className={`badge ${riskBadge(a.overall_risk)}`}>{a.overall_risk}</span></td>
                    <td style={{ fontFamily: 'var(--mono)', color: a.compliance_score >= 0.8 ? 'var(--accent-green)' : a.compliance_score >= 0.6 ? 'var(--accent-amber)' : 'var(--accent-red)' }}>
                      {(a.compliance_score * 100).toFixed(0)}%
                    </td>
                    <td><span className={`badge ${statusBadge(a.status)}`}>{a.status.replace('_', ' ')}</span></td>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{new Date(a.generated_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-text">No audits run yet. Use the Run Audit tab to start.</div>
            </div>
          )}
        </div>
      )}

      {tab === 'matrix' && matrix && (
        <div className="card">
          <div className="card-header"><span className="card-title">Compliance Requirements Matrix — {matrix.jurisdiction}</span></div>
          {matrix.regulations?.map((reg, i) => (
            <div key={i} style={{ marginBottom: 20, paddingBottom: 20, borderBottom: i < matrix.regulations.length - 1 ? '1px solid var(--border)' : 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>{reg.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Enforcement: {reg.enforcement_date} · Penalty: {reg.penalty}</div>
                  <div style={{ fontSize: 11, color: 'var(--accent-cyan)', marginTop: 2 }}>{reg.applicability}</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {reg.articles?.map((art, j) => (
                  <span key={j} style={{ fontSize: 11, padding: '3px 10px', borderRadius: 20, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{art}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
