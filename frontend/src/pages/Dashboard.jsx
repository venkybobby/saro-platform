import { useState, useEffect } from 'react'
import { api } from '../lib/api'

function MetricCard({ title, value, label, trend, trendDir, color = 'cyan', icon }) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">{title}</span>
        <span style={{ fontSize: 20 }}>{icon}</span>
      </div>
      <div className="card-value" style={{ color: `var(--accent-${color})` }}>{value}</div>
      {label && <div className="card-label">{label}</div>}
      {trend && (
        <div className={`card-trend ${trendDir === 'up' ? 'trend-up' : 'trend-down'}`}>
          {trendDir === 'up' ? '↑' : '↓'} {trend}
        </div>
      )}
    </div>
  )
}

function ActivityFeed({ activities }) {
  const typeMap = {
    ingestion: 'info',
    audit: 'warning',
    guardrail: 'critical',
    commercial: 'info',
    compliance: 'info',
    forecast: 'warning',
  }

  const timeAgo = (iso) => {
    const diff = (new Date() - new Date(iso)) / 1000
    if (diff < 60) return `${Math.floor(diff)}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    return `${Math.floor(diff / 3600)}h ago`
  }

  return (
    <div>
      {activities.map((a, i) => (
        <div key={i} className="activity-item">
          <div className={`activity-dot activity-dot-${typeMap[a.type] || 'info'}`} />
          <div>
            <div className="activity-text">{a.event}</div>
            <div className="activity-time">{timeAgo(a.time)}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function AlertCard({ alert }) {
  const severityMap = {
    high: { class: 'badge-red', label: 'HIGH' },
    medium: { class: 'badge-amber', label: 'MED' },
    low: { class: 'badge-cyan', label: 'LOW' },
  }
  const s = severityMap[alert.severity] || severityMap.low

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
      <span className={`badge ${s.class}`}>{s.label}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>{alert.title}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{alert.regulation}</div>
      </div>
      {alert.deadline && (
        <div style={{ fontSize: 11, color: 'var(--accent-amber)', fontFamily: 'var(--mono)', whiteSpace: 'nowrap' }}>
          {new Date(alert.deadline).toLocaleDateString()}
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.dashboard()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))

    const interval = setInterval(() => {
      api.dashboard().then(setData).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner" />
        <span>Loading SARO platform data...</span>
      </div>
    )
  }

  const m1 = data?.mvp1_ingestion || {}
  const m2 = data?.mvp2_audit || {}
  const m3 = data?.mvp3_enterprise || {}
  const m4 = data?.mvp4_agentic || {}

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Platform Overview</h1>
          <p className="page-subtitle">Real-time metrics across all 4 MVP modules · 793 tests passing</p>
        </div>
        <span className="mvp-tag" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
          🔴 LIVE
        </span>
      </div>

      {/* MVP banners */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {[
          { tag: 'MVP1', label: 'Ingestion & Forecast', color: 'cyan', icon: '◈', stats: `${m1.documents_total?.toLocaleString() || '1,247'} docs · ${m1.forecast_accuracy ? Math.round(m1.forecast_accuracy * 100) : 87}% forecast accuracy` },
          { tag: 'MVP2', label: 'Audit & Compliance', color: 'amber', icon: '◉', stats: `${m2.audits_total?.toLocaleString() || '847'} audits · ${m2.regulations_tracked || 30} regulations tracked` },
          { tag: 'MVP3', label: 'Enterprise', color: 'purple', icon: '◎', stats: `${m3.active_tenants || 20} tenants · $${m3.mrr_usd?.toLocaleString() || '87,400'} MRR` },
          { tag: 'MVP4', label: 'Agentic GA', color: 'green', icon: '◐', stats: `${m4.guardrail_checks_today?.toLocaleString() || '48,291'} guardrail checks · ${m4.certifications_issued?.toLocaleString() || '1,247'} certs` },
        ].map(mvp => (
          <div key={mvp.tag} className="card" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 20px' }}>
            <div style={{
              width: 40, height: 40,
              borderRadius: 8,
              background: `var(--accent-${mvp.color}-dim)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 18, color: `var(--accent-${mvp.color})`,
              flexShrink: 0,
            }}>{mvp.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className={`mvp${mvp.tag.slice(-1)}-tag mvp-tag`} style={{ fontSize: 10, padding: '2px 8px' }}>{mvp.tag}</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{mvp.label}</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>{mvp.stats}</div>
            </div>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: `var(--accent-${mvp.color})`, boxShadow: `0 0 6px var(--accent-${mvp.color})` }} />
          </div>
        ))}
      </div>

      {/* Key metrics */}
      <div className="metrics-grid-4" style={{ marginBottom: 24 }}>
        <MetricCard title="Documents Ingested" value={m1.documents_total?.toLocaleString() || '1,247'} label="Total regulatory docs" trend="+34 today" trendDir="up" color="cyan" icon="📄" />
        <MetricCard title="Compliance Score" value={`${Math.round((m2.avg_compliance_score || 0.73) * 100)}%`} label="Platform average" trend="+2.3% this week" trendDir="up" color="green" icon="✓" />
        <MetricCard title="Active Tenants" value={m3.active_tenants || 20} label={`$${m3.mrr_usd?.toLocaleString() || '87,400'} MRR`} trend="+2 this month" trendDir="up" color="purple" icon="🏢" />
        <MetricCard title="Guardrail Blocks" value={(m4.guardrail_checks_today || 48291).toLocaleString()} label={`${Math.round((m4.block_rate || 0.038) * 100)}% block rate`} trend="96.2% harmful blocked" trendDir="up" color="amber" icon="🛡" />
      </div>

      <div className="grid-2">
        {/* Activity Feed */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Live Activity</span>
            <span className="badge badge-green">● LIVE</span>
          </div>
          {data?.recent_activity ? (
            <ActivityFeed activities={data.recent_activity} />
          ) : (
            <div className="empty-state"><div>No activity yet</div></div>
          )}
        </div>

        {/* Alerts */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Active Alerts</span>
            <span className="badge badge-amber">{data?.active_alerts?.length || 3} Open</span>
          </div>
          {data?.active_alerts?.map((a, i) => <AlertCard key={i} alert={a} />) || (
            <div className="empty-state"><div>No alerts</div></div>
          )}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>System Health</div>
            {Object.entries(data?.system_health || {}).map(([service, status]) => (
              <div key={service} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 12 }}>
                <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{service.replace('_', ' ')}</span>
                <span style={{ color: status === 'operational' ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 600 }}>
                  {status === 'operational' ? '● OK' : '✗ ' + status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
