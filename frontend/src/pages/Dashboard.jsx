/**
 * SARO v9.3 — Operator Overview (Client-First)
 * ===============================================
 * Elon-critique fix: show client outcomes, not internal stats.
 * One answer: "What happened to my models last?"
 *
 * Sections:
 *   1. Recent Audits — last 5 models, outcome + quick actions
 *   2. Compliance Trend — simple score trajectory
 *   3. Secondary: Live alerts + system health (collapsed by default on small screens)
 */
import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const get  = (p) => fetch(`${BASE}${p}`).then(r => r.json())

const scoreColor = s => s >= 0.75 ? 'var(--accent-green)' : s >= 0.5 ? 'var(--accent-amber)' : 'var(--accent-red)'
const riskBadge  = l => ({ low:'badge-green', medium:'badge-amber', high:'badge-red', critical:'badge-red' }[l] || 'badge-gray')

export default function Dashboard({ onNavigate }) {
  const [audits,  setAudits]   = useState([])
  const [loading, setLoading]  = useState(true)
  const [health,  setHealth]   = useState(null)

  useEffect(() => {
    Promise.all([
      get('/api/v1/audit-engine/reports?limit=5'),
      get('/api/v1/checklist/compliance-status').catch(() => null),
    ]).then(([rep, hlt]) => {
      setAudits(rep.reports || [])
      setHealth(hlt)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleRerun = (audit) => {
    localStorage.setItem('saro_rerun_audit_id', audit.audit_id)
    localStorage.setItem('saro_rerun_model',    audit.model_name)
    onNavigate('upload')
  }

  // Compute trend: are scores improving?
  const trend = audits.length >= 2
    ? audits[0].compliance_score - audits[audits.length - 1].compliance_score
    : null

  if (loading) return (
    <div className="loading-overlay">
      <div className="loading-spinner" />
      <span>Loading your audits...</span>
    </div>
  )

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Your Models — Latest Audits</h1>
          <p className="page-subtitle">Last scanned models and their compliance outcomes</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {trend !== null && (
            <span style={{ fontSize: 12, fontWeight: 700, color: trend >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', background: trend >= 0 ? 'rgba(0,255,136,0.08)' : 'rgba(255,61,106,0.08)', padding: '4px 10px', borderRadius: 6 }}>
              {trend >= 0 ? '↑' : '↓'} Risk {trend >= 0 ? 'trending down' : 'trending up'}
            </span>
          )}
          <button className="btn btn-primary" style={{ fontSize: 13, padding: '9px 18px' }}
            onClick={() => onNavigate('upload')}>
            ⚡ Run Full Audit
          </button>
        </div>
      </div>

      {/* ── Recent Audits ──────────────────────────────────────── */}
      {audits.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>📋</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
            No audits yet
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 24, maxWidth: 400, margin: '0 auto 24px' }}>
            Upload your first AI model output to get a full compliance score, NIST checklist, bias analysis, and remediation plan.
          </div>
          <button className="btn btn-primary" style={{ padding: '12px 28px', fontSize: 14 }}
            onClick={() => onNavigate('upload')}>
            ⚡ Upload & Analyze First Model
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
          {audits.map((a, i) => {
            const score  = a.compliance_score || 0
            const status = a.audit_status || 'open'
            const statusColor = status === 'fully_fixed' ? 'var(--accent-green)' : status === 'partially_fixed' ? 'var(--accent-amber)' : 'var(--text-muted)'
            const ts     = a.timestamp ? new Date(a.timestamp) : null
            const ago    = ts ? (() => {
              const diff = (Date.now() - ts) / 1000
              return diff < 3600 ? `${Math.floor(diff/60)}m ago` : diff < 86400 ? `${Math.floor(diff/3600)}h ago` : ts.toLocaleDateString()
            })() : '—'

            return (
              <div key={a.audit_id} className="card" style={{ borderLeft: `3px solid ${scoreColor(score)}`, padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
                  {/* Left: model info */}
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>{a.model_name}</span>
                      <span className={`badge ${riskBadge(a.risk_level)}`} style={{ fontSize: 10 }}>
                        {(a.risk_level || 'medium').toUpperCase()}
                      </span>
                      {status !== 'open' && (
                        <span style={{ fontSize: 10, color: statusColor, fontWeight: 600 }}>
                          {status === 'fully_fixed' ? '✓ Fully Fixed' : '~ Partially Fixed'}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {a.domain?.toUpperCase() || 'GENERAL'} · Audited {ago} · ID: <span style={{ fontFamily: 'var(--mono)', color: 'var(--accent-cyan)' }}>{a.audit_id?.slice(0, 16)}</span>
                    </div>
                  </div>

                  {/* Center: compliance score + quick metrics */}
                  <div style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, fontWeight: 800, fontFamily: 'var(--mono)', color: scoreColor(score) }}>
                        {Math.round(score * 100)}%
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Compliance</div>
                    </div>
                    {a.nist_total > 0 && (
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--text-primary)' }}>
                          {a.nist_pass_count}/{a.nist_total}
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>NIST Controls</div>
                      </div>
                    )}
                    {a.bias_status && (
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: a.bias_status === 'pass' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                          {a.bias_status.toUpperCase()}
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Bias</div>
                      </div>
                    )}
                    {a.mit_coverage_score != null && (
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--accent-cyan)' }}>
                          {a.mit_coverage_score}%
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>MIT Coverage</div>
                      </div>
                    )}
                  </div>

                  {/* Right: actions */}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                    <button className="btn btn-secondary" style={{ fontSize: 11, padding: '6px 12px' }}
                      onClick={() => onNavigate('reports')}>
                      📋 View Report
                    </button>
                    <button className="btn btn-primary" style={{ fontSize: 11, padding: '6px 12px' }}
                      onClick={() => handleRerun(a)}>
                      ↻ Re-run
                    </button>
                  </div>
                </div>
              </div>
            )
          })}

          <div style={{ textAlign: 'center', marginTop: 4 }}>
            <button className="btn btn-secondary" style={{ fontSize: 12 }} onClick={() => onNavigate('reports')}>
              View All Reports →
            </button>
          </div>
        </div>
      )}

      {/* ── Compliance Alerts ──────────────────────────────────── */}
      {health?.items?.filter(i => i.status !== 'pass').length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <span className="card-title">Open Compliance Issues</span>
            <span className="badge badge-red">{health.items.filter(i => i.status !== 'pass').length} open</span>
          </div>
          {health.items.filter(i => i.status !== 'pass').slice(0, 4).map((item, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '9px 0', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
              <span style={{ fontSize: 14, color: item.status === 'critical' ? 'var(--accent-red)' : 'var(--accent-amber)', flexShrink: 0 }}>
                {item.status === 'critical' ? '✗' : '⚠'}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{item.check}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{item.module} · {item.detail}</div>
              </div>
              <button className="btn btn-secondary" style={{ fontSize: 10, padding: '3px 9px' }}
                onClick={() => onNavigate('upload')}>
                Fix →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
