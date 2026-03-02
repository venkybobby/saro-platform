/**
 * AuditFlow — Full End-to-End Pipeline Page
 * Covers all gaps from the analysis doc:
 * 1. Model output ingestion (text or structured)
 * 2. Non-standard doc upload with agent extraction
 * 3. Live policy run with ingestion status log
 * 4. Interactive checklist (fail/warn/pass with article refs)
 * 5. Pipeline stage visualizer
 * 6. Standards-aligned report output
 */
import { useState, useEffect, useRef } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (p, b) => fetch(`${BASE}${p}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b) }).then(r=>r.json())
const get  = (p) => fetch(`${BASE}${p}`).then(r=>r.json())

const SEV = {
  critical: { color:'var(--accent-red)',   bg:'rgba(255,61,106,0.08)',  border:'rgba(255,61,106,0.3)',  icon:'🚫', label:'CRITICAL' },
  warn:     { color:'var(--accent-amber)', bg:'rgba(255,184,0,0.08)',   border:'rgba(255,184,0,0.3)',   icon:'⚠️', label:'WARN' },
  pass:     { color:'var(--accent-green)', bg:'rgba(0,255,136,0.06)',   border:'rgba(0,255,136,0.2)',   icon:'✓',  label:'PASS' },
}
const VERDICT = {
  FAIL:   { color:'var(--accent-red)',   icon:'🚫', label:'FAIL — Compliance Gaps Detected' },
  REVIEW: { color:'var(--accent-amber)', icon:'⚠️', label:'REVIEW — Warnings Need Attention' },
  PASS:   { color:'var(--accent-green)', icon:'✅', label:'PASS — Compliant' },
}

const DEMO_SCENARIOS = [
  {
    label: '🔴 Finance — Bias + PII + No Oversight',
    desc: 'Worst-case credit model with multiple critical violations',
    payload: {
      model_name: 'CreditScorer-v2', domain: 'finance', policy: 'EU AI Act', mode: 'text',
      output_text: 'Loan denied. Model used gender and race as direct input features, leading to disparate impact ratio of 0.61. No adverse action reason provided. No human review mechanism configured. Bias score exceeds threshold. Black box decision — no explanation available.',
    },
  },
  {
    label: '🟡 Healthcare — Accuracy + Documentation Gap',
    desc: 'Diagnostic AI below FDA accuracy threshold',
    payload: {
      model_name: 'DiagnosticAI-v1', domain: 'healthcare', policy: 'FDA SaMD', mode: 'text',
      output_text: 'Cancer probability: 64%. Model validation on limited 200-patient dataset. Technical documentation is incomplete. Physician override mechanism is configured for review. Explainability features available for clinicians.',
    },
  },
  {
    label: '🟢 HR — Clean Compliant Output',
    desc: 'Well-documented HR screening model passing all checks',
    payload: {
      model_name: 'HRScreener-v3', domain: 'hr', policy: 'NIST AI RMF', mode: 'text',
      output_text: 'Candidate ranked #4/47. Selection reason: technical assessment 91/100, experience match 87%. Disparate impact ratio: 0.88 (above 4/5 threshold). Human review flag: YES — all decisions reviewed by HR lead. Audit trail ID: HR-20260301-881. Documentation complete. Override mechanism active.',
    },
  },
  {
    label: '⚙️ Structured — Custom Metrics',
    desc: 'Provide your own metric values directly',
    payload: {
      model_name: 'CustomModel-v1', domain: 'general', policy: 'ISO 42001', mode: 'structured',
      output_data: { bias_score: 0.22, accuracy: 0.81, transparency_score: 0.57, human_oversight: false },
    },
  },
]

const NONSTANDARD_DEMOS = [
  {
    label: '📄 Custom Internal AI Policy',
    text: 'All AI systems that process personal data must undergo a DPIA before deployment. High-risk AI systems require documented bias testing, transparency obligations, and mandatory human oversight. Prohibited use cases include emotion recognition in workplace settings and social scoring. Model documentation must include training data sources, accuracy metrics, and fairness validation results.',
  },
  {
    label: '📋 Vendor Contract AI Clause',
    text: 'The vendor warrants that all AI models are free from discriminatory bias affecting protected characteristics. Accuracy must meet or exceed 85% on validation dataset. Facial recognition features are explicitly prohibited. Customer retains right to audit model behaviour and contest automated decisions. Model card and technical specifications must be provided prior to deployment.',
  },
]

export default function AuditFlow({ onNavigate }) {
  const [tab, setTab] = useState('pipeline')
  const [form, setForm] = useState({ model_name:'', domain:'finance', policy:'EU AI Act', mode:'text', output_text:'', output_data:{ bias_score:0.18, accuracy:0.83, transparency_score:0.61, human_oversight:true } })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [stageAnim, setStageAnim] = useState(-1)
  const [resolved, setResolved] = useState({})
  const [botState, setBotState] = useState({})

  const [nsForm, setNsForm] = useState({ title:'', jurisdiction:'EU', content:'' })
  const [nsResult, setNsResult] = useState(null)
  const [nsLoading, setNsLoading] = useState(false)

  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)

  useEffect(() => {
    get('/api/v1/agent/runs').then(d => setRuns(d.runs || [])).catch(() => {})
  }, [])

  const triggerBotFix = async (i, item) => {
    setBotState(b => ({...b,[i]:'running'}))
    try {
      await post('/api/v1/mvp5/bots/execute', { bot_type: item.check?.toLowerCase().includes('bias')?'retrain_bot':'remediation_bot', finding_id:`FIND-${result?.run_id}-${i}` })
      setBotState(b => ({...b,[i]:'done'}))
    } catch(e) { setBotState(b => ({...b,[i]:'error'})) }
  }

  const runPipeline = async () => {
    if (!form.model_name.trim()) return
    setLoading(true); setResult(null); setStageAnim(-1); setResolved({}); setBotState({})
    try {
      const payload = {
        model_name: form.model_name, domain: form.domain, policy: form.policy,
        ...(form.mode === 'text' ? { output_text: form.output_text } : { output_data: form.output_data }),
      }
      // Animate stages while waiting
      let i = 0
      const timer = setInterval(() => { setStageAnim(i++); if (i > 7) clearInterval(timer) }, 320)
      const res = await post('/api/v1/agent/run', payload)
      clearInterval(timer); setStageAnim(7)
      setResult(res)
      setRuns(prev => [res, ...prev])
    } catch(e) {}
    finally { setLoading(false) }
  }

  const applyDemo = (d) => {
    setForm(f => ({ ...f, ...d.payload }))
    setResult(null); setStageAnim(-1)
  }

  const runNonStandard = async () => {
    if (!nsForm.content.trim()) return
    setNsLoading(true); setNsResult(null)
    try { setNsResult(await post('/api/v1/agent/ingest-nonstandard', nsForm)) }
    catch(e) {} finally { setNsLoading(false) }
  }

  const v = result?.summary?.verdict
  const vCfg = VERDICT[v] || VERDICT.REVIEW

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Flow</h1>
          <p className="page-subtitle">
            End-to-end pipeline: ingest model output → agent extracts metrics → evaluate against policy benchmark → checklist → report
          </p>
        </div>
        <span className="badge badge-purple" style={{ padding:'6px 14px',fontSize:12 }}>⚡ Agent-Powered</span>
      </div>

      {/* Flow diagram */}
      <div style={{ marginBottom:24,padding:'16px 20px',background:'var(--bg-card)',borderRadius:10,border:'1px solid var(--border)' }}>
        <div style={{ display:'flex',gap:0,alignItems:'center',overflow:'auto' }}>
          {[
            { icon:'📤', label:'Upload Output',   desc:'Text or JSON' },
            { icon:'🤖', label:'Agent Extracts',  desc:'Bias, accuracy, transparency' },
            { icon:'📋', label:'Policy Check',    desc:'EU AI Act / NIST / ISO / FDA' },
            { icon:'✅', label:'Checklist',       desc:'Fail / Warn / Pass' },
            { icon:'📄', label:'Report',          desc:'Article refs + remediation' },
          ].map((s,i) => (
            <div key={i} style={{ display:'flex',alignItems:'center',flex:1 }}>
              <div style={{ flex:1,textAlign:'center',padding:'0 4px' }}>
                <div style={{ fontSize:22,marginBottom:4 }}>{s.icon}</div>
                <div style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{s.label}</div>
                <div style={{ fontSize:10,color:'var(--text-muted)',marginTop:2 }}>{s.desc}</div>
              </div>
              {i < 4 && <div style={{ fontSize:18,color:'var(--accent-cyan)',flexShrink:0,margin:'0 -4px' }}>→</div>}
            </div>
          ))}
        </div>
      </div>

      <div className="tabs">
        {[['pipeline','⚡ Run Pipeline'],['nonstandard','📄 Custom Doc Ingest'],['history','📋 Run History']].map(([t,l]) => (
          <div key={t} className={`tab ${tab===t?'active':''}`} onClick={() => setTab(t)}>{l}</div>
        ))}
      </div>

      {/* ── PIPELINE TAB ── */}
      {tab === 'pipeline' && (
        <div className="grid-2">

          {/* Left: config + demos */}
          <div>
            <div className="card" style={{ marginBottom:16 }}>
              <div className="card-header"><span className="card-title">Demo Scenarios</span></div>
              {DEMO_SCENARIOS.map((d,i) => (
                <div key={i} style={{ padding:'10px 0',borderBottom:'1px solid var(--border)',cursor:'pointer' }} onClick={() => applyDemo(d)}>
                  <div style={{ fontSize:13,fontWeight:600,color:'var(--text-primary)',marginBottom:2 }}>{d.label}</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)' }}>{d.desc}</div>
                </div>
              ))}
            </div>

            <div className="card">
              <div className="card-header"><span className="card-title">Configure Pipeline</span></div>
              <div className="grid-2" style={{ marginBottom:0 }}>
                <div className="form-group">
                  <label className="form-label">Model Name</label>
                  <input className="form-input" placeholder="CreditScorer-v2" value={form.model_name} onChange={e=>setForm(f=>({...f,model_name:e.target.value}))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Domain</label>
                  <select className="form-select" value={form.domain} onChange={e=>setForm(f=>({...f,domain:e.target.value}))}>
                    {['finance','healthcare','hr','general'].map(d=><option key={d}>{d}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Policy Benchmark</label>
                <select className="form-select" value={form.policy} onChange={e=>setForm(f=>({...f,policy:e.target.value}))}>
                  {['EU AI Act','NIST AI RMF','ISO 42001','FDA SaMD'].map(p=><option key={p}>{p}</option>)}
                </select>
              </div>
              <div style={{ display:'flex',gap:8,marginBottom:12 }}>
                {[['text','📝 Text Input'],['structured','⚙️ Metrics']].map(([m,l])=>(
                  <button key={m} className={`btn ${form.mode===m?'btn-primary':'btn-secondary'}`} style={{ flex:1,justifyContent:'center',fontSize:12 }} onClick={()=>setForm(f=>({...f,mode:m}))}>
                    {l}
                  </button>
                ))}
              </div>
              {form.mode === 'text' ? (
                <div className="form-group">
                  <label className="form-label">Model Output / Decision Log</label>
                  <textarea className="form-textarea" rows={5}
                    placeholder="Paste your AI model's output, decision log, prediction text, or compliance description. The agent will extract bias score, accuracy, transparency, oversight and evaluate against the selected policy."
                    value={form.output_text} onChange={e=>setForm(f=>({...f,output_text:e.target.value}))} />
                </div>
              ) : (
                <div className="form-group">
                  <label className="form-label">Metric Values</label>
                  <div style={{ background:'var(--bg-primary)',borderRadius:8,border:'1px solid var(--border)',padding:12,display:'flex',flexDirection:'column',gap:10 }}>
                    {[['bias_score','Bias Score (lower=better)',0.001],['accuracy','Accuracy (higher=better)',0.01],['transparency_score','Transparency (higher=better)',0.01]].map(([k,label,step])=>(
                      <div key={k} style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                        <label style={{ fontSize:12,color:'var(--text-secondary)',flex:1 }}>{label}</label>
                        <input type="number" step={step} min={0} max={1}
                          style={{ width:75,padding:'4px 8px',background:'var(--bg-secondary)',border:'1px solid var(--border)',borderRadius:4,color:'var(--text-primary)',fontFamily:'var(--mono)',fontSize:12 }}
                          value={form.output_data[k]}
                          onChange={e=>setForm(f=>({...f,output_data:{...f.output_data,[k]:parseFloat(e.target.value)}}))} />
                      </div>
                    ))}
                    <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                      <label style={{ fontSize:12,color:'var(--text-secondary)',flex:1 }}>Human Oversight</label>
                      <select style={{ width:75,padding:'4px 8px',background:'var(--bg-secondary)',border:'1px solid var(--border)',borderRadius:4,color:'var(--text-primary)',fontSize:12 }}
                        value={form.output_data.human_oversight?'yes':'no'}
                        onChange={e=>setForm(f=>({...f,output_data:{...f.output_data,human_oversight:e.target.value==='yes'}}))}>
                        <option value="yes">Yes</option><option value="no">No</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
              <button className="btn btn-primary" onClick={runPipeline} disabled={loading||!form.model_name.trim()} style={{ width:'100%',justifyContent:'center' }}>
                {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Running pipeline...</> : '⚡ Run Full Audit Pipeline'}
              </button>
            </div>
          </div>

          {/* Right: pipeline stages + results */}
          <div>
            {/* Pipeline stage log */}
            <div className="card" style={{ marginBottom:16 }}>
              <div className="card-header">
                <span className="card-title">Pipeline Execution Log</span>
                {result && <span className="badge badge-green">Complete · {result.total_pipeline_ms?.toFixed(0)}ms</span>}
              </div>
              {(result?.pipeline_stages || Array.from({length:8},(_,i)=>({ stage:['Input Received','Agent Metric Extraction','Policy Benchmark Load','Compliance Evaluation','Checklist Generation','Remediation Mapping','Report Assembly','Audit Trail Logged'][i], status:'pending', duration_ms:null, detail:'' }))).map((s,i) => {
                const done = result ? true : i <= stageAnim
                const active = !result && i === stageAnim
                return (
                  <div key={i} style={{ display:'flex',gap:10,padding:'8px 0',borderBottom:'1px solid rgba(30,45,69,0.5)',alignItems:'flex-start' }}>
                    <div style={{ width:22,height:22,borderRadius:'50%',background:done?'rgba(0,255,136,0.15)':active?'rgba(0,212,255,0.15)':'var(--bg-primary)',border:`1px solid ${done?'var(--accent-green)':active?'var(--accent-cyan)':'var(--border)'}`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,flexShrink:0,marginTop:1 }}>
                      {done ? <span style={{ color:'var(--accent-green)' }}>✓</span> : active ? <div className="loading-spinner" style={{ width:10,height:10 }} /> : <span style={{ color:'var(--text-muted)',fontSize:9 }}>{i+1}</span>}
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:12,fontWeight:600,color:done?'var(--text-primary)':active?'var(--accent-cyan)':'var(--text-muted)' }}>{s.stage}</div>
                      {(done || active) && s.detail && <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:1 }}>{s.detail}</div>}
                    </div>
                    {s.duration_ms && <span style={{ fontSize:10,fontFamily:'var(--mono)',color:'var(--accent-green)',flexShrink:0 }}>{s.duration_ms}ms</span>}
                  </div>
                )
              })}
            </div>

            {/* Results checklist */}
            {result && (
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Compliance Checklist</span>
                  <span style={{ fontFamily:'var(--mono)',fontSize:11,color:'var(--text-muted)' }}>{result.run_id}</span>
                </div>

                {/* Verdict banner */}
                <div style={{ padding:'14px 16px',borderRadius:10,marginBottom:16,background:result.summary.verdict==='FAIL'?'rgba(255,61,106,0.08)':result.summary.verdict==='REVIEW'?'rgba(255,184,0,0.08)':'rgba(0,255,136,0.06)',border:`1px solid ${result.summary.verdict==='FAIL'?'rgba(255,61,106,0.3)':result.summary.verdict==='REVIEW'?'rgba(255,184,0,0.3)':'rgba(0,255,136,0.2)'}` }}>
                  <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                    <div>
                      <div style={{ fontSize:17,fontWeight:800,color:vCfg.color }}>{vCfg.icon} {vCfg.label}</div>
                      <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:3 }}>
                        {result.model_name} · {result.policy} · {result.domain}
                        {result.agent_extracted && <span style={{ marginLeft:8,color:'var(--accent-purple)' }}>⚡ agent-extracted</span>}
                      </div>
                    </div>
                    <div style={{ display:'flex',gap:12,textAlign:'center' }}>
                      {[['CRITICAL',result.summary.critical,'var(--accent-red)'],['WARN',result.summary.warn,'var(--accent-amber)'],['PASS',result.summary.pass,'var(--accent-green)']].map(([l,n,c])=>(
                        <div key={l}><div style={{ fontSize:22,fontWeight:800,fontFamily:'var(--mono)',color:c }}>{n}</div><div style={{ fontSize:9,color:'var(--text-muted)',textTransform:'uppercase' }}>{l}</div></div>
                      ))}
                    </div>
                  </div>
                  <div style={{ marginTop:10,display:'flex',gap:12,fontSize:12,color:'var(--text-muted)' }}>
                    <span>Pass rate: <strong style={{ color:'var(--accent-green)' }}>{result.summary.pass_rate}%</strong></span>
                    <span>Compliance: <strong style={{ color:'var(--accent-cyan)' }}>{(result.summary.compliance_score*100).toFixed(0)}%</strong></span>
                    <span>Fine avoided: <strong style={{ color:'var(--accent-amber)' }}>${result.summary.fine_avoided_usd?.toLocaleString()}</strong></span>
                  </div>
                </div>

                {/* Per-check items */}
                <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
                  {result.checklist?.map((item,i) => {
                    const cfg = SEV[item.severity] || SEV.pass
                    return (
                      <div key={i} style={{ padding:'12px 14px',borderRadius:8,background:cfg.bg,border:`1px solid ${cfg.border}` }}>
                        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:4 }}>
                          <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                            <span>{cfg.icon}</span>
                            <div>
                              <span style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)' }}>{item.check}</span>
                              <span style={{ marginLeft:8,fontSize:10,fontFamily:'var(--mono)',color:cfg.color,fontWeight:700 }}>{item.article_ref}</span>
                            </div>
                          </div>
                          <span style={{ fontSize:10,fontWeight:800,padding:'2px 7px',borderRadius:20,background:cfg.border,color:cfg.color,flexShrink:0 }}>{cfg.label}</span>
                        </div>
                        <div style={{ fontSize:12,color:'var(--text-secondary)',marginBottom:item.severity!=='pass'?5:0 }}>{item.finding}</div>
                        {item.severity !== 'pass' && (
                          <div style={{ fontSize:11,color:cfg.color,display:'flex',gap:5,marginBottom:resolved[i]?0:8 }}>
                            <span style={{ flexShrink:0 }}>→</span><span>{item.remediation}</span>
                          </div>
                        )}
                        {item.severity !== 'pass' && !resolved[i] && (
                          <div style={{ display:'flex',gap:8,marginTop:4 }}>
                            <button className="btn btn-secondary" style={{ fontSize:11,padding:'3px 10px',color:'var(--accent-green)',borderColor:'rgba(0,255,136,0.3)' }}
                              onClick={() => setResolved(r=>({...r,[i]:true}))}>✓ Resolved</button>
                            <button className="btn btn-secondary" style={{ fontSize:11,padding:'3px 10px',color:'var(--accent-purple)',borderColor:'rgba(139,92,246,0.3)' }}
                              disabled={botState[i]==='running'||botState[i]==='done'}
                              onClick={() => triggerBotFix(i,item)}>
                              {botState[i]==='running'?<><div className="loading-spinner" style={{width:10,height:10}} />Running...</>:botState[i]==='done'?'✓ Bot Applied':'🤖 Bot Fix'}
                            </button>
                          </div>
                        )}
                        {resolved[i] && <div style={{ fontSize:11,color:'var(--accent-green)',marginTop:4 }}>✓ Marked as resolved</div>}
                        {typeof item.measured === 'number' && (
                          <div style={{ marginTop:6,display:'flex',alignItems:'center',gap:8 }}>
                            <div className="progress-bar" style={{ flex:1 }}>
                              <div style={{ height:'100%',borderRadius:3,background:cfg.color,width:`${Math.min(100,(item.direction==='lower_is_better'?Math.max(0,1-item.measured):item.measured)*100)}%`,transition:'width 0.6s ease' }} />
                            </div>
                            <span style={{ fontSize:10,fontFamily:'var(--mono)',color:cfg.color,width:40,flexShrink:0 }}>
                              {typeof item.measured === 'number' ? (item.measured < 2 ? (item.measured*100).toFixed(1)+'%' : item.measured) : String(item.measured)}
                            </span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                {/* Signals found */}
                {result.signals_found?.length > 0 && (
                  <div style={{ marginTop:14,padding:'10px 14px',background:'var(--bg-primary)',borderRadius:8 }}>
                    <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:6 }}>Agent Signals Detected in Text</div>
                    <div style={{ display:'flex',gap:6,flexWrap:'wrap' }}>
                      {result.signals_found.map(s => <span key={s} className="badge badge-purple" style={{ fontSize:10 }}>{s}</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!result && !loading && (
              <div className="card">
                <div className="empty-state" style={{ padding:'48px 20px' }}>
                  <div className="empty-state-icon">⚡</div>
                  <div className="empty-state-text">Select a demo or fill in the form, then click Run Full Audit Pipeline</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:8,maxWidth:280,textAlign:'center',lineHeight:1.6 }}>
                    The pipeline ingests your model output, extracts metrics via agent analysis, evaluates against your chosen policy benchmark, and generates a fail/warn/pass checklist with remediation steps
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── NON-STANDARD DOC TAB ── */}
      {tab === 'nonstandard' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Ingest Custom / Non-Standard Document</span></div>
            <div style={{ fontSize:12,color:'var(--text-muted)',marginBottom:16,lineHeight:1.6 }}>
              Upload internal AI policies, vendor contracts, or custom governance documents. The agent will extract compliance rules, map them to regulatory articles, and generate a checklist.
            </div>

            <div style={{ marginBottom:14 }}>
              <div style={{ fontSize:11,color:'var(--text-muted)',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Demo Documents</div>
              {NONSTANDARD_DEMOS.map((d,i) => (
                <button key={i} className="btn btn-secondary" style={{ width:'100%',justifyContent:'flex-start',fontSize:12,marginBottom:6 }}
                  onClick={() => setNsForm(f => ({ ...f, content:d.text, title:d.label.replace(/[📄📋]/g,'').trim() }))}>
                  {d.label}
                </button>
              ))}
            </div>

            <div className="form-group">
              <label className="form-label">Document Title</label>
              <input className="form-input" placeholder="Internal AI Governance Policy v2" value={nsForm.title} onChange={e=>setNsForm(f=>({...f,title:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Jurisdiction</label>
              <select className="form-select" value={nsForm.jurisdiction} onChange={e=>setNsForm(f=>({...f,jurisdiction:e.target.value}))}>
                {['EU','US','UK','GLOBAL','SG','CN'].map(j=><option key={j}>{j}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Document Content</label>
              <textarea className="form-textarea" style={{ minHeight:160 }}
                placeholder="Paste your custom policy document, vendor AI contract clause, or internal governance text. The agent will extract compliance obligations and map them to regulatory frameworks."
                value={nsForm.content} onChange={e=>setNsForm(f=>({...f,content:e.target.value}))} />
            </div>
            <button className="btn btn-primary" onClick={runNonStandard} disabled={nsLoading||!nsForm.content.trim()} style={{ width:'100%',justifyContent:'center' }}>
              {nsLoading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Agent processing...</> : '🤖 Agent Ingest & Extract Rules'}
            </button>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Extracted Rules & Mappings</span></div>
            {nsResult ? (
              <div>
                <div style={{ marginBottom:16,padding:'12px 14px',background:'var(--bg-primary)',borderRadius:8 }}>
                  <div style={{ fontSize:14,fontWeight:700,marginBottom:4 }}>{nsResult.title}</div>
                  <div style={{ display:'flex',gap:8,flexWrap:'wrap' }}>
                    <span className="badge badge-cyan">{nsResult.jurisdiction}</span>
                    <span className="badge badge-gray">{nsResult.word_count} words</span>
                    <span className="badge badge-purple">⚡ Agent processed</span>
                    <span style={{ fontFamily:'var(--mono)',fontSize:11,color:'var(--text-muted)',padding:'2px 6px',border:'1px solid var(--border)',borderRadius:4 }}>{nsResult.doc_id}</span>
                  </div>
                </div>

                <div style={{ marginBottom:16 }}>
                  <div style={{ display:'flex',justifyContent:'space-between',marginBottom:8 }}>
                    <span style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px' }}>Risk Score</span>
                    <span style={{ fontFamily:'var(--mono)',fontWeight:700,color:nsResult.overall_risk_score>0.6?'var(--accent-red)':nsResult.overall_risk_score>0.35?'var(--accent-amber)':'var(--accent-green)' }}>{(nsResult.overall_risk_score*100).toFixed(0)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div style={{ height:'100%',borderRadius:3,width:`${nsResult.overall_risk_score*100}%`,background:nsResult.overall_risk_score>0.6?'var(--accent-red)':nsResult.overall_risk_score>0.35?'var(--accent-amber)':'var(--accent-green)',transition:'width 0.6s' }} />
                  </div>
                </div>

                <div style={{ marginBottom:14 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Extracted Rules ({nsResult.extracted_rules?.length})</div>
                  {nsResult.extracted_rules?.map((r,i) => (
                    <div key={i} style={{ padding:'10px 12px',borderRadius:8,marginBottom:8,background:r.severity==='critical'?'rgba(255,61,106,0.08)':r.severity==='high'?'rgba(255,184,0,0.06)':'rgba(0,212,255,0.05)',border:`1px solid ${r.severity==='critical'?'rgba(255,61,106,0.25)':r.severity==='high'?'rgba(255,184,0,0.25)':'rgba(0,212,255,0.2)'}` }}>
                      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4 }}>
                        <span style={{ fontSize:12,fontWeight:700,color:'var(--text-primary)',textTransform:'capitalize' }}>{r.signal.replace(/_/g,' ')}</span>
                        <span style={{ fontSize:10,fontFamily:'var(--mono)',color:'var(--accent-cyan)',fontWeight:700 }}>{r.article_ref}</span>
                      </div>
                      <div style={{ fontSize:12,color:'var(--text-secondary)',marginBottom:4 }}>{r.obligation}</div>
                      <div style={{ display:'flex',gap:4,flexWrap:'wrap' }}>
                        {r.matched_phrases?.map(p => <span key={p} className="badge badge-gray" style={{ fontSize:10 }}>"{p}"</span>)}
                      </div>
                    </div>
                  ))}
                </div>

                <div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Recommended Benchmarks to Run Against</div>
                  <div style={{ display:'flex',gap:8,flexWrap:'wrap' }}>
                    {nsResult.recommended_benchmarks?.map(b => <span key={b} className="badge badge-cyan">{b}</span>)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">📄</div>
                <div className="empty-state-text">Select a demo document or paste your custom policy content, then click Agent Ingest & Extract Rules</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── HISTORY TAB ── */}
      {tab === 'history' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Pipeline Run History</span><span className="badge badge-cyan">{runs.length} runs</span></div>
            {runs.length === 0 ? (
              <div className="empty-state"><div className="empty-state-icon">📋</div><div className="empty-state-text">No runs yet — use the pipeline tab</div></div>
            ) : (
              runs.map((r,i) => {
                const cfg = VERDICT[r.summary?.verdict] || VERDICT.REVIEW
                return (
                  <div key={i} style={{ padding:'11px 0',borderBottom:'1px solid var(--border)',cursor:'pointer' }} onClick={() => setSelectedRun(r)}>
                    <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                      <div>
                        <div style={{ fontSize:13,fontWeight:600,color:selectedRun?.run_id===r.run_id?'var(--accent-cyan)':'var(--text-primary)' }}>{r.model_name}</div>
                        <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{r.policy} · {r.domain} · {new Date(r.run_at).toLocaleTimeString()}</div>
                      </div>
                      <div style={{ display:'flex',gap:6,alignItems:'center' }}>
                        <span style={{ fontSize:11,fontFamily:'var(--mono)',color:'var(--accent-amber)' }}>{r.summary?.critical}crit/{r.summary?.warn}warn</span>
                        <span style={{ fontSize:11,fontWeight:800,padding:'3px 8px',borderRadius:20,color:cfg.color,background:r.summary?.verdict==='FAIL'?'rgba(255,61,106,0.12)':r.summary?.verdict==='REVIEW'?'rgba(255,184,0,0.12)':'rgba(0,255,136,0.1)' }}>{r.summary?.verdict}</span>
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
          <div className="card">
            {selectedRun ? (
              <div>
                <div className="card-header">
                  <div><div style={{ fontSize:14,fontWeight:700 }}>{selectedRun.model_name}</div><div style={{ fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>{selectedRun.run_id}</div></div>
                </div>
                <div style={{ display:'flex',gap:12,marginBottom:16 }}>
                  {[['Critical',selectedRun.summary?.critical,'var(--accent-red)'],['Warn',selectedRun.summary?.warn,'var(--accent-amber)'],['Pass',selectedRun.summary?.pass,'var(--accent-green)']].map(([l,n,c])=>(
                    <div key={l} style={{ flex:1,padding:'10px',background:'var(--bg-primary)',borderRadius:8,textAlign:'center' }}>
                      <div style={{ fontSize:20,fontWeight:800,fontFamily:'var(--mono)',color:c }}>{n}</div>
                      <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase' }}>{l}</div>
                    </div>
                  ))}
                </div>
                {selectedRun.checklist?.map((c,i) => {
                  const cfg = SEV[c.severity]||SEV.pass
                  return (
                    <div key={i} style={{ padding:'8px 0',borderBottom:'1px solid var(--border)',display:'flex',gap:8,alignItems:'flex-start' }}>
                      <span style={{ fontSize:14,flexShrink:0 }}>{cfg.icon}</span>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{c.check}</div>
                        <div style={{ fontSize:10,fontFamily:'var(--mono)',color:cfg.color }}>{c.article_ref}</div>
                        <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:1 }}>{c.finding}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="empty-state"><div className="empty-state-icon">📊</div><div className="empty-state-text">Select a run to view checklist</div></div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
