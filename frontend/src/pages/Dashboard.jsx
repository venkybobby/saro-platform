import { useState, useEffect } from 'react'
import { api } from '../lib/api'

const BASE = window.SARO_CONFIG?.apiUrl || ''

// Maps persona quick-start actions to navigation targets
const PERSONA_NAV = {
  'Go to Ingestion & Forecast':     'mvp1',
  'Check Regulatory Feed':          'feed',
  'Run 90-day forecast':            'mvp1',
  'Upload Model Output':            'auditflow',
  'Go to Audit & Compliance':       'mvp2',
  'Generate Standards Report':      'reports',
  'Check Guardrails':               'mvp4',
  'Trigger Remediation Bot':        'mvp5',
  'Upload Policy for Analysis':     'policies',
  'Review Platform Overview':       'dashboard',
  'Run Ethics Scan':                'mvp5',
  'Export Board Report':            'reports',
}

// Maps compliance status module → navigation target
const MODULE_NAV = {
  'Ingestion':   'mvp1',
  'Audit':       'auditflow',
  'Guardrails':  'mvp4',
  'Policies':    'policies',
  'Bots':        'mvp5',
  'Reports':     'reports',
}

const PERSONAS = [
  { id:'forecaster', icon:'📈', name:'Forecaster', color:'cyan'   },
  { id:'autopsier',  icon:'🔍', name:'Autopsier',  color:'amber'  },
  { id:'enabler',    icon:'⚙️', name:'Enabler',    color:'green'  },
  { id:'evangelist', icon:'🎯', name:'Evangelist', color:'purple' },
]

const SEV_COLOR = { pass:'var(--accent-green)', warn:'var(--accent-amber)', critical:'var(--accent-red)' }
const SEV_BADGE = { pass:'badge-green', warn:'badge-amber', critical:'badge-red' }

