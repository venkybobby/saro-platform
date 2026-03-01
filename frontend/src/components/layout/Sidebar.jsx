export default function Sidebar({ activePage, onNavigate, isOpen }) {
  const navItems = [
    { id: 'dashboard', icon: '⬡', label: 'Overview', section: 'main' },
    { id: 'mvp1', icon: '◈', label: 'Ingestion & Forecast', section: 'mvps', badge: 'MVP1', color: 'cyan' },
    { id: 'mvp2', icon: '◉', label: 'Audit & Compliance', section: 'mvps', badge: 'MVP2', color: 'amber' },
    { id: 'mvp3', icon: '◎', label: 'Enterprise', section: 'mvps', badge: 'MVP3', color: 'purple' },
    { id: 'mvp4', icon: '◐', label: 'Agentic GA', section: 'mvps', badge: 'MVP4', color: 'green' },
    { id: 'mvp5', icon: '◆', label: 'Autonomous Gov', section: 'mvps', badge: 'MVP5', color: 'purple', isNew: true },
  ]

  const sections = [
    { key: 'main', label: 'Platform' },
    { key: 'mvps', label: 'MVP Modules' },
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
                <div
                  key={item.id}
                  className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                  onClick={() => onNavigate(item.id)}
                >
                  <span className="nav-item-icon">{item.icon}</span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.isNew && (
                    <span style={{ fontSize: 9, fontWeight: 700, color: '#8b5cf6', background: 'rgba(139,92,246,0.15)', padding: '2px 5px', borderRadius: 3, marginRight: 4 }}>NEW</span>
                  )}
                  {item.badge && (
                    <span className="nav-mvp-badge">{item.badge}</span>
                  )}
                </div>
              ))}
            </div>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status">
          <div className="status-dot" />
          <span>All systems operational</span>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>
          v5.0.0 · 943 tests passed
        </div>
      </div>
    </aside>
  )
}
