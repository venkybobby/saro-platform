/**
 * SARO v9.2 — Audits & Reports
 * ==============================
 * Fetches from both in-memory + DB (via /audit-engine/reports).
 * Features:
 *  - Fixed vs Not Fixed comparison view (when fixed_delta is present)
 *  - Status badge: open / partially_fixed / fully_fixed
 *  - Re-run after fix button (stores previousAuditId in localStorage, navigates to upload)
 *  - NIST checklist table (collapsible)
 *  - Evidence hash display (Merkle root for regulatory trail)
 *  - Generate sample audit button
 */
import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''

const scoreColor = s => s >= 0.75 ? 'var(--accent-green)' : s >= 0.5 ? 'var(--accent-amber)' : 'var(--accent-red)'
const riskBadge  = lv => ({ low:'badge-green', medium:'badge-amber', high:'badge-red', critical:'badge-red' }[lv] || 'badge-gray')

const STATUS_BADGE = {
  open:             { cls: 'badge-red',   label: 'Open' },
  partially_fixed:  { cls: 'badge-amber', label: 'Partially Fixed' },
  fully_fixed:      { cls: 'badge-green', label: 'Fully Fixed' },
}

const DELTA_ICON = improved => improved ? '↑' : '→'
const DELTA_COLOR = improved => improved ? 'var(--accent-green)' : 'var(--accent-muted)'

