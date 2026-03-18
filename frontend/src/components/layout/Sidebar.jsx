/**
 * SARO v9.1 Sidebar — Two-role clean nav
 * - Admin: sees Setup Hub + all platform items
 * - Operator: sees all platform items
 * - No persona switcher, no role-switcher dropdown
 */
import { usePersona } from '../../hooks/PersonaContext'

// All platform nav items — operator sees all; admin additionally sees Setup Hub
const OPERATOR_SECTIONS = [
  {
    key: 'platform', label: 'Platform',
    items: [
      { id:'dashboard',      icon:'📊', label:'Overview',            screen: null },
      { id:'gateway',        icon:'⚡', label:'Gateway',             screen: null, isNew: true },
      { id:'onboarding',     icon:'🚀', label:'Onboarding',          screen: null },
    ],
  },
  {
    key: 'modules', label: 'Modules',
    items: [
      { id:'mvp1',  icon:'📈', label:'Ingestion & Forecast',  screen: null },
      { id:'mvp2',  icon:'🔍', label:'Audit & Compliance',    screen: null },
      { id:'mvp3',  icon:'🏢', label:'Enterprise',            screen: null },
      { id:'mvp4',  icon:'⚙️', label:'Agentic Guardrails',    screen: null },
      { id:'mvp5',  icon:'🤖', label:'Autonomous Governance', screen: null },
    ],
  },
  {
    key: 'intelligence', label: 'Intelligence',
    items: [
      { id:'auditflow',           icon:'⚡', label:'Audit Flow',           screen: null },
      { id:'modelchecker',        icon:'🔌', label:'Model Output Checker', screen: null },
      { id:'policy-intelligence', icon:'💬', label:'Policy Intelligence',  screen: null, isNew: true },
      { id:'feed',                icon:'📡', label:'Regulatory Feed',      screen: null },
      { id:'reports',             icon:'📊', label:'Audit Reports',        screen: null },
    ],
  },
  {
    key: 'ops', label: 'Operations',
    items: [
      { id:'platformhealth', icon:'📈', label:'Platform Health', screen: null },
    ],
  },
]

const ADMIN_SECTION = {
  key: 'admin', label: 'Admin',
  items: [
    { id:'admin-hub', icon:'🔧', label:'Setup Hub',     screen: null, isAdmin: true },
  ],
}

export default function Sidebar({ activePage, onNavigate, isOpen, session }) {
  const { userRole } = usePersona()
  const isAdmin = userRole === 'admin' || session?.role === 'admin' || session?.is_admin

  // Admin gets Setup Hub section prepended
  const sections = isAdmin
    ? [ADMIN_SECTION, ...OPERATOR_SECTIONS]
    : OPERATOR_SECTIONS

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

      {/* Simple role badge — admin or operator, no persona icons */}
      {session && (
        <div style={{
          margin: '0 12px 12px',
          padding: '10px 12px',
          borderRadius: 8,
          background: isAdmin ? 'rgba(168,85,247,0.1)' : 'rgba(0,212,255,0.08)',
          border: `1px solid ${isAdmin ? 'rgba(168,85,247,0.3)' : 'rgba(0,212,255,0.2)'}`,
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: isAdmin ? 'var(--accent-purple)' : 'var(--accent-cyan)' }}>
            {isAdmin ? '🔧 Super Admin' : '👤 Operator'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>
            {session.email?.split('@')[0]} · {session.is_trial ? 'Trial' : 'Full Access'}
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {sections.map(section => (
          <div key={section.key} className="nav-section">
            <div className="nav-section-label">{section.label}</div>
            {section.items.map(item => (
              <div
                key={item.id}
                className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                onClick={() => onNavigate(item.id)}
                style={item.isAdmin ? { borderLeft: '2px solid var(--accent-purple)' } : {}}
              >
                <span className="nav-item-icon">{item.icon}</span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.isNew && (
                  <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--accent-cyan)', background: 'var(--accent-cyan-dim)', padding: '2px 5px', borderRadius: 3 }}>
                    NEW
                  </span>
                )}
                {item.isAdmin && (
                  <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--accent-purple)', background: 'rgba(168,85,247,0.12)', padding: '2px 5px', borderRadius: 3 }}>
                    ADMIN
                  </span>
                )}
              </div>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status"><div className="status-dot" /><span>All systems operational</span></div>
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>
          v9.1.0 · {isAdmin ? 'Admin' : 'Operator'} Mode
        </div>
      </div>
    </aside>
  )
}
