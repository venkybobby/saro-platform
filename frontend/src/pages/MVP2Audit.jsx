import { useState, useEffect } from 'react'
import { api } from '../lib/api'

const BASE = window.SARO_CONFIG?.apiUrl || ''

export default function MVP2Audit() {
  const [tab, setTab] = useState('run')
  const [form, setForm] = useState({ model_name:'', model_version:'1.0', use_case:'', jurisdiction:'EU', risk_category:'medium' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [audits, setAudits] = useState([])
  const [matrix, setMatrix] = useState(null)
  const [error, setError] = useState(null)
  const [reportResult, setReportResult] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportStandard, setReportStandard] = useState('EU AI Act')

  useEffect(() => {
    api.listAudits().then(setAudits).catch(() => {})
    api.complianceMatrix('EU').then(setMatrix).catch(() => {})
  }, [])

  const handleAudit = async () => {
    if (!form.model_name || !form.use_case) { setError('Model name and use case are required'); return }
    setLoading(true); setError(null)
    try {
      const res = await api.runAudit(form)
      setResult(res); setAudits(a => [res, ...a])
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const generateReport = async () => {
    if (!result) return
    setReportLoading(true)
    try {
      const res = await fetch(`${BASE}/api/v1/audit-reports/generate`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ audit_result: result, standard: reportStandard, sector: form.use_case, jurisdiction: form.jurisdiction })
      })
      setReportResult(await res.json())
      setTab('report')
    } catch(e) {}
    finally { setReportLoading(false) }
  }

  const rb = r => ({critical:'badge-red',high:'badge-red',medium:'badge-amber',low:'badge-green'}[r]||'badge-gray')
  const sb = s => ({compliant:'badge-green',non_compliant:'badge-red',pending:'badge-amber',review:'badge-cyan'}[s]||'badge-gray')

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">AI Model Audit</h1>
          <p className="page-subtitle">Run compliance audits, assess regulatory risk, and generate standards-aligned reports</p>
        </div>
      </div>

      <div className="tabs">
        {[['run','▶ Run Audit'],['history','📋 History'],['matrix','📊 Compliance Matrix'],['report','📄 Standards Report']].map(([t,l]) => (
          <div key={t} className={`tab ${tab===t?'active':''}`} onClick={() => setTab(t)}>{l}</div>
        ))}
      </div>

      {tab === 'run' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Audit Configuration</span></div>
            {error && <div style={{ background:'var(--accent-red-dim)',color:'var(--accent-red)',border:'1px solid rgba(255,61,106,0.3)',borderRadius:6,padding:'10px 14px',marginBottom:16,fontSize:13 }}>{error}</div>}
            <div className="grid-2" style={{ marginBottom:0 }}>
              <div className="form-group">
                <label className="form-label">Model Name</label>
                <input className="form-input" placeholder="CreditScorer-v2" value={form.model_name} onChange={e => setForm(f=>({...f,model_name:e.target.value}))} />
              </div>
              <div className="form-group">
                <label className="form-label">Version</label>
                <input className="form-input" placeholder="2.1.0" value={form.model_version} onChange={e => setForm(f=>({...f,model_version:e.target.value}))} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Use Case / Domain</label>
              <input className="form-input" placeholder="healthcare, finance, hr, fraud detection..." value={form.use_case} onChange={e => setForm(f=>({...f,use_case:e.target.value}))} />
            </div>
            <div className="grid-2" style={{ marginBottom:0 }}>
              <div className="form-group">
                <label className="form-label">Jurisdiction</label>
                <select className="form-select" value={form.jurisdiction} onChange={e => setForm(f=>({...f,jurisdiction:e.target.value}))}>
                  {['EU','US','UK','APAC'].map(j => <option key={j}>{j}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Risk Category</label>
                <select className="form-select" value={form.risk_category} onChange={e => setForm(f=>({...f,risk_category:e.target.value}))}>
                  {['low','medium','high','critical'].map(r => <option key={r}>{r}</option>)}
                </select>
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleAudit} disabled={loading} style={{ width:'100%',justifyContent:'center' }}>
              {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Running...</> : '◉ Run Compliance Audit'}
            </button>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Audit Results</span></div>
            {result ? (
              <div>
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:16 }}>
                  <div>
                    <div style={{ fontSize:15,fontWeight:600 }}>{result.model_name}</div>
                    <div style={{ fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>{result.audit_id}</div>
                    <div style={{ display:'flex',gap:6,marginTop:8,flexWrap:'wrap' }}>
                      <span className={`badge ${rb(result.overall_risk)}`}>{result.overall_risk} risk</span>
                      <span className={`badge ${sb(result.status)}`}>{result.status?.replace('_',' ')}</span>
                    </div>
                  </div>
                  <div className="score-ring">
                    <div className="score-ring-value" style={{ color:result.compliance_score>=0.8?'var(--accent-green)':result.compliance_score>=0.6?'var(--accent-amber)':'var(--accent-red)' }}>
                      {(result.compliance_score*100).toFixed(0)}%
                    </div>
                    <div className="score-ring-label">Compliance</div>
                  </div>
                </div>
                <div style={{ marginBottom:14 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Findings ({result.findings?.length})</div>
                  {result.findings?.map((f,i) => (
                    <div key={i} style={{ display:'flex',gap:10,padding:'8px 0',borderBottom:'1px solid var(--border)' }}>
                      <span className={`badge ${f.severity==='critical'||f.severity==='high'?'badge-red':f.severity==='medium'?'badge-amber':'badge-gray'}`} style={{ flexShrink:0 }}>{f.severity}</span>
                      <div><div style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{f.category}</div><div style={{ fontSize:11,color:'var(--text-secondary)' }}>{f.finding}</div></div>
                    </div>
                  ))}
                </div>
                <div style={{ marginBottom:16 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Recommendations</div>
                  {result.recommendations?.slice(0,3).map((r,i) => (
                    <div key={i} style={{ display:'flex',gap:8,padding:'5px 0',fontSize:12,color:'var(--text-secondary)' }}>
                      <span style={{ color:'var(--accent-cyan)',flexShrink:0 }}>→</span><span>{r}</span>
                    </div>
                  ))}
                </div>
                <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                  <select className="form-select" style={{ flex:1 }} value={reportStandard} onChange={e => setReportStandard(e.target.value)}>
                    {['EU AI Act','NIST AI RMF','ISO 42001'].map(s => <option key={s}>{s}</option>)}
                  </select>
                  <button className="btn btn-secondary" onClick={generateReport} disabled={reportLoading}>
                    {reportLoading ? 'Generating...' : '📄 Standards Report'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state"><div className="empty-state-icon">◉</div><div className="empty-state-text">Configure and run an audit to see results</div></div>
            )}
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div className="card">
          <div className="card-header"><span className="card-title">Audit History</span><span className="badge badge-cyan">{audits.length} audits</span></div>
          {audits.length > 0 ? (
            <table className="data-table">
              <thead><tr><th>Audit ID</th><th>Model</th><th>Risk</th><th>Score</th><th>Status</th><th>Date</th></tr></thead>
              <tbody>
                {audits.map((a,i) => (
                  <tr key={i}>
                    <td style={{ fontFamily:'var(--mono)',fontSize:11 }}>{a.audit_id}</td>
                    <td style={{ color:'var(--text-primary)' }}>{a.model_name}</td>
                    <td><span className={`badge ${rb(a.overall_risk)}`}>{a.overall_risk}</span></td>
                    <td style={{ fontFamily:'var(--mono)',color:a.compliance_score>=0.8?'var(--accent-green)':a.compliance_score>=0.6?'var(--accent-amber)':'var(--accent-red)' }}>{(a.compliance_score*100).toFixed(0)}%</td>
                    <td><span className={`badge ${sb(a.status)}`}>{a.status?.replace('_',' ')}</span></td>
                    <td style={{ fontFamily:'var(--mono)',fontSize:11 }}>{new Date(a.generated_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <div className="empty-state"><div className="empty-state-icon">📋</div><div className="empty-state-text">No audits yet. Use Run Audit to start.</div></div>}
        </div>
      )}

      {tab === 'matrix' && matrix && (
        <div className="card">
          <div className="card-header"><span className="card-title">Compliance Requirements Matrix — {matrix.jurisdiction}</span></div>
          {matrix.regulations?.map((reg,i) => (
            <div key={i} style={{ marginBottom:20,paddingBottom:20,borderBottom:i<matrix.regulations.length-1?'1px solid var(--border)':'none' }}>
              <div style={{ fontSize:15,fontWeight:600,marginBottom:4 }}>{reg.name}</div>
              <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:6 }}>Enforcement: {reg.enforcement_date} · Penalty: {reg.penalty}</div>
              <div style={{ display:'flex',gap:6,flexWrap:'wrap' }}>
                {reg.articles?.map((art,j) => <span key={j} style={{ fontSize:11,padding:'3px 10px',borderRadius:20,background:'var(--bg-primary)',border:'1px solid var(--border)',color:'var(--text-secondary)' }}>{art}</span>)}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'report' && (
        <div>
          {reportResult ? (
            <div>
              <div className="grid-2" style={{ marginBottom:20 }}>
                {[
                  {label:'Compliance Score',value:`${(reportResult.executive_summary?.overall_compliance_score*100).toFixed(0)}%`,color:'green'},
                  {label:'Mitigation',value:`${reportResult.executive_summary?.mitigation_percent}%`,color:'cyan'},
                  {label:'Fine Avoided',value:`$${reportResult.executive_summary?.estimated_fine_avoided_usd?.toLocaleString()}`,color:'amber'},
                  {label:'Gaps Identified',value:reportResult.gaps_identified,color:'red'},
                ].map(m => (
                  <div key={m.label} className="card" style={{ padding:'14px 16px' }}>
                    <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:6 }}>{m.label}</div>
                    <div style={{ fontSize:22,fontWeight:700,fontFamily:'var(--mono)',color:`var(--accent-${m.color})` }}>{m.value}</div>
                  </div>
                ))}
              </div>

              <div className="card" style={{ marginBottom:16 }}>
                <div className="card-header">
                  <span className="card-title">Standards Mapping — {reportResult.standard}</span>
                  <span style={{ fontFamily:'var(--mono)',fontSize:11,color:'var(--text-muted)' }}>{reportResult.report_id}</span>
                </div>
                <table className="data-table">
                  <thead><tr><th>Finding</th><th>Article</th><th>Requirement</th><th>Score</th><th>Status</th></tr></thead>
                  <tbody>
                    {reportResult.standards_mapping?.map((m,i) => (
                      <tr key={i}>
                        <td style={{ color:'var(--text-primary)',fontWeight:500 }}>{m.finding_category}</td>
                        <td><span className="badge badge-cyan">{m.article}</span></td>
                        <td style={{ fontSize:11,color:'var(--text-secondary)',maxWidth:240 }}>{m.requirement}</td>
                        <td style={{ fontFamily:'var(--mono)',color:m.compliance_score>=0.75?'var(--accent-green)':'var(--accent-amber)',fontWeight:600 }}>{(m.compliance_score*100).toFixed(0)}%</td>
                        <td><span className={`badge ${m.status==='compliant'?'badge-green':'badge-amber'}`}>{m.status?.replace('_',' ')}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="grid-2">
                <div className="card">
                  <div className="card-header"><span className="card-title">Recommendations</span></div>
                  {reportResult.recommendations?.map((r,i) => (
                    <div key={i} style={{ display:'flex',gap:8,padding:'8px 0',borderBottom:'1px solid var(--border)',fontSize:13,color:'var(--text-secondary)' }}>
                      <span style={{ color:'var(--accent-cyan)',flexShrink:0,fontWeight:700 }}>→</span><span>{r}</span>
                    </div>
                  ))}
                </div>
                <div className="card">
                  <div className="card-header"><span className="card-title">Evidence Chain</span></div>
                  {reportResult.evidence_chain?.map((e,i) => (
                    <div key={i} style={{ display:'flex',gap:10,padding:'8px 0',borderBottom:'1px solid var(--border)',alignItems:'center' }}>
                      <span className={`badge ${e.type==='system'?'badge-gray':e.type==='output'?'badge-green':'badge-cyan'}`} style={{ fontSize:10,flexShrink:0 }}>{e.type}</span>
                      <span style={{ fontSize:12,color:'var(--text-secondary)' }}>{e.event}</span>
                    </div>
                  ))}
                  <div style={{ marginTop:16,padding:'10px 14px',background:'var(--accent-green-dim)',borderRadius:8,border:'1px solid rgba(0,255,136,0.2)',textAlign:'center' }}>
                    <div style={{ fontWeight:700,color:'var(--accent-green)' }}>{reportResult.ready_for_submission ? '✓ Ready for Submission' : '⚠ Review Required'}</div>
                    <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>Generated in {reportResult.generation_time_seconds}s</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <div className="empty-state-text">Run an audit first, then click "Standards Report" to generate a standards-aligned output</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
