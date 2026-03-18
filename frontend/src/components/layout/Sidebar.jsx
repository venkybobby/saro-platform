/**
 * SARO v9.2 Sidebar — Clean 4-item operator nav + 1-item admin nav
 *
 * Operator: Overview | Upload & Analyze | Audits & Reports | Policy Intelligence
 * Admin:    Setup Hub only (Switch to Operator View is in AdminHub)
 *
 * No personas, no sections, no role-switcher.
 */
import { usePersona } from '../../hooks/PersonaContext'

const OPERATOR_NAV = [
  { id:'dashboard',           icon:'📊', label:'Overview' },
  { id:'upload',              icon:'📤', label:'Upload & Analyze' },
  { id:'reports',             icon:'📋', label:'Audits & Reports' },
  { id:'policy-intelligence', icon:'💬', label:'Policy Intelligence' },
]

const ADMIN_NAV = [
  { id:'admin-hub', icon:'🔧', label:'Setup Hub', isAdmin: true },
]

export default function Sidebar({ activePage, onNavigate, isOpen, session }) {
  const { userRole } = usePersona()
  const isAdmin = userRole === 'admin' || session?.role === 'admin' || session?.is_admin

  const nav = isAdmin ? ADMIN_NAV : OPERATOR_NAV

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="logo-badge">
          <div className="logo-icon">S</div>
          <div>
            <div className="logo-text">SARO</div>
            <div className="logo-sub">AI Governance in One Flow</div>
          </div>
        </div>
      </div>

      {/* Role badge */}
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
        <div className="nav-section">
          {nav.map(item => (
            <div
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              style={item.isAdmin ? { borderLeft: '2px solid var(--accent-purple)' } : {}}
            >
              <span className="nav-item-icon">{item.icon}</span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.isAdmin && (
                <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--accent-purple)', background: 'rgba(168,85,247,0.12)', padding: '2px 5px', borderRadius: 3 }}>
                  ADMIN
                </span>
              )}
            </div>
          ))}
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="system-status"><div className="status-dot" /><span>All systems operational</span></div>
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>
          v9.2.0 · {isAdmin ? 'Admin' : 'Operator'}
        </div>
      </div>
    </aside>
  )
}
