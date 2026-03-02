import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_URL || 'https://underground-hildagard-saro-94ba3130.koyeb.app'

const STANDARD_COLORS = {
  'EU AI Act':   { bg: 'rgba(59,130,246,0.1)', border: '#3b82f6', badge: '#1d4ed8', emoji: '🇪🇺' },
  'NIST AI RMF': { bg: 'rgba(16,185,129,0.1)', border: '#10b981', badge: '#065f46', emoji: '🇺🇸' },
  'ISO 42001':   { bg: 'rgba(139,92,246,0.1)', border: '#8b5cf6', badge: '#5b21b6', emoji: '🌐' },
  'FDA SaMD':    { bg: 'rgba(239,68,68,0.1)',  border: '#ef4444', badge: '#991b1b', emoji: '🏥' },
  'MAS TREx':    { bg: 'rgba(245,158,11,0.1)', border: '#f59e0b', badge: '#92400e', emoji: '🇸🇬' },
  'GDPR':        { bg: 'rgba(236,72,153,0.1)', border: '#ec4899', badge: '#9d174d', emoji: '🔒' },
}

const RISK_COLORS = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' }

export default function StandardsExplorer({ onNavigate }) {
  const [standards, setStandards] = useState(null)
  const [selected, setSelected] = useState('EU AI Act')
  const [activeArticle, setActiveArticle] = useState(null)
  const [searchQ, setSearchQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [chatQ, setChatQ] = useState('')
  const [chatA, setChatA] = useState(null)
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/v1/mvp1/standards-explorer`)
      .then(r => r.json()).then(d => { setStandards(d.standards || d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const askPolicy = async () => {
    if (!chatQ.trim()) return
    setChatLoading(true); setChatA(null)
    try {
      const r = await fetch(`${API}/api/v1/policy-chat/ask`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: chatQ, session_id: 'standards-explorer' })
      })
      const d = await r.json()
      setChatA(d.answer || d.detail || 'No answer returned.')
    } catch { setChatA('Error contacting policy chat.') }
    setChatLoading(false)
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div className="spinner" /><span style={{ marginLeft: 12, color: '#94a3b8' }}>Loading standards library...</span>
    </div>
  )

  const stdNames = standards ? Object.keys(standards) : Object.keys(STANDARD_COLORS)
  const currentStd = standards?.[selected]
  const c = STANDARD_COLORS[selected] || STANDARD_COLORS['EU AI Act']

  const filteredArticles = (currentStd?.articles || []).filter(a =>
    !searchQ || a.title.toLowerCase().includes(searchQ.toLowerCase()) || a.id.toLowerCase().includes(searchQ.toLowerCase())
  )

  return (
    <div style={{ padding: '24px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
          <span style={{ fontSize: 28 }}>📚</span>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', margin: 0 }}>Standards Explorer</h1>
          <span style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc', padding: '2px 10px', borderRadius: 12, fontSize: 12 }}>FR-006</span>
        </div>
        <p style={{ color: '#94a3b8', margin: 0, fontSize: 14 }}>
          Browse EU AI Act, NIST AI RMF, ISO 42001, FDA SaMD, MAS TREx, GDPR — article-level detail with compliance benchmarks
        </p>
      </div>

      {/* Standards Tab Bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {stdNames.map(s => {
          const col = STANDARD_COLORS[s] || STANDARD_COLORS['EU AI Act']
          return (
            <button key={s} onClick={() => { setSelected(s); setActiveArticle(null); setSearchQ('') }}
              style={{
                padding: '8px 16px', borderRadius: 8, border: `1px solid ${selected === s ? col.border : '#334155'}`,
                background: selected === s ? col.bg : 'rgba(30,41,59,0.6)',
                color: selected === s ? '#f1f5f9' : '#94a3b8', cursor: 'pointer', fontSize: 13, fontWeight: 500,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
              {col.emoji} {s}
            </button>
          )
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 20 }}>
        {/* Left: Standard overview + article list */}
        <div>
          {/* Standard card */}
          {currentStd && (
            <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: 12, padding: 20, marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span style={{ fontSize: 24 }}>{c.emoji}</span>
                <div>
                  <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 15 }}>{currentStd.full_name || selected}</div>
                  <div style={{ color: '#94a3b8', fontSize: 12 }}>
                    {currentStd.jurisdiction} · Effective: {currentStd.effective}
                  </div>
                </div>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: 10, fontSize: 12, color: '#fbbf24' }}>
                ⚠️ Fines: {currentStd.fines}
              </div>
              {currentStd.applies_to && (
                <div style={{ marginTop: 10, fontSize: 12, color: '#94a3b8' }}>
                  Applies to: {currentStd.applies_to.join(', ')}
                </div>
              )}
            </div>
          )}

          {/* Search */}
          <input value={searchQ} onChange={e => setSearchQ(e.target.value)} placeholder="🔍 Search articles..."
            style={{ width: '100%', padding: '8px 12px', background: 'rgba(30,41,59,0.8)', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9', fontSize: 13, marginBottom: 12, boxSizing: 'border-box' }} />

          {/* Article list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 420, overflowY: 'auto' }}>
            {filteredArticles.map(art => (
              <button key={art.id} onClick={() => setActiveArticle(art)}
                style={{
                  textAlign: 'left', padding: '10px 14px', borderRadius: 8,
                  border: `1px solid ${activeArticle?.id === art.id ? c.border : '#334155'}`,
                  background: activeArticle?.id === art.id ? c.bg : 'rgba(30,41,59,0.4)',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                }}>
                <span style={{ background: RISK_COLORS[art.risk_level] + '22', color: RISK_COLORS[art.risk_level], padding: '1px 7px', borderRadius: 6, fontSize: 11, fontWeight: 600, minWidth: 52, textAlign: 'center' }}>
                  {art.risk_level}
                </span>
                <div>
                  <div style={{ color: '#a5b4fc', fontWeight: 600, fontSize: 12 }}>{art.id}</div>
                  <div style={{ color: '#cbd5e1', fontSize: 13 }}>{art.title}</div>
                </div>
              </button>
            ))}
            {filteredArticles.length === 0 && <div style={{ color: '#64748b', padding: '12px', textAlign: 'center' }}>No articles match "{searchQ}"</div>}
          </div>
        </div>

        {/* Right: Article detail + Policy Chat */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Article detail */}
          {activeArticle ? (
            <div style={{ background: 'rgba(30,41,59,0.8)', border: `1px solid ${c.border}`, borderRadius: 12, padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                <span style={{ background: RISK_COLORS[activeArticle.risk_level] + '22', color: RISK_COLORS[activeArticle.risk_level], padding: '3px 10px', borderRadius: 8, fontSize: 12, fontWeight: 700 }}>{activeArticle.risk_level.toUpperCase()}</span>
                <div>
                  <span style={{ color: '#a5b4fc', fontWeight: 700, fontSize: 16 }}>{activeArticle.id}</span>
                  <span style={{ color: '#94a3b8', marginLeft: 8, fontSize: 14 }}>·</span>
                  <span style={{ color: '#e2e8f0', fontSize: 15, marginLeft: 8 }}>{activeArticle.title}</span>
                </div>
              </div>
              <div style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.7, marginBottom: 16 }}>
                {activeArticle.description || `This article establishes requirements for ${activeArticle.title.toLowerCase()} under ${selected}. Organizations must ensure full compliance to avoid regulatory enforcement action and maintain certification status.`}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: 12 }}>
                  <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>COMPLIANCE BENCHMARK</div>
                  <div style={{ color: '#22c55e', fontWeight: 700 }}>≥ 85% required</div>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: 12 }}>
                  <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>ASSESSMENT TYPE</div>
                  <div style={{ color: '#f1f5f9', fontWeight: 600 }}>Conformity assessment</div>
                </div>
              </div>
              <button onClick={() => { setChatQ(`Explain ${activeArticle.id} — ${activeArticle.title} requirements in detail`); setChatA(null) }}
                style={{ marginTop: 14, padding: '8px 16px', background: 'rgba(99,102,241,0.2)', border: '1px solid #6366f1', color: '#a5b4fc', borderRadius: 8, cursor: 'pointer', fontSize: 13 }}>
                💬 Ask AI about {activeArticle.id}
              </button>
            </div>
          ) : (
            <div style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid #334155', borderRadius: 12, padding: 32, textAlign: 'center', color: '#64748b' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>👈</div>
              <div>Select an article to view details</div>
            </div>
          )}

          {/* Policy Chat Widget */}
          <div style={{ background: 'rgba(30,41,59,0.8)', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <span>🤖</span>
              <span style={{ fontWeight: 600, color: '#f1f5f9' }}>AI Policy Assistant</span>
              <span style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc', padding: '1px 8px', borderRadius: 8, fontSize: 11 }}>FR-007</span>
            </div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <input value={chatQ} onChange={e => setChatQ(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && askPolicy()}
                placeholder="Ask about any regulation or article..."
                style={{ flex: 1, padding: '8px 12px', background: 'rgba(15,23,42,0.8)', border: '1px solid #475569', borderRadius: 8, color: '#f1f5f9', fontSize: 13 }} />
              <button onClick={askPolicy} disabled={chatLoading}
                style={{ padding: '8px 16px', background: chatLoading ? '#334155' : 'rgba(99,102,241,0.3)', border: '1px solid #6366f1', color: '#a5b4fc', borderRadius: 8, cursor: 'pointer', fontSize: 13 }}>
                {chatLoading ? '...' : 'Ask'}
              </button>
            </div>
            {chatA && (
              <div style={{ background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: 14, fontSize: 13, color: '#cbd5e1', lineHeight: 1.7, maxHeight: 200, overflowY: 'auto' }}>
                {chatA}
              </div>
            )}
            {/* Quick question chips */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
              {[`What does ${selected} require?`, 'What are the key fines?', 'How to achieve compliance?'].map(q => (
                <button key={q} onClick={() => { setChatQ(q); setChatA(null) }}
                  style={{ padding: '4px 10px', background: 'rgba(30,41,59,0.8)', border: '1px solid #334155', color: '#94a3b8', borderRadius: 6, cursor: 'pointer', fontSize: 11 }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
