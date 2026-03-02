const PERSONA_COLORS = { forecaster:'cyan', autopsier:'amber', enabler:'green', evangelist:'purple' }

export default function Sidebar({ activePage, onNavigate, isOpen, session }) {
  const pColor = PERSONA_COLORS[session?.persona] || 'cyan'

  const sections = [
    {
      key: 'platform', label: 'Platform',
      items: [
        { id:'dashboard',   icon:'⬡', label:'Overview' },
        { id:'gateway',     icon:'⚡', label:'Gateway',    isNew:true },
        { id:'onboarding',  icon:'🚀', label:'Onboarding' },
      ]
    },
    {
      key: 'modules', label: 'Modules',
      items: [
        { id:'mvp1',  icon:'◈', label:'Ingestion & Forecast' },
        { id:'mvp2',  icon:'◉', label:'Audit & Compliance' },
        { id:'mvp3',  icon:'◎', label:'Enterprise' },
        { id:'mvp4',  icon:'◐', label:'Agentic Guardrails' },
        { id:'mvp5',  icon:'◆', label:'Autonomous Governance' },
      ]
    },
    {
      key: 'intelligence', label: 'Intelligence',
      items: [
        { id:'auditflow',    icon:'⚡', label:'Audit Flow' },
        { id:'modelchecker', icon:'🔍', label:'Model Output Checker' },
        { id:'policies',     icon:'📋', label:'Policy Library' },
        { id:'feed',         icon:'📡', label:'Regulatory Feed' },
        { id:'reports',      icon:'📊', label:'Audit Reports' },
      ]
    },
    {
      key: 'ai', label: 'AI Tools',
      items: [
        { id:'policychat', icon:'💬', label:'Policy Chat Agent', isNew:true },
      ]
    },
  ]

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="logo-badge">
          <div className="logo-icon">S</div>
          <div>
            <div className="logo-text">SARO</div>
            <div className="logo-sub">AI Regulatory Intel</div>
          </div>
        </div>
      </div>

      {/* Persona badge */}
      {session?.persona && (
        <div style={{ margin:'0 12px 16px',padding:'10px 12px',borderRadius:8,background:`var(--accent-${pColor}-dim)`,border:`1px solid rgba(${pColor==='cyan'?'0,212,255':pColor==='amber'?'255,184,0':pColor==='green'?'0,255,136':'139,92,246'},0.2)` }}>
          <div style={{ fontSize:12,fontWeight:700,color:`var(--accent-${pColor})` }}>
            {session.persona_icon} {session.persona_name}
          </div>
          <div style={{ fontSize:10,color:'var(--text-muted)',marginTop:1 }}>
            {session.email?.split('@')[0]} · {session.is_trial?'Trial':'Full Access'}
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {sections.map(section => (
          <div key={section.key} className="nav-section">
            <div className="nav-section-label">{section.label}</div>
            {section.items.map(item => (
              <div key={item.id} className={`nav-item ${activePage===item.id?'active':''}`} onClick={() => onNavigate(item.id)}>
                <span className="nav-item-icon">{item.icon}</span>
                <span style={{ flex:1 }}>{item.label}</span>
                {item.isNew && (
                  <span style={{ fontSize:9,fontWeight:700,color:'var(--accent-cyan)',background:'var(--accent-cyan-dim)',padding:'2px 5px',borderRadius:3,letterSpacing:'0.3px' }}>NEW</span>
                )}
              </div>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status"><div className="status-dot" /><span>All systems operational</span></div>
        <div style={{ marginTop:8,fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>v6.0.0 · 963 tests passed</div>
      </div>
    </aside>
  )
}
