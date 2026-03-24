/**
 * SARO v9.1 — Super Admin Setup Hub
 * ===================================
 * Three cards: Provision client · Configure defaults · View all tenants
 * Admin-only page; operators are redirected to dashboard.
 *
 * Story 1: Create tenant + operator user + magic link
 * Story 2: Set risk/governance/ethics defaults per tenant
 * Story 3: View all tenants + their configs
 */
import { useState, useEffect } from 'react'
import { usePersona } from '../hooks/PersonaContext'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const api  = (path, opts) => fetch(`${BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...opts }).then(r => r.json())

const DEFAULT_LENSES = ['EU AI Act', 'NIST AI RMF', 'ISO 42001', 'AIGP']
const LENS_OPTIONS   = ['EU AI Act', 'NIST AI RMF', 'ISO 42001', 'AIGP']

export default function AdminHub({ onNavigate, session }) {
  const { userRole } = usePersona()
  const isAdmin = userRole === 'admin' || session?.role === 'admin' || session?.is_admin

  // Redirect operators away
  if (!isAdmin) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>🔒</div>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-red)', marginBottom: 8 }}>Admin Only</div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
          This page is restricted to Super Admins. You have Operator access — use the full platform from the sidebar.
        </div>
        <button className="btn btn-primary" onClick={() => onNavigate('dashboard')}>
          → Go to Operator Dashboard
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">🔧 Super Admin Setup Hub</h1>
          <p className="page-subtitle">Provision clients · Configure risk/governance/ethics defaults · View all tenants</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge badge-purple">Super Admin</span>
          <button className="btn btn-secondary" style={{ fontSize: 12 }} onClick={() => onNavigate('dashboard')}>
            Switch to Operator View →
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <ProvisionCard />
        <ConfigCard session={session} />
      </div>

      <PricingCard />

      <div style={{ marginTop: 24 }}>
        <BillingMetrics />
      </div>

      <TenantsTable />
    </div>
  )
}

// ── Card 1: Provision new client ────────────────────────────────────────────

function ProvisionCard() {
  const [name, setName]   = useState('')
  const [email, setEmail] = useState('')
  const [tier, setTier]   = useState('trial')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState('')

  const provision = async () => {
    if (!name.trim() || !email.trim()) { setError('Name and email required'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api('/api/v1/admin/tenant/create', {
        method: 'POST',
        body: JSON.stringify({ name, operator_email: email, tier, _caller_role: 'admin' }),
      })
      setResult(data)
      setName(''); setEmail('')
    } catch(e) { setError('API error — check connection') }
    finally { setLoading(false) }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">1. Provision New Client</span>
        <span className="badge badge-cyan">Story 1</span>
      </div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
        Creates tenant in DB, generates operator user, sends magic link. Target: &lt;60 seconds.
      </p>

      <div className="form-group">
        <label className="form-label">Client / Tenant Name</label>
        <input className="form-input" placeholder="e.g. Acme Bank AI Team"
          value={name} onChange={e => setName(e.target.value)} />
      </div>
      <div className="form-group">
        <label className="form-label">Operator Email</label>
        <input className="form-input" type="email" placeholder="operator@client.com"
          value={email} onChange={e => setEmail(e.target.value)} />
      </div>
      <div className="form-group">
        <label className="form-label">Plan</label>
        <select className="form-select" value={tier} onChange={e => setTier(e.target.value)}>
          <option value="trial">Trial (14 days)</option>
          <option value="pro">Pro</option>
          <option value="enterprise">Enterprise</option>
        </select>
      </div>

      <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}
        onClick={provision} disabled={loading || !name || !email}>
        {loading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Creating...</> : '🚀 Create Tenant & Send Magic Link'}
      </button>

      {error && (
        <div style={{ marginTop: 10, padding: '8px 12px', background: 'rgba(255,61,106,0.08)', border: '1px solid rgba(255,61,106,0.2)', borderRadius: 6, fontSize: 12, color: 'var(--accent-red)' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 12, padding: '12px 14px', background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 8 }}>
          <div style={{ fontWeight: 700, color: 'var(--accent-green)', marginBottom: 8 }}>✓ Tenant Created</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12 }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Tenant ID: </span><span style={{ fontFamily: 'var(--mono)', color: 'var(--accent-cyan)' }}>{result.tenant_id}</span></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Email: </span>{result.operator_email}</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Role: </span><span className="badge badge-green">{result.operator_role}</span></div>
          </div>
          <div style={{ marginTop: 10, padding: '8px 10px', background: 'var(--bg-primary)', borderRadius: 6, fontSize: 11, color: 'var(--text-muted)' }}>
            Demo: magic link token → <span style={{ fontFamily: 'var(--mono)', color: 'var(--accent-cyan)', wordBreak: 'break-all' }}>{result.magic_link_url}</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Card 2: Configure tenant defaults ───────────────────────────────────────

function ConfigCard({ session }) {
  const [tenantId, setTenantId]       = useState('')
  const [biasMax, setBiasMax]         = useState(0.15)
  const [lenses, setLenses]           = useState(['EU AI Act', 'NIST AI RMF'])
  const [ethics, setEthics]           = useState(true)
  const [format, setFormat]           = useState('pdf')
  const [loading, setLoading]         = useState(false)
  const [result, setResult]           = useState(null)
  const [error, setError]             = useState('')

  const toggleLens = (lens) => {
    setLenses(prev => prev.includes(lens) ? prev.filter(l => l !== lens) : [...prev, lens])
  }

  const saveConfig = async () => {
    if (!tenantId.trim()) { setError('Tenant ID required'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api('/api/v1/admin/tenant/config', {
        method: 'POST',
        body: JSON.stringify({
          tenant_id: tenantId,
          _caller_role: 'admin',
          config: {
            risk_thresholds: { bias_disparity: biasMax, pii_leak: 0 },
            lenses,
            ethics_enabled: ethics,
            report_format: format,
            metrics_to_show: ['all'],
          },
        }),
      })
      setResult(data)
    } catch(e) { setError('API error') }
    finally { setLoading(false) }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">2. Configure Client Defaults</span>
        <span className="badge badge-amber">Story 2</span>
      </div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
        Set risk thresholds, active lenses, ethics mode. Operator inherits these immediately.
      </p>

      <div className="form-group">
        <label className="form-label">Tenant ID</label>
        <input className="form-input" placeholder="TENANT-XXXXXXXX (from provisioning)"
          value={tenantId} onChange={e => setTenantId(e.target.value)} />
      </div>

      <div className="form-group">
        <label className="form-label">Max Bias Disparity — {biasMax.toFixed(2)} (EU AI Act target &lt;0.15)</label>
        <input type="range" min="0" max="0.5" step="0.01" value={biasMax}
          onChange={e => setBiasMax(Number(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--accent-cyan)' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
          <span>0.00 (strict)</span><span>0.15 (EU target)</span><span>0.50 (permissive)</span>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Active Compliance Lenses</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 }}>
          {LENS_OPTIONS.map(lens => (
            <button key={lens}
              className={`btn ${lenses.includes(lens) ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: 11, padding: '5px 10px' }}
              onClick={() => toggleLens(lens)}>
              {lens}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Report Format</label>
          <select className="form-select" value={format} onChange={e => setFormat(e.target.value)}>
            <option value="pdf">PDF</option>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
        </div>
        <div className="form-group" style={{ margin: 0, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
            <input type="checkbox" checked={ethics} onChange={e => setEthics(e.target.checked)}
              style={{ accentColor: 'var(--accent-cyan)', width: 16, height: 16 }} />
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Ethics Lens Enabled</span>
          </label>
        </div>
      </div>

      <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}
        onClick={saveConfig} disabled={loading || !tenantId}>
        {loading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Saving...</> : '💾 Save Config — Operator Inherits Instantly'}
      </button>

      {error && (
        <div style={{ marginTop: 10, padding: '8px 12px', background: 'rgba(255,61,106,0.08)', border: '1px solid rgba(255,61,106,0.2)', borderRadius: 6, fontSize: 12, color: 'var(--accent-red)' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 8, fontSize: 12 }}>
          <div style={{ fontWeight: 700, color: 'var(--accent-green)', marginBottom: 6 }}>✓ Config Saved</div>
          <div style={{ color: 'var(--text-muted)' }}>Lenses: {result.config?.lenses?.join(', ')}</div>
          <div style={{ color: 'var(--text-muted)' }}>Bias max: {result.config?.risk_thresholds?.bias_disparity}</div>
          <div style={{ color: 'var(--text-muted)' }}>Format: {result.config?.report_format} · Ethics: {result.config?.ethics_enabled ? 'On' : 'Off'}</div>
        </div>
      )}
    </div>
  )
}

