import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import MVP1Ingestion from './pages/MVP1Ingestion'
import MVP2Audit from './pages/MVP2Audit'
import MVP3Enterprise from './pages/MVP3Enterprise'
import MVP4Agentic from './pages/MVP4Agentic'
import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import './App.css'

const PAGES = {
  dashboard: Dashboard,
  mvp1: MVP1Ingestion,
  mvp2: MVP2Audit,
  mvp3: MVP3Enterprise,
  mvp4: MVP4Agentic,
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const PageComponent = PAGES[activePage] || Dashboard
  const apiUrl = import.meta.env.VITE_API_URL

  return (
    <div className="app-shell">
      {!apiUrl && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
          background: '#ff3d6a', color: '#fff', padding: '10px 20px',
          fontSize: 13, fontWeight: 600, textAlign: 'center', lineHeight: 1.5
        }}>
          ⚠️ VITE_API_URL not set — Koyeb → saro-frontend → Environment Variables → VITE_API_URL = https://your-backend.koyeb.app → Redeploy
        </div>
      )}
      <Sidebar activePage={activePage} onNavigate={setActivePage} isOpen={sidebarOpen} />
      <div className={`main-area ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} activePage={activePage} />
        <main className="page-content" style={!apiUrl ? { paddingTop: 60 } : {}}>
          <PageComponent />
        </main>
      </div>
    </div>
  )
}
