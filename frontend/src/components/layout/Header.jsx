import { useState, useEffect } from 'react'

const PAGE_LABELS = {
  dashboard: 'Overview Dashboard',
  mvp1: 'MVP1 — Ingestion & Forecast',
  mvp2: 'MVP2 — Audit & Compliance',
  mvp3: 'MVP3 — Enterprise',
  mvp4: 'MVP4 — Agentic GA',
}

export default function Header({ onToggleSidebar, activePage }) {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <header className="header">
      <button className="header-toggle" onClick={onToggleSidebar}>☰</button>
      <div className="header-breadcrumb">
        SARO / <strong>{PAGE_LABELS[activePage] || activePage}</strong>
      </div>
      <div className="header-spacer" />
      <div className="header-pills">
        <span className="pill pill-green">● LIVE</span>
        <span className="pill pill-cyan" style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>
          {time.toLocaleTimeString()}
        </span>
      </div>
      <div className="header-avatar">AD</div>
    </header>
  )
}