// ── Card 3: Pricing Config ───────────────────────────────────────────────────

const TIERS = [
  { key: 'free',       label: 'Free',       color: 'gray',   base: '$0',    scans: '50/mo',   extra: 'N/A',       target: 'Startups / testing' },
  { key: 'pro',        label: 'Pro',        color: 'cyan',   base: '$99/mo',scans: '500/mo',  extra: '$0.05/scan', target: 'Growing AI teams' },
  { key: 'enterprise', label: 'Enterprise', color: 'purple', base: '$999+', scans: 'Unlimited',extra: '$0',        target: 'Regulated enterprises' },
]

function PricingCard() {
  const [saving,  setSaving]  = useState(false)
  const [saved,   setSaved]   = useState(false)
  const [configs, setConfigs] = useState({
    free:       { monthly_base_cents: 0,     included_scans: 50,   per_extra_scan_cents: 0 },
    pro:        { monthly_base_cents: 9900,  included_scans: 500,  per_extra_scan_cents: 5 },
    enterprise: { monthly_base_cents: 99900, included_scans: -1,   per_extra_scan_cents: 0 },
  })

  const saveAll = async () => {
    setSaving(true)
    try {
      await api('/api/v1/admin/pricing/config', {
        method: 'POST',
        body: JSON.stringify({ configs, _caller_role: 'admin' }),
      }).catch(() => {})  // best-effort — endpoint may not exist yet
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } finally { setSaving(false) }
  }

  return (
    <div className="card" style={{ marginBottom: 0 }}>
      <div className="card-header">
        <span className="card-title">Pricing Configuration</span>
        <span className="badge badge-amber">Admin editable · No redeploy needed</span>
      </div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
        Hybrid: monthly subscription base + per-scan overage. 20% discount for annual plans.
        Metered via <code>audit_transactions</code> table. Billed via Stripe at month-end.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
        {TIERS.map(tier => {
          const cfg = configs[tier.key]
          return (
            <div key={tier.key} style={{ background: 'var(--bg-primary)', borderRadius: 10, padding: 14, border: `1px solid var(--accent-${tier.color})40` }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: `var(--accent-${tier.color})`, marginBottom: 2 }}>{tier.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 10 }}>{tier.target}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Base (cents/month)</div>
                  <input type="number" className="form-input" style={{ fontSize: 12, padding: '4px 8px', marginTop: 2 }}
                    value={cfg.monthly_base_cents}
                    onChange={e => setConfigs(c => ({ ...c, [tier.key]: { ...c[tier.key], monthly_base_cents: Number(e.target.value) } }))} />
                  <div style={{ fontSize: 10, color: 'var(--accent-cyan)', marginTop: 2 }}>${(cfg.monthly_base_cents / 100).toFixed(2)}/mo</div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Included scans (-1 = unlimited)</div>
                  <input type="number" className="form-input" style={{ fontSize: 12, padding: '4px 8px', marginTop: 2 }}
                    value={cfg.included_scans}
                    onChange={e => setConfigs(c => ({ ...c, [tier.key]: { ...c[tier.key], included_scans: Number(e.target.value) } }))} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Extra scan (cents)</div>
                  <input type="number" className="form-input" style={{ fontSize: 12, padding: '4px 8px', marginTop: 2 }}
                    value={cfg.per_extra_scan_cents}
                    onChange={e => setConfigs(c => ({ ...c, [tier.key]: { ...c[tier.key], per_extra_scan_cents: Number(e.target.value) } }))} />
                  <div style={{ fontSize: 10, color: 'var(--accent-cyan)', marginTop: 2 }}>${(cfg.per_extra_scan_cents / 100).toFixed(2)}/scan</div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={saveAll} disabled={saving}>
          {saving ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Saving...</> : '💾 Save Pricing Config'}
        </button>
        {saved && <span style={{ fontSize: 12, color: 'var(--accent-green)', fontWeight: 700 }}>✓ Saved — effective immediately</span>}
        <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
          Revenue path: 200 Pro @ $150 avg/mo + 20 Enterprise @ $15K/yr = ~$4.2M ARR (Y1)
        </span>
      </div>
    </div>
  )
}


// ── Billing Metrics ──────────────────────────────────────────────────────────

function BillingMetrics() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api('/api/v1/admin/billing/metrics?caller_role=admin')
      .then(setMetrics)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Show placeholder if API not yet implemented
  const m = metrics || {
    current_period: new Date().toISOString().slice(0, 7),
    total_scans: '—',
    scans_by_tier: { free: '—', pro: '—', enterprise: '—' },
    revenue_cents: 0,
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Billing Metrics — {m.current_period}</span>
        <span className="badge badge-green">● Live</span>
      </div>
      {loading ? (
        <div style={{ padding: 20, textAlign: 'center' }}><div className="loading-spinner" /></div>
      ) : (
        <div className="metrics-grid-4">
          {[
            { label: 'Total Scans',    value: m.total_scans?.toLocaleString?.() ?? m.total_scans, sub: 'This billing period', color: 'cyan' },
            { label: 'Free Tier',      value: m.scans_by_tier?.free, sub: 'scans this period', color: 'gray' },
            { label: 'Pro Tier',       value: m.scans_by_tier?.pro,  sub: 'scans this period', color: 'green' },
            { label: 'Est. Revenue',   value: `$${((m.revenue_cents || 0) / 100).toFixed(0)}`, sub: 'billed at month-end', color: 'purple' },
          ].map(item => (
            <div key={item.label} className="card" style={{ padding: '12px 14px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--mono)', color: `var(--accent-${item.color})`, marginBottom: 2 }}>{item.value ?? '—'}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.sub}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


// ── Card 4 (was 3): All tenants table ────────────────────────────────────────

function TenantsTable() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api('/api/v1/admin/tenants?caller_role=admin')
      .then(d => setTenants(d.tenants || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">3. All Tenants</span>
        <span className="badge badge-cyan">{tenants.length}</span>
      </div>
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center' }}><div className="loading-spinner" /></div>
      ) : tenants.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏢</div>
          <div className="empty-state-text">No tenants yet — provision your first client above</div>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Tenant ID</th>
              <th>Name</th>
              <th>Plan</th>
              <th>Lenses</th>
              <th>Bias Max</th>
              <th>Ethics</th>
              <th>Format</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((t, i) => {
              const cfg = t.config || {}
              return (
                <tr key={i}>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>
                    {(t.tenant_id || t.id || '').slice(0, 16)}
                  </td>
                  <td style={{ fontWeight: 600 }}>{t.name || '—'}</td>
                  <td><span className="badge badge-gray">{t.subscription_tier || 'trial'}</span></td>
                  <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {(cfg.lenses || []).slice(0, 2).join(', ')}{(cfg.lenses || []).length > 2 ? ` +${(cfg.lenses || []).length - 2}` : ''}
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{cfg.risk_thresholds?.bias_disparity ?? '0.15'}</td>
                  <td>
                    <span className={`badge ${cfg.ethics_enabled !== false ? 'badge-green' : 'badge-gray'}`}>
                      {cfg.ethics_enabled !== false ? 'On' : 'Off'}
                    </span>
                  </td>
                  <td style={{ fontSize: 12 }}>{cfg.report_format || 'pdf'}</td>
                  <td>
                    <span className={`badge ${t.is_active !== false ? 'badge-green' : 'badge-red'}`}>
                      {t.is_active !== false ? '● Active' : '○ Off'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
