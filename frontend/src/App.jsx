import { useState } from 'react'
import Dashboard          from './pages/Dashboard'
import MVP1Ingestion      from './pages/MVP1Ingestion'
import MVP2Audit          from './pages/MVP2Audit'
import MVP3Enterprise     from './pages/MVP3Enterprise'
import MVP4Agentic        from './pages/MVP4Agentic'
import MVP5Autonomous     from './pages/MVP5Autonomous'
import AuditFlow          from './pages/AuditFlow'
import ModelOutputChecker from './pages/ModelOutputChecker'
import PolicyLibrary      from './pages/PolicyLibrary'
import FeedLog            from './pages/FeedLog'
import AuditReports       from './pages/AuditReports'
import Onboarding         from './pages/Onboarding'
import Sidebar            from './components/layout/Sidebar'
import Header             from './components/layout/Header'
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
}

// Context so child pages can navigate
export let navigateTo = null

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  navigateTo = setActivePage   // expose globally

  const PageComponent = PAGES[activePage] || Dashboard
  const apiUrl = window.SARO_CONFIG?.apiUrl

  return (
    <div className="app-shell">
      {!apiUrl && (
        <div style={{ position:'fixed',top:0,left:0,right:0,zIndex:9999,background:'#ff3d6a',color:'#fff',padding:'10px 20px',fontSize:13,fontWeight:600,textAlign:'center' }}>
          ⚠️ API not configured — edit frontend/public/config.js → set apiUrl → redeploy
        </div>
      )}
      <Sidebar activePage={activePage} onNavigate={setActivePage} isOpen={sidebarOpen} />
      <div className={`main-area ${sidebarOpen?'sidebar-open':''}`}>
        <Header onToggleSidebar={() => setSidebarOpen(s => !s)} activePage={activePage} />
        <main className="page-content" style={!apiUrl?{paddingTop:60}:{}}>
          <PageComponent onNavigate={setActivePage} />
        </main>
      </div>
    </div>
  )
}
