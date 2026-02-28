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

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onNavigate={setActivePage} isOpen={sidebarOpen} />
      <div className={`main-area ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} activePage={activePage} />
        <main className="page-content">
          <PageComponent />
        </main>
      </div>
    </div>
  )
}
