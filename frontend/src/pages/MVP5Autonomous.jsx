import { useState, useEffect } from 'react'
import { api } from '../lib/api'

// Extend api with MVP5 endpoints
const mvp5 = {
  botStatus: () => api._req('/api/v1/mvp5/bots/status'),
  botActions: () => api._req('/api/v1/mvp5/bots/actions'),
  executeBot: (data) => api._req('/api/v1/mvp5/bots/execute', { method: 'POST', body: JSON.stringify(data) }),
  revertBot: (jobId) => api._req(`/api/v1/mvp5/bots/revert/${jobId}`, { method: 'POST', body: '{}' }),
  marketplaceListings: (cat) => api._req(`/api/v1/mvp5/marketplace/listings?category=${cat || 'ALL'}`),
  purchaseModel: (data) => api._req('/api/v1/mvp5/marketplace/purchase', { method: 'POST', body: JSON.stringify(data) }),
  listModel: (data) => api._req('/api/v1/mvp5/marketplace/list', { method: 'POST', body: JSON.stringify(data) }),
  marketplaceStats: () => api._req('/api/v1/mvp5/marketplace/stats'),
  surveillanceScan: (data) => api._req('/api/v1/mvp5/ethics/surveillance-scan', { method: 'POST', body: JSON.stringify(data) }),
  prohibitedUseCases: () => api._req('/api/v1/mvp5/ethics/prohibited-use-cases'),
  generateDPIA: (data) => api._req('/api/v1/mvp5/ethics/dpia-generate', { method: 'POST', body: JSON.stringify(data) }),
}

