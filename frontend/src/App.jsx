import { useState, useEffect } from 'react'
import { PersonaProvider, usePersona } from './hooks/PersonaContext'
import { ScreenGate } from './components/PersonaGate'
import Login             from './pages/Login'
import Dashboard         from './pages/Dashboard'
import MVP1Ingestion     from './pages/MVP1Ingestion'
import MVP2Audit         from './pages/MVP2Audit'
import MVP3Enterprise    from './pages/MVP3Enterprise'
import MVP4Agentic       from './pages/MVP4Agentic'
import MVP5Autonomous    from './pages/MVP5Autonomous'
import AuditFlow         from './pages/AuditFlow'
import ModelOutputChecker from './pages/ModelOutputChecker'
import PolicyLibrary     from './pages/PolicyLibrary'
import FeedLog           from './pages/FeedLog'
import AuditReports      from './pages/AuditReports'
import Onboarding        from './pages/Onboarding'
import PolicyChat           from './pages/PolicyChat'
import Gateway              from './pages/Gateway'
import StandardsExplorer    from './pages/StandardsExplorer'
import PlatformHealth       from './pages/PlatformHealth'
import Sidebar           from './components/layout/Sidebar'
import Header            from './components/layout/Header'
import './App.css'

// ── Page registry with persona screen mapping ─────────────────────
// "screen" ties each page to a persona screen ID from PersonaContext.
// If screen is null, the page is accessible to everyone.
const PAGES = {
  dashboard:       { component: Dashboard,          screen: 'dashboard' },
  onboarding:      { component: Onboarding,         screen: 'onboarding' },
  mvp1:            { component: MVP1Ingestion,       screen: 'mvp1' },
  mvp2:            { component: MVP2Audit,           screen: 'auditflow' },
  mvp3:            { component: MVP3Enterprise,      screen: 'mvp4' },
  mvp4:            { component: MVP4Agentic,         screen: 'mvp4' },
  mvp5:            { component: MVP5Autonomous,      screen: 'mvp4' },
  auditflow:       { component: AuditFlow,           screen: 'auditflow' },
  modelchecker:    { component: ModelOutputChecker,   screen: 'auditflow' },
  policies:        { component: PolicyLibrary,        screen: 'mvp4' },
  feed:            { component: FeedLog,              screen: 'mvp1' },
  reports:         { component: AuditReports,         screen: 'reports' },
  policychat:      { component: PolicyChat,           screen: 'ethics' },
  gateway:         { component: Gateway,              screen: 'dashboard' },
  standards:       { component: StandardsExplorer,    screen: 'compliance-map' },
  platformhealth:  { component: PlatformHealth,       screen: null },
}

export default function App() {
  return (
    <PersonaProvider>
      <AppShell />
    </PersonaProvider>
  )
}

function AppShell() {
  const { personaDef } = usePersona()
  const [session, setSession]     = useState(null)
  const [activePage, setActivePage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sessionLoaded, setSessionLoaded] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('saro_session')
    if (stored) {
      try { setSession(JSON.parse(stored)) } catch(e) {}
    }
    setSessionLoaded(true)
    const params = new URLSearchParams(window.location.search)
    if (params.get('token')) {
      setSession(null)
      setSessionLoaded(true)
    }
  }, [])

  const handleLogin = (sessionData) => {
    setSession(sessionData)
    const defaultPage = personaDef?.defaultPage || sessionData.default_page
    if (defaultPage && PAGES[defaultPage]) {
      setActivePage(defaultPage)
    }
    window.history.replaceState({}, '', window.location.pathname)
  }

  const handleLogout = () => {
    localStorage.removeItem('saro_session')
    setSession(null)
    setActivePage('dashboard')
  }

  if (!sessionLoaded) {
    return <div className="loading-overlay"><div className="loading-spinner" /><span>Loading SARO...</span></div>
  }

  if (!session) {
    return <Login onLogin={handleLogin} />
  }

  const pageEntry = PAGES[activePage] || PAGES.dashboard
  const PageComponent = pageEntry.component
  const screenId = pageEntry.screen
  const apiUrl = window.SARO_CONFIG?.apiUrl

  return (
    <div className="app-shell">
      {!apiUrl && (
        <div style={{ position:'fixed',top:0,left:0,right:0,zIndex:9999,background:'#ff3d6a',color:'#fff',padding:'10px 20px',fontSize:13,fontWeight:600,textAlign:'center' }}>
          API not configured - edit frontend/public/config.js - set apiUrl - redeploy
        </div>
      )}
      <Sidebar activePage={activePage} onNavigate={setActivePage} isOpen={sidebarOpen} session={session} />
      <div className={`main-area ${sidebarOpen?'sidebar-open':''}`}>
        <Header onToggleSidebar={() => setSidebarOpen(s => !s)} activePage={activePage} session={session} onLogout={handleLogout} />
        <main className="page-content" style={!apiUrl?{paddingTop:60}:{}}>
          {screenId ? (
            <ScreenGate screen={screenId}>
              <PageComponent onNavigate={setActivePage} session={session} />
            </ScreenGate>
          ) : (
            <PageComponent onNavigate={setActivePage} session={session} />
          )}
        </main>
      </div>
    </div>
  )
}
