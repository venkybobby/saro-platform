/**
 * Model Output Checker
 * Upload your AI model's output — agent evaluates against policy benchmark
 * and generates a fail/warn/pass checklist with article refs + remediation.
 */
import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (path, body) => fetch(`${BASE}${path}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }).then(r => r.json())
const get  = (path) => fetch(`${BASE}${path}`).then(r => r.json())

const SEV = {
  critical: { color:'var(--accent-red)',   bg:'rgba(255,61,106,0.08)',  border:'rgba(255,61,106,0.25)', icon:'🚫', label:'CRITICAL' },
  warn:     { color:'var(--accent-amber)', bg:'rgba(255,184,0,0.08)',   border:'rgba(255,184,0,0.25)',  icon:'⚠️', label:'WARN' },
  pass:     { color:'var(--accent-green)', bg:'rgba(0,255,136,0.06)',   border:'rgba(0,255,136,0.2)',   icon:'✓',  label:'PASS' },
}

const DEMO_SCENARIOS = [
  {
    label: '🔴 Finance — Bias + Missing Fields',
    desc: 'Credit model with direct protected attribute use, no adverse action reason, no human review',
    model_name: 'CreditScorer-v2', domain: 'finance', policy: 'EU AI Act', mode: 'text',
    output_text: 'Loan denied. The model used gender and race as input features. No adverse action reason provided. Decision confidence: unknown. No human review was applied.',
  },
  {
    label: '🟡 Healthcare — Accuracy + Oversight Gap',
    desc: 'Diagnostic AI with incomplete dataset, no contraindication check',
    model_name: 'DiagnosticAI-v1', domain: 'healthcare', policy: 'FDA SaMD', mode: 'text',
    output_text: 'Cancer probability: 73%. Model was trained on limited dataset of 200 patients. Physician override mechanism is not configured. No contraindication check performed. Clinical documentation incomplete.',
  },
  {
    label: '🟢 HR — Clean Compliant Output',
    desc: 'Well-documented HR screening model with human review and audit trail',
    model_name: 'HRScreener-v3', domain: 'hr', policy: 'NIST AI RMF', mode: 'text',
    output_text: 'Candidate ranked #3. Selection reason: technical skills score 92/100. Disparate impact ratio: 0.87 (above 4/5 threshold). Human review flag: YES. Audit trail ID: HR-20260301-A. Documentation complete.',
  },
  {
    label: '⚙️ Structured — Direct Metrics',
    desc: 'Provide numeric metric values directly (bias, accuracy, transparency)',
    model_name: 'CustomModel-v1', domain: 'general', policy: 'ISO 42001', mode: 'structured',
    output_data: { bias_score: 0.22, accuracy: 0.81, transparency_score: 0.52, human_oversight: false },
  },
  {
    label: '🔴 General — Critical Violations',
    desc: 'Multiple critical findings across bias, transparency, and oversight',
    model_name: 'RiskModel-v4', domain: 'finance', policy: 'EU AI Act', mode: 'structured',
    output_data: { bias_score: 0.35, accuracy: 0.71, transparency_score: 0.38, human_oversight: false },
  },
]

export default function ModelOutputChecker({ onNavigate }) {
  const [form, setForm] = useState({
    model_name: '', domain: 'finance', policy: 'EU AI Act', mode: 'text',
    output_text: '',
    output_data: { bias_score: 0.18, accuracy: 0.83, transparency_score: 0.61, human_oversight: true },
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [resolved, setResolved] = useState({})   // track which checklist items user marked resolved
  const [botTrigger, setBotTrigger] = useState({}) // track bot trigger states

  useEffect(() => {
    get('/api/v1/model-output/uploads').then(d => setHistory(d.uploads || [])).catch(() => {})
  }, [])

  const runCheck = async (overrideForm) => {
    const f = overrideForm || form
    if (!f.model_name?.trim()) return
    setLoading(true); setResult(null); setResolved({}); setBotTrigger({})
    try {
      const payload = {
        model_name: f.model_name, policy: f.policy, domain: f.domain,
        ...(f.mode === 'text' ? { output_text: f.output_text } : { output_data: f.output_data }),
      }
      const res = await post('/api/v1/model-output/upload', payload)
      setResult(res)
      setHistory(h => [res, ...h])
    } catch(e) {}
    finally { setLoading(false) }
  }

  const applyDemo = (d) => {
    const newForm = {
      model_name: d.model_name, domain: d.domain, policy: d.policy, mode: d.mode,
      output_text: d.output_text || '',
      output_data: d.output_data || { bias_score: 0.18, accuracy: 0.83, transparency_score: 0.61, human_oversight: true },
    }
    setForm(newForm)
    setResult(null)
    // Auto-run with the demo
    runCheck(newForm)
  }

  const triggerBot = async (itemIndex, item) => {
    setBotTrigger(b => ({ ...b, [itemIndex]: 'running' }))
    try {
      await post('/api/v1/mvp5/bots/execute', {
        bot_type: item.check?.toLowerCase().includes('bias') ? 'retrain_bot' : 'remediation_bot',
        finding_id: `FIND-${result?.upload_id}-${itemIndex}`,
      })
      setBotTrigger(b => ({ ...b, [itemIndex]: 'done' }))
    } catch(e) {
      setBotTrigger(b => ({ ...b, [itemIndex]: 'error' }))
    }
  }

  const verdict = result?.summary?.overall_verdict
  const vColor = verdict === 'FAIL' ? 'var(--accent-red)' : verdict === 'REVIEW' ? 'var(--accent-amber)' : 'var(--accent-green)'
  const vIcon  = verdict === 'FAIL' ? '🚫' : verdict === 'REVIEW' ? '⚠️' : '✅'

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Model Output Checker</h1>
          <p className="page-subtitle">Upload your AI model's output or decision log — evaluate against EU AI Act, NIST, ISO 42001, or FDA SaMD benchmarks with article-level checklist</p>
        </div>
        <button className="btn btn-secondary" style={{ fontSize:12 }} onClick={() => onNavigate && onNavigate('auditflow')}>
          ⚡ Full Pipeline →
        </button>
      </div>

      <div className="grid-2">

        {/* Left: demo scenarios + form */}
        <div>
          {/* Demo scenarios — one click runs immediately */}
          <div className="card" style={{ marginBottom:16 }}>
            <div className="card-header">
              <span className="card-title">Demo Scenarios</span>
              <span style={{ fontSize:11,color:'var(--text-muted)' }}>Click to run immediately</span>
            </div>
            <div style={{ display:'flex',flexDirection:'column',gap:4 }}>
              {DEMO_SCENARIOS.map((d, i) => (
                <div key={i}
                  style={{ padding:'10px 12px',borderRadius:8,cursor:'pointer',border:'1px solid var(--border)',transition:'all 0.15s' }}
                  onClick={() => applyDemo(d)}
                  onMouseEnter={el => { el.currentTarget.style.borderColor = 'var(--accent-cyan)'; el.currentTarget.style.background = 'rgba(0,212,255,0.04)' }}
                  onMouseLeave={el => { el.currentTarget.style.borderColor = 'var(--border)'; el.currentTarget.style.background = 'transparent' }}>
                  <div style={{ fontSize:13,fontWeight:600,color:'var(--text-primary)',marginBottom:2 }}>{d.label}</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)' }}>{d.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Manual form */}
          <div className="card">
            <div className="card-header"><span className="card-title">Custom Input</span></div>
            <div className="grid-2" style={{ marginBottom:0 }}>
              <div className="form-group">
                <label className="form-label">Model Name</label>
                <input className="form-input" placeholder="MyModel-v1" value={form.model_name} onChange={e => setForm(f=>({...f,model_name:e.target.value}))} />
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
              {[['text','📝 Paste Output'],['structured','⚙️ Enter Metrics']].map(([m,l]) => (
                <button key={m} className={`btn ${form.mode===m?'btn-primary':'btn-secondary'}`}
                  style={{ flex:1,justifyContent:'center',fontSize:12 }} onClick={() => setForm(f=>({...f,mode:m}))}>
                  {l}
                </button>
              ))}
            </div>
            {form.mode === 'text' ? (
              <div className="form-group">
                <label className="form-label">Model Output / Decision Log</label>
                <textarea className="form-textarea"
                  placeholder="Paste your AI model's decision text, prediction output, or log. The system extracts bias, accuracy, transparency, and oversight signals automatically."
                  value={form.output_text} onChange={e => setForm(f=>({...f,output_text:e.target.value}))} />
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label">Metric Values</label>
                <div style={{ background:'var(--bg-primary)',borderRadius:8,border:'1px solid var(--border)',padding:14,display:'flex',flexDirection:'column',gap:12 }}>
                  {[['bias_score','Bias Score','lower = safer',0.001],['accuracy','Model Accuracy','higher = better',0.01],['transparency_score','Transparency','higher = better',0.01]].map(([k,label,hint,step]) => (
                    <div key={k}>
                      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4 }}>
                        <label style={{ fontSize:12,color:'var(--text-secondary)' }}>{label} <span style={{ fontSize:10,color:'var(--text-muted)' }}>({hint})</span></label>
                        <span style={{ fontFamily:'var(--mono)',fontSize:13,fontWeight:700,color:'var(--accent-cyan)' }}>{form.output_data[k]}</span>
                      </div>
                      <input type="range" min={0} max={1} step={step}
                        value={form.output_data[k]}
                        onChange={e => setForm(f=>({...f,output_data:{...f.output_data,[k]:parseFloat(e.target.value)}}))}
                        style={{ width:'100%',accentColor:'var(--accent-cyan)' }} />
                    </div>
                  ))}
                  <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                    <label style={{ fontSize:12,color:'var(--text-secondary)' }}>Human Oversight</label>
                    <select style={{ padding:'5px 10px',background:'var(--bg-secondary)',border:'1px solid var(--border)',borderRadius:4,color:'var(--text-primary)',fontSize:12 }}
                      value={form.output_data.human_oversight?'yes':'no'}
                      onChange={e => setForm(f=>({...f,output_data:{...f.output_data,human_oversight:e.target.value==='yes'}}))}>
                      <option value="yes">✓ Yes</option><option value="no">✗ No</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
            <button className="btn btn-primary" onClick={() => runCheck()} disabled={loading||!form.model_name.trim()} style={{ width:'100%',justifyContent:'center' }}>
              {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Checking...</> : '🔍 Check Model Output'}
            </button>
          </div>
        </div>

        {/* Right: checklist result */}
        <div>
          {result ? (
            <div>
              {/* Verdict banner */}
              <div style={{ padding:'16px 20px',borderRadius:12,marginBottom:16,background:verdict==='FAIL'?'rgba(255,61,106,0.08)':verdict==='REVIEW'?'rgba(255,184,0,0.08)':'rgba(0,255,136,0.06)',border:`1px solid ${verdict==='FAIL'?'rgba(255,61,106,0.3)':verdict==='REVIEW'?'rgba(255,184,0,0.3)':'rgba(0,255,136,0.2)'}` }}>
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start' }}>
                  <div>
                    <div style={{ fontSize:18,fontWeight:800,color:vColor,marginBottom:4 }}>{vIcon} {verdict} — {result.policy}</div>
                    <div style={{ fontSize:12,color:'var(--text-muted)' }}>
                      {result.model_name} · {result.domain} domain
                      {result.agent_processed && <span style={{ marginLeft:8,color:'var(--accent-purple)',fontWeight:600 }}>⚡ agent-extracted</span>}
                    </div>
                  </div>
                  <div style={{ display:'flex',gap:14,textAlign:'center' }}>
                    {[['CRIT',result.summary.critical,'var(--accent-red)'],['WARN',result.summary.warn,'var(--accent-amber)'],['PASS',result.summary.pass,'var(--accent-green)']].map(([l,n,c])=>(
                      <div key={l}><div style={{ fontSize:22,fontWeight:800,fontFamily:'var(--mono)',color:c }}>{n}</div><div style={{ fontSize:9,color:'var(--text-muted)',textTransform:'uppercase' }}>{l}</div></div>
                    ))}
                  </div>
                </div>
                <div style={{ marginTop:10,fontSize:12,color:'var(--text-muted)' }}>
                  Pass rate: <strong style={{ color:'var(--accent-green)' }}>{result.summary.pass_rate}%</strong> ·
                  Policy: <strong style={{ color:'var(--accent-cyan)' }}>{result.policy_applied}</strong> ·
                  ID: <span style={{ fontFamily:'var(--mono)' }}>{result.upload_id}</span>
                </div>
              </div>

              {/* Per-check items — with Resolve + Bot buttons */}
              <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
                {result.checklist?.map((item, i) => {
                  const cfg = SEV[item.severity] || SEV.pass
                  const isResolved = resolved[i]
                  const botState = botTrigger[i]
                  return (
                    <div key={i} style={{ padding:'12px 14px',borderRadius:10,background:isResolved?'rgba(0,255,136,0.04)':cfg.bg,border:`1px solid ${isResolved?'rgba(0,255,136,0.3)':cfg.border}`,transition:'all 0.3s' }}>
                      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:4 }}>
                        <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                          <span>{isResolved ? '✅' : cfg.icon}</span>
                          <div>
                            <span style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)' }}>{item.check}</span>
                            <span style={{ marginLeft:8,fontSize:10,fontFamily:'var(--mono)',color:cfg.color,fontWeight:700 }}>{item.article_ref}</span>
                          </div>
                        </div>
                        <span style={{ fontSize:10,fontWeight:800,padding:'2px 7px',borderRadius:20,background:isResolved?'rgba(0,255,136,0.15)':cfg.border,color:isResolved?'var(--accent-green)':cfg.color,flexShrink:0 }}>
                          {isResolved ? 'RESOLVED' : cfg.label}
                        </span>
                      </div>

                      <div style={{ fontSize:12,color:'var(--text-secondary)',marginBottom:item.severity!=='pass'?8:0 }}>{item.finding}</div>

                      {item.severity !== 'pass' && !isResolved && (
                        <>
                          <div style={{ fontSize:11,color:cfg.color,display:'flex',gap:5,marginBottom:10 }}>
                            <span style={{ flexShrink:0 }}>→ Remediation:</span>
                            <span>{item.remediation}</span>
                          </div>
                          <div style={{ display:'flex',gap:8 }}>
                            <button
                              className="btn btn-secondary"
                              style={{ fontSize:11,padding:'4px 12px',color:'var(--accent-green)',borderColor:'rgba(0,255,136,0.3)' }}
                              onClick={() => setResolved(r => ({...r,[i]:true}))}>
                              ✓ Mark Resolved
                            </button>
                            <button
                              className="btn btn-secondary"
                              style={{ fontSize:11,padding:'4px 12px',color:'var(--accent-purple)',borderColor:'rgba(139,92,246,0.3)' }}
                              disabled={botState === 'running' || botState === 'done'}
                              onClick={() => triggerBot(i, item)}>
                              {botState === 'running' ? <><div className="loading-spinner" style={{width:10,height:10}} /> Running bot...</>
                               : botState === 'done'    ? '✓ Bot Applied'
                               : '🤖 Trigger Bot Fix'}
                            </button>
                          </div>
                        </>
                      )}

                      {/* Progress bar for numeric metrics */}
                      {typeof item.measured === 'number' && (
                        <div style={{ marginTop:8,display:'flex',alignItems:'center',gap:8 }}>
                          <div className="progress-bar" style={{ flex:1 }}>
                            <div style={{ height:'100%',borderRadius:3,background:isResolved?'var(--accent-green)':cfg.color,width:`${Math.min(100,Math.max(0,(item.check.toLowerCase().includes('bias')?Math.max(0,1-item.measured):item.measured)*100))}%`,transition:'width 0.5s' }} />
                          </div>
                          <span style={{ fontSize:10,fontFamily:'var(--mono)',color:isResolved?'var(--accent-green)':cfg.color,width:45,flexShrink:0 }}>
                            {(item.measured*100).toFixed(1)}%
                          </span>
                          <span style={{ fontSize:10,color:'var(--text-muted)',width:60,flexShrink:0 }}>
                            limit: {(item.threshold*100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Risk tags if any */}
              {result.risk_tags?.length > 0 && (
                <div style={{ marginTop:16,padding:'12px 14px',background:'var(--bg-primary)',borderRadius:8 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Detected Risk Signals</div>
                  {result.risk_tags.map((t,i) => (
                    <div key={i} style={{ display:'flex',justifyContent:'space-between',alignItems:'center',padding:'5px 0',borderBottom:'1px solid var(--border)' }}>
                      <span style={{ fontSize:12,color:'var(--text-secondary)' }}>{t.tag}</span>
                      <span style={{ fontSize:11,fontFamily:'var(--mono)',color:'var(--accent-amber)',fontWeight:700 }}>{(t.probability*100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Full pipeline link */}
              <div style={{ marginTop:14,padding:'12px 14px',background:'rgba(139,92,246,0.06)',borderRadius:8,border:'1px solid rgba(139,92,246,0.2)',display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                <div>
                  <div style={{ fontSize:13,fontWeight:600,color:'var(--text-primary)' }}>Want pipeline stages + standards report?</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>Run the full Audit Flow for EU AI Act / NIST / ISO article-level report</div>
                </div>
                <button className="btn btn-secondary" style={{ fontSize:12,color:'var(--accent-purple)',borderColor:'rgba(139,92,246,0.3)',flexShrink:0 }}
                  onClick={() => onNavigate && onNavigate('auditflow')}>
                  ⚡ Full Pipeline →
                </button>
              </div>
            </div>
          ) : (
            <div className="card" style={{ height:'100%' }}>
              <div className="empty-state" style={{ padding:'64px 20px' }}>
                <div className="empty-state-icon">🔍</div>
                <div className="empty-state-text">Click a demo scenario or fill the form to run a check</div>
                <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:8,maxWidth:280,textAlign:'center',lineHeight:1.7 }}>
                  The system evaluates your model's output against the selected policy benchmark and produces a fail/warn/pass checklist with article references and remediation steps
                </div>
              </div>
              {/* History */}
              {history.length > 0 && (
                <div style={{ borderTop:'1px solid var(--border)',padding:'14px 0 0' }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:10 }}>Recent Checks</div>
                  {history.slice(0,5).map((h,i) => (
                    <div key={i} style={{ display:'flex',justifyContent:'space-between',padding:'7px 0',borderBottom:'1px solid rgba(30,45,69,0.4)',fontSize:12 }}>
                      <span style={{ color:'var(--text-primary)',fontWeight:500 }}>{h.model_name}</span>
                      <span style={{ color:h.summary?.overall_verdict==='FAIL'?'var(--accent-red)':h.summary?.overall_verdict==='REVIEW'?'var(--accent-amber)':'var(--accent-green)',fontFamily:'var(--mono)',fontWeight:700 }}>{h.summary?.overall_verdict}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
