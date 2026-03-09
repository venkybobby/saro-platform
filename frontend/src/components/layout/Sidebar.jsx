import { usePersona } from '../../hooks/PersonaContext'

const PERSONA_COLORS = { forecaster:'cyan', autopsier:'amber', enabler:'green', evangelist:'purple' }

// ── Nav sections with screen IDs for persona gating ───────────────
// Each item has a "screen" that maps to PERSONA_SCREENS in PersonaContext.
// If screen is null, the item is visible to everyone.
const SECTIONS = [
  {
    key: 'platform', label: 'Platform',
    items: [
      { id:'dashboard',   icon:'\u{1F4CA}', label:'Overview',     screen:'dashboard' },
      { id:'gateway',     icon:'\u26A1',     label:'Gateway',      screen:'dashboard',  isNew:true },
      { id:'onboarding',  icon:'\u{1F680}',  label:'Onboarding',   screen:'onboarding' },
    ]
  },
  {
    key: 'modules', label: 'Modules',
    items: [
      { id:'mvp1',  icon:'\u{1F4C8}', label:'Ingestion & Forecast', screen:'mvp1' },
      { id:'mvp2',  icon:'\u{1F50D}', label:'Audit & Compliance',   screen:'auditflow' },
      { id:'mvp3',  icon:'\u{1F3E2}', label:'Enterprise',           screen:'mvp4' },
      { id:'mvp4',  icon:'\u2699\uFE0F', label:'Agentic Guardrails',screen:'mvp4' },
      { id:'mvp5',  icon:'\u{1F916}', label:'Autonomous Governance', screen:'mvp4' },
    ]
  },
  {
    key: 'intelligence', label: 'Intelligence',
    items: [
      { id:'auditflow',    icon:'\u26A1',     label:'Audit Flow',            screen:'auditflow' },
      { id:'modelchecker', icon:'\u{1F50C}',  label:'Model Output Checker',  screen:'auditflow' },
      { id:'standards',    icon:'\u{1F4D6}',  label:'Standards Explorer',     screen:'compliance-map', isNew:true },
      { id:'policies',     icon:'\u{1F4CB}',  label:'Policy Library',         screen:'mvp4' },
      { id:'feed',         icon:'\u{1F4E1}',  label:'Regulatory Feed',        screen:'mvp1' },
      { id:'reports',      icon:'\u{1F4CA}',  label:'Audit Reports',          screen:'reports' },
    ]
  },
  {
    key: 'ai', label: 'AI Tools',
    items: [
      { id:'policychat',  icon:'\u{1F4AC}', label:'Policy Chat Agent', screen:'ethics', isNew:true },
    ]
  },
  {
    key: 'ops', label: 'Operations',
    items: [
      { id:'platformhealth', icon:'\u{1F4CA}', label:'Platform Health', screen:null, isNew:true },
    ]
  },
]

export default function Sidebar({ activePage, onNavigate, isOpen, session }) {
  const { canAccessScreen, persona, personaDef, roles, switchRole, PERSONA_SCREENS } = usePersona()
  const pColor = PERSONA_COLORS[session?.persona] || 'cyan'

  // Filter sections: only show items the persona can access
  const filteredSections = SECTIONS.map(section => ({
    ...section,
    items: section.items.filter(item =>
      item.screen === null || canAccessScreen(item.screen)
    ),
  })).filter(section => section.items.length > 0)

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
        <div style={{ margin:'0 12px 8px',padding:'10px 12px',borderRadius:8,background:`var(--accent-${pColor}-dim)`,border:`1px solid rgba(${pColor==='cyan'?'0,212,255':pColor==='amber'?'255,184,0':pColor==='green'?'0,255,136':'139,92,246'},0.2)` }}>
          <div style={{ fontSize:12,fontWeight:700,color:`var(--accent-${pColor})` }}>
            {session.persona_icon} {session.persona_name}
          </div>
          <div style={{ fontSize:10,color:'var(--text-muted)',marginTop:1 }}>
            {session.email?.split('@')[0]} &middot; {session.is_trial?'Trial':'Full Access'}
          </div>
        </div>
      )}

      {/* Multi-role switcher — only shows if user has 2+ roles */}
      {roles && roles.length > 1 && (
        <div style={{ margin:'0 12px 12px',padding:'8px',borderRadius:6,background:'rgba(255,255,255,0.03)',border:'1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize:9,fontWeight:700,textTransform:'uppercase',letterSpacing:'0.5px',color:'var(--text-muted)',marginBottom:6 }}>
            Switch Role
          </div>
          <div style={{ display:'flex',flexWrap:'wrap',gap:4 }}>
            {roles.map(role => {
              const def = PERSONA_SCREENS?.[role]
              if (!def) return null
              const isActive = role === persona
              return (
                <button
                  key={role}
                  onClick={() => {
                    switchRole(role)
                    if (def.defaultPage) onNavigate(def.defaultPage)
                  }}
                  style={{
                    fontSize:10, padding:'3px 8px', borderRadius:12, cursor:'pointer',
                    border: isActive ? `1px solid ${def.color}` : '1px solid rgba(255,255,255,0.1)',
                    background: isActive ? `${def.color}22` : 'transparent',
                    color: def.color,
                    opacity: isActive ? 1 : 0.5,
                    transition: 'all 0.2s',
                  }}
                >
                  {def.icon} {def.label}
                </button>
              )
            })}
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {filteredSections.map(section => (
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
        <div style={{ marginTop:8,fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>v8.0.0 &middot; Persona RBAC Active</div>
      </div>
    </aside>
  )
}
