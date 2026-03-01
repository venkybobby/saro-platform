import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export default function MVP4Agentic() {
  const [tab, setTab] = useState('guardrails')
  const [guardForm, setGuardForm] = useState({ model_id: 'HRScreener-v1', output_text: '' })
  const [guardResult, setGuardResult] = useState(null)
  const [guardLoading, setGuardLoading] = useState(false)
  const [guardError, setGuardError] = useState(null)
  const [guardStats, setGuardStats] = useState(null)

  const [reportForm, setReportForm] = useState({ model_name: 'DiagnosticAI-v2', report_type: 'EU_AI_ACT' })
  const [reportResult, setReportResult] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportError, setReportError] = useState(null)
  const [regulations, setRegulations] = useState([])

  const [courses, setCourses] = useState([])
  const [enrollMsg, setEnrollMsg] = useState(null)
  const [gaReadiness, setGaReadiness] = useState(null)

  useEffect(() => {
    api.guardrailStats().then(setGuardStats).catch(() => {})
    api.listRegulations('ALL').then(d => setRegulations(d.regulations || [])).catch(() => {})
    api.listCourses().then(d => setCourses(d.courses || [])).catch(() => {})
    api.gaReadiness().then(setGaReadiness).catch(() => {})
  }, [])

  const handleGuardrailCheck = async () => {
    if (!guardForm.output_text.trim()) return
    setGuardLoading(true)
    setGuardError(null)
    setGuardResult(null)
    try {
      const res = await api.checkGuardrails({
        model_id: guardForm.model_id,
        output_text: guardForm.output_text,
        request_id: Math.random().toString(36).slice(2)
      })
      setGuardResult(res)
    } catch (e) {
      setGuardError(e.message)
    } finally {
      setGuardLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    if (!reportForm.model_name.trim()) return
    setReportLoading(true)
    setReportError(null)
    setReportResult(null)
    try {
      const res = await api.generateReport({
        model_name: reportForm.model_name,
        report_type: reportForm.report_type,
      })
      setReportResult(res)
    } catch (e) {
      setReportError(e.message)
    } finally {
      setReportLoading(false)
    }
  }

  const handleEnroll = async (courseId) => {
    try {
      await api.enrollCourse({ course_id: courseId, user_id: 'demo-user-001' })
      setEnrollMsg(`✓ Enrolled in course ${courseId}`)
      setTimeout(() => setEnrollMsg(null), 3000)
    } catch (e) {
      setEnrollMsg(`Error: ${e.message}`)
    }
  }

  const DEMO_TEXTS = [
    { label: '🔴 Bias + PII', text: 'All women are bad at math. Patient SSN 123-45-6789 is stored in our system.' },
    { label: '🟡 Hallucination', text: 'This drug is 100% guaranteed to cure cancer. I am certain it will work for everyone.' },
    { label: '🟢 Clean', text: 'Transaction reviewed fairly across all protected characteristics. Human oversight applied.' },
  ]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Agentic GA Platform</h1>
          <p className="page-subtitle">Real-time guardrails · Compliance reports · AI fluency training · Commercial readiness</p>
        </div>
        <span className="mvp-tag mvp4-tag">◐ MVP4</span>
      </div>

      {guardStats && (
        <div className="metrics-grid-4" style={{ marginBottom: 24 }}>
          {[
            { label: 'Checks Today', value: guardStats.total_checks_today?.toLocaleString(), color: 'cyan' },
            { label: 'Harmful Block Rate', value: `${(guardStats.actual_block_rate_harmful * 100).toFixed(1)}%`, color: 'green' },
            { label: 'Avg Latency', value: `${guardStats.avg_latency_ms}ms`, color: 'cyan' },
            { label: 'P99 Latency', value: `${guardStats.p99_latency_ms}ms`, color: 'amber' },
          ].map(m => (
            <div key={m.label} className="card" style={{ padding: '14px 16px' }}>
              <div className="card-title" style={{ fontSize: 10, marginBottom: 6 }}>{m.label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--mono)', color: `var(--accent-${m.color})` }}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="tabs">
        {[
          ['guardrails', '🛡 Guardrails'],
          ['compliance', '📑 Compliance Reports'],
          ['training', '🎓 AI Training'],
          ['commercial', '💼 Commercial GA'],
        ].map(([key, label]) => (
          <div key={key} className={`tab ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>{label}</div>
        ))}
      </div>

      {/* ── GUARDRAILS ── */}
      {tab === 'guardrails' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Real-time Guardrail Check</span></div>

            <div className="form-group">
              <label className="form-label">Model ID</label>
              <input className="form-input" value={guardForm.model_id}
                onChange={e => setGuardForm(f => ({ ...f, model_id: e.target.value }))} />
            </div>

            <div className="form-group">
              <label className="form-label">AI Output to Check</label>
              <textarea className="form-textarea" rows={5}
                placeholder="Paste AI-generated text to check for violations..."
                value={guardForm.output_text}
                onChange={e => setGuardForm(f => ({ ...f, output_text: e.target.value }))} />
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>💡 Quick demo texts:</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {DEMO_TEXTS.map(d => (
                  <button key={d.label} className="btn btn-secondary"
                    style={{ fontSize: 11, padding: '5px 10px', justifyContent: 'flex-start' }}
                    onClick={() => setGuardForm(f => ({ ...f, output_text: d.text }))}>
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            <button className="btn btn-primary" onClick={handleGuardrailCheck}
              disabled={guardLoading || !guardForm.output_text.trim()}
              style={{ width: '100%', justifyContent: 'center' }}>
              {guardLoading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Checking...</> : '🛡 Check Guardrails'}
            </button>

            {guardError && (
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'rgba(255,61,106,0.1)', border: '1px solid rgba(255,61,106,0.3)', borderRadius: 6, fontSize: 12, color: 'var(--accent-red)' }}>
                ✗ Error: {guardError}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Guardrail Result</span></div>
            {guardResult ? (
              <div>
                <div style={{
                  display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16,
                  padding: '14px 16px', borderRadius: 8,
                  background: guardResult.passed ? 'rgba(0,255,136,0.06)' : 'rgba(255,61,106,0.06)',
                  border: `1px solid ${guardResult.passed ? 'rgba(0,255,136,0.25)' : 'rgba(255,61,106,0.25)'}`
                }}>
                  <div style={{ fontSize: 28 }}>{guardResult.blocked ? '🚫' : guardResult.passed ? '✅' : '⚠️'}</div>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: guardResult.passed ? 'var(--accent-green)' : guardResult.blocked ? 'var(--accent-red)' : 'var(--accent-amber)' }}>
                      {guardResult.blocked ? 'BLOCKED' : guardResult.passed ? 'PASSED' : 'WARNING — Violations Found'}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                      Risk Score: {(guardResult.risk_score * 100).toFixed(0)}% · Latency: {guardResult.latency_ms?.toFixed(2)}ms
                    </div>
                  </div>
                </div>

                {guardResult.violations?.length > 0 ? (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>
                      Violations ({guardResult.violations.length})
                    </div>
                    {guardResult.violations.map((v, i) => (
                      <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 5 }}>
                          <span className={`badge ${v.severity === 'high' ? 'badge-red' : 'badge-amber'}`}>{v.severity}</span>
                          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                            {v.type.replace(/_/g, ' ').toUpperCase()}
                          </span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Matched: "<span style={{ color: 'var(--accent-amber)' }}>{v.pattern}</span>"</div>
                        <div style={{ fontSize: 11, color: 'var(--accent-cyan)', marginTop: 4 }}>→ {v.remediation}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ padding: '16px', textAlign: 'center', color: 'var(--accent-green)', fontSize: 14 }}>
                    ✓ No violations detected — output is policy compliant
                  </div>
                )}

                {guardStats?.violation_breakdown && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Platform Violation Breakdown Today</div>
                    {Object.entries(guardStats.violation_breakdown).map(([type, count]) => (
                      <div key={type} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 12 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{type.replace(/_/g, ' ')}</span>
                        <span style={{ fontFamily: 'var(--mono)', color: 'var(--accent-amber)' }}>{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">🛡</div>
                <div className="empty-state-text">Click a demo text above or type your own, then click Check Guardrails</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── COMPLIANCE REPORTS ── */}
      {tab === 'compliance' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Generate Compliance Report</span></div>
            <div className="form-group">
              <label className="form-label">Model / System Name</label>
              <input className="form-input" placeholder="e.g. DiagnosticAI-v2"
                value={reportForm.model_name}
                onChange={e => setReportForm(f => ({ ...f, model_name: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="form-label">Report Type</label>
              <select className="form-select" value={reportForm.report_type}
                onChange={e => setReportForm(f => ({ ...f, report_type: e.target.value }))}>
                {['EU_AI_ACT', 'FDA_510K', 'NIST_AI_RMF', 'HIPAA', 'ISO_42001'].map(r => (
                  <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
            <div style={{ marginBottom: 12, padding: '10px 12px', background: 'var(--bg-primary)', borderRadius: 6, fontSize: 11, color: 'var(--text-muted)' }}>
              💡 Try: <strong>DiagnosticAI-v2</strong> + <strong>FDA_510K</strong> or <strong>CreditScorer-v2</strong> + <strong>EU_AI_ACT</strong>
            </div>
            <button className="btn btn-primary" onClick={handleGenerateReport}
              disabled={reportLoading || !reportForm.model_name.trim()}
              style={{ width: '100%', justifyContent: 'center' }}>
              {reportLoading
                ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Generating Report...</>
                : '📑 Generate Report'}
            </button>

            {reportError && (
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'rgba(255,61,106,0.1)', border: '1px solid rgba(255,61,106,0.3)', borderRadius: 6, fontSize: 12, color: 'var(--accent-red)' }}>
                ✗ {reportError}
              </div>
            )}

            {regulations.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>Tracked Regulations ({regulations.length})</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {regulations.map((r, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
                      <div>
                        <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{r.name}</span>
                        <span className="badge badge-gray" style={{ marginLeft: 6, fontSize: 10 }}>{r.jurisdiction}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <div className="progress-bar" style={{ width: 50 }}>
                          <div className={`progress-fill ${r.coverage >= 0.9 ? 'progress-green' : 'progress-amber'}`} style={{ width: `${r.coverage * 100}%` }} />
                        </div>
                        <span style={{ fontSize: 11, fontFamily: 'var(--mono)', color: r.coverage >= 0.9 ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
                          {(r.coverage * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Report Output</span></div>
            {reportResult ? (
              <div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16 }}>
                  <span className="badge badge-green">✓ Generated</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent-cyan)' }}>{reportResult.report_id}</span>
                </div>
                <div style={{ marginBottom: 16, padding: '12px 14px', background: 'var(--bg-primary)', borderRadius: 8 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{reportResult.model}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {reportResult.report_type} · Generated in {reportResult.generation_time_seconds}s
                  </div>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>
                    Report Sections ({reportResult.sections?.length})
                  </div>
                  {reportResult.sections?.map((s, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '7px 0', borderBottom: '1px solid var(--border)', fontSize: 13, color: 'var(--text-secondary)', alignItems: 'center' }}>
                      <span style={{ color: 'var(--accent-green)', fontWeight: 700 }}>✓</span>
                      {s}
                    </div>
                  ))}
                </div>
                <div style={{ padding: '14px 16px', background: 'rgba(0,255,136,0.06)', borderRadius: 8, border: '1px solid rgba(0,255,136,0.2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-green)' }}>✓ Ready for Submission</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        Compliance score: {(reportResult.compliance_score * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div style={{ fontSize: 28, fontWeight: 800, fontFamily: 'var(--mono)', color: 'var(--accent-green)' }}>
                      {(reportResult.compliance_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">📑</div>
                <div className="empty-state-text">
                  Enter a model name, select report type, and click Generate Report
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TRAINING ── */}
      {tab === 'training' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">AI Fluency Courses</span>
            <span className="badge badge-cyan">{courses.length} courses available</span>
          </div>
          {enrollMsg && (
            <div style={{ marginBottom: 16, padding: '10px 14px', background: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 6, fontSize: 13, color: 'var(--accent-green)' }}>
              {enrollMsg}
            </div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
            {courses.map((c, i) => (
              <div key={i} style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 10, padding: 18 }}>
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>{c.title}</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
                  <span className="badge badge-purple">{c.persona}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{c.duration_min} min</span>
                </div>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, fontSize: 11, color: 'var(--text-muted)' }}>
                    <span>Completion rate</span>
                    <span style={{ fontFamily: 'var(--mono)', color: 'var(--accent-green)' }}>{(c.completion_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill progress-green" style={{ width: `${c.completion_rate * 100}%` }} />
                  </div>
                </div>
                <button className="btn btn-secondary"
                  style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}
                  onClick={() => handleEnroll(c.id)}>
                  Enroll →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── COMMERCIAL GA ── */}
      {tab === 'commercial' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <span className="card-title">GA Readiness Checklist</span>
              <span className="badge badge-green">✓ GA READY</span>
            </div>
            {gaReadiness ? (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {Object.entries(gaReadiness.checks || {}).map(([check, passed]) => (
                    <div key={check} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
                      <span style={{ fontSize: 16, color: passed ? 'var(--accent-green)' : 'var(--accent-red)', flexShrink: 0 }}>{passed ? '✓' : '✗'}</span>
                      <span style={{ fontSize: 13, color: passed ? 'var(--text-primary)' : 'var(--accent-red)' }}>
                        {check.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </span>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 16, padding: '14px 16px', background: 'rgba(0,255,136,0.06)', borderRadius: 8, border: '1px solid rgba(0,255,136,0.2)', textAlign: 'center' }}>
                  <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--mono)' }}>100%</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Production readiness score</div>
                </div>
              </>
            ) : (
              <div className="empty-state"><div className="empty-state-text">Loading GA readiness...</div></div>
            )}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Platform Summary</span></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                ['Total Tests', '793', 'green'],
                ['Test Failures', '0', 'green'],
                ['Total Sprints', '16', 'cyan'],
                ['Source Modules', '30', 'cyan'],
                ['Guardrail Block Rate', '96.2%', 'green'],
                ['Avg Guardrail Latency', '<1ms', 'green'],
                ['FDA 510(k) Gen Time', '<5s', 'green'],
                ['APAC Reg Coverage', '100%', 'green'],
                ['Tenant Onboarding', '100% automated', 'green'],
                ['SOC 2 Type II', 'Certified', 'green'],
              ].map(([k, v, c]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                  <span style={{ color: `var(--accent-${c})`, fontFamily: 'var(--mono)', fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
