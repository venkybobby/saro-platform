import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (path, body) => fetch(`${BASE}${path}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }).then(r => r.json())
const get = (path) => fetch(`${BASE}${path}`).then(r => r.json())

const SEVERITY_CONFIG = {
  critical: { color: 'var(--accent-red)',   bg: 'rgba(255,61,106,0.08)',  border: 'rgba(255,61,106,0.25)', icon: '🚫', label: 'CRITICAL' },
  warn:     { color: 'var(--accent-amber)', bg: 'rgba(255,184,0,0.08)',   border: 'rgba(255,184,0,0.25)',  icon: '⚠️', label: 'WARN' },
  pass:     { color: 'var(--accent-green)', bg: 'rgba(0,255,136,0.06)',   border: 'rgba(0,255,136,0.2)',   icon: '✓',  label: 'PASS' },
}

const DEMO_SCENARIOS = [
  {
    label: '🔴 Finance — Bias + Missing Fields',
    form: { model_name: 'CreditScorer-v2', domain: 'finance', policy: 'EU AI Act', mode: 'text',
      output_text: 'Loan denied. The model used gender and race as input features. No adverse action reason provided. Decision confidence: unknown. No human review was applied.' },
  },
  {
    label: '🟡 Healthcare — Accuracy + Oversight Gap',
    form: { model_name: 'DiagnosticAI-v1', domain: 'healthcare', policy: 'FDA SaMD', mode: 'text',
      output_text: 'Cancer probability: 73%. Model was trained on limited dataset. Physician override mechanism is not configured. No contraindication check performed.' },
  },
  {
    label: '🟢 HR — Clean Output',
    form: { model_name: 'HRScreener-v3', domain: 'hr', policy: 'NIST AI RMF', mode: 'text',
      output_text: 'Candidate ranked #3. Selection reason: technical skills score 92/100. Disparate impact ratio: 0.87 (above 4/5 threshold). Human review flag: YES. Audit trail ID: HR-20260301-A' },
  },
  {
    label: '🔴 Structured — Critical Bias',
    form: { model_name: 'LoanEngine-v4', domain: 'finance', policy: 'EU AI Act', mode: 'structured',
      output_data: { bias_score: 0.31, transparency_score: 0.42, accuracy: 0.74, human_oversight: false, feature_names: ['gender', 'race', 'age'], fields_present: [] } },
  },
]

export default function ModelOutputChecker() {
  const [tab, setTab] = useState('checker')
  const [form, setForm] = useState({
    model_name: '', domain: 'finance', policy: 'EU AI Act', mode: 'text',
    output_text: '',
    output_data: { bias_score: 0.18, transparency_score: 0.62, accuracy: 0.84, human_oversight: true, feature_names: [], fields_present: [] }
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploads, setUploads] = useState([])
  const [selectedUpload, setSelectedUpload] = useState(null)
  const [policies, setPolicies] = useState([])

  useEffect(() => {
    get('/api/v1/model-output/uploads').then(d => setUploads(d.uploads || [])).catch(() => {})
    get('/api/v1/model-output/policies/list').then(d => setPolicies(d.policies || [])).catch(() => {})
  }, [])

  const runCheck = async () => {
    if (!form.model_name.trim()) return
    setLoading(true)
    try {
      const payload = {
        model_name: form.model_name,
        domain: form.domain,
        policy: form.policy,
        ...(form.mode === 'text' ? { output_text: form.output_text } : { output_data: form.output_data }),
      }
      const res = await post('/api/v1/model-output/upload', payload)
      setResult(res)
      setUploads(prev => [res, ...prev])
    } catch(e) {}
    finally { setLoading(false) }
  }

  const applyDemo = (scenario) => {
    setForm(f => ({ ...f, ...scenario.form }))
    setResult(null)
  }

  const verdict = result?.summary?.overall_verdict
  const verdictCfg = verdict === 'FAIL' ? SEVERITY_CONFIG.critical : verdict === 'REVIEW' ? SEVERITY_CONFIG.warn : SEVERITY_CONFIG.pass

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Model Output Checker</h1>
          <p className="page-subtitle">
            Upload AI model outputs → evaluate against policy benchmarks → get fail/warn/pass checklist with article-level mappings
          </p>
        </div>
        <span className="badge badge-cyan" style={{ padding:'6px 14px',fontSize:12 }}>Agent-Powered</span>
      </div>

      {/* How it works banner */}
      <div style={{ marginBottom:24,padding:'14px 20px',background:'var(--bg-card)',borderRadius:10,border:'1px solid var(--border)',display:'flex',gap:20,alignItems:'center',flexWrap:'wrap' }}>
        {[
          { step:'1', label:'Upload Output', desc:'Paste AI text or structured JSON output from your model' },
          { step:'2', label:'Select Benchmark', desc:'Choose policy: EU AI Act, NIST, ISO 42001, FDA SaMD' },
          { step:'3', label:'Agent Analysis', desc:'SARO evaluates bias, transparency, accuracy, oversight, fields' },
          { step:'4', label:'Checklist', desc:'Fail/Warn/Pass per article with remediation steps' },
        ].map((s,i) => (
          <div key={i} style={{ display:'flex',gap:10,alignItems:'flex-start',flex:'1 1 180px' }}>
            <div style={{ width:28,height:28,borderRadius:'50%',background:'var(--accent-cyan)',color:'#000',display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,fontWeight:800,flexShrink:0 }}>{s.step}</div>
            <div>
              <div style={{ fontSize:12,fontWeight:700,color:'var(--text-primary)' }}>{s.label}</div>
              <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{s.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="tabs">
        {[['checker','🔍 Run Checker'],['history','📋 Upload History'],['benchmarks','📊 Policy Benchmarks']].map(([t,l]) => (
          <div key={t} className={`tab ${tab===t?'active':''}`} onClick={() => setTab(t)}>{l}</div>
        ))}
      </div>

      {/* ── CHECKER ── */}
      {tab === 'checker' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Configure Check</span></div>

            {/* Demo scenarios */}
            <div style={{ marginBottom:16 }}>
              <div style={{ fontSize:11,color:'var(--text-muted)',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Quick Demo Scenarios</div>
              <div style={{ display:'flex',flexDirection:'column',gap:6 }}>
                {DEMO_SCENARIOS.map((d,i) => (
                  <button key={i} className="btn btn-secondary" style={{ justifyContent:'flex-start',fontSize:12,padding:'8px 12px' }} onClick={() => applyDemo(d)}>
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ height:1,background:'var(--border)',margin:'0 0 16px' }} />

            <div className="grid-2" style={{ marginBottom:0 }}>
              <div className="form-group">
                <label className="form-label">Model Name</label>
                <input className="form-input" placeholder="CreditScorer-v2" value={form.model_name} onChange={e => setForm(f=>({...f,model_name:e.target.value}))} />
              </div>
              <div className="form-group">
                <label className="form-label">Domain</label>
                <select className="form-select" value={form.domain} onChange={e => setForm(f=>({...f,domain:e.target.value}))}>
                  {['finance','healthcare','hr','general'].map(d => <option key={d}>{d}</option>)}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Policy Benchmark</label>
              <select className="form-select" value={form.policy} onChange={e => setForm(f=>({...f,policy:e.target.value}))}>
                {['EU AI Act','NIST AI RMF','ISO 42001','FDA SaMD'].map(p => <option key={p}>{p}</option>)}
              </select>
            </div>

            <div style={{ display:'flex',gap:8,marginBottom:12 }}>
              {[['text','📝 Text / Description'],['structured','⚙️ Structured JSON']].map(([m,l]) => (
                <button key={m} className={`btn ${form.mode===m?'btn-primary':'btn-secondary'}`} style={{ flex:1,justifyContent:'center',fontSize:12 }} onClick={() => setForm(f=>({...f,mode:m}))}>
                  {l}
                </button>
              ))}
            </div>

            {form.mode === 'text' ? (
              <div className="form-group">
                <label className="form-label">Model Output Text</label>
                <textarea className="form-textarea" rows={6}
                  placeholder="Paste your AI model's output, decision log, or prediction description here. The agent will extract metrics and evaluate against the selected policy benchmark."
                  value={form.output_text}
                  onChange={e => setForm(f=>({...f,output_text:e.target.value}))} />
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label">Structured Output Metrics</label>
                <div style={{ display:'flex',flexDirection:'column',gap:8,padding:'12px',background:'var(--bg-primary)',borderRadius:8,border:'1px solid var(--border)' }}>
                  {[
                    ['bias_score','Bias Score (0–1)','number',0.001],
                    ['transparency_score','Transparency (0–1)','number',0.01],
                    ['accuracy','Accuracy (0–1)','number',0.01],
                  ].map(([k,label,type,step]) => (
                    <div key={k} style={{ display:'flex',justifyContent:'space-between',alignItems:'center',gap:12 }}>
                      <label style={{ fontSize:12,color:'var(--text-secondary)',flex:1 }}>{label}</label>
                      <input type={type} step={step} min={0} max={1} style={{ width:80,padding:'4px 8px',background:'var(--bg-secondary)',border:'1px solid var(--border)',borderRadius:4,color:'var(--text-primary)',fontFamily:'var(--mono)',fontSize:12 }}
                        value={form.output_data[k]}
                        onChange={e => setForm(f=>({...f,output_data:{...f.output_data,[k]:parseFloat(e.target.value)}}))} />
                    </div>
                  ))}
                  <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',gap:12 }}>
                    <label style={{ fontSize:12,color:'var(--text-secondary)',flex:1 }}>Human Oversight</label>
                    <select style={{ width:80,padding:'4px 8px',background:'var(--bg-secondary)',border:'1px solid var(--border)',borderRadius:4,color:'var(--text-primary)',fontSize:12 }}
                      value={form.output_data.human_oversight ? 'yes' : 'no'}
                      onChange={e => setForm(f=>({...f,output_data:{...f.output_data,human_oversight:e.target.value==='yes'}}))}>
                      <option value="yes">Yes</option><option value="no">No</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            <button className="btn btn-primary" onClick={runCheck} disabled={loading || !form.model_name.trim()} style={{ width:'100%',justifyContent:'center' }}>
              {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Running compliance check...</> : '🔍 Run Compliance Check'}
            </button>
          </div>

          {/* Results panel */}
          <div className="card">
            <div className="card-header"><span className="card-title">Compliance Checklist</span></div>
            {result ? (
              <div>
                {/* Verdict banner */}
                <div style={{ padding:'14px 16px',borderRadius:10,marginBottom:16,background:verdictCfg.bg,border:`1px solid ${verdictCfg.border}` }}>
                  <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                    <div>
                      <div style={{ fontSize:18,fontWeight:800,color:verdictCfg.color }}>{verdictCfg.icon} {verdict}</div>
                      <div style={{ fontSize:12,color:'var(--text-muted)',marginTop:3 }}>
                        {result.model_name} · {result.policy}
                      </div>
                    </div>
                    <div style={{ textAlign:'right' }}>
                      <div style={{ display:'flex',gap:8 }}>
                        {[
                          ['CRITICAL',result.summary?.critical,'var(--accent-red)'],
                          ['WARN',result.summary?.warn,'var(--accent-amber)'],
                          ['PASS',result.summary?.pass,'var(--accent-green)'],
                        ].map(([l,v,c]) => (
                          <div key={l} style={{ textAlign:'center' }}>
                            <div style={{ fontSize:20,fontWeight:800,fontFamily:'var(--mono)',color:c }}>{v}</div>
                            <div style={{ fontSize:9,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px' }}>{l}</div>
                          </div>
                        ))}
                      </div>
                      <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:6 }}>Pass rate: {result.summary?.pass_rate}%</div>
                    </div>
                  </div>
                </div>

                {/* Checklist items */}
                <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
                  {result.checklist?.map((item,i) => {
                    const cfg = SEVERITY_CONFIG[item.severity] || SEVERITY_CONFIG.pass
                    return (
                      <div key={i} style={{ padding:'12px 14px',borderRadius:8,background:cfg.bg,border:`1px solid ${cfg.border}` }}>
                        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:6 }}>
                          <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                            <span style={{ fontSize:16 }}>{cfg.icon}</span>
                            <div>
                              <div style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)' }}>{item.check}</div>
                              <div style={{ fontSize:10,color:cfg.color,fontFamily:'var(--mono)',fontWeight:700 }}>{item.article_ref} · {item.article_title}</div>
                            </div>
                          </div>
                          <span style={{ fontSize:10,fontWeight:800,padding:'3px 8px',borderRadius:20,background:cfg.border,color:cfg.color,flexShrink:0 }}>{cfg.label}</span>
                        </div>
                        <div style={{ fontSize:12,color:'var(--text-secondary)',marginBottom:item.severity!=='pass'?6:0 }}>{item.finding}</div>
                        {item.severity !== 'pass' && (
                          <div style={{ fontSize:11,color:cfg.color,display:'flex',gap:6,alignItems:'flex-start' }}>
                            <span style={{ flexShrink:0 }}>→</span>
                            <span>{item.remediation}</span>
                          </div>
                        )}
                        {typeof item.measured === 'number' && (
                          <div style={{ marginTop:6,display:'flex',alignItems:'center',gap:8 }}>
                            <div className="progress-bar" style={{ flex:1 }}>
                              <div style={{ height:'100%',borderRadius:3,background:cfg.color,width:`${Math.min(100,item.measured*100)}%`,transition:'width 0.5s' }} />
                            </div>
                            <span style={{ fontSize:11,fontFamily:'var(--mono)',color:cfg.color,width:38,flexShrink:0 }}>
                              {(item.measured*100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                <div style={{ marginTop:14,padding:'10px 14px',background:'var(--bg-primary)',borderRadius:8,fontSize:11,color:'var(--text-muted)',borderTop:'1px solid var(--border)' }}>
                  Upload ID: <span style={{ fontFamily:'var(--mono)',color:'var(--accent-cyan)' }}>{result.upload_id}</span> ·
                  Benchmark: <span style={{ color:'var(--text-secondary)' }}>{result.benchmark_source}</span> ·
                  {result.agent_processed && <span style={{ color:'var(--accent-purple)',marginLeft:6 }}>⚡ Agent-processed text</span>}
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">🔍</div>
                <div className="empty-state-text">Select a demo scenario or fill in the form, then click Run Compliance Check</div>
                <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:8,maxWidth:300,textAlign:'center',lineHeight:1.6 }}>
                  The agent will evaluate your model output against EU AI Act, NIST, ISO 42001, or FDA benchmarks and generate a fail/warn/pass checklist
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── HISTORY ── */}
      {tab === 'history' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <span className="card-title">Upload History</span>
              <span className="badge badge-cyan">{uploads.length} checks</span>
            </div>
            {uploads.length === 0 ? (
              <div className="empty-state"><div className="empty-state-icon">📋</div><div className="empty-state-text">No checks run yet</div></div>
            ) : (
              <div style={{ display:'flex',flexDirection:'column',gap:0 }}>
                {uploads.map((u,i) => {
                  const cfg = SEVERITY_CONFIG[u.summary?.overall_verdict==='FAIL'?'critical':u.summary?.overall_verdict==='REVIEW'?'warn':'pass']
                  return (
                    <div key={i} style={{ padding:'12px 0',borderBottom:'1px solid var(--border)',cursor:'pointer' }} onClick={() => setSelectedUpload(u)}>
                      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                        <div>
                          <div style={{ fontSize:13,fontWeight:600,color:selectedUpload?.upload_id===u.upload_id?'var(--accent-cyan)':'var(--text-primary)' }}>{u.model_name}</div>
                          <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{u.policy} · {u.domain} · {new Date(u.uploaded_at).toLocaleTimeString()}</div>
                        </div>
                        <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                          <div style={{ textAlign:'right' }}>
                            <div style={{ fontSize:10,color:'var(--accent-red)',fontWeight:700 }}>{u.summary?.critical} crit</div>
                            <div style={{ fontSize:10,color:'var(--accent-amber)',fontWeight:700 }}>{u.summary?.warn} warn</div>
                          </div>
                          <span style={{ fontSize:11,fontWeight:800,padding:'3px 8px',borderRadius:20,background:cfg.border,color:cfg.color }}>{u.summary?.overall_verdict}</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="card">
            {selectedUpload ? (
              <div>
                <div className="card-header">
                  <div>
                    <div style={{ fontSize:14,fontWeight:700 }}>{selectedUpload.model_name}</div>
                    <div style={{ fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>{selectedUpload.upload_id}</div>
                  </div>
                </div>
                <div style={{ display:'flex',gap:16,marginBottom:16 }}>
                  {[['Critical',selectedUpload.summary?.critical,'var(--accent-red)'],['Warn',selectedUpload.summary?.warn,'var(--accent-amber)'],['Pass',selectedUpload.summary?.pass,'var(--accent-green)']].map(([l,v,c]) => (
                    <div key={l} style={{ flex:1,padding:'10px',background:'var(--bg-primary)',borderRadius:8,textAlign:'center' }}>
                      <div style={{ fontSize:20,fontWeight:800,fontFamily:'var(--mono)',color:c }}>{v}</div>
                      <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase' }}>{l}</div>
                    </div>
                  ))}
                </div>
                {selectedUpload.checklist?.map((item,i) => {
                  const cfg = SEVERITY_CONFIG[item.severity] || SEVERITY_CONFIG.pass
                  return (
                    <div key={i} style={{ padding:'9px 0',borderBottom:'1px solid var(--border)',display:'flex',gap:10,alignItems:'flex-start' }}>
                      <span style={{ fontSize:14,flexShrink:0 }}>{cfg.icon}</span>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{item.check}</div>
                        <div style={{ fontSize:11,color:cfg.color,fontFamily:'var(--mono)' }}>{item.article_ref}</div>
                        <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{item.finding}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="empty-state"><div className="empty-state-icon">📊</div><div className="empty-state-text">Select a check from the left to view details</div></div>
            )}
          </div>
        </div>
      )}

      {/* ── BENCHMARKS ── */}
      {tab === 'benchmarks' && (
        <div>
          <div style={{ marginBottom:20,fontSize:13,color:'var(--text-secondary)',lineHeight:1.7 }}>
            SARO evaluates your model outputs against these policy benchmarks. Each benchmark defines thresholds for bias, transparency, accuracy, and human oversight — mapped to specific regulatory articles.
          </div>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(280px,1fr))',gap:16 }}>
            {[
              { name:'EU AI Act', color:'cyan', checks:['Bias ≤ 15% (Art. 10)','Transparency ≥ 60% (Art. 13)','Accuracy ≥ 80% (Art. 15)','Human oversight required (Art. 14)','Technical docs complete (Art. 11)'], penalty:'€30M or 6% global turnover', scope:'High-risk AI systems' },
              { name:'NIST AI RMF', color:'green', checks:['Bias ≤ 12% (MAP 2.3)','Transparency ≥ 65% (GOV 6.1)','Accuracy ≥ 82% (MEASURE 2.5)','Governance policies (GOVERN 1.1)','Privacy harm docs (MAP 1.1)'], penalty:'Federal enforcement', scope:'US federal AI systems' },
              { name:'ISO 42001', color:'purple', checks:['Bias ≤ 18% (A.8.4)','Transparency ≥ 55% (A.6.2)','Accuracy ≥ 78% (A.9.3)','Roles defined (A.5.2)','Documentation (A.6.1)'], penalty:'Certification revocation', scope:'Global AI management systems' },
              { name:'FDA SaMD', color:'amber', checks:['Bias ≤ 10% (§3.2)','Transparency ≥ 75% (§4.1)','Accuracy ≥ 90% (§2.1)','Clinician override (§5.3)','Software docs (§1.0)'], penalty:'Market withdrawal', scope:'AI/ML medical devices' },
            ].map(b => (
              <div key={b.name} className="card">
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:12 }}>
                  <div style={{ fontSize:15,fontWeight:700,color:`var(--accent-${b.color})` }}>{b.name}</div>
                  <span className={`badge badge-${b.color}`} style={{ fontSize:10 }}>Active</span>
                </div>
                <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:12 }}>Scope: {b.scope}</div>
                <div style={{ display:'flex',flexDirection:'column',gap:5,marginBottom:12 }}>
                  {b.checks.map((c,i) => (
                    <div key={i} style={{ fontSize:12,color:'var(--text-secondary)',display:'flex',gap:6 }}>
                      <span style={{ color:`var(--accent-${b.color})`,flexShrink:0 }}>→</span>{c}
                    </div>
                  ))}
                </div>
                <div style={{ padding:'8px 10px',background:`var(--accent-${b.color}-dim)`,borderRadius:6,fontSize:11,color:`var(--accent-${b.color})`,fontWeight:600 }}>
                  Penalty: {b.penalty}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