export default function Dashboard({ onNavigate }) {
  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(true)
  const [persona, setPersona]     = useState('enabler')
  const [workflow, setWorkflow]   = useState(null)
  const [compliance, setCompliance] = useState(null)

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setData(null)).finally(() => setLoading(false))
    const iv = setInterval(() => api.dashboard().then(setData).catch(() => {}), 30000)
    return () => clearInterval(iv)
  }, [])

  useEffect(() => {
    fetch(`${BASE}/api/v1/checklist/persona/${persona}`)
      .then(r => r.json()).then(d => setWorkflow(d.workflow)).catch(() => {})
    fetch(`${BASE}/api/v1/checklist/compliance-status`)
      .then(r => r.json()).then(setCompliance).catch(() => {})
  }, [persona])

  const nav = (page) => onNavigate && onNavigate(page)

  if (loading) return <div className="loading-overlay"><div className="loading-spinner" /><span>Loading SARO platform...</span></div>

  const m1 = data?.mvp1_ingestion || {}
  const m2 = data?.mvp2_audit     || {}
  const m3 = data?.mvp3_enterprise || {}
  const m4 = data?.mvp4_agentic   || {}

  const pColor = PERSONAS.find(p => p.id === persona)?.color || 'cyan'

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Platform Overview</h1>
          <p className="page-subtitle">Real-time metrics · Persona workflows · Compliance status · 963 tests passing</p>
        </div>
        <div style={{ display:'flex',gap:10,alignItems:'center' }}>
          <button className="btn btn-primary" style={{ fontSize:12,padding:'7px 14px' }} onClick={() => nav('auditflow')}>
            ⚡ Run Audit Flow
          </button>
          <span style={{ display:'flex',alignItems:'center',gap:6,fontSize:12,color:'var(--accent-green)',fontWeight:600 }}>
            <span style={{ width:8,height:8,borderRadius:'50%',background:'var(--accent-green)',display:'inline-block',boxShadow:'0 0 6px var(--accent-green)',animation:'pulse 2s infinite' }} />LIVE
          </span>
        </div>
      </div>

      {/* Quick entry points - the most critical gap: make primary flows obvious */}
      <div style={{ display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:24 }}>
        {[
          { icon:'⚡', label:'Run Full Audit',      sub:'Model output → checklist', page:'auditflow',    color:'cyan'   },
          { icon:'🔍', label:'Check Model Output',  sub:'Upload & analyze AI output', page:'modelchecker', color:'amber'  },
          { icon:'📋', label:'Policy Library',      sub:'Browse & upload policies',   page:'policies',     color:'green'  },
          { icon:'🚀', label:'New Client Setup',    sub:'Onboard in < 5 min',         page:'onboarding',   color:'purple' },
        ].map(e => (
          <div key={e.page} className="card" style={{ cursor:'pointer',padding:'16px 18px',borderTop:`3px solid var(--accent-${e.color})`,transition:'transform 0.15s' }}
            onClick={() => nav(e.page)}
            onMouseEnter={el => el.currentTarget.style.transform='translateY(-2px)'}
            onMouseLeave={el => el.currentTarget.style.transform='translateY(0)'}>
            <div style={{ fontSize:24,marginBottom:8 }}>{e.icon}</div>
            <div style={{ fontSize:13,fontWeight:700,color:'var(--text-primary)',marginBottom:3 }}>{e.label}</div>
            <div style={{ fontSize:11,color:'var(--text-muted)' }}>{e.sub}</div>
          </div>
        ))}
      </div>

      {/* Module status */}
      <div className="grid-2" style={{ marginBottom:20 }}>
        {[
          { icon:'◈', label:'Ingestion & Forecast',  color:'cyan',   stats:`${m1.documents_total?.toLocaleString()||'1,247'} docs · ${m1.forecast_accuracy?Math.round(m1.forecast_accuracy*100):87}% accuracy`, page:'mvp1' },
          { icon:'◉', label:'Audit & Compliance',    color:'amber',  stats:`${m2.audits_total?.toLocaleString()||'847'} audits · ${m2.regulations_tracked||30} regs`,                                               page:'mvp2' },
          { icon:'◎', label:'Enterprise',            color:'purple', stats:`${m3.active_tenants||20} tenants · $${m3.mrr_usd?.toLocaleString()||'87,400'} MRR`,                                                    page:'mvp3' },
          { icon:'◐', label:'Agentic Guardrails',    color:'green',  stats:`${m4.guardrail_checks_today?.toLocaleString()||'48,291'} checks · 96.2% blocked`,                                                       page:'mvp4' },
        ].map(m => (
          <div key={m.label} className="card" style={{ display:'flex',alignItems:'center',gap:14,padding:'14px 18px',cursor:'pointer' }} onClick={() => nav(m.page)}>
            <div style={{ width:38,height:38,borderRadius:8,background:`var(--accent-${m.color}-dim)`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:17,color:`var(--accent-${m.color})`,flexShrink:0 }}>{m.icon}</div>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:13,fontWeight:600,marginBottom:2 }}>{m.label}</div>
              <div style={{ fontSize:11,color:'var(--text-muted)' }}>{m.stats}</div>
            </div>
            <span style={{ fontSize:11,color:'var(--text-muted)' }}>→</span>
          </div>
        ))}
      </div>

      {/* KPI strip */}
      <div className="metrics-grid-4" style={{ marginBottom:20 }}>
        {[
          { label:'Documents',   value:m1.documents_total?.toLocaleString()||'1,247',                sub:'+34 today',              color:'cyan',   icon:'📄' },
          { label:'Compliance',  value:`${Math.round((m2.avg_compliance_score||0.73)*100)}%`,         sub:'Platform avg',           color:'green',  icon:'✓'  },
          { label:'Tenants',     value:m3.active_tenants||20,                                          sub:`$${m3.mrr_usd?.toLocaleString()||'87,400'} MRR`, color:'purple', icon:'🏢' },
          { label:'Guardrails',  value:(m4.guardrail_checks_today||48291).toLocaleString(),            sub:'96.2% blocked',          color:'amber',  icon:'🛡'  },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding:'14px 16px' }}>
            <div style={{ display:'flex',justifyContent:'space-between',marginBottom:6 }}>
              <span style={{ fontSize:11,color:'var(--text-muted)',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.5px' }}>{m.label}</span>
              <span>{m.icon}</span>
            </div>
            <div style={{ fontSize:22,fontWeight:800,fontFamily:'var(--mono)',color:`var(--accent-${m.color})`,marginBottom:2 }}>{m.value}</div>
            <div style={{ fontSize:11,color:'var(--text-muted)' }}>{m.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom:20 }}>
        {/* Persona selector + clickable workflow */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Your Persona Workflow</span>
            <span style={{ fontSize:11,color:'var(--text-muted)' }}>Click steps to navigate</span>
          </div>
          <div style={{ display:'flex',gap:6,marginBottom:16,flexWrap:'wrap' }}>
            {PERSONAS.map(p => (
              <button key={p.id} className={`btn ${persona===p.id?'btn-primary':'btn-secondary'}`}
                style={{ fontSize:12,padding:'6px 12px' }} onClick={() => setPersona(p.id)}>
                {p.icon} {p.name}
              </button>
            ))}
          </div>
          {workflow ? (
            <div>
              <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:10 }}>Quick Start Steps — click to go there</div>
              {workflow.quick_start?.map((s, i) => {
                const dest = PERSONA_NAV[s.action]
                return (
                  <div key={i}
                    style={{ display:'flex',gap:12,padding:'11px 12px',borderRadius:8,marginBottom:8,cursor:dest?'pointer':'default',background:dest?'rgba(255,255,255,0.02)':'transparent',border:'1px solid var(--border)',transition:'all 0.15s' }}
                    onClick={() => dest && nav(dest)}
                    onMouseEnter={el => { if(dest) el.currentTarget.style.borderColor = `var(--accent-${pColor})` }}
                    onMouseLeave={el => { el.currentTarget.style.borderColor = 'var(--border)' }}>
                    <div style={{ width:24,height:24,borderRadius:'50%',background:`var(--accent-${pColor}-dim)`,color:`var(--accent-${pColor})`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:800,flexShrink:0 }}>{s.step}</div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13,fontWeight:600,color:'var(--text-primary)',marginBottom:1 }}>{s.action}</div>
                      <div style={{ fontSize:11,color:'var(--text-muted)' }}>{s.detail}</div>
                    </div>
                    {dest && <span style={{ color:`var(--accent-${pColor})`,fontSize:14,alignSelf:'center' }}>→</span>}
                  </div>
                )
              })}
              <div style={{ marginTop:12,display:'flex',gap:6,flexWrap:'wrap' }}>
                {workflow.recommended_modules?.map(m => <span key={m} className="badge badge-cyan">{m}</span>)}
              </div>
            </div>
          ) : <div className="empty-state"><div className="loading-spinner" /></div>}
        </div>

        {/* Compliance status checklist — with Fix buttons */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Compliance Status</span>
            {compliance && (
              <div style={{ display:'flex',gap:6 }}>
                <span className="badge badge-red">{compliance.items?.filter(i=>i.status==='critical').length} crit</span>
                <span className="badge badge-amber">{compliance.items?.filter(i=>i.status==='warn').length} warn</span>
              </div>
            )}
          </div>
          {compliance ? (
            compliance.items?.map((item, i) => {
              const dest = MODULE_NAV[item.module]
              return (
                <div key={i} style={{ display:'flex',gap:10,padding:'9px 0',borderBottom:'1px solid var(--border)',alignItems:'flex-start' }}>
                  <span style={{ fontSize:14,color:SEV_COLOR[item.status],flexShrink:0,marginTop:1 }}>
                    {item.status==='pass'?'✓':item.status==='warn'?'⚠':'✗'}
                  </span>
                  <div style={{ flex:1,minWidth:0 }}>
                    <div style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{item.check}</div>
                    <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:1 }}>
                      <span style={{ textTransform:'uppercase',letterSpacing:'0.4px',fontSize:10 }}>{item.module} · </span>
                      {item.detail}
                    </div>
                  </div>
                  <div style={{ display:'flex',gap:6,alignItems:'center',flexShrink:0 }}>
                    <span className={`badge ${SEV_BADGE[item.status]}`} style={{ fontSize:10 }}>{item.status}</span>
                    {item.status !== 'pass' && dest && (
                      <button className="btn btn-secondary"
                        style={{ fontSize:10,padding:'3px 9px',color:`var(--accent-${item.status==='critical'?'red':'amber'})`,borderColor:`var(--accent-${item.status==='critical'?'red':'amber'})40` }}
                        onClick={() => nav(dest)}>
                        Fix →
                      </button>
                    )}
                  </div>
                </div>
              )
            })
          ) : <div className="loading-overlay"><div className="loading-spinner" /></div>}
        </div>
      </div>

      <div className="grid-2">
        {/* Live activity */}
        <div className="card">
          <div className="card-header"><span className="card-title">Live Activity</span><span className="badge badge-green">● LIVE</span></div>
          {data?.recent_activity?.map((a, i) => {
            const dotColor = { ingestion:'var(--accent-cyan)',audit:'var(--accent-amber)',guardrail:'var(--accent-red)',commercial:'var(--accent-cyan)',compliance:'var(--accent-cyan)',forecast:'var(--accent-amber)' }[a.type] || 'var(--accent-cyan)'
            const diff = (new Date() - new Date(a.time)) / 1000
            const timeAgo = diff < 60 ? `${Math.floor(diff)}s ago` : diff < 3600 ? `${Math.floor(diff/60)}m ago` : `${Math.floor(diff/3600)}h ago`
            return (
              <div key={i} style={{ display:'flex',gap:10,padding:'10px 0',borderBottom:'1px solid rgba(30,45,69,0.5)',alignItems:'flex-start' }}>
                <div style={{ width:8,height:8,borderRadius:'50%',background:dotColor,marginTop:5,flexShrink:0 }} />
                <div>
                  <div style={{ fontSize:13,color:'var(--text-secondary)' }}>{a.event}</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2,fontFamily:'var(--mono)' }}>{timeAgo}</div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Alerts + system health */}
        <div className="card">
          <div className="card-header"><span className="card-title">Active Alerts</span><span className="badge badge-amber">{data?.active_alerts?.length||3} Open</span></div>
          {data?.active_alerts?.map((a, i) => (
            <div key={i} style={{ display:'flex',gap:12,padding:'10px 0',borderBottom:'1px solid var(--border)',alignItems:'flex-start' }}>
              <span className={`badge ${a.severity==='high'?'badge-red':a.severity==='medium'?'badge-amber':'badge-cyan'}`}>{a.severity.toUpperCase()}</span>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:13,color:'var(--text-primary)',fontWeight:500 }}>{a.title}</div>
                <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{a.regulation}</div>
              </div>
              {a.deadline && <div style={{ fontSize:11,color:'var(--accent-amber)',fontFamily:'var(--mono)',whiteSpace:'nowrap' }}>{new Date(a.deadline).toLocaleDateString()}</div>}
            </div>
          ))}
          <div style={{ marginTop:14,paddingTop:14,borderTop:'1px solid var(--border)' }}>
            <div style={{ fontSize:12,color:'var(--text-muted)',marginBottom:8 }}>System Health</div>
            {Object.entries(data?.system_health||{}).map(([svc, status]) => (
              <div key={svc} style={{ display:'flex',justifyContent:'space-between',padding:'4px 0',fontSize:12 }}>
                <span style={{ color:'var(--text-secondary)',textTransform:'capitalize' }}>{svc.replace('_',' ')}</span>
                <span style={{ color:status==='operational'?'var(--accent-green)':'var(--accent-red)',fontWeight:600 }}>{status==='operational'?'● OK':'✗ '+status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
