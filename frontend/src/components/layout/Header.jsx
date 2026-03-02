import { useState, useEffect } from 'react'

const PAGE_LABELS = {
  dashboard:    'Overview Dashboard',
  onboarding:   'Client Onboarding',
  mvp1:         'Ingestion & Forecast',
  mvp2:         'Audit & Compliance',
  mvp3:         'Enterprise',
  mvp4:         'Agentic Guardrails',
  mvp5:         'Autonomous Governance',
  auditflow:    'Audit Flow',
  modelchecker: 'Model Output Checker',
  policies:     'Policy Library',
  feed:         'Regulatory Feed',
  reports:      'Audit Reports',
  policychat:   'AI Policy Chat',
  gateway:      'Gateway & Orchestrator',
}

const PERSONA_COLORS = { forecaster:'cyan', autopsier:'amber', enabler:'green', evangelist:'purple' }

export default function Header({ onToggleSidebar, activePage, session, onLogout }) {
  const [time, setTime] = useState(new Date())
  const [showUser, setShowUser] = useState(false)

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const pColor = PERSONA_COLORS[session?.persona] || 'cyan'
  const initials = session?.email?.slice(0,2).toUpperCase() || 'AD'

  return (
    <header className="header">
      <button className="header-toggle" onClick={onToggleSidebar}>☰</button>
      <div className="header-breadcrumb">
        SARO / <strong>{PAGE_LABELS[activePage] || activePage}</strong>
      </div>
      <div className="header-spacer" />
      <div className="header-pills">
        {session?.persona && (
          <span style={{ fontSize:11,fontWeight:700,padding:'3px 10px',borderRadius:20,background:`var(--accent-${pColor}-dim)`,color:`var(--accent-${pColor})`,border:`1px solid ${`var(--accent-${pColor})`}30` }}>
            {session.persona_icon || '⚙️'} {session.persona_name || session.persona}
          </span>
        )}
        {session?.is_trial && (
          <span style={{ fontSize:10,fontWeight:700,padding:'3px 8px',borderRadius:20,background:'rgba(255,184,0,0.1)',color:'var(--accent-amber)',border:'1px solid rgba(255,184,0,0.3)' }}>
            TRIAL
          </span>
        )}
        <span className="pill pill-green">● LIVE</span>
        <span className="pill pill-cyan" style={{ fontFamily:'var(--mono)',fontSize:11 }}>
          {time.toLocaleTimeString()}
        </span>
      </div>
      <div style={{ position:'relative' }}>
        <div className="header-avatar" style={{ cursor:'pointer',background:`var(--accent-${pColor}-dim)`,color:`var(--accent-${pColor})`,border:`1px solid ${`var(--accent-${pColor})`}40` }}
          onClick={() => setShowUser(s => !s)}>
          {initials}
        </div>
        {showUser && (
          <div style={{ position:'absolute',right:0,top:44,width:220,background:'var(--bg-card)',border:'1px solid var(--border)',borderRadius:10,padding:'12px 14px',boxShadow:'0 8px 24px rgba(0,0,0,0.4)',zIndex:1000 }}>
            <div style={{ fontSize:12,fontWeight:700,color:'var(--text-primary)',marginBottom:2 }}>{session?.email || 'Demo User'}</div>
            <div style={{ fontSize:10,color:'var(--text-muted)',marginBottom:2 }}>Tenant: {session?.tenant_id || 'DEMO'}</div>
            <div style={{ fontSize:10,color:`var(--accent-${pColor})`,fontWeight:600,marginBottom:12 }}>
              {session?.persona_icon} {session?.persona_name || session?.persona}
              {session?.is_trial && <span style={{ color:'var(--accent-amber)',marginLeft:6 }}>· Trial</span>}
            </div>
            <button className="btn btn-secondary" style={{ width:'100%',justifyContent:'center',fontSize:12,color:'var(--accent-red)',borderColor:'rgba(255,61,106,0.3)' }}
              onClick={() => { setShowUser(false); onLogout && onLogout() }}>
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
