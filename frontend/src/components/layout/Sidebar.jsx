export default function Sidebar({ activePage, onNavigate, isOpen }) {
  const navItems = [
    { id:'dashboard',     icon:'⬡', label:'Overview',              section:'platform' },
    { id:'onboarding',    icon:'🚀', label:'Onboarding',            section:'platform' },
    { id:'mvp1',          icon:'◈', label:'Ingestion & Forecast',   section:'modules' },
    { id:'mvp2',          icon:'◉', label:'Audit & Compliance',     section:'modules' },
    { id:'mvp3',          icon:'◎', label:'Enterprise',             section:'modules' },
    { id:'mvp4',          icon:'◐', label:'Agentic Guardrails',     section:'modules' },
    { id:'mvp5',          icon:'◆', label:'Autonomous Governance',  section:'modules' },
    { id:'modelchecker',  icon:'🔍', label:'Model Output Checker',  section:'intelligence', isNew:true },
    { id:'policies',      icon:'📋', label:'Policy Library',        section:'intelligence' },
    { id:'feed',          icon:'📡', label:'Regulatory Feed',       section:'intelligence' },
    { id:'reports',       icon:'📊', label:'Audit Reports',         section:'intelligence' },
  ]

  const sections = [
    { key:'platform',     label:'Platform' },
    { key:'modules',      label:'Modules' },
    { key:'intelligence', label:'Intelligence' },
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
      <nav className="sidebar-nav">
        {sections.map(section => {
          const items = navItems.filter(i => i.section === section.key)
          return (
            <div key={section.key} className="nav-section">
              <div className="nav-section-label">{section.label}</div>
              {items.map(item => (
                <div key={item.id} className={`nav-item ${activePage===item.id?'active':''}`} onClick={() => onNavigate(item.id)}>
                  <span className="nav-item-icon">{item.icon}</span>
                  <span style={{ flex:1 }}>{item.label}</span>
                  {item.isNew && <span style={{ fontSize:9,fontWeight:700,color:'var(--accent-cyan)',background:'var(--accent-cyan-dim)',padding:'2px 5px',borderRadius:3 }}>NEW</span>}
                </div>
              ))}
            </div>
          )
        })}
      </nav>
      <div className="sidebar-footer">
        <div className="system-status"><div className="status-dot" /><span>All systems operational</span></div>
        <div style={{ marginTop:8,fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>v5.1.0 · 963 tests passed</div>
      </div>
    </aside>
  )
}
