import { useState } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''

const PERSONAS = [
  { id:'forecaster', icon:'📈', name:'Forecaster', desc:'Regulatory intelligence, risk prediction, upcoming changes', color:'cyan', modules:['Ingestion & Forecast','Regulatory Alerts','Feed Log'] },
  { id:'autopsier',  icon:'🔍', name:'Autopsier',  desc:'Deep-dive audit findings, evidence chains, standards reports', color:'amber', modules:['Audit & Compliance','Standards Reports','Evidence Chain'] },
  { id:'enabler',    icon:'⚙️', name:'Enabler',    desc:'Implement controls, manage policies, drive remediation', color:'green', modules:['Guardrails','Autonomous Bots','Policy Library'] },
  { id:'evangelist', icon:'🎯', name:'Evangelist', desc:'Executive summaries, ROI metrics, board reporting', color:'purple', modules:['Executive Dashboard','Commercial','Ethics & Surveillance'] },
]

const INDUSTRIES = ['Technology','Financial Services','Healthcare','Retail','Manufacturing','Government','Legal','Other']
const PLANS = [
  { id:'starter', name:'Starter', price:'$299/mo', features:['5 AI model audits/mo','Basic guardrails','EU AI Act coverage','Email support'] },
  { id:'professional', name:'Professional', price:'$899/mo', features:['Unlimited audits','Full guardrails suite','All jurisdictions','Autonomous bots','Standards reports','Priority support'] },
  { id:'enterprise', name:'Enterprise', price:'Custom', features:['Everything in Pro','Multi-tenant','HA infrastructure','Custom integrations','Dedicated CSM','SLA 99.99%'] },
]

