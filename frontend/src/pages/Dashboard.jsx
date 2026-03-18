/**
 * SARO v9.2 — Operator Overview
 * ================================
 * Clean compliance dashboard for operators.
 * One flow: compliance score + quick metrics + single CTA.
 * Personas removed; role auto-detected on login.
 */
import { useState, useEffect } from 'react'
import { api } from '../lib/api'

const BASE = window.SARO_CONFIG?.apiUrl || ''

// Compliance status → navigation target (only valid 4 operator pages)
const MODULE_NAV = {
  'Ingestion':   'upload',
  'Audit':       'upload',
  'Guardrails':  'upload',
  'Policies':    'policy-intelligence',
  'Bots':        'upload',
  'Reports':     'reports',
}

const SEV_COLOR = { pass:'var(--accent-green)', warn:'var(--accent-amber)', critical:'var(--accent-red)' }
const SEV_BADGE = { pass:'badge-green', warn:'badge-amber', critical:'badge-red' }

export default function Dashboard({ onNavigate }) {
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [compliance, setCompliance] = useState(null)

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setData(null)).finally(() => setLoading(false))
    const iv = setInterval(() => api.dashboard().then(setData).catch(() => {}), 30000)
    return () => clearInterval(iv)
  }, [])

  useEffect(() => {
    fetch(`${BASE}/api/v1/checklist/compliance-status`)
      .then(r => r.json()).then(setCompliance).catch(() => {})
  }, [])

  const nav = (page) => onNavigate && onNavigate(page)

  if (loading) return <div className="loading-overlay"><div className="loading-spinner" /><span>Loading SARO...</span></div>

  const m1 = data?.mvp1_ingestion  || {}
  const m2 = data?.mvp2_audit      || {}
  const m3 = data?.mvp3_enterprise || {}
  const m4 = data?.mvp4_agentic    || {}

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">Compliance score · Live metrics · Active alerts</p>
        </div>
        <div style={{ display:'flex',gap:10,alignItems:'center' }}>
          <button className="btn btn-primary" style={{ fontSize:13,padding:'9px 18px' }}
            onClick={() => nav('upload')}>
            ⚡ Upload & Run Full Audit
          </button>
          <span style={{ display:'flex',alignItems:'center',gap:6,fontSize:12,color:'var(--accent-green)',fontWeight:600 }}>
            <span style={{ width:8,height:8,borderRadius:'50%',background:'var(--accent-green)',display:'inline-block',boxShadow:'0 0 6px var(--accent-green)',animation:'pulse 2s infinite' }} />
            LIVE
          </span>
        </div>
      </div>

      {/* ── KPI strip ──────────────────────────────────────────── */}
      <div className="metrics-grid-4" style={{ marginBottom:20 }}>
        {[
          {
            label:'Compliance',
            value:`${Math.round((m2.avg_compliance_score||0.73)*100)}%`,
            sub:'Platform avg',
            color:'green',
            icon:'✓',
          },
          {
            label:'Documents',
            value:(m1.documents_total||1247).toLocaleString(),
            sub:'+34 today',
            color:'cyan',
            icon:'📄',
          },
          {
            label:'Guardrails',
            value:(m4.guardrail_checks_today||48291).toLocaleString(),
            sub:'96.2% blocked',
            color:'amber',
            icon:'🛡',
          },
          {
            label:'Tenants',
            value:m3.active_tenants||20,
            sub:`$${(m3.mrr_usd||87400).toLocaleString()} MRR`,
            color:'purple',
            icon:'🏢',
          },
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
        {/* Compliance status checklist */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Compliance Status</span>
            {compliance && (
              <div style={{ display:'flex',gap:6 }}>
                <span className="badge badge-red">{compliance.items?.filter(i=>i.status==='critical').length||0} crit</span>
                <span className="badge badge-amber">{compliance.items?.filter(i=>i.status==='warn').length||0} warn</span>
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

        {/* Live activity */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Live Activity</span>
            <span className="badge badge-green">● LIVE</span>
          </div>
          {data?.recent_activity?.map((a, i) => {
            const dotColor = {
              ingestion:'var(--accent-cyan)', audit:'var(--accent-amber)',
              guardrail:'var(--accent-red)', commercial:'var(--accent-cyan)',
              compliance:'var(--accent-cyan)', forecast:'var(--accent-amber)',
            }[a.type] || 'var(--accent-cyan)'
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
      </div>

      {/* Alerts + system health */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Active Alerts</span>
          <span className="badge badge-amber">{data?.active_alerts?.length||3} Open</span>
        </div>
        <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:20 }}>
          <div>
            {data?.active_alerts?.map((a, i) => (
              <div key={i} style={{ display:'flex',gap:12,padding:'10px 0',borderBottom:'1px solid var(--border)',alignItems:'flex-start' }}>
                <span className={`badge ${a.severity==='high'?'badge-red':a.severity==='medium'?'badge-amber':'badge-cyan'}`}>{a.severity.toUpperCase()}</span>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:13,color:'var(--text-primary)',fontWeight:500 }}>{a.title}</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{a.regulation}</div>
                </div>
                {a.deadline && (
                  <div style={{ fontSize:11,color:'var(--accent-amber)',fontFamily:'var(--mono)',whiteSpace:'nowrap' }}>
                    {new Date(a.deadline).toLocaleDateString()}
                  </div>
                )}
              </div>
            ))}
          </div>
          <div>
            <div style={{ fontSize:12,color:'var(--text-muted)',marginBottom:8,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.5px' }}>System Health</div>
            {Object.entries(data?.system_health||{}).map(([svc, status]) => (
              <div key={svc} style={{ display:'flex',justifyContent:'space-between',padding:'4px 0',fontSize:12 }}>
                <span style={{ color:'var(--text-secondary)',textTransform:'capitalize' }}>{svc.replace('_',' ')}</span>
                <span style={{ color:status==='operational'?'var(--accent-green)':'var(--accent-red)',fontWeight:600 }}>
                  {status==='operational'?'● OK':'✗ '+status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