export default function MVP5Autonomous() {
  const [tab, setTab] = useState('bots')

  // Bots state
  const [botStatus, setBotStatus] = useState(null)
  const [botActions, setBotActions] = useState([])
  const [botForm, setBotForm] = useState({ bot_type: 'remediation_bot', finding_id: '' })
  const [botResult, setBotResult] = useState(null)
  const [botLoading, setBotLoading] = useState(false)
  const [revertMsg, setRevertMsg] = useState(null)

  // Marketplace state
  const [listings, setListings] = useState([])
  const [mktStats, setMktStats] = useState(null)
  const [purchaseResult, setPurchaseResult] = useState(null)
  const [listForm, setListForm] = useState({ name: '', vendor: '', category: 'finance', price_usd: 5000 })
  const [listResult, setListResult] = useState(null)
  const [mktLoading, setMktLoading] = useState(false)

  // Ethics state
  const [ethicsForm, setEthicsForm] = useState({ system_name: '', description: '' })
  const [ethicsResult, setEthicsResult] = useState(null)
  const [ethicsLoading, setEthicsLoading] = useState(false)
  const [prohibited, setProhibited] = useState([])
  const [dpiaResult, setDpiaResult] = useState(null)

  useEffect(() => {
    fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/bots/status`)
      .then(r => r.json()).then(setBotStatus).catch(() => {})
    fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/bots/actions`)
      .then(r => r.json()).then(d => setBotActions(d.actions || [])).catch(() => {})
    fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/marketplace/listings`)
      .then(r => r.json()).then(d => setListings(d.listings || [])).catch(() => {})
    fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/marketplace/stats`)
      .then(r => r.json()).then(setMktStats).catch(() => {})
    fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/ethics/prohibited-use-cases`)
      .then(r => r.json()).then(d => setProhibited(d.prohibited || [])).catch(() => {})
  }, [])

  const executeBot = async () => {
    setBotLoading(true)
    setBotResult(null)
    try {
      const res = await fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/bots/execute`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(botForm)
      })
      const data = await res.json()
      setBotResult(data)
      setBotActions(prev => [data, ...prev])
    } catch (e) { setBotResult({ error: e.message }) }
    finally { setBotLoading(false) }
  }

  const revertAction = async (jobId) => {
    const res = await fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/bots/revert/${jobId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}'
    })
    const data = await res.json()
    setRevertMsg(data.message)
    setTimeout(() => setRevertMsg(null), 4000)
  }

  const purchaseModel = async (listing) => {
    setMktLoading(true)
    try {
      const res = await fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/marketplace/purchase`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ listing_id: listing.listing_id, tenant_id: 'TENANT-DEMO' })
      })
      setPurchaseResult(await res.json())
    } catch (e) {}
    finally { setMktLoading(false) }
  }

  const listNewModel = async () => {
    setMktLoading(true)
    try {
      const res = await fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/marketplace/list`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(listForm)
      })
      const data = await res.json()
      setListResult(data)
      setListings(prev => [data, ...prev])
    } catch (e) {}
    finally { setMktLoading(false) }
  }

  const runEthicsScan = async () => {
    setEthicsLoading(true)
    setEthicsResult(null)
    try {
      const res = await fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/ethics/surveillance-scan`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ethicsForm)
      })
      setEthicsResult(await res.json())
    } catch (e) {}
    finally { setEthicsLoading(false) }
  }

  const generateDPIA = async () => {
    if (!ethicsResult) return
    const res = await fetch(`${window.SARO_CONFIG?.apiUrl || ''}/api/v1/mvp5/ethics/dpia-generate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system_name: ethicsForm.system_name, risk_level: ethicsResult.overall_risk?.toLowerCase() })
    })
    setDpiaResult(await res.json())
  }

  const DEMO_SURVEILLANCE = [
    { label: '🚨 Prohibited', text: 'Our system uses real-time facial recognition and emotion detection in public spaces for law enforcement and predictive policing based on behavioral profiling.' },
    { label: '⚠️ High Risk', text: 'Employee monitoring system tracks location history and biometric fingerprint data for attendance and performance scoring.' },
    { label: '✅ Compliant', text: 'Our AI assistant provides customer recommendations based on purchase history with explicit consent and opt-out mechanisms.' },
  ]

  const BOT_TYPES = [
    { value: 'remediation_bot', label: '🔧 Risk Remediation Bot' },
    { value: 'retrain_bot', label: '🔄 Auto-Retrain Bot' },
    { value: 'policy_bot', label: '📋 Policy Enforcement Bot' },
    { value: 'oversight_bot', label: '👁 Oversight Injection Bot' },
  ]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Autonomous Governance</h1>
          <p className="page-subtitle">Self-healing bots · AI Model Marketplace · Ethics & Surveillance Scanner · DPIA Generator</p>
        </div>
      </div>

      {botStatus && (
        <div className="metrics-grid-4" style={{ marginBottom: 24 }}>
          {[
            { label: 'Actions Today', value: botStatus.total_actions_today, color: 'cyan' },
            { label: 'Success Rate', value: `${(botStatus.success_rate * 100).toFixed(1)}%`, color: 'green' },
            { label: 'Hours Saved', value: `${botStatus.estimated_hours_saved}h`, color: 'amber' },
            { label: 'Cost Avoided', value: `$${(18600).toLocaleString()}`, color: 'purple' },
          ].map(m => (
            <div key={m.label} className="card" style={{ padding: '14px 16px' }}>
              <div className="card-title" style={{ fontSize: 10, marginBottom: 6 }}>{m.label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--mono)', color: `var(--accent-${m.color})` }}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="tabs">
        {[
          ['bots', '🤖 Autonomous Bots'],
          ['marketplace', '🏪 AI Marketplace'],
          ['ethics', '⚖️ Ethics & Surveillance'],
        ].map(([key, label]) => (
          <div key={key} className={`tab ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>{label}</div>
        ))}
      </div>

      {/* ── BOTS ── */}
      {tab === 'bots' && (
        <div>
          {revertMsg && (
            <div style={{ marginBottom: 16, padding: '10px 14px', background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 6, fontSize: 13, color: 'var(--accent-cyan)' }}>
              ↩ {revertMsg}
            </div>
          )}
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="card">
              <div className="card-header"><span className="card-title">Trigger Bot Remediation</span></div>
              <div className="form-group">
                <label className="form-label">Bot Type</label>
                <select className="form-select" value={botForm.bot_type} onChange={e => setBotForm(f => ({ ...f, bot_type: e.target.value }))}>
                  {BOT_TYPES.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Finding ID (optional)</label>
                <input className="form-input" placeholder="FIND-ABC123 or leave blank" value={botForm.finding_id}
                  onChange={e => setBotForm(f => ({ ...f, finding_id: e.target.value }))} />
              </div>
              <button className="btn btn-primary" onClick={executeBot} disabled={botLoading} style={{ width: '100%', justifyContent: 'center' }}>
                {botLoading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Executing...</> : '🤖 Execute Bot'}
              </button>

              {botResult && (
                <div style={{ marginTop: 16, padding: '14px', background: 'var(--bg-primary)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
                    <span className={`badge ${botResult.status === 'completed' ? 'badge-green' : 'badge-red'}`}>{botResult.status?.toUpperCase()}</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>{botResult.job_id}</span>
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', marginBottom: 8 }}>{botResult.action_taken}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>
                    {botResult.execution_time_ms}ms · {botResult.logged_to_chain ? '⛓ On-chain logged' : ''}
                  </div>
                  {botResult.reversible && (
                    <button className="btn btn-secondary" style={{ fontSize: 12 }} onClick={() => revertAction(botResult.job_id)}>
                      ↩ Revert Action
                    </button>
                  )}
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title">Bot Fleet Status</span>
                <span className="badge badge-green">● All Active</span>
              </div>
              {botStatus?.bots?.map((bot, i) => (
                <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{bot.name}</span>
                    <span className="badge badge-green">● Active</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{bot.desc}</div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 11 }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>{bot.actions_today} actions today</span>
                    <span style={{ color: 'var(--accent-green)' }}>{(bot.success_rate * 100).toFixed(1)}% success</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Recent Bot Actions</span>
              <span className="badge badge-cyan">{botActions.length} logged</span>
            </div>
            <table className="data-table">
              <thead><tr><th>Job ID</th><th>Bot</th><th>Action</th><th>Status</th><th>Time</th><th>Revert</th></tr></thead>
              <tbody>
                {botActions.slice(0, 8).map((a, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>{a.job_id}</td>
                    <td style={{ fontSize: 12 }}>{a.bot_name || a.bot_type}</td>
                    <td style={{ fontSize: 11, color: 'var(--text-secondary)', maxWidth: 300 }}>{a.action_taken?.slice(0, 60)}...</td>
                    <td><span className={`badge ${a.status === 'completed' ? 'badge-green' : 'badge-red'}`}>{a.status}</span></td>
                    <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.execution_time_ms}ms</td>
                    <td>
                      <button className="btn btn-secondary" style={{ fontSize: 10, padding: '3px 8px' }} onClick={() => revertAction(a.job_id)}>↩</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── MARKETPLACE ── */}
      {tab === 'marketplace' && (
        <div>
          {mktStats && (
            <div className="metrics-grid-4" style={{ marginBottom: 24 }}>
              {[
                { label: 'Total Listings', value: mktStats.total_listings, color: 'cyan' },
                { label: 'SARO Verified', value: mktStats.saro_verified, color: 'green' },
                { label: 'Volume (Total)', value: `$${(mktStats.total_volume_usd || 2840000).toLocaleString()}`, color: 'amber' },
                { label: 'Partner Vendors', value: mktStats.partner_vendors, color: 'purple' },
              ].map(m => (
                <div key={m.label} className="card" style={{ padding: '14px 16px' }}>
                  <div className="card-title" style={{ fontSize: 10, marginBottom: 6 }}>{m.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--mono)', color: `var(--accent-${m.color})` }}>{m.value}</div>
                </div>
              ))}
            </div>
          )}

          {purchaseResult && (
            <div style={{ marginBottom: 16, padding: '14px 16px', background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, color: 'var(--accent-green)', marginBottom: 6 }}>✓ Purchase Complete — {purchaseResult.model_name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>TX: {purchaseResult.tx_hash?.slice(0, 24)}...</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Block #{purchaseResult.block_number} · SARO stamp transferred: {purchaseResult.saro_stamp_transferred ? '✓' : '✗'}</div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16, marginBottom: 24 }}>
            {listings.map((l, i) => (
              <div key={i} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{l.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{l.vendor}</div>
                  </div>
                  {l.saro_stamp && <span className="badge badge-green" style={{ fontSize: 10 }}>✓ SARO</span>}
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                  <span className="badge badge-gray">{l.category}</span>
                  {l.jurisdictions?.map(j => <span key={j} className="badge badge-cyan" style={{ fontSize: 10 }}>{j}</span>)}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4, fontSize: 12 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Compliance Score</span>
                  <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--mono)', fontWeight: 700 }}>{(l.compliance_score * 100).toFixed(0)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, fontSize: 12 }}>
                  <span style={{ color: 'var(--text-muted)' }}>{l.downloads || 0} downloads · ⭐ {l.rating || '–'}</span>
                  <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--mono)' }}>
                    ${l.price_usd?.toLocaleString()}
                  </span>
                </div>
                <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}
                  onClick={() => purchaseModel(l)} disabled={mktLoading}>
                  {mktLoading ? 'Processing...' : '⛓ Purchase on-chain'}
                </button>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">List Your AI Model</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Model Name</label>
                <input className="form-input" placeholder="e.g. RiskEngine-v1" value={listForm.name}
                  onChange={e => setListForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Vendor Name</label>
                <input className="form-input" placeholder="Your company name" value={listForm.vendor}
                  onChange={e => setListForm(f => ({ ...f, vendor: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Category</label>
                <select className="form-select" value={listForm.category} onChange={e => setListForm(f => ({ ...f, category: e.target.value }))}>
                  {['finance', 'healthcare', 'hr', 'nlp', 'general'].map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Price (USD)</label>
                <input className="form-input" type="number" value={listForm.price_usd}
                  onChange={e => setListForm(f => ({ ...f, price_usd: Number(e.target.value) }))} />
              </div>
            </div>
            <button className="btn btn-primary" onClick={listNewModel} disabled={mktLoading || !listForm.name}>
              {mktLoading ? 'Listing...' : '📤 List on Marketplace'}
            </button>
            {listResult && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 6 }}>
                <div style={{ color: 'var(--accent-green)', fontWeight: 600, marginBottom: 4 }}>✓ Listed — {listResult.listing_id}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Compliance score: {(listResult.compliance_score * 100).toFixed(0)}% · SARO stamp applied</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── ETHICS & SURVEILLANCE ── */}
      {tab === 'ethics' && (
        <div>
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="card">
              <div className="card-header"><span className="card-title">Surveillance Risk Scanner</span></div>
              <div className="form-group">
                <label className="form-label">System Name</label>
                <input className="form-input" placeholder="e.g. CityWatch-AI" value={ethicsForm.system_name}
                  onChange={e => setEthicsForm(f => ({ ...f, system_name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">System Description</label>
                <textarea className="form-textarea" rows={5}
                  placeholder="Describe what your AI system does..."
                  value={ethicsForm.description}
                  onChange={e => setEthicsForm(f => ({ ...f, description: e.target.value }))} />
              </div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>💡 Quick demo scenarios:</div>
                {DEMO_SURVEILLANCE.map(d => (
                  <button key={d.label} className="btn btn-secondary"
                    style={{ fontSize: 11, padding: '5px 10px', marginBottom: 4, width: '100%', justifyContent: 'flex-start' }}
                    onClick={() => setEthicsForm(f => ({ ...f, description: d.text }))}>
                    {d.label}
                  </button>
                ))}
              </div>
              <button className="btn btn-primary" onClick={runEthicsScan}
                disabled={ethicsLoading || !ethicsForm.description.trim()}
                style={{ width: '100%', justifyContent: 'center' }}>
                {ethicsLoading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Scanning...</> : '⚖️ Run Ethics Scan'}
              </button>
            </div>

            <div className="card">
              <div className="card-header"><span className="card-title">Scan Result</span></div>
              {ethicsResult ? (
                <div>
                  <div style={{
                    padding: '14px 16px', borderRadius: 8, marginBottom: 16,
                    background: ethicsResult.overall_risk === 'PROHIBITED' ? 'rgba(255,61,106,0.08)' : ethicsResult.overall_risk === 'HIGH' ? 'rgba(255,184,0,0.08)' : 'rgba(0,255,136,0.08)',
                    border: `1px solid ${ethicsResult.overall_risk === 'PROHIBITED' ? 'rgba(255,61,106,0.3)' : ethicsResult.overall_risk === 'HIGH' ? 'rgba(255,184,0,0.3)' : 'rgba(0,255,136,0.3)'}`,
                  }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: ethicsResult.overall_risk === 'PROHIBITED' ? 'var(--accent-red)' : ethicsResult.overall_risk === 'HIGH' ? 'var(--accent-amber)' : 'var(--accent-green)' }}>
                      {ethicsResult.overall_risk === 'PROHIBITED' ? '🚫 EU AI ACT PROHIBITED' : ethicsResult.overall_risk === 'HIGH' ? '⚠️ HIGH RISK' : '✅ COMPLIANT'}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      {ethicsResult.findings_count} findings · DPIA required: {ethicsResult.requires_dpia ? 'YES' : 'No'}
                    </div>
                  </div>

                  {ethicsResult.findings?.map((f, i) => (
                    <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                        <span className={`badge ${f.severity === 'critical' ? 'badge-red' : 'badge-amber'}`}>{f.severity}</span>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{f.risk_type}</span>
                        {f.eu_ai_act_prohibited && <span className="badge badge-red" style={{ fontSize: 10 }}>EU AI ACT §5</span>}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                        Matched: {f.matched_patterns?.join(', ')}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--accent-cyan)' }}>→ {f.remediation}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                        Regulations: {f.applicable_regulations?.join(' · ')}
                      </div>
                    </div>
                  ))}

                  {ethicsResult.findings_count > 0 && (
                    <button className="btn btn-secondary" style={{ marginTop: 16, width: '100%', justifyContent: 'center' }} onClick={generateDPIA}>
                      📋 Generate DPIA
                    </button>
                  )}
                </div>
              ) : (
                <div className="empty-state">
                  <div className="empty-state-icon">⚖️</div>
                  <div className="empty-state-text">Describe your AI system and run an ethics scan to detect surveillance risks</div>
                </div>
              )}
            </div>
          </div>

          {dpiaResult && (
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <span className="card-title">DPIA — {dpiaResult.system_name}</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>{dpiaResult.dpia_id}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
                {dpiaResult.sections?.map((s, i) => (
                  <div key={i} style={{ padding: '12px 14px', background: 'var(--bg-primary)', borderRadius: 8, border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 14, color: s.status === 'complete' ? 'var(--accent-green)' : s.status === 'required' ? 'var(--accent-amber)' : 'var(--accent-cyan)' }}>
                        {s.status === 'complete' ? '✓' : s.status === 'required' ? '!' : '◎'}
                      </span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{s.title}</span>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.notes}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-header">
              <span className="card-title">EU AI Act — Prohibited Use Cases (Article 5)</span>
              <span className="badge badge-red">{prohibited.length} prohibited</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {prohibited.map((p, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: 20, flexShrink: 0 }}>🚫</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-red)', marginBottom: 3 }}>{p.category}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>{p.description}</div>
                    <div style={{ fontSize: 11, color: 'var(--accent-amber)', fontFamily: 'var(--mono)' }}>Penalty: {p.penalty}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
