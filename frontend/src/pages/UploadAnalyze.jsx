/**
 * SARO v9.2 — Upload & Analyze
 * ================================
 * Core operator flow: upload model output → Run Full Audit → inline results.
 * One button. One flow. No clutter.
 *
 * API: POST /api/v1/audit-engine/run
 * Returns: summary, NIST checklist, bias/fairness, PII detection, recommendations
 */
import { useState } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (p, b) =>
  fetch(`${BASE}${p}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(b),
  }).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json()
  })

const DOMAINS  = ['general', 'finance', 'healthcare', 'hr', 'tech', 'government']
const LENSES   = ['EU AI Act', 'NIST AI RMF', 'ISO 42001', 'AIGP']

const scoreColor = s =>
  s >= 0.75 ? 'var(--accent-green)' : s >= 0.5 ? 'var(--accent-amber)' : 'var(--accent-red)'

const riskBadge = level => ({
  low:      'badge-green',
  medium:   'badge-amber',
  high:     'badge-red',
  critical: 'badge-red',
}[level] || 'badge-gray')

export default function UploadAnalyze({ onNavigate }) {
  const [modelName,    setModelName]    = useState('')
  const [content,      setContent]      = useState('')
  const [domain,       setDomain]       = useState('general')
  const [jurisdiction, setJurisdiction] = useState('EU')
  const [lenses,       setLenses]       = useState([...LENSES])
  const [loading,      setLoading]      = useState(false)
  const [result,       setResult]       = useState(null)
  const [error,        setError]        = useState('')

  const toggleLens = lens =>
    setLenses(prev => prev.includes(lens) ? prev.filter(l => l !== lens) : [...prev, lens])

  const runAudit = async () => {
    if (!modelName.trim()) { setError('Model name is required'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const payload = {
        model_name:   modelName.trim(),
        domain,
        mode:         'reactive',
        lenses,
        text_samples: content.trim() ? [content.trim().slice(0, 2000)] : [],
        model_type:   'classifier',
        logging_enabled: true,
        human_oversight: true,
      }
      const data = await post('/api/v1/audit-engine/run', payload)
      setResult(data)
    } catch (e) {
      const msg = e.message?.includes('429') ? 'Rate limit — retry in 60 seconds'
        : e.message?.includes('HTTP 5') ? 'Audit engine error — check API connection'
        : 'Audit failed — check your input and retry'
      setError(msg)
    } finally { setLoading(false) }
  }

  const summary = result?.summary || {}
  const recs    = result?.recommendations || []
  const nist    = result?.nist_rmf_checklist || []
  const bias    = result?.bias_fairness_summary || {}
  const pii     = result?.pii_phi_summary || {}

  const nistPass = nist.filter(c => c.status === 'pass').length
  const nistFail = nist.filter(c => c.status === 'fail').length
  const nistWarn = nist.filter(c => c.status === 'warn').length

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Upload & Analyze</h1>
          <p className="page-subtitle">Paste model output → Run Full Audit → Get forecast, compliance report &amp; remediation plan</p>
        </div>
        {result && (
          <button className="btn btn-secondary" style={{ fontSize: 12 }}
            onClick={() => onNavigate('reports')}>
            📋 View All Reports →
          </button>
        )}
      </div>

      {/* ── Upload form ────────────────────────────────────────── */}
      {!result && (
        <div className="card" style={{ maxWidth: 760, marginBottom: 24 }}>
          <div className="card-header">
            <span className="card-title">Model Details</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>EU AI Act · NIST AI RMF · ISO 42001 · AIGP</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Model Name *</label>
              <input className="form-input" placeholder="e.g. credit-risk-classifier-v2"
                value={modelName} onChange={e => setModelName(e.target.value)} />
            </div>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Domain</label>
              <select className="form-select" value={domain} onChange={e => setDomain(e.target.value)}>
                {DOMAINS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Model Output / Code Sample <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional — paste for PII/bias analysis)</span></label>
            <textarea className="form-input" rows={6}
              placeholder="Paste model output, prediction samples, or code snippet for deep analysis. Leave blank for domain-default audit."
              value={content} onChange={e => setContent(e.target.value)}
              style={{ resize: 'vertical', minHeight: 120, fontFamily: 'var(--mono)', fontSize: 12 }} />
          </div>

          <div className="form-group" style={{ marginBottom: 20 }}>
            <label className="form-label">Active Compliance Lenses</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
              {LENSES.map(lens => (
                <button key={lens}
                  className={`btn ${lenses.includes(lens) ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: 11, padding: '5px 10px' }}
                  onClick={() => toggleLens(lens)}>
                  {lens}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div style={{ marginBottom: 14, padding: '10px 14px', background: 'rgba(255,61,106,0.08)', border: '1px solid rgba(255,61,106,0.3)', borderRadius: 8, fontSize: 13, color: 'var(--accent-red)' }}>
              ⚠️ {error}
            </div>
          )}

          <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '13px 20px', fontSize: 15, fontWeight: 700 }}
            onClick={runAudit} disabled={loading || !modelName.trim()}>
            {loading
              ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} /> Running Full Audit...</>
              : '⚡ Run Full Audit'}
          </button>
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
            Produces: Compliance score · 58 NIST controls · Bias/fairness · PII detection · Remediation plan
          </div>
        </div>
      )}

      {/* ── Results ────────────────────────────────────────────── */}
      {result && (
        <div>
          {/* Summary hero */}
          <div className="card" style={{ marginBottom: 20, borderTop: `3px solid ${scoreColor(summary.overall_compliance_score||0)}` }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>
                  Full Audit Complete — {modelName}
                </div>
                <div style={{ fontSize: 36, fontWeight: 800, fontFamily: 'var(--mono)', color: scoreColor(summary.overall_compliance_score||0) }}>
                  {Math.round((summary.overall_compliance_score||0)*100)}%
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Overall compliance score</div>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-amber)' }}>{summary.mitigation_percent||0}%</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Mitigated</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-green)' }}>${((summary.estimated_fine_avoided_usd||0)/1000).toFixed(0)}K</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Fine avoided</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span className={`badge ${riskBadge(summary.risk_level)}`} style={{ fontSize: 12, padding: '6px 12px' }}>
                    {(summary.risk_level||'medium').toUpperCase()} RISK
                  </span>
                </div>
              </div>
            </div>
            {summary.key_insight && (
              <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--bg-primary)', borderRadius: 8, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65, borderLeft: '3px solid var(--accent-cyan)' }}>
                💡 {summary.key_insight}
              </div>
            )}
          </div>

          {/* 4-metric quick badges */}
          <div className="metrics-grid-4" style={{ marginBottom: 20 }}>
            {[
              {
                label: 'NIST Controls',
                value: `${nistPass}/${nist.length}`,
                sub: `${nistFail} fail · ${nistWarn} warn`,
                color: nistFail > 0 ? 'red' : nistWarn > 0 ? 'amber' : 'green',
              },
              {
                label: 'Bias Status',
                value: bias.overall_status === 'pass' ? 'PASS' : 'FAIL',
                sub: `${(bias.dimensions||[]).length} dimensions checked`,
                color: bias.overall_status === 'pass' ? 'green' : 'red',
              },
              {
                label: 'PII Detection',
                value: `${Math.round((pii.detection_rate||0.95)*100)}%`,
                sub: pii.status === 'pass' ? 'No leaks detected' : 'Leaks found',
                color: pii.status === 'pass' ? 'green' : 'red',
              },
              {
                label: 'Findings',
                value: summary.total_findings||0,
                sub: `${summary.critical||0} critical · ${summary.high||0} high`,
                color: (summary.critical||0) > 0 ? 'red' : (summary.high||0) > 0 ? 'amber' : 'green',
              },
            ].map(m => (
              <div key={m.label} className="card" style={{ padding: '14px 16px' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>{m.label}</div>
                <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--mono)', color: `var(--accent-${m.color})`, marginBottom: 2 }}>{m.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{m.sub}</div>
              </div>
            ))}
          </div>

          {/* Recommendations */}
          {recs.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-header">
                <span className="card-title">Remediation Plan</span>
                <span className="badge badge-cyan">{recs.length} actions</span>
              </div>
              {recs.slice(0, 5).map((r, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                  <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'rgba(0,212,255,0.1)', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800, flexShrink: 0 }}>{i+1}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{r.action}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{r.detail}</div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
                    <span className={`badge ${r.priority === 'critical' ? 'badge-red' : r.priority === 'high' ? 'badge-amber' : 'badge-cyan'}`} style={{ fontSize: 10 }}>{r.priority}</span>
                    {r.effort_days && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{r.effort_days}d effort</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => { setResult(null); setContent('') }}>
              ⚡ Run Another Audit
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('reports')}>
              📋 View All Reports
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('policy-intelligence')}>
              💬 Ask Policy AI
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
