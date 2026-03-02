/**
 * FR-001: Regulatory Ingestion + NLP Entity Extraction (95% accuracy)
 * FR-003: Proactive Bayesian Forecasting + Monte Carlo Simulation (85% accuracy)
 * FR-006: Standards Explorer — EU AI Act, NIST, ISO, FDA, MAS with article detail
 */
import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const get  = p => fetch(`${BASE}${p}`).then(r => r.json())
const post = (p,b) => fetch(`${BASE}${p}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json())

const RC = s => s >= 0.7 ? 'var(--accent-red)' : s >= 0.4 ? 'var(--accent-amber)' : 'var(--accent-green)'

export default function MVP1Ingestion() {
  const [tab, setTab] = useState('forecast')
  const [form, setForm] = useState({ title:'', content:'', jurisdiction:'EU', doc_type:'regulation' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [docs, setDocs] = useState([])
  const [forecast, setForecast] = useState(null)
  const [forecastHorizon, setForecastHorizon] = useState('90d')
  const [simulation, setSimulation] = useState(null)
  const [simDomain, setSimDomain] = useState('finance')
  const [simLoading, setSimLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [standards, setStandards] = useState([])
  const [selectedStd, setSelectedStd] = useState(null)
  const [stdDetail, setStdDetail] = useState(null)

  useEffect(() => {
    get('/api/v1/mvp1/stats').then(setStats).catch(()=>{})
    get('/api/v1/mvp1/documents').then(d => setDocs(d.documents||[])).catch(()=>{})
    get('/api/v1/mvp1/forecast').then(setForecast).catch(()=>{})
    get('/api/v1/mvp1/standards-explorer').then(d => setStandards(d.standards||[])).catch(()=>{})
  }, [])

  const loadForecast = () => get(`/api/v1/mvp1/forecast?horizon=${forecastHorizon}`).then(setForecast).catch(()=>{})

  const handleIngest = async () => {
    if (!form.title || !form.content) return
    setLoading(true)
    try {
      const res = await post('/api/v1/mvp1/ingest', form)
      setResult(res); setDocs(d => [res, ...d])
    } finally { setLoading(false) }
  }

  const runSim = async () => {
    setSimLoading(true)
    try { setSimulation(await get(`/api/v1/mvp1/forecast/simulation?domain=${simDomain}&iterations=500`)) }
    finally { setSimLoading(false) }
  }

  const loadStd = async name => {
    setSelectedStd(name)
    try { setStdDetail(await get(`/api/v1/mvp1/standards-explorer?standard=${encodeURIComponent(name)}`)) }
    catch(e){}
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Ingestion & Forecasting</h1>
          <p className="page-subtitle">FR-001 · FR-003 · FR-006 — Proactive Bayesian forecasting · Regulatory ingestion · Standards explorer</p>
        </div>
      </div>

      {stats && (
        <div className="metrics-grid" style={{marginBottom:20}}>
          {[
            {l:'Total Documents',   v:stats.total_documents?.toLocaleString()},
            {l:'Today',             v:stats.documents_today},
            {l:'Avg Risk Score',    v:(stats.avg_risk_score*100).toFixed(0)+'%'},
            {l:'Entity Accuracy',   v:stats.entity_accuracy},
            {l:'Standards Covered', v:stats.standards_covered},
          ].map(s => (
            <div key={s.l} className="metric-card">
              <div className="metric-value">{s.v}</div>
              <div className="metric-label">{s.l}</div>
            </div>
          ))}
        </div>
      )}

      <div className="tab-nav" style={{marginBottom:20}}>
        {[['forecast','📈 Forecast'],['simulate','🎲 Monte Carlo'],['ingest','⬆ Ingest'],['docs','📄 Documents'],['standards','📚 Standards']].map(([id,lbl]) => (
          <button key={id} className={`tab-btn ${tab===id?'active':''}`} onClick={()=>setTab(id)}>{lbl}</button>
        ))}
      </div>

      {/* FORECAST */}
      {tab==='forecast' && (
        <div>
          <div className="card" style={{marginBottom:16}}>
            <div className="card-header">
              <span className="card-title">📈 Bayesian Gap Probability Forecast</span>
              <div style={{display:'flex',gap:8,alignItems:'center'}}>
                <select value={forecastHorizon} onChange={e=>setForecastHorizon(e.target.value)}
                  style={{background:'var(--surface)',border:'1px solid var(--border)',color:'var(--text-secondary)',borderRadius:6,padding:'4px 10px',fontSize:12}}>
                  {[['30d','30 days'],['90d','90 days'],['180d','6 months'],['1y','1 year']].map(([v,l])=><option key={v} value={v}>{l}</option>)}
                </select>
                <button className="btn btn-primary" onClick={loadForecast} style={{padding:'5px 14px',fontSize:12}}>Update</button>
              </div>
            </div>
            {forecast ? (
              <>
                <div className="metrics-grid" style={{marginBottom:16}}>
                  {[
                    {l:'Overall Gap Probability', v:`${(forecast.overall_gap_probability*100).toFixed(0)}%`, c:RC(forecast.overall_gap_probability)},
                    {l:'Confidence Interval',     v:`${(forecast.ci_lower*100).toFixed(0)}–${(forecast.ci_upper*100).toFixed(0)}%`, c:'var(--text-primary)'},
                    {l:'Forecast Horizon',         v:forecast.horizon, c:'var(--accent-cyan)'},
                    {l:'Model Accuracy (ROC-AUC)', v:`${forecast.forecast_accuracy_pct}%`, c:'var(--accent-green)'},
                  ].map(s => (
                    <div key={s.l} className="metric-card">
                      <div className="metric-value" style={{color:s.c}}>{s.v}</div>
                      <div className="metric-label">{s.l}</div>
                    </div>
                  ))}
                </div>
                <div style={{marginBottom:16}}>
                  <div style={{fontSize:11,fontWeight:700,color:'var(--text-muted)',marginBottom:8,letterSpacing:'0.5px'}}>DOMAIN RISK BREAKDOWN</div>
                  {forecast.domain_breakdown?.map(d => (
                    <div key={d.domain} style={{display:'flex',alignItems:'center',gap:12,marginBottom:8}}>
                      <div style={{width:88,fontSize:12,color:'var(--text-secondary)',textTransform:'capitalize',fontWeight:500}}>{d.domain}</div>
                      <div style={{flex:1,height:7,background:'rgba(255,255,255,0.05)',borderRadius:4,overflow:'hidden'}}>
                        <div style={{height:'100%',width:`${d.probability*100}%`,background:RC(d.probability),borderRadius:4,transition:'width 0.8s ease'}}/>
                      </div>
                      <div style={{width:36,fontSize:13,fontWeight:700,color:RC(d.probability),textAlign:'right'}}>{(d.probability*100).toFixed(0)}%</div>
                      <div style={{width:110,fontSize:10,color:'var(--text-muted)',textAlign:'right'}}>{d.primary_regulation}</div>
                    </div>
                  ))}
                </div>
                {forecast.upcoming_deadlines?.length > 0 && (
                  <>
                    <div style={{fontSize:11,fontWeight:700,color:'var(--text-muted)',marginBottom:8,letterSpacing:'0.5px'}}>UPCOMING REGULATORY DEADLINES</div>
                    {forecast.upcoming_deadlines.map((d,i)=>(
                      <div key={i} style={{display:'flex',gap:10,alignItems:'center',padding:'8px 0',borderBottom:'1px solid var(--border)'}}>
                        <span style={{fontSize:9,fontWeight:800,padding:'2px 7px',borderRadius:4,letterSpacing:'0.3px',
                          background:d.risk==='critical'?'rgba(255,61,106,0.15)':d.risk==='high'?'rgba(255,184,0,0.12)':'rgba(0,255,136,0.08)',
                          color:d.risk==='critical'?'var(--accent-red)':d.risk==='high'?'var(--accent-amber)':'var(--accent-green)'}}>
                          {d.risk.toUpperCase()}
                        </span>
                        <span style={{fontSize:11,color:'var(--text-muted)',width:100,flexShrink:0}}>{d.date}</span>
                        <span style={{flex:1,fontSize:12,color:'var(--text-secondary)'}}>{d.milestone}</span>
                        <span style={{fontSize:10,color:'var(--text-muted)'}}>{d.regulation}</span>
                      </div>
                    ))}
                  </>
                )}
              </>
            ) : <div style={{color:'var(--text-muted)',padding:24}}>Loading forecast...</div>}
          </div>
        </div>
      )}

      {/* MONTE CARLO */}
      {tab==='simulate' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">🎲 Monte Carlo Risk Simulation</span>
            <div style={{display:'flex',gap:8,alignItems:'center'}}>
              <select value={simDomain} onChange={e=>setSimDomain(e.target.value)}
                style={{background:'var(--surface)',border:'1px solid var(--border)',color:'var(--text-secondary)',borderRadius:6,padding:'4px 10px',fontSize:12}}>
                {['finance','healthcare','hr','general'].map(d=><option key={d} value={d}>{d}</option>)}
              </select>
              <button className="btn btn-primary" onClick={runSim} disabled={simLoading} style={{padding:'5px 14px',fontSize:12}}>
                {simLoading?'Running...':'▶ Run 500 Iterations'}
              </button>
            </div>
          </div>
          {simulation ? (
            <>
              <div className="metrics-grid" style={{marginBottom:16}}>
                {[
                  {l:'Mean',   v:`${(simulation.mean*100).toFixed(1)}%`},
                  {l:'Median', v:`${(simulation.median*100).toFixed(1)}%`},
                  {l:'P10',    v:`${(simulation.p10*100).toFixed(1)}%`},
                  {l:'P90',    v:`${(simulation.p90*100).toFixed(1)}%`},
                ].map(s => (
                  <div key={s.l} className="metric-card">
                    <div className="metric-value">{s.v}</div>
                    <div className="metric-label">{s.l}</div>
                  </div>
                ))}
              </div>
              <div style={{marginBottom:16}}>
                <div style={{fontSize:11,fontWeight:700,color:'var(--text-muted)',marginBottom:10,letterSpacing:'0.5px'}}>PROBABILITY DISTRIBUTION (500 iterations)</div>
                <div style={{display:'flex',gap:3,alignItems:'flex-end',height:72,padding:'0 4px'}}>
                  {simulation.histogram?.map((h,i)=>{
                    const maxC = Math.max(...simulation.histogram.map(x=>x.count),1)
                    return (
                      <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',gap:3}}>
                        <div style={{width:'100%',height:`${(h.count/maxC)*62}px`,background:i<5?'var(--accent-green)':'var(--accent-red)',borderRadius:'3px 3px 0 0',opacity:0.75,minHeight:3,transition:'height 0.4s ease'}}/>
                        <div style={{fontSize:8,color:'var(--text-muted)'}}>{i*10}%</div>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div style={{padding:'10px 14px',background:'rgba(0,212,255,0.06)',border:'1px solid rgba(0,212,255,0.15)',borderRadius:8,fontSize:12,color:'var(--text-secondary)'}}>
                💡 {simulation.interpretation}
              </div>
            </>
          ) : (
            <div style={{padding:40,textAlign:'center',color:'var(--text-muted)'}}>
              <div style={{fontSize:28,marginBottom:8}}>🎲</div>
              <div>Select domain and run simulation to see gap probability distribution across 500 scenarios</div>
            </div>
          )}
        </div>
      )}

      {/* INGEST */}
      {tab==='ingest' && (
        <div className="card">
          <div className="card-header"><span className="card-title">⬆ Ingest Regulatory Document</span></div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:14}}>
            <div>
              <label style={{fontSize:11,color:'var(--text-muted)',display:'block',marginBottom:4,fontWeight:600}}>DOCUMENT TITLE *</label>
              <input className="form-input" value={form.title} onChange={e=>setForm(f=>({...f,title:e.target.value}))}
                placeholder="e.g. EU AI Act Art.10 Data Governance Update" />
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
              <div>
                <label style={{fontSize:11,color:'var(--text-muted)',display:'block',marginBottom:4,fontWeight:600}}>JURISDICTION</label>
                <select className="form-input" value={form.jurisdiction} onChange={e=>setForm(f=>({...f,jurisdiction:e.target.value}))}>
                  {['EU','US','UK','APAC','INT'].map(j=><option key={j}>{j}</option>)}
                </select>
              </div>
              <div>
                <label style={{fontSize:11,color:'var(--text-muted)',display:'block',marginBottom:4,fontWeight:600}}>TYPE</label>
                <select className="form-input" value={form.doc_type} onChange={e=>setForm(f=>({...f,doc_type:e.target.value}))}>
                  {['regulation','guidance','whitepaper','standard'].map(t=><option key={t}>{t}</option>)}
                </select>
              </div>
            </div>
          </div>
          <div style={{marginBottom:14}}>
            <label style={{fontSize:11,color:'var(--text-muted)',display:'block',marginBottom:4,fontWeight:600}}>CONTENT *</label>
            <textarea className="form-input" rows={5} value={form.content}
              onChange={e=>setForm(f=>({...f,content:e.target.value}))}
              placeholder="Paste regulatory document text. The system extracts entities, scores risk, maps to standards, and generates 90-day Bayesian gap probability..." />
          </div>
          <button className="btn btn-primary" onClick={handleIngest} disabled={loading||!form.title||!form.content}>
            {loading?'Analyzing...':'⬆ Ingest & Analyze'}
          </button>
          {result && (
            <div style={{marginTop:18,padding:16,background:'rgba(0,255,136,0.05)',border:'1px solid rgba(0,255,136,0.2)',borderRadius:8}}>
              <div style={{fontWeight:700,color:'var(--accent-green)',marginBottom:10}}>✓ Ingested: {result.title}</div>
              <div className="metrics-grid" style={{marginBottom:12}}>
                <div className="metric-card"><div className="metric-value" style={{color:RC(result.risk_score)}}>{(result.risk_score*100).toFixed(0)}%</div><div className="metric-label">Risk Score</div></div>
                <div className="metric-card"><div className="metric-value">{(result.gap_probability_90d*100).toFixed(0)}%</div><div className="metric-label">90d Gap Prob</div></div>
                <div className="metric-card"><div className="metric-value">{result.entities_found?.length||0}</div><div className="metric-label">Standards Found</div></div>
                <div className="metric-card"><div className="metric-value" style={{fontSize:12,textTransform:'capitalize'}}>{result.remediation_urgency}</div><div className="metric-label">Urgency</div></div>
              </div>
              {result.entities_found?.length > 0 && (
                <div style={{display:'flex',flexWrap:'wrap',gap:6}}>
                  {result.entities_found.map(e=>(
                    <span key={e} style={{padding:'3px 9px',background:'rgba(0,212,255,0.08)',color:'var(--accent-cyan)',borderRadius:4,fontSize:11,border:'1px solid rgba(0,212,255,0.2)'}}>📋 {e}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* DOCUMENTS */}
      {tab==='docs' && (
        <div className="card">
          <div className="card-header"><span className="card-title">📄 Document Library ({docs.length})</span></div>
          {docs.length===0 ? (
            <p style={{color:'var(--text-muted)',padding:'20px 0'}}>No documents ingested yet. Use the Ingest tab to add documents.</p>
          ) : (
            <div style={{display:'grid',gap:8}}>
              {docs.map((d,i)=>(
                <div key={d.id||i} style={{padding:'12px 14px',background:'var(--surface)',borderRadius:8,border:'1px solid var(--border)',display:'flex',gap:12,alignItems:'center'}}>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600,fontSize:13,color:'var(--text-primary)'}}>{d.title}</div>
                    <div style={{fontSize:11,color:'var(--text-muted)',marginTop:2}}>
                      {d.jurisdiction} · {d.processed_at?new Date(d.processed_at).toLocaleDateString():'N/A'}
                    </div>
                  </div>
                  <div style={{textAlign:'right',flexShrink:0}}>
                    <div style={{fontSize:15,fontWeight:700,color:RC(d.risk_score||0)}}>{((d.risk_score||0)*100).toFixed(0)}%</div>
                    <div style={{fontSize:10,color:'var(--text-muted)'}}>risk</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* STANDARDS EXPLORER */}
      {tab==='standards' && (
        <div style={{display:'grid',gridTemplateColumns:'260px 1fr',gap:14}}>
          <div className="card" style={{height:'fit-content',padding:'12px'}}>
            <div style={{fontSize:11,fontWeight:700,color:'var(--text-muted)',marginBottom:10,letterSpacing:'0.5px'}}>STANDARDS ({standards.length})</div>
            {standards.map(s=>(
              <div key={s.name} onClick={()=>loadStd(s.name)}
                style={{padding:'10px 10px',borderRadius:7,cursor:'pointer',marginBottom:3,
                  background:selectedStd===s.name?'var(--accent-cyan-dim)':'transparent',
                  border:`1px solid ${selectedStd===s.name?'rgba(0,212,255,0.3)':'transparent'}`,
                  transition:'all 0.15s'}}>
                <div style={{fontWeight:600,fontSize:12,color:selectedStd===s.name?'var(--accent-cyan)':'var(--text-secondary)'}}>{s.name}</div>
                <div style={{fontSize:10,color:'var(--text-muted)',marginTop:2}}>{s.jurisdiction} · {s.articles} articles</div>
              </div>
            ))}
          </div>
          <div className="card">
            {stdDetail ? (
              <>
                <div className="card-header">
                  <span className="card-title">{selectedStd}</span>
                  <span style={{fontSize:11,color:'var(--text-muted)'}}>Effective {stdDetail.effective}</span>
                </div>
                <div style={{fontSize:11,color:'var(--text-muted)',marginBottom:12}}>{stdDetail.full_name}</div>
                <div style={{padding:'8px 14px',background:'rgba(255,184,0,0.06)',border:'1px solid rgba(255,184,0,0.2)',borderRadius:6,fontSize:12,color:'var(--accent-amber)',marginBottom:16}}>
                  ⚠️ Penalties: {stdDetail.fines}
                </div>
                <div style={{marginBottom:14}}>
                  <div style={{fontSize:11,fontWeight:700,color:'var(--text-muted)',marginBottom:8,letterSpacing:'0.5px'}}>ARTICLES & REQUIREMENTS</div>
                  {stdDetail.articles?.map(a=>(
                    <div key={a.id} style={{display:'flex',gap:12,padding:'9px 0',borderBottom:'1px solid var(--border)',alignItems:'center'}}>
                      <code style={{fontSize:11,color:'var(--accent-cyan)',width:90,flexShrink:0,fontFamily:'var(--mono)'}}>{a.id}</code>
                      <span style={{flex:1,fontSize:12,color:'var(--text-secondary)'}}>{a.title}</span>
                      <span style={{fontSize:9,fontWeight:800,padding:'2px 7px',borderRadius:4,letterSpacing:'0.3px',
                        background:a.risk_level==='critical'?'rgba(255,61,106,0.12)':a.risk_level==='high'?'rgba(255,184,0,0.1)':'rgba(0,255,136,0.08)',
                        color:a.risk_level==='critical'?'var(--accent-red)':a.risk_level==='high'?'var(--accent-amber)':'var(--accent-green)'}}>
                        {a.risk_level.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
                <div style={{fontSize:11,color:'var(--text-muted)'}}>Applies to: {stdDetail.applies_to?.join(' · ')}</div>
              </>
            ) : (
              <div style={{padding:48,textAlign:'center',color:'var(--text-muted)'}}>
                <div style={{fontSize:36,marginBottom:12}}>📚</div>
                <div style={{fontSize:13}}>Select a standard from the left to explore its articles and compliance requirements</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
