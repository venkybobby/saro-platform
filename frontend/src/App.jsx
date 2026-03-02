import { useState, useEffect } from 'react'
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
import PolicyChat        from './pages/PolicyChat'
import Gateway           from './pages/Gateway'
import Sidebar           from './components/layout/Sidebar'
import Header            from './components/layout/Header'
import './App.css'

const PAGES = {
  dashboard:    Dashboard,
  onboarding:   Onboarding,
  mvp1:         MVP1Ingestion,
  mvp2:         MVP2Audit,
  mvp3:         MVP3Enterprise,
  mvp4:         MVP4Agentic,
  mvp5:         MVP5Autonomous,
  auditflow:    AuditFlow,
  modelchecker: ModelOutputChecker,
  policies:     PolicyLibrary,
  feed:         FeedLog,
  reports:      AuditReports,
  policychat:   PolicyChat,
  gateway:      Gateway,
}

export default function App() {
  const [session, setSession]     = useState(null)
  const [activePage, setActivePage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sessionLoaded, setSessionLoaded] = useState(false)

  // Check for existing session on load
  useEffect(() => {
    const stored = localStorage.getItem('saro_session')
    if (stored) {
      try { setSession(JSON.parse(stored)) } catch(e) {}
    }
    setSessionLoaded(true)

    // Also check URL for ?token= (magic link click)
    const params = new URLSearchParams(window.location.search)
    if (params.get('token')) {
      setSession(null)  // Force Login page to handle the token
      setSessionLoaded(true)
    }
  }, [])

  const handleLogin = (sessionData) => {
    setSession(sessionData)
    // Navigate to persona's default page
    if (sessionData.default_page && PAGES[sessionData.default_page]) {
      setActivePage(sessionData.default_page)
    }
    // Clear token from URL
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

  // Show login if no session
  if (!session) {
    return <Login onLogin={handleLogin} />
  }

  const PageComponent = PAGES[activePage] || Dashboard
  const apiUrl = window.SARO_CONFIG?.apiUrl

  return (
    <div className="app-shell">
      {!apiUrl && (
        <div style={{ position:'fixed',top:0,left:0,right:0,zIndex:9999,background:'#ff3d6a',color:'#fff',padding:'10px 20px',fontSize:13,fontWeight:600,textAlign:'center' }}>
          ⚠️ API not configured — edit frontend/public/config.js → set apiUrl → redeploy
        </div>
      )}
      <Sidebar activePage={activePage} onNavigate={setActivePage} isOpen={sidebarOpen} session={session} />
      <div className={`main-area ${sidebarOpen?'sidebar-open':''}`}>
        <Header onToggleSidebar={() => setSidebarOpen(s => !s)} activePage={activePage} session={session} onLogout={handleLogout} />
        <main className="page-content" style={!apiUrl?{paddingTop:60}:{}}>
          <PageComponent onNavigate={setActivePage} session={session} />
        </main>
      </div>
    </div>
  )
}
