/**
 * Magic Link Login Page (FR-01, FR-SIMP-01..03, FR-ONB-01..03)
 * Passwordless login + 1-click Try Free trial.
 * Auto-detects persona from email domain.
 * Validates ?token= query param on load (link click).
 */
import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (p, b) => fetch(`${BASE}${p}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b) }).then(r => r.json())
const get  = (p) => fetch(`${BASE}${p}`).then(r => r.json())

const PERSONA_COLORS = {
  forecaster: 'cyan', autopsier: 'amber', enabler: 'green', evangelist: 'purple'
}

const PERSONA_ICONS = {
  forecaster: '📈', autopsier: '🔍', enabler: '⚙️', evangelist: '🎯'
}

const PERSONA_DESCRIPTIONS = {
  forecaster: 'Regulatory intelligence & risk forecasting',
  autopsier:  'Deep audit findings & evidence chains',
  enabler:    'Controls, policies & remediation automation',
  evangelist: 'Executive summaries & ROI metrics',
}

export default function Login({ onLogin }) {
  const [mode, setMode]           = useState('magic')   // 'magic' | 'tryfree'
  const [email, setEmail]         = useState('')
  const [persona, setPersona]     = useState('enabler')
  const [autoDetected, setAutoDetected] = useState(false)
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)
  const [error, setError]         = useState('')
  const [validating, setValidating] = useState(false)

  // On mount: check for ?token= in URL (magic link click)
  useEffect(() => {
    const params  = new URLSearchParams(window.location.search)
    const token   = params.get('token')
    if (token) {
      setValidating(true)
      get(`/api/v1/auth/validate?token=${encodeURIComponent(token)}`)
        .then(data => {
          if (data.status === 'authenticated') {
            localStorage.setItem('saro_session', JSON.stringify(data))
            onLogin && onLogin(data)
          } else {
            setError('Invalid or expired magic link — request a new one')
          }
        })
        .catch(() => setError('Could not validate link — please try again'))
        .finally(() => setValidating(false))
    }
  }, [])

  // Auto-detect persona from email domain
  const handleEmailChange = (val) => {
    setEmail(val)
    if (val.includes('@')) {
      const domain = val.toLowerCase().split('@')[1]?.split('.')[0] || ''
      const map = {
        bank:'forecaster', finance:'forecaster', invest:'forecaster', capital:'forecaster',
        audit:'autopsier', compliance:'autopsier', risk:'autopsier', legal:'autopsier',
        tech:'enabler', eng:'enabler', data:'enabler', it:'enabler',
        exec:'evangelist', ceo:'evangelist', cfo:'evangelist',
      }
      for (const [kw, p] of Object.entries(map)) {
        if (domain.includes(kw)) { setPersona(p); setAutoDetected(true); return }
      }
      setAutoDetected(false)
    }
  }

  const sendMagicLink = async () => {
    if (!email.trim() || !email.includes('@')) { setError('Valid email required'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await post('/api/v1/auth/magic-link', { email, persona })
      setResult(data)
    } catch(e) { setError('Could not generate link — check API connection') }
    finally { setLoading(false) }
  }

  const handleTryFree = async () => {
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await post('/api/v1/auth/try-free', email ? { email, persona } : {})
      setResult({ ...data, mode: 'trial' })
    } catch(e) { setError('Could not start trial — check API connection') }
    finally { setLoading(false) }
  }

  const useToken = (token) => {
    setValidating(true)
    get(`/api/v1/auth/validate?token=${encodeURIComponent(token)}`)
      .then(data => {
        if (data.status === 'authenticated') {
          localStorage.setItem('saro_session', JSON.stringify(data))
          onLogin && onLogin(data)
        } else { setError('Token validation failed') }
      })
      .catch(() => setError('Validation error'))
      .finally(() => setValidating(false))
  }

  const skipLogin = () => {
    // Demo mode: skip auth and use platform directly
    const demo = { email:'demo@saro.ai', persona:'enabler', persona_name:'Enabler', persona_icon:'⚙️', persona_color:'green', default_page:'dashboard', tenant_id:'DEMO-0000', is_trial:false }
    localStorage.setItem('saro_session', JSON.stringify(demo))
    onLogin && onLogin(demo)
  }

  if (validating) {
    return (
      <div style={{ display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',minHeight:'100vh',background:'var(--bg-primary)',gap:16 }}>
        <div className="loading-spinner" style={{ width:32,height:32 }} />
        <div style={{ color:'var(--text-muted)',fontSize:14 }}>Validating magic link...</div>
      </div>
    )
  }

  return (
    <div style={{ display:'flex',minHeight:'100vh',background:'var(--bg-primary)' }}>
      {/* Left branding panel */}
      <div style={{ width:420,background:'var(--bg-secondary)',borderRight:'1px solid var(--border)',padding:'48px 40px',display:'flex',flexDirection:'column',justifyContent:'space-between' }}>
        <div>
          <div style={{ display:'flex',alignItems:'center',gap:12,marginBottom:48 }}>
            <div style={{ width:44,height:44,background:'var(--accent-cyan)',borderRadius:10,display:'flex',alignItems:'center',justifyContent:'center',fontSize:20,fontWeight:900,color:'#000' }}>S</div>
            <div>
              <div style={{ fontSize:20,fontWeight:800,letterSpacing:'-0.5px' }}>SARO</div>
              <div style={{ fontSize:11,color:'var(--text-muted)' }}>AI Regulatory Intelligence</div>
            </div>
          </div>
          <div style={{ fontSize:28,fontWeight:800,lineHeight:1.2,marginBottom:16 }}>
            AI governance,<br />
            <span style={{ color:'var(--accent-cyan)' }}>without the complexity</span>
          </div>
          <div style={{ fontSize:14,color:'var(--text-muted)',lineHeight:1.7,marginBottom:32 }}>
            Ingest regulatory standards, audit AI model outputs, enforce guardrails, and generate standards-aligned reports — all in one platform.
          </div>
          <div style={{ display:'flex',flexDirection:'column',gap:12 }}>
            {[
              ['◈', 'Regulatory ingestion & forecasting', 'cyan'],
              ['◉', 'EU AI Act / NIST / ISO 42001 audits', 'amber'],
              ['◐', 'Real-time bias & PII guardrails', 'green'],
              ['◆', 'Autonomous remediation bots', 'purple'],
            ].map(([icon, label, color]) => (
              <div key={label} style={{ display:'flex',alignItems:'center',gap:10,fontSize:13 }}>
                <span style={{ color:`var(--accent-${color})`,fontSize:16 }}>{icon}</span>
                <span style={{ color:'var(--text-secondary)' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ fontSize:11,color:'var(--text-muted)' }}>
          963 tests passing · v6.0.0 · SOC 2 compliant
        </div>
      </div>

      {/* Right login panel */}
      <div style={{ flex:1,display:'flex',alignItems:'center',justifyContent:'center',padding:40 }}>
        <div style={{ width:'100%',maxWidth:440 }}>
          <h1 style={{ fontSize:26,fontWeight:800,marginBottom:6 }}>Sign in to SARO</h1>
          <p style={{ fontSize:13,color:'var(--text-muted)',marginBottom:32 }}>Passwordless — magic link sent instantly</p>

          {/* Mode toggle */}
          <div style={{ display:'flex',gap:0,marginBottom:28,background:'var(--bg-secondary)',borderRadius:8,border:'1px solid var(--border)',padding:4 }}>
            {[['magic','✉️ Magic Link'],['tryfree','🚀 Try Free']].map(([m,l]) => (
              <button key={m} className={`btn ${mode===m?'btn-primary':'btn-secondary'}`}
                style={{ flex:1,justifyContent:'center',fontSize:13,border:'none',borderRadius:6 }}
                onClick={() => { setMode(m); setResult(null); setError('') }}>
                {l}
              </button>
            ))}
          </div>

          {mode === 'magic' && (
            <>
              <div className="form-group">
                <label className="form-label">Work email</label>
                <input className="form-input" type="email" placeholder="you@company.com"
                  value={email} onChange={e => handleEmailChange(e.target.value)} />
              </div>

              <div className="form-group">
                <label className="form-label" style={{ display:'flex',justifyContent:'space-between' }}>
                  <span>Persona</span>
                  {autoDetected && <span style={{ fontSize:10,color:'var(--accent-cyan)',fontWeight:600 }}>✓ Auto-detected from email</span>}
                </label>
                <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:8 }}>
                  {['forecaster','autopsier','enabler','evangelist'].map(p => {
                    const c = PERSONA_COLORS[p]
                    return (
                      <div key={p}
                        style={{ padding:'10px 12px',borderRadius:8,cursor:'pointer',border:`1px solid ${persona===p?`var(--accent-${c})`:'var(--border)'}`,background:persona===p?`var(--accent-${c}-dim)`:'transparent',transition:'all 0.15s' }}
                        onClick={() => { setPersona(p); setAutoDetected(false) }}>
                        <div style={{ fontSize:16,marginBottom:3 }}>{PERSONA_ICONS[p]}</div>
                        <div style={{ fontSize:12,fontWeight:700,color:'var(--text-primary)',textTransform:'capitalize' }}>{p}</div>
                        <div style={{ fontSize:10,color:'var(--text-muted)',lineHeight:1.4 }}>{PERSONA_DESCRIPTIONS[p]}</div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center',marginTop:8 }}
                onClick={sendMagicLink} disabled={loading}>
                {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Sending...</> : '✉️ Send Magic Link'}
              </button>
            </>
          )}

          {mode === 'tryfree' && (
            <>
              <div style={{ padding:'16px',background:'rgba(0,255,136,0.05)',borderRadius:10,border:'1px solid rgba(0,255,136,0.2)',marginBottom:20 }}>
                <div style={{ fontSize:14,fontWeight:700,color:'var(--accent-green)',marginBottom:6 }}>🚀 1-Click Trial — No Card Required</div>
                <div style={{ fontSize:12,color:'var(--text-muted)',lineHeight:1.6 }}>
                  14 days free · 10 model audits · All modules · Auto-configured for your persona
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Email (optional — gets you the magic link)</label>
                <input className="form-input" type="email" placeholder="you@company.com (optional)"
                  value={email} onChange={e => handleEmailChange(e.target.value)} />
              </div>
              <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center',fontSize:15,padding:'12px' }}
                onClick={handleTryFree} disabled={loading}>
                {loading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Creating trial...</> : '🚀 Start Free Trial — 1 Click'}
              </button>
            </>
          )}

          {error && (
            <div style={{ marginTop:14,padding:'10px 14px',background:'rgba(255,61,106,0.08)',border:'1px solid rgba(255,61,106,0.3)',borderRadius:8,fontSize:12,color:'var(--accent-red)' }}>
              {error}
            </div>
          )}

          {result && (
            <div style={{ marginTop:16,padding:'16px',background:'rgba(0,212,255,0.05)',border:'1px solid rgba(0,212,255,0.2)',borderRadius:10 }}>
              {result.mode === 'trial' ? (
                <>
                  <div style={{ fontSize:14,fontWeight:700,color:'var(--accent-green)',marginBottom:10 }}>
                    ✅ Trial Started — {result.persona_icon} {result.persona_name} Persona
                  </div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:12 }}>
                    Tenant: <span style={{ fontFamily:'var(--mono)',color:'var(--accent-cyan)' }}>{result.tenant_id}</span> ·
                    Expires: {new Date(result.trial_ends).toLocaleDateString()} · {result.model_limit} model audits
                  </div>
                  <div style={{ display:'flex',flexDirection:'column',gap:4,marginBottom:14 }}>
                    {result.onboarding_steps?.map((s, i) => (
                      <div key={i} style={{ display:'flex',gap:8,alignItems:'center',fontSize:12 }}>
                        <span style={{ color:s.done?'var(--accent-green)':'var(--text-muted)' }}>{s.done?'✓':'○'}</span>
                        <span style={{ color:s.done?'var(--text-primary)':'var(--text-muted)' }}>{s.label}</span>
                      </div>
                    ))}
                  </div>
                  <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center' }}
                    onClick={() => useToken(result.token)} disabled={validating}>
                    {validating ? 'Entering platform...' : '→ Enter SARO Platform'}
                  </button>
                </>
              ) : (
                <>
                  <div style={{ fontSize:14,fontWeight:700,color:'var(--accent-cyan)',marginBottom:8 }}>
                    ✉️ Link Generated — {result.persona_icon} {result.persona_name} Persona
                  </div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:12 }}>
                    Persona auto-detected: <strong style={{ color:`var(--accent-${PERSONA_COLORS[result.persona]})` }}>{result.persona}</strong> ·
                    Expires in {result.expires_in}
                  </div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:10,fontStyle:'italic' }}>
                    In production this is emailed. For demo — click below to enter directly:
                  </div>
                  <button className="btn btn-primary" style={{ width:'100%',justifyContent:'center' }}
                    onClick={() => useToken(result.token)} disabled={validating}>
                    {validating ? 'Validating...' : '→ Use This Link — Enter Platform'}
                  </button>
                </>
              )}
            </div>
          )}

          <div style={{ marginTop:24,textAlign:'center' }}>
            <button style={{ background:'none',border:'none',color:'var(--text-muted)',cursor:'pointer',fontSize:12,textDecoration:'underline' }}
              onClick={skipLogin}>
              Skip login — Demo mode
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