export default function Onboarding() {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({ company_name:'', industry:'Technology', plan:'professional', persona:'enabler' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(null)

  const totalSteps = 4

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/api/v1/onboard`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify(form)
      })
      setResult(await res.json())
      setStep(5)
    } catch(e) {}
    finally { setLoading(false) }
  }

  const copy = (text, key) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Client Onboarding</h1>
          <p className="page-subtitle">Self-service portal — get your account, API keys, and persona configured in under 5 minutes</p>
        </div>
      </div>

      {step < 5 && (
        <div style={{ marginBottom:24 }}>
          <div style={{ display:'flex',gap:0,alignItems:'center' }}>
            {['Company','Persona','Plan','Review'].map((s,i) => (
              <div key={s} style={{ display:'flex',alignItems:'center',flex:1 }}>
                <div style={{ display:'flex',flexDirection:'column',alignItems:'center',flex:1 }}>
                  <div style={{ width:32,height:32,borderRadius:'50%',background:step>i+1?'var(--accent-green)':step===i+1?'var(--accent-cyan)':'var(--bg-card)',border:`2px solid ${step>i+1?'var(--accent-green)':step===i+1?'var(--accent-cyan)':'var(--border)'}`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:13,fontWeight:700,color:step>i+1?'#000':step===i+1?'#000':'var(--text-muted)',flexShrink:0 }}>
                    {step>i+1 ? '✓' : i+1}
                  </div>
                  <div style={{ fontSize:11,color:step===i+1?'var(--accent-cyan)':'var(--text-muted)',marginTop:4,fontWeight:step===i+1?600:400 }}>{s}</div>
                </div>
                {i < 3 && <div style={{ flex:1,height:2,background:step>i+1?'var(--accent-green)':'var(--border)',marginBottom:20 }} />}
              </div>
            ))}
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="card" style={{ maxWidth:560 }}>
          <div className="card-header"><span className="card-title">Company Details</span></div>
          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input className="form-input" placeholder="Acme Corp Ltd" value={form.company_name} onChange={e => setForm(f=>({...f,company_name:e.target.value}))} />
          </div>
          <div className="form-group">
            <label className="form-label">Industry</label>
            <select className="form-select" value={form.industry} onChange={e => setForm(f=>({...f,industry:e.target.value}))}>
              {INDUSTRIES.map(i => <option key={i}>{i}</option>)}
            </select>
          </div>
          <button className="btn btn-primary" disabled={!form.company_name} onClick={() => setStep(2)} style={{ width:'100%',justifyContent:'center' }}>
            Next: Choose Persona →
          </button>
        </div>
      )}

      {step === 2 && (
        <div>
          <div style={{ marginBottom:16 }}>
            <div style={{ fontSize:14,color:'var(--text-secondary)',marginBottom:4 }}>Choose the persona that best fits your role. This configures your default dashboard and workflow.</div>
          </div>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(260px,1fr))',gap:16,marginBottom:24 }}>
            {PERSONAS.map(p => (
              <div key={p.id} className="card" style={{ cursor:'pointer',border:`2px solid ${form.persona===p.id?`var(--accent-${p.color})`:'var(--border)'}`,background:form.persona===p.id?`var(--accent-${p.color}-dim)`:'var(--bg-card)' }} onClick={() => setForm(f=>({...f,persona:p.id}))}>
                <div style={{ fontSize:28,marginBottom:10 }}>{p.icon}</div>
                <div style={{ fontSize:15,fontWeight:700,marginBottom:6,color:form.persona===p.id?`var(--accent-${p.color})`:'var(--text-primary)' }}>{p.name}</div>
                <div style={{ fontSize:12,color:'var(--text-muted)',marginBottom:12,lineHeight:1.6 }}>{p.desc}</div>
                <div style={{ display:'flex',flexDirection:'column',gap:4 }}>
                  {p.modules.map(m => <div key={m} style={{ fontSize:11,color:'var(--text-secondary)',display:'flex',gap:6,alignItems:'center' }}><span style={{ color:`var(--accent-${p.color})` }}>→</span>{m}</div>)}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display:'flex',gap:12 }}>
            <button className="btn btn-secondary" onClick={() => setStep(1)}>← Back</button>
            <button className="btn btn-primary" onClick={() => setStep(3)}>Next: Choose Plan →</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(260px,1fr))',gap:16,marginBottom:24 }}>
            {PLANS.map(p => (
              <div key={p.id} className="card" style={{ cursor:'pointer',border:`2px solid ${form.plan===p.id?'var(--accent-cyan)':'var(--border)'}`,position:'relative' }} onClick={() => setForm(f=>({...f,plan:p.id}))}>
                {p.id==='professional' && <div style={{ position:'absolute',top:-10,left:'50%',transform:'translateX(-50%)',background:'var(--accent-cyan)',color:'#000',fontSize:10,fontWeight:700,padding:'2px 12px',borderRadius:20 }}>MOST POPULAR</div>}
                <div style={{ fontSize:15,fontWeight:700,marginBottom:4 }}>{p.name}</div>
                <div style={{ fontSize:22,fontWeight:800,color:'var(--accent-cyan)',fontFamily:'var(--mono)',marginBottom:16 }}>{p.price}</div>
                {p.features.map(feat => (
                  <div key={feat} style={{ display:'flex',gap:8,fontSize:12,color:'var(--text-secondary)',padding:'4px 0' }}>
                    <span style={{ color:'var(--accent-green)',flexShrink:0 }}>✓</span>{feat}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div style={{ display:'flex',gap:12 }}>
            <button className="btn btn-secondary" onClick={() => setStep(2)}>← Back</button>
            <button className="btn btn-primary" onClick={() => setStep(4)}>Next: Review →</button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="card" style={{ maxWidth:560 }}>
          <div className="card-header"><span className="card-title">Review & Confirm</span></div>
          {[
            ['Company', form.company_name],
            ['Industry', form.industry],
            ['Persona', PERSONAS.find(p=>p.id===form.persona)?.name + ' ' + PERSONAS.find(p=>p.id===form.persona)?.icon],
            ['Plan', PLANS.find(p=>p.id===form.plan)?.name + ' — ' + PLANS.find(p=>p.id===form.plan)?.price],
          ].map(([k,v]) => (
            <div key={k} style={{ display:'flex',justifyContent:'space-between',padding:'10px 0',borderBottom:'1px solid var(--border)',fontSize:13 }}>
              <span style={{ color:'var(--text-muted)',fontWeight:600 }}>{k}</span>
              <span style={{ color:'var(--text-primary)',fontWeight:500 }}>{v}</span>
            </div>
          ))}
          <div style={{ display:'flex',gap:12,marginTop:20 }}>
            <button className="btn btn-secondary" onClick={() => setStep(3)}>← Back</button>
            <button className="btn btn-primary" style={{ flex:1,justifyContent:'center' }} onClick={handleSubmit} disabled={loading}>
              {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Creating account...</> : '🚀 Complete Onboarding'}
            </button>
          </div>
        </div>
      )}

      {step === 5 && result && (
        <div>
          <div style={{ padding:'20px 24px',background:'rgba(0,255,136,0.06)',border:'1px solid rgba(0,255,136,0.2)',borderRadius:12,marginBottom:24,textAlign:'center' }}>
            <div style={{ fontSize:32,marginBottom:8 }}>🎉</div>
            <div style={{ fontSize:20,fontWeight:700,color:'var(--accent-green)',marginBottom:4 }}>Welcome to SARO, {result.company_name}!</div>
            <div style={{ fontSize:13,color:'var(--text-muted)' }}>Tenant ID: <span style={{ fontFamily:'var(--mono)',color:'var(--accent-cyan)' }}>{result.tenant_id}</span></div>
          </div>

          <div className="grid-2" style={{ marginBottom:20 }}>
            <div className="card">
              <div className="card-header"><span className="card-title">API Keys</span></div>
              {[['Live API Key', result.api_key],['Sandbox Key', result.sandbox_key]].map(([label,key]) => (
                <div key={label} style={{ marginBottom:14 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:6 }}>{label}</div>
                  <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                    <code style={{ flex:1,padding:'8px 12px',background:'var(--bg-primary)',borderRadius:6,fontSize:11,fontFamily:'var(--mono)',color:'var(--accent-cyan)',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',border:'1px solid var(--border)' }}>{key}</code>
                    <button className="btn btn-secondary" style={{ fontSize:11,padding:'6px 12px',flexShrink:0 }} onClick={() => copy(key, label)}>
                      {copied===label ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="card">
              <div className="card-header"><span className="card-title">Onboarding Checklist</span></div>
              {result.steps?.map((s,i) => (
                <div key={i} style={{ display:'flex',gap:10,padding:'9px 0',borderBottom:'1px solid var(--border)',alignItems:'center' }}>
                  <span style={{ fontSize:16,color:s.done?'var(--accent-green)':'var(--border)',flexShrink:0 }}>{s.done?'✓':'○'}</span>
                  <span style={{ fontSize:13,color:s.done?'var(--text-primary)':'var(--text-muted)' }}>{s.step}</span>
                  {!s.done && <span className="badge badge-amber" style={{ marginLeft:'auto',fontSize:10 }}>Pending</span>}
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Your Persona: {PERSONAS.find(p=>p.id===result.persona)?.icon} {PERSONAS.find(p=>p.id===result.persona)?.name}</span></div>
            <div style={{ fontSize:13,color:'var(--text-secondary)',marginBottom:12 }}>{PERSONAS.find(p=>p.id===result.persona)?.desc}</div>
            <div style={{ display:'flex',gap:8,flexWrap:'wrap' }}>
              {PERSONAS.find(p=>p.id===result.persona)?.modules.map(m => (
                <span key={m} className="badge badge-cyan">{m}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
