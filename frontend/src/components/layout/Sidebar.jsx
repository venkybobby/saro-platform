export default function Sidebar({ activePage, onNavigate, isOpen }) {
  const sections = [
    {
      key: 'platform', label: 'Platform',
      items: [
        { id:'dashboard',    icon:'⬡', label:'Overview' },
        { id:'onboarding',   icon:'🚀', label:'Onboarding' },
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
        { id:'auditflow',     icon:'⚡', label:'Audit Flow',          isNew:true },
        { id:'modelchecker',  icon:'🔍', label:'Model Output Checker' },
        { id:'policies',      icon:'📋', label:'Policy Library' },
        { id:'feed',          icon:'📡', label:'Regulatory Feed' },
        { id:'reports',       icon:'📊', label:'Audit Reports' },
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
        <div style={{ marginTop:8,fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>v5.2.0 · 963 tests passed</div>
      </div>
    </aside>
  )
}
