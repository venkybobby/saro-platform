/**
 * Gateway & Orchestrator Page (FR-GW-01..05, Elon specs)
 * Unified entry: submit model output / repo URL → async pipeline → persona-tailored results
 * Also: GitHub Scanner, ROI Simulator, Industry Test Datasets
 */
import { useState, useEffect, useRef } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (p, b) => fetch(`${BASE}${p}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b) }).then(r => r.json())
const get  = (p) => fetch(`${BASE}${p}`).then(r => r.json())

const VERDICT_CFG = {
  FAIL:   { color:'var(--accent-red)',   bg:'rgba(255,61,106,0.08)',  border:'rgba(255,61,106,0.3)',  icon:'🚫', label:'FAIL' },
  REVIEW: { color:'var(--accent-amber)', bg:'rgba(255,184,0,0.08)',   border:'rgba(255,184,0,0.3)',   icon:'⚠️', label:'REVIEW' },
  PASS:   { color:'var(--accent-green)', bg:'rgba(0,255,136,0.06)',   border:'rgba(0,255,136,0.2)',   icon:'✅', label:'PASS' },
}

const SEV_CFG = {
  critical: { color:'var(--accent-red)',   icon:'🚫' },
  warn:     { color:'var(--accent-amber)', icon:'⚠️' },
  pass:     { color:'var(--accent-green)', icon:'✓' },
}

export default function Gateway({ onNavigate }) {
  const [tab, setTab] = useState('submit')

  // Submit tab state
  const [form, setForm]       = useState({ model_name:'', domain:'finance', policy:'EU AI Act', persona:'enabler', input_type:'text', output_text:'', repo_url:'' })
  const [jobId, setJobId]     = useState(null)
  const [jobResult, setJobResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [polling, setPolling] = useState(false)
  const pollRef               = useRef(null)
  const [jobs, setJobs]       = useState([])

  // GitHub scanner state
  const [repoUrl, setRepoUrl] = useState('')
  const [ghResult, setGhResult] = useState(null)
  const [ghLoading, setGhLoading] = useState(false)

  // ROI state
  const [roi, setRoi]         = useState({ annual_ai_spend_usd:500000, num_ai_models:10, industry:'finance', jurisdictions:['EU'] })
  const [roiResult, setRoiResult] = useState(null)
  const [roiLoading, setRoiLoading] = useState(false)

  // Industry datasets state
  const [datasets, setDatasets] = useState([])
  const [dsFilter, setDsFilter] = useState('all')

  useEffect(() => {
    get('/api/v1/gateway/jobs').then(d => setJobs(d.jobs || [])).catch(() => {})
    get('/api/v1/gateway/industry-data').then(d => setDatasets(d.datasets || [])).catch(() => {})
  }, [])

  // Poll job until complete
  const startPolling = (id) => {
    setPolling(true)
    pollRef.current = setInterval(async () => {
      try {
        const data = await get(`/api/v1/gateway/status/${id}`)
        if (data.status === 'complete' || data.status === 'error') {
          clearInterval(pollRef.current)
          setPolling(false)
          setJobResult(data)
          setJobs(j => [data, ...j.filter(x => x.job_id !== id)])
        }
      } catch(e) { clearInterval(pollRef.current); setPolling(false) }
    }, 1000)
  }

  const submitJob = async () => {
    setSubmitting(true); setJobResult(null); setJobId(null)
    try {
      const payload = {
        model_name: form.model_name || 'unnamed-model',
        domain: form.domain, policy: form.policy, persona: form.persona,
        ...(form.input_type === 'text'  && { output_text: form.output_text }),
        ...(form.input_type === 'repo'  && { repo_url: form.repo_url }),
        ...(form.input_type === 'structured' && { output_data: { bias_score: 0.18, accuracy: 0.83, transparency_score: 0.61, human_oversight: true } }),
      }
      const data = await post('/api/v1/gateway/submit', payload)
      setJobId(data.job_id)
      startPolling(data.job_id)
    } catch(e) {} finally { setSubmitting(false) }
  }

  const scanGithub = async () => {
    if (!repoUrl.trim()) return
    setGhLoading(true); setGhResult(null)
    try { setGhResult(await post('/api/v1/gateway/scan-github', { repo_url: repoUrl })) }
    catch(e) {} finally { setGhLoading(false) }
  }

  const calcRoi = async () => {
    setRoiLoading(true); setRoiResult(null)
    try { setRoiResult(await post('/api/v1/gateway/roi-estimate', roi)) }
    catch(e) {} finally { setRoiLoading(false) }
  }

  const verdictCfg = VERDICT_CFG[jobResult?.verdict] || VERDICT_CFG.REVIEW

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Gateway & Orchestrator</h1>
          <p className="page-subtitle">Unified submission: model output / repo URL → pipeline → persona-tailored results · GitHub Scanner · ROI Simulator</p>
        </div>
        <span className="badge badge-purple" style={{ padding:'6px 14px',fontSize:12 }}>⚡ Orchestrated</span>
      </div>

      {/* Flow banner */}
      <div style={{ padding:'12px 20px',background:'var(--bg-card)',borderRadius:10,border:'1px solid var(--border)',marginBottom:20,display:'flex',gap:0,alignItems:'center',overflow:'auto' }}>
        {[['📤','Submit Input','Text / JSON / Repo URL'],['⚙️','Route Pipeline','Domain + Policy detection'],['🤖','Agent Extracts','Bias, accuracy, transparency'],['✅','Checklist','Fail/Warn/Pass per article'],['📊','Persona View','Tailored to your role']].map((s,i)=>(
          <div key={i} style={{ display:'flex',alignItems:'center',flex:1 }}>
            <div style={{ flex:1,textAlign:'center',padding:'0 4px' }}>
              <div style={{ fontSize:20,marginBottom:2 }}>{s[0]}</div>
              <div style={{ fontSize:11,fontWeight:700,color:'var(--text-primary)' }}>{s[1]}</div>
              <div style={{ fontSize:10,color:'var(--text-muted)' }}>{s[2]}</div>
            </div>
            {i < 4 && <div style={{ fontSize:18,color:'var(--accent-cyan)',flexShrink:0 }}>→</div>}
          </div>
        ))}
      </div>

      <div className="tabs">
        {[['submit','📤 Submit Job'],['github','🐙 GitHub Scanner'],['roi','💰 ROI Simulator'],['datasets','📊 Test Datasets'],['history','📋 Job History']].map(([t,l])=>(
          <div key={t} className={`tab ${tab===t?'active':''}`} onClick={()=>setTab(t)}>{l}</div>
        ))}
      </div>

      {/* ── SUBMIT TAB ── */}
      {tab === 'submit' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Submit to Pipeline</span></div>
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
            <div className="grid-2" style={{ marginBottom:0 }}>
              <div className="form-group">
                <label className="form-label">Policy Benchmark</label>
                <select className="form-select" value={form.policy} onChange={e=>setForm(f=>({...f,policy:e.target.value}))}>
                  {['EU AI Act','NIST AI RMF','ISO 42001','FDA SaMD'].map(p=><option key={p}>{p}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Your Persona</label>
                <select className="form-select" value={form.persona} onChange={e=>setForm(f=>({...f,persona:e.target.value}))}>
                  {[['forecaster','📈 Forecaster'],['autopsier','🔍 Autopsier'],['enabler','⚙️ Enabler'],['evangelist','🎯 Evangelist']].map(([v,l])=><option key={v} value={v}>{l}</option>)}
                </select>
              </div>
            </div>
            <div style={{ display:'flex',gap:6,marginBottom:12 }}>
              {[['text','📝 Text'],['repo','🐙 Repo URL'],['structured','⚙️ Metrics']].map(([t,l])=>(
                <button key={t} className={`btn ${form.input_type===t?'btn-primary':'btn-secondary'}`} style={{ flex:1,justifyContent:'center',fontSize:12 }} onClick={()=>setForm(f=>({...f,input_type:t}))}>{l}</button>
              ))}
            </div>
            {form.input_type === 'text' && (
              <div className="form-group">
                <label className="form-label">Model Output / Decision Log</label>
                <textarea className="form-textarea" rows={5} placeholder="Paste model output, decision log, or any text describing AI behaviour..."
                  value={form.output_text} onChange={e=>setForm(f=>({...f,output_text:e.target.value}))} />
              </div>
            )}
            {form.input_type === 'repo' && (
              <div className="form-group">
                <label className="form-label">GitHub Repository URL</label>
                <input className="form-input" placeholder="https://github.com/org/ai-model-repo" value={form.repo_url} onChange={e=>setForm(f=>({...f,repo_url:e.target.value}))} />
                <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:4 }}>Repo metadata and structure will be analyzed for governance signals</div>
              </div>
            )}
            {form.input_type === 'structured' && (
              <div style={{ padding:14,background:'var(--bg-primary)',borderRadius:8,border:'1px solid var(--border)',marginBottom:12,fontSize:12,color:'var(--text-muted)' }}>
                Default structured metrics will be used: bias 0.18, accuracy 0.83, transparency 0.61, oversight: on
              </div>
            )}
            <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center' }} onClick={submitJob} disabled={submitting||polling}>
              {submitting ? <><div className="loading-spinner" style={{width:14,height:14}} /> Submitting...</>
               : polling   ? <><div className="loading-spinner" style={{width:14,height:14}} /> Processing job {jobId}...</>
               : '⚡ Submit to Gateway Pipeline'}
            </button>
            {jobId && !jobResult && (
              <div style={{ marginTop:10,padding:'8px 12px',background:'rgba(0,212,255,0.05)',borderRadius:6,fontSize:11,color:'var(--accent-cyan)',fontFamily:'var(--mono)' }}>
                Job queued: {jobId} — polling for results...
              </div>
            )}
          </div>

          <div>
            {jobResult ? (
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Pipeline Results</span>
                  <span style={{ fontFamily:'var(--mono)',fontSize:10,color:'var(--text-muted)' }}>{jobResult.job_id}</span>
                </div>
                <div style={{ padding:'14px 16px',borderRadius:10,marginBottom:14,background:verdictCfg.bg,border:`1px solid ${verdictCfg.border}` }}>
                  <div style={{ fontSize:18,fontWeight:800,color:verdictCfg.color,marginBottom:4 }}>{verdictCfg.icon} {verdictCfg.label} — {jobResult.policy}</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:10 }}>
                    {jobResult.model_name} · {jobResult.domain} · {jobResult.processing_ms}ms
                  </div>
                  <div style={{ display:'flex',gap:14,fontSize:12 }}>
                    <span>Compliance: <strong style={{ color:'var(--accent-cyan)' }}>{(jobResult.compliance_score*100).toFixed(0)}%</strong></span>
                    <span>Fine avoided: <strong style={{ color:'var(--accent-amber)' }}>${jobResult.fine_avoided_usd?.toLocaleString()}</strong></span>
                  </div>
                </div>

                {/* Persona-tailored view */}
                {jobResult.persona_view && (
                  <div style={{ padding:'12px 14px',borderRadius:8,background:'rgba(139,92,246,0.06)',border:'1px solid rgba(139,92,246,0.2)',marginBottom:14 }}>
                    <div style={{ fontSize:11,color:'var(--accent-purple)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:6 }}>Your Persona View</div>
                    <div style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)',marginBottom:4 }}>{jobResult.persona_view.headline}</div>
                    <div style={{ fontSize:12,color:'var(--text-muted)',marginBottom:4 }}>{jobResult.persona_view.focus}</div>
                    <div style={{ fontSize:12,color:'var(--accent-cyan)',fontWeight:600,marginBottom:6 }}>{jobResult.persona_view.key_metric}</div>
                    <div style={{ fontSize:11,color:'var(--accent-purple)' }}>→ {jobResult.persona_view.action}</div>
                  </div>
                )}

                {/* Checklist */}
                <div style={{ display:'flex',flexDirection:'column',gap:8 }}>
                  {jobResult.checklist?.items?.map((item,i) => {
                    const cfg = SEV_CFG[item.severity] || SEV_CFG.pass
                    return (
                      <div key={i} style={{ display:'flex',justifyContent:'space-between',padding:'10px 12px',borderRadius:8,background:'var(--bg-primary)',border:'1px solid var(--border)',alignItems:'center' }}>
                        <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                          <span>{cfg.icon}</span>
                          <div>
                            <div style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{item.check}</div>
                            <div style={{ fontSize:10,fontFamily:'var(--mono)',color:cfg.color }}>{item.article}</div>
                          </div>
                        </div>
                        <div style={{ textAlign:'right',fontSize:11 }}>
                          <div style={{ fontFamily:'var(--mono)',color:cfg.color,fontWeight:700 }}>{typeof item.measured === 'number' ? (item.measured*100).toFixed(1)+'%' : String(item.measured)}</div>
                          <div style={{ color:'var(--text-muted)' }}>limit {typeof item.threshold === 'number' ? (item.threshold*100).toFixed(0)+'%' : String(item.threshold)}</div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div style={{ marginTop:12,display:'flex',gap:8 }}>
                  <button className="btn btn-secondary" style={{ flex:1,justifyContent:'center',fontSize:12 }} onClick={() => onNavigate && onNavigate('auditflow')}>
                    Full Audit Flow →
                  </button>
                  <button className="btn btn-secondary" style={{ flex:1,justifyContent:'center',fontSize:12 }} onClick={() => onNavigate && onNavigate('reports')}>
                    Standards Report →
                  </button>
                </div>
              </div>
            ) : (
              <div className="card" style={{ height:300 }}>
                <div className="empty-state" style={{ padding:'60px 20px' }}>
                  <div className="empty-state-icon">⚡</div>
                  <div className="empty-state-text">Submit a job to see pipeline results here</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:8,textAlign:'center',lineHeight:1.6,maxWidth:240 }}>Results are persona-tailored — set your persona to get a view relevant to your role</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── GITHUB SCANNER TAB ── */}
      {tab === 'github' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">🐙 GitHub Repo Scanner</span></div>
            <div style={{ fontSize:13,color:'var(--text-muted)',lineHeight:1.6,marginBottom:16 }}>
              Scan any public GitHub repository for AI governance signals. The agent analyzes repo metadata and structure, maps to regulatory articles, and recommends audits.
            </div>
            <div className="form-group">
              <label className="form-label">GitHub Repository URL</label>
              <input className="form-input" placeholder="https://github.com/org/credit-scoring-model"
                value={repoUrl} onChange={e => setRepoUrl(e.target.value)} />
            </div>
            <div style={{ display:'flex',gap:6,marginBottom:14,flexWrap:'wrap' }}>
              {['https://github.com/example/credit-loan-model','https://github.com/example/healthcare-diagnostic-ai','https://github.com/example/hr-screening-v2'].map(url => (
                <button key={url} className="btn btn-secondary" style={{ fontSize:10,padding:'3px 8px' }}
                  onClick={() => setRepoUrl(url)}>{url.split('/').slice(-1)[0]}</button>
              ))}
            </div>
            <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center' }} onClick={scanGithub} disabled={ghLoading||!repoUrl.trim()}>
              {ghLoading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Scanning...</> : '🔍 Scan Repository'}
            </button>
          </div>
          <div className="card">
            {ghResult ? (
              <div>
                <div className="card-header"><span className="card-title">{ghResult.repo_name}</span><span style={{ fontFamily:'var(--mono)',fontSize:10,color:'var(--text-muted)' }}>{ghResult.scan_id}</span></div>
                <div style={{ marginBottom:14,padding:'10px 12px',background:'var(--bg-primary)',borderRadius:8 }}>
                  <div style={{ display:'flex',justifyContent:'space-between',marginBottom:8 }}>
                    <span style={{ fontSize:12,color:'var(--text-muted)' }}>Risk Level</span>
                    <span style={{ fontSize:13,fontWeight:800,color:ghResult.risk_level==='critical'?'var(--accent-red)':ghResult.risk_level==='high'?'var(--accent-amber)':'var(--accent-cyan)',fontFamily:'var(--mono)',textTransform:'uppercase' }}>{ghResult.risk_level}</span>
                  </div>
                  <div className="progress-bar">
                    <div style={{ height:'100%',borderRadius:3,background:ghResult.risk_level==='critical'?'var(--accent-red)':'var(--accent-amber)',width:`${ghResult.overall_risk_score*100}%` }} />
                  </div>
                </div>
                <div style={{ marginBottom:12 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',marginBottom:8 }}>Signals Found</div>
                  <div style={{ display:'flex',gap:6,flexWrap:'wrap' }}>
                    {ghResult.signals_found?.map(s => <span key={s} className="badge badge-amber">{s}</span>)}
                  </div>
                </div>
                <div style={{ marginBottom:12 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',marginBottom:8 }}>Articles Triggered</div>
                  <div style={{ display:'flex',gap:6,flexWrap:'wrap' }}>
                    {ghResult.articles_triggered?.map(a => <span key={a} className="badge badge-red" style={{ fontSize:10 }}>{a}</span>)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',marginBottom:8 }}>Recommended Actions</div>
                  {ghResult.recommended_actions?.map((a,i) => (
                    <div key={i} style={{ display:'flex',gap:8,padding:'6px 0',borderBottom:'1px solid var(--border)',fontSize:12 }}>
                      <span style={{ color:'var(--accent-cyan)',flexShrink:0 }}>{i+1}.</span>
                      <span style={{ color:'var(--text-secondary)' }}>{a}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : <div className="empty-state"><div className="empty-state-icon">🐙</div><div className="empty-state-text">Paste a repo URL and click Scan</div></div>}
          </div>
        </div>
      )}

      {/* ── ROI SIMULATOR TAB ── */}
      {tab === 'roi' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">💰 ROI Simulator</span></div>
            <div style={{ fontSize:13,color:'var(--text-muted)',lineHeight:1.6,marginBottom:16 }}>
              Enter your AI spend and model count — SARO calculates regulatory fine risk, fines avoided, and net savings.
            </div>
            {[['annual_ai_spend_usd','Annual AI Spend (USD)',50000,5000000,50000],['num_ai_models','Number of AI Models',1,200,1]].map(([k,label,min,max,step])=>(
              <div key={k} className="form-group">
                <label className="form-label" style={{ display:'flex',justifyContent:'space-between' }}>
                  <span>{label}</span>
                  <strong style={{ color:'var(--accent-cyan)',fontFamily:'var(--mono)' }}>${roi[k]?.toLocaleString()}</strong>
                </label>
                <input type="range" min={min} max={max} step={step} value={roi[k]}
                  onChange={e => setRoi(r=>({...r,[k]:Number(e.target.value)}))}
                  style={{ width:'100%',accentColor:'var(--accent-cyan)' }} />
              </div>
            ))}
            <div className="form-group">
              <label className="form-label">Industry</label>
              <select className="form-select" value={roi.industry} onChange={e=>setRoi(r=>({...r,industry:e.target.value}))}>
                {['finance','healthcare','hr','general'].map(i=><option key={i}>{i}</option>)}
              </select>
            </div>
            <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center' }} onClick={calcRoi} disabled={roiLoading}>
              {roiLoading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Calculating...</> : '💰 Calculate ROI'}
            </button>
          </div>
          <div className="card">
            {roiResult ? (
              <div>
                <div className="card-header"><span className="card-title">ROI Analysis</span></div>
                <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:12,marginBottom:16 }}>
                  {[
                    { label:'Total Fine Risk',     value:`$${roiResult.risk_analysis.total_fine_risk_usd?.toLocaleString()}`, color:'red' },
                    { label:'Fines Avoided',       value:`$${roiResult.risk_analysis.fines_avoided_usd?.toLocaleString()}`,  color:'green' },
                    { label:'SARO Annual Cost',    value:`$${roiResult.saro_economics.saro_annual_cost_usd?.toLocaleString()}`, color:'amber' },
                    { label:'Net Annual Saving',   value:`$${roiResult.saro_economics.net_saving_usd?.toLocaleString()}`,    color:'cyan' },
                  ].map(m => (
                    <div key={m.label} style={{ padding:'12px 14px',background:'var(--bg-primary)',borderRadius:8 }}>
                      <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase',marginBottom:4 }}>{m.label}</div>
                      <div style={{ fontSize:18,fontWeight:800,fontFamily:'var(--mono)',color:`var(--accent-${m.color})` }}>{m.value}</div>
                    </div>
                  ))}
                </div>
                <div style={{ padding:'14px 16px',borderRadius:10,background:'rgba(0,255,136,0.06)',border:'1px solid rgba(0,255,136,0.2)',marginBottom:14 }}>
                  <div style={{ fontSize:24,fontWeight:900,color:'var(--accent-green)',fontFamily:'var(--mono)',marginBottom:4 }}>{roiResult.saro_economics.roi_pct}% ROI</div>
                  <div style={{ fontSize:12,color:'var(--text-muted)' }}>Payback: {roiResult.saro_economics.payback_months} months</div>
                </div>
                <div style={{ fontSize:12,color:'var(--text-secondary)',lineHeight:1.6,marginBottom:8 }}>{roiResult.summary}</div>
                <div style={{ fontSize:10,color:'var(--text-muted)',fontStyle:'italic' }}>{roiResult.disclaimer}</div>
              </div>
            ) : (
              <div className="empty-state"><div className="empty-state-icon">💰</div><div className="empty-state-text">Adjust inputs and click Calculate ROI</div></div>
            )}
          </div>
        </div>
      )}

      {/* ── DATASETS TAB ── */}
      {tab === 'datasets' && (
        <div>
          <div style={{ display:'flex',gap:8,marginBottom:16,flexWrap:'wrap' }}>
            {['all','finance','healthcare','hr','general'].map(f => (
              <button key={f} className={`btn ${dsFilter===f?'btn-primary':'btn-secondary'}`} style={{ fontSize:12,padding:'6px 12px',textTransform:'capitalize' }} onClick={()=>setDsFilter(f)}>{f}</button>
            ))}
          </div>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(340px,1fr))',gap:16 }}>
            {datasets.filter(d => dsFilter==='all' || d.industry===dsFilter).map((d,i) => (
              <div key={i} className="card">
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:10 }}>
                  <div>
                    <div style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)',marginBottom:2 }}>{d.name}</div>
                    <div style={{ display:'flex',gap:6 }}>
                      <span className="badge badge-cyan" style={{ fontSize:10 }}>{d.industry}</span>
                      <span className="badge badge-gray" style={{ fontSize:10 }}>{d.source}</span>
                      <span className="badge badge-green" style={{ fontSize:10 }}>{d.size}</span>
                    </div>
                  </div>
                </div>
                <div style={{ fontSize:12,color:'var(--text-muted)',marginBottom:10,lineHeight:1.5 }}>{d.use_case}</div>
                <div style={{ display:'flex',gap:4,flexWrap:'wrap',marginBottom:10 }}>
                  {d.relevant_articles?.map(a => <span key={a} className="badge badge-red" style={{ fontSize:10 }}>{a}</span>)}
                </div>
                <div style={{ display:'flex',gap:8 }}>
                  <a href={d.url} target="_blank" rel="noreferrer" style={{ flex:1,textDecoration:'none' }}>
                    <button className="btn btn-secondary" style={{ width:'100%',justifyContent:'center',fontSize:11 }}>↗ View Dataset</button>
                  </a>
                  <button className="btn btn-secondary" style={{ flex:1,justifyContent:'center',fontSize:11 }}
                    onClick={() => { setTab('submit'); setForm(f=>({...f,domain:d.industry,input_type:'text',output_text:`Sample AI model output from ${d.name}. Testing bias and fairness per ${d.relevant_articles?.[0]}.`})) }}>
                    ⚡ Test in Pipeline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── HISTORY TAB ── */}
      {tab === 'history' && (
        <div>
          <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:14 }}>
            <span style={{ fontSize:13,color:'var(--text-muted)' }}>{jobs.length} jobs submitted this session</span>
            <button className="btn btn-secondary" style={{ fontSize:12 }} onClick={() => get('/api/v1/gateway/jobs').then(d=>setJobs(d.jobs||[]))}>↻ Refresh</button>
          </div>
          {jobs.length === 0 ? (
            <div className="empty-state card" style={{ padding:'48px 20px' }}>
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-text">No jobs yet — use Submit tab to run your first gateway job</div>
            </div>
          ) : jobs.map((j,i) => {
            const cfg = VERDICT_CFG[j.verdict] || VERDICT_CFG.REVIEW
            return (
              <div key={i} className="card" style={{ marginBottom:10,padding:'14px 18px',display:'flex',justifyContent:'space-between',alignItems:'center' }}>
                <div>
                  <div style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)',marginBottom:2 }}>{j.model_name} <span style={{ fontFamily:'var(--mono)',fontSize:10,color:'var(--text-muted)',marginLeft:6 }}>{j.job_id}</span></div>
                  <div style={{ fontSize:11,color:'var(--text-muted)' }}>{j.policy} · {j.domain} · {j.input_type} input · {new Date(j.submitted_at).toLocaleTimeString()}</div>
                </div>
                <div style={{ display:'flex',gap:10,alignItems:'center' }}>
                  {j.status === 'complete' ? (
                    <>
                      <span style={{ fontSize:12,fontFamily:'var(--mono)',color:'var(--accent-cyan)' }}>{(j.compliance_score*100).toFixed(0)}%</span>
                      <span style={{ fontSize:11,fontWeight:800,padding:'3px 10px',borderRadius:20,color:cfg.color,background:cfg.bg,border:`1px solid ${cfg.border}` }}>{j.verdict}</span>
                    </>
                  ) : (
                    <span style={{ fontSize:11,color:'var(--text-muted)' }}>{j.status} · {j.stage}</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
