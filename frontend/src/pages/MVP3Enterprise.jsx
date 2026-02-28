import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export default function MVP3Enterprise() {
  const [tab, setTab] = useState('overview')
  const [tenants, setTenants] = useState([])
  const [haStatus, setHaStatus] = useState(null)
  const [integrations, setIntegrations] = useState(null)
  const [entMetrics, setEntMetrics] = useState(null)
  const [newTenant, setNewTenant] = useState({ name: '', industry: 'technology', plan: 'professional' })
  const [creating, setCreating] = useState(false)
  const [createdTenant, setCreatedTenant] = useState(null)

  useEffect(() => {
    api.listTenants().then(setTenants).catch(() => {})
    api.haStatus().then(setHaStatus).catch(() => {})
    api.integrations().then(setIntegrations).catch(() => {})
    api.enterpriseDashboard().then(setEntMetrics).catch(() => {})
  }, [])

  const handleCreateTenant = async () => {
    if (!newTenant.name) return
    setCreating(true)
    try {
      const res = await api.createTenant(newTenant)
      setCreatedTenant(res)
      setTenants(t => [res, ...t])
      setNewTenant({ name: '', industry: 'technology', plan: 'professional' })
    } catch (e) {}
    finally { setCreating(false) }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Enterprise Platform</h1>
          <p className="page-subtitle">Multi-tenant management, HA infrastructure, and third-party integrations</p>
        </div>
        <span className="mvp-tag mvp3-tag">◎ MVP3</span>
      </div>

      {entMetrics && (
        <div className="metrics-grid" style={{ marginBottom: 24 }}>
          {[
            { label: 'Active Tenants', value: entMetrics.tenant_count, color: 'purple' },
            { label: 'MRR', value: `$${entMetrics.mrr_usd?.toLocaleString()}`, color: 'green' },
            { label: 'NPS Score', value: entMetrics.nps_score, color: 'cyan' },
            { label: 'Uptime SLA', value: `${(entMetrics.sla_adherence * 100).toFixed(1)}%`, color: 'green' },
            { label: 'Active Users (30d)', value: entMetrics.active_users_30d, color: 'cyan' },
          ].map(m => (
            <div key={m.label} className="card" style={{ padding: '14px 16px' }}>
              <div className="card-title" style={{ fontSize: 10, marginBottom: 6 }}>{m.label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--mono)', color: `var(--accent-${m.color})` }}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="tabs">
        {['overview', 'tenants', 'ha', 'integrations'].map(t => (
          <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'overview' ? '📊 Overview' : t === 'tenants' ? '🏢 Tenants' : t === 'ha' ? '🌐 HA Status' : '🔗 Integrations'}
          </div>
        ))}
      </div>

      {tab === 'overview' && entMetrics && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Compliance Coverage</span></div>
            {Object.entries(entMetrics.compliance_coverage || {}).map(([reg, score]) => (
              <div key={reg} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{reg}</span>
                  <span style={{ fontSize: 12, fontFamily: 'var(--mono)', color: score >= 0.9 ? 'var(--accent-green)' : 'var(--accent-amber)' }}>{(score * 100).toFixed(0)}%</span>
                </div>
                <div className="progress-bar">
                  <div className={`progress-fill ${score >= 0.9 ? 'progress-green' : 'progress-amber'}`} style={{ width: `${score * 100}%` }} />
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Provision New Tenant</span></div>
            <div className="form-group">
              <label className="form-label">Organization Name</label>
              <input className="form-input" placeholder="Acme Corp" value={newTenant.name} onChange={e => setNewTenant(n => ({ ...n, name: e.target.value }))} />
            </div>
            <div className="grid-2" style={{ marginBottom: 0 }}>
              <div className="form-group">
                <label className="form-label">Industry</label>
                <select className="form-select" value={newTenant.industry} onChange={e => setNewTenant(n => ({ ...n, industry: e.target.value }))}>
                  {['technology', 'finance', 'healthcare', 'consulting', 'insurance', 'government'].map(i => <option key={i}>{i}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Plan</label>
                <select className="form-select" value={newTenant.plan} onChange={e => setNewTenant(n => ({ ...n, plan: e.target.value }))}>
                  {['starter', 'professional', 'enterprise'].map(p => <option key={p}>{p}</option>)}
                </select>
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleCreateTenant} disabled={creating} style={{ width: '100%', justifyContent: 'center' }}>
              {creating ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Provisioning...</> : '+ Provision Tenant'}
            </button>
            {createdTenant && (
              <div style={{ marginTop: 14, background: 'var(--accent-green-dim)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 8, padding: 14 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-green)', marginBottom: 6 }}>✓ Tenant Provisioned!</div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'var(--mono)', wordBreak: 'break-all' }}>API Key: {createdTenant.api_key}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>ID: {createdTenant.tenant_id}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'tenants' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">All Tenants</span>
            <span className="badge badge-purple">{tenants.length} tenants</span>
          </div>
          <table className="data-table">
            <thead><tr><th>Tenant ID</th><th>Name</th><th>Plan</th><th>Industry</th><th>API Calls</th><th>Status</th></tr></thead>
            <tbody>
              {tenants.map((t, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{t.tenant_id}</td>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{t.name}</td>
                  <td><span className={`badge ${t.plan === 'enterprise' ? 'badge-purple' : t.plan === 'professional' ? 'badge-cyan' : 'badge-gray'}`}>{t.plan}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{t.industry}</td>
                  <td style={{ fontFamily: 'var(--mono)' }}>{t.monthly_usage?.api_calls?.toLocaleString() || '—'}</td>
                  <td><span className={`badge ${t.status === 'active' ? 'badge-green' : 'badge-amber'}`}>{t.status || 'active'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'ha' && haStatus && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Infrastructure Status</span></div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent-green)', fontFamily: 'var(--mono)' }}>{haStatus.actual_uptime_30d}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>30-day uptime</div>
              </div>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--mono)' }}>{haStatus.failover_time_ms}ms</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Failover time</div>
              </div>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>Regions</div>
            {Object.entries(haStatus.replicas || {}).map(([region, count]) => (
              <div key={region} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 6px var(--accent-green)' }} />
                  <span style={{ fontSize: 12, fontFamily: 'var(--mono)' }}>{region}</span>
                </div>
                <span style={{ fontSize: 12, color: 'var(--accent-cyan)' }}>{count} replicas</span>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">Deployment Info</span></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                ['Deployment Mode', haStatus.deployment],
                ['Load Balancer', haStatus.load_balancer],
                ['SLA Target', haStatus.uptime_sla],
                ['Last Incident', haStatus.last_incident || 'None'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'integrations' && integrations && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Active Integrations</span>
            <span className="badge badge-cyan">{integrations.webhooks_active} webhooks active</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginTop: 8 }}>
            {integrations.available?.map((integ, i) => (
              <div key={i} style={{ background: 'var(--bg-primary)', border: `1px solid ${integ.status === 'connected' ? 'rgba(0,255,136,0.2)' : 'var(--border)'}`, borderRadius: 8, padding: '14px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{integ.name}</div>
                  <span className={`badge ${integ.status === 'connected' ? 'badge-green' : 'badge-amber'}`}>{integ.status}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>Sync: {integ.sync_interval}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginTop: 3 }}>{integ.type.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