export default function AuditReports({ onNavigate }) {
  const [reports,    setReports]    = useState([])
  const [selected,   setSelected]   = useState(null)
  const [loading,    setLoading]    = useState(true)
  const [generating, setGenerating] = useState(false)
  const [genMsg,     setGenMsg]     = useState(null)
  const [nistExpanded, setNistExpanded] = useState(false)
  const [fullReport, setFullReport] = useState(null)
  const [fullLoading, setFullLoading] = useState(false)

  const loadReports = () => {
    setLoading(true)
    // Single endpoint — returns merged in-memory + DB records with full summary
    fetch(`${BASE}/api/v1/audit-engine/reports?limit=50`)
      .then(r => r.json())
      .then(d => setReports(d.reports || []))
      .catch(() => setReports([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadReports() }, [])

  const selectReport = async (r) => {
    setSelected(r)
    setNistExpanded(false)
    setFullReport(null)
    // Fetch full report for detail panel (NIST checklist, evidence chain, etc.)
    setFullLoading(true)
    try {
      const data = await fetch(`${BASE}/api/v1/audit-engine/report/${r.audit_id}`).then(res => res.json())
      if (!data.error) setFullReport(data)
    } catch(e) {}
    finally { setFullLoading(false) }
  }

  const generateSample = async (domain = 'finance') => {
    setGenerating(true); setGenMsg(null)
    try {
      await fetch(`${BASE}/api/v1/audit-engine/run`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: `demo-${domain}-model`, domain, mode: 'reactive' }),
      })
      setGenMsg(`Sample ${domain} audit generated ✓`)
      setTimeout(() => setGenMsg(null), 4000)
      loadReports()
    } catch { setGenMsg('Error generating report') }
    finally { setGenerating(false) }
  }

  const handleRerun = (r) => {
    // Store previousAuditId so UploadAnalyze picks it up
    localStorage.setItem('saro_rerun_audit_id', r.audit_id)
    localStorage.setItem('saro_rerun_model', r.model_name)
    onNavigate && onNavigate('upload')
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Audits & Reports</h1>
          <p className="page-subtitle">EU AI Act · NIST AI RMF (58 controls) · ISO 42001 · AIGP · Immutable evidence chain</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" style={{ fontSize: 12 }} onClick={loadReports}>↻ Refresh</button>
          <button className="btn btn-primary"   style={{ fontSize: 12 }} onClick={() => generateSample('finance')} disabled={generating}>
            {generating ? <><div className="loading-spinner" style={{ width: 12, height: 12 }} /> Generating...</> : '⚡ Generate Sample'}
          </button>
        </div>
      </div>

      {genMsg && (
        <div style={{ marginBottom: 16, padding: '10px 16px', background: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.25)', borderRadius: 8, fontSize: 13, color: 'var(--accent-green)' }}>
          ✓ {genMsg}
        </div>
      )}

      {loading ? (
        <div className="loading-overlay"><div className="loading-spinner" /></div>
      ) : reports.length === 0 ? (
        <div className="empty-state" style={{ padding: 80 }}>
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-text">No audit reports yet</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8, marginBottom: 20 }}>
            Run an audit from Upload &amp; Analyze, or generate a sample below
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
            {['finance', 'healthcare', 'hr'].map(d => (
              <button key={d} className="btn btn-primary" style={{ fontSize: 12 }}
                onClick={() => generateSample(d)} disabled={generating}>
                ⚡ Generate {d} audit
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid-2">
          {/* ── Left: report list ────────────────────────────────────── */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Audit History</span>
              <span className="badge badge-cyan">{reports.length}</span>
            </div>
            {reports.map((r, i) => {
              const statusInfo = STATUS_BADGE[r.audit_status] || STATUS_BADGE.open
              return (
                <div key={i}
                  style={{ padding: '12px 0', borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                  onClick={() => selectReport(r)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: selected?.audit_id === r.audit_id ? 'var(--accent-cyan)' : 'var(--text-primary)', marginBottom: 2 }}>
                        {r.model_name}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>
                        {r.audit_id?.slice(0, 20)}... · {r.domain} · {new Date(r.timestamp).toLocaleDateString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 12 }}>
                      <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--mono)', color: scoreColor(r.compliance_score || 0) }}>
                        {Math.round((r.compliance_score || 0) * 100)}%
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span className={`badge ${riskBadge(r.risk_level)}`}>{r.risk_level || 'unknown'}</span>
                    <span className={`badge ${statusInfo.cls}`}>{statusInfo.label}</span>
                    {r.nist_total > 0 && (
                      <span className="badge badge-cyan" style={{ fontSize: 9 }}>NIST {r.nist_pass_count}/{r.nist_total}</span>
                    )}
                    {r.previous_audit_id && (
                      <span className="badge badge-purple" style={{ fontSize: 9 }}>Re-run</span>
                    )}
                    {r.mit_coverage?.coverage_pct > 0 && (
                      <span className="badge badge-cyan" style={{ fontSize: 9 }}>MIT {r.mit_coverage.coverage_pct}%</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* ── Right: detail panel ──────────────────────────────────── */}
          <div className="card">
            {selected ? (
              <div>
                {/* Header */}
                <div className="card-header" style={{ marginBottom: 16 }}>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700 }}>{selected.model_name}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--mono)', marginTop: 2 }}>
                      {selected.audit_id}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span className={`badge ${(STATUS_BADGE[selected.audit_status] || STATUS_BADGE.open).cls}`}>
                      {(STATUS_BADGE[selected.audit_status] || STATUS_BADGE.open).label}
                    </span>
                    <button className="btn btn-secondary" style={{ fontSize: 11, padding: '4px 10px' }}
                      onClick={() => handleRerun(selected)}>
                      ↻ Re-run after fix
                    </button>
                  </div>
                </div>

                {fullLoading && <div style={{ padding: 24, textAlign: 'center' }}><div className="loading-spinner" /></div>}

                {!fullLoading && (
                  <>
                    {/* KPI strip */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 16 }}>
                      {[
                        { label: 'Compliance',  value: `${Math.round((selected.compliance_score||0)*100)}%`, color: scoreColor(selected.compliance_score||0) },
                        { label: 'NIST Pass',   value: selected.nist_total > 0 ? `${selected.nist_pass_count}/${selected.nist_total}` : '—', color: 'var(--accent-cyan)' },
                        { label: 'Bias',        value: selected.bias_status || '—', color: selected.bias_status === 'pass' ? 'var(--accent-green)' : 'var(--accent-red)' },
                      ].map(m => (
                        <div key={m.label} style={{ padding: '10px 12px', background: 'var(--bg-primary)', borderRadius: 8, textAlign: 'center' }}>
                          <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>{m.label}</div>
                          <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'var(--mono)', color: m.color }}>{m.value}</div>
                        </div>
                      ))}
                    </div>

                    {/* ── Fixed vs Not Fixed (only shown on re-run) ── */}
                    {selected.fixed_delta && Object.keys(selected.fixed_delta).length > 0 && (
                      <div style={{ marginBottom: 16, padding: '12px 14px', background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 10 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>
                          Fixed vs Not Fixed — vs previous audit
                        </div>
                        {Object.entries(selected.fixed_delta).map(([metric, d]) => {
                          const improved = d.improved || d.fixed || false
                          const label = {
                            compliance_score: 'Compliance Score',
                            risk_level:       'Risk Level',
                            bias_status:      'Bias Status',
                            pii_status:       'PII Status',
                            nist_pass_rate:   'NIST Pass Rate',
                          }[metric] || metric
                          return (
                            <div key={metric} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
                              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</div>
                              <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontFamily: 'var(--mono)', fontSize: 12 }}>
                                <span style={{ color: 'var(--text-muted)' }}>{typeof d.before === 'number' ? `${(d.before*100).toFixed(0)}%` : d.before}</span>
                                <span style={{ color: DELTA_COLOR(improved) }}>→</span>
                                <span style={{ color: DELTA_COLOR(improved), fontWeight: 700 }}>{typeof d.after === 'number' ? `${(d.after*100).toFixed(0)}%` : d.after}</span>
                                <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: improved ? 'rgba(0,255,136,0.1)' : 'rgba(255,61,106,0.08)', color: improved ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                  {improved ? '✓ Fixed' : '✗ Open'}
                                </span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}

                    {/* ── MIT Risk Coverage ── */}
                    {(fullReport?.mit_coverage || fullReport?.summary?.mit_coverage) && (() => {
                      const mc = fullReport.mit_coverage || fullReport.summary.mit_coverage
                      return (
                        <div style={{ marginBottom: 16, padding: '10px 12px', background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.15)', borderRadius: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>MIT AI Risk Coverage</div>
                            <span className="badge badge-cyan" style={{ fontSize: 10 }}>{mc.coverage_pct}%</span>
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>{mc.label}</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {(mc.covered_domains || []).map(d => <span key={d} className="badge badge-green" style={{ fontSize: 9 }}>✓ {d}</span>)}
                            {(mc.missing_domains || []).map(d => <span key={d} className="badge badge-gray" style={{ fontSize: 9, opacity: 0.5 }}>○ {d}</span>)}
                          </div>
                        </div>
                      )
                    })()}

                    {/* ── Remediation plan ── */}
                    {Array.isArray(fullReport?.recommendations) && fullReport.recommendations.length > 0 && (
                      <div style={{ marginBottom: 16 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>
                          Remediation Plan ({fullReport.recommendations.length} actions)
                        </div>
                        {fullReport.recommendations.slice(0, 4).map((rec, i) => (
                          <div key={i} style={{ display: 'flex', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                            <span className={`badge ${rec.priority === 'critical' || rec.priority === 'high' ? 'badge-red' : rec.priority === 'medium' ? 'badge-amber' : 'badge-cyan'}`} style={{ fontSize: 9, flexShrink: 0 }}>{rec.priority}</span>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{rec.action}</div>
                              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{rec.detail}</div>
                              {rec.mit_domain && <div style={{ fontSize: 10, color: 'var(--accent-purple)', marginTop: 2 }}>MIT: {rec.mit_domain} · {rec.mit_category}</div>}
                            </div>
                            {rec.effort_days && <span style={{ fontSize: 10, color: 'var(--text-muted)', flexShrink: 0 }}>{rec.effort_days}d</span>}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* ── NIST Checklist (collapsible) ── */}
                    {(() => {
                      // nist_rmf_checklist is flat array; handle legacy dict form too
                      const nistArr = Array.isArray(fullReport?.nist_rmf_checklist)
                        ? fullReport.nist_rmf_checklist
                        : (fullReport?.nist_rmf_checklist?.controls || [])
                      if (!nistArr.length) return null
                      return (
                        <div style={{ marginBottom: 16 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, cursor: 'pointer' }}
                            onClick={() => setNistExpanded(e => !e)}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                              NIST AI RMF — 58 Controls
                            </div>
                            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                              <span className="badge badge-green">{nistArr.filter(c => c.status === 'pass').length} pass</span>
                              <span className="badge badge-amber">{nistArr.filter(c => c.status === 'warn').length} warn</span>
                              <span className="badge badge-red">{nistArr.filter(c => c.status === 'fail').length} fail</span>
                              <span style={{ fontSize: 12, color: 'var(--text-muted)', transform: nistExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
                            </div>
                          </div>
                          {nistExpanded && (
                            <div style={{ maxHeight: 280, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 8 }}>
                              <table className="data-table">
                                <thead>
                                  <tr>
                                    <th>Control</th>
                                    <th>Function</th>
                                    <th>Status</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {nistArr.map((c, i) => (
                                    <tr key={i}>
                                      <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>{c.control_id || c.id}</td>
                                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.function}</td>
                                      <td>
                                        <span className={`badge ${c.status === 'pass' ? 'badge-green' : c.status === 'warn' ? 'badge-amber' : 'badge-red'}`} style={{ fontSize: 9 }}>
                                          {c.status}
                                        </span>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      )
                    })()}

                    {/* ── Evidence chain ── */}
                    {fullReport?.evidence_chain?.length > 0 && (
                      <div style={{ marginBottom: 16 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>
                          Evidence Chain
                        </div>
                        {fullReport.evidence_chain.map((e, i) => (
                          <div key={i} style={{ display: 'flex', gap: 8, padding: '5px 0', borderBottom: '1px solid var(--border)', fontSize: 12, alignItems: 'center' }}>
                            <span className={`badge ${e.type === 'output' ? 'badge-green' : e.type === 'fairness' ? 'badge-amber' : 'badge-gray'}`} style={{ fontSize: 9, flexShrink: 0 }}>
                              {e.type}
                            </span>
                            <span style={{ color: 'var(--text-secondary)', flex: 1 }}>{e.event}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* ── Evidence hash (regulatory trail) ── */}
                    {fullReport?.evidence_hash && (
                      <div style={{ padding: '8px 10px', background: 'var(--bg-primary)', borderRadius: 6, fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                        🔒 SHA-256 Evidence Hash: {fullReport.evidence_hash}
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <div className="empty-state-text">Select an audit to view details</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                  Click "↻ Re-run after fix" to compare before &amp; after remediation
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
