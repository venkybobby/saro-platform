/**
 * SARO Policy Intelligence — Merged Chat + Library + Standards
 * =============================================================
 * Primary: AI Policy Chat Agent (instant answers)
 * Secondary: Embedded Policy Library (collapsible, read-only for operators)
 * Secondary: Embedded Standards Explorer (collapsible, article → chat)
 *
 * Replaces three separate nav items (PolicyChat, PolicyLibrary, StandardsExplorer).
 * Admin-only policy management (upload/approve) lives in AdminHub.
 */
import { useState, useEffect, useRef } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (p, b) => fetch(`${BASE}${p}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) }).then(r => r.json())
const get  = (p) => fetch(`${BASE}${p}`).then(r => r.json())

const SESSION_ID = `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

const CATEGORY_COLORS = {
  'EU AI Act':   'red',
  'NIST AI RMF': 'cyan',
  'ISO 42001':   'purple',
  'FDA SaMD':    'amber',
  'MAS TREx':    'green',
  'Compliance':  'amber',
  'SARO':        'cyan',
}

const STANDARD_COLORS = {
  'EU AI Act':   { bg: 'rgba(59,130,246,0.1)',  border: '#3b82f6', emoji: '🇪🇺' },
  'NIST AI RMF': { bg: 'rgba(16,185,129,0.1)',  border: '#10b981', emoji: '🇺🇸' },
  'ISO 42001':   { bg: 'rgba(139,92,246,0.1)',  border: '#8b5cf6', emoji: '🌐' },
  'FDA SaMD':    { bg: 'rgba(239,68,68,0.1)',   border: '#ef4444', emoji: '🏥' },
  'MAS TREx':    { bg: 'rgba(245,158,11,0.1)',  border: '#f59e0b', emoji: '🇸🇬' },
  'GDPR':        { bg: 'rgba(236,72,153,0.1)',  border: '#ec4899', emoji: '🔒' },
}

const RISK_COLORS = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' }

export default function PolicyIntelligence({ onNavigate, session }) {
  // ── Chat state ───────────────────────────────────────────────
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [suggested, setSuggested] = useState([])
  const [chatError, setChatError] = useState('')
  const [turns, setTurns]         = useState(0)
  const bottomRef = useRef(null)

  // ── Panel collapse state ─────────────────────────────────────
  const [libraryOpen, setLibraryOpen]   = useState(false)
  const [standardsOpen, setStandardsOpen] = useState(false)

  // ── Policy Library state ─────────────────────────────────────
  const [policies, setPolicies]     = useState([])
  const [libLoading, setLibLoading] = useState(false)
  const [libFilter, setLibFilter]   = useState({ jurisdiction: 'ALL', search: '' })
  const [selectedPolicy, setSelectedPolicy] = useState(null)

  // ── Standards Explorer state ─────────────────────────────────
  const [standards, setStandards]         = useState(null)
  const [stdLoading, setStdLoading]       = useState(false)
  const [selectedStd, setSelectedStd]     = useState('EU AI Act')
  const [activeArticle, setActiveArticle] = useState(null)
  const [stdSearch, setStdSearch]         = useState('')

  // ── Init: load suggested questions + chat history ────────────
  useEffect(() => {
    get('/api/v1/policy-chat/suggested').then(d => setSuggested(d.questions || [])).catch(() => {})
    get(`/api/v1/policy-chat/history?session_id=${SESSION_ID}`)
      .then(d => {
        if (d.history?.length > 0) {
          setMessages(d.history.map(m => ({ role: m.role, content: m.content })))
          setTurns(d.turns)
        }
      }).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatLoading])

  // ── Load policy library when panel opens ────────────────────
  useEffect(() => {
    if (!libraryOpen) return
    setLibLoading(true)
    get(`/api/v1/policies?jurisdiction=${libFilter.jurisdiction}&status=ALL`)
      .then(d => setPolicies(d.policies || []))
      .catch(() => {})
      .finally(() => setLibLoading(false))
  }, [libraryOpen, libFilter.jurisdiction])

  // ── Load standards when panel opens ─────────────────────────
  useEffect(() => {
    if (!standardsOpen || standards) return
    setStdLoading(true)
    get('/api/v1/mvp1/standards-explorer')
      .then(d => setStandards(d.standards || d))
      .catch(() => {})
      .finally(() => setStdLoading(false))
  }, [standardsOpen])

  // ── Chat actions ─────────────────────────────────────────────
  const sendMessage = async (query = null) => {
    const text = (query || input).trim()
    if (!text) return
    setInput('')
    setChatError('')
    setMessages(m => [...m, { role: 'user', content: text }])
    setChatLoading(true)
    try {
      const data = await post('/api/v1/policy-chat/ask', { query: text, session_id: SESSION_ID })
      setMessages(m => [...m, { role: 'assistant', content: data.answer }])
      setTurns(data.turn)
    } catch (e) {
      const msg = e.message?.includes('429') ? 'Rate limit — max 10 questions/minute' : 'Policy agent unavailable — check API connection'
      setChatError(msg)
      setMessages(m => m.slice(0, -1))
    } finally { setChatLoading(false) }
  }

  const clearChat = async () => {
    await post('/api/v1/policy-chat/clear', { session_id: SESSION_ID }).catch(() => {})
    setMessages([]); setTurns(0); setChatError('')
  }

  // Ask AI about a specific article (from standards explorer)
  const askAboutArticle = (art, stdName) => {
    setInput(`Explain ${art.id} — ${art.title} requirements in detail under ${stdName}`)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // ── Render helpers ───────────────────────────────────────────
  const renderMessage = (msg, i) => {
    const isUser = msg.role === 'user'
    return (
      <div key={i} style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 14 }}>
        {!isUser && (
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(0,212,255,0.15)', border: '1px solid rgba(0,212,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0, marginRight: 10, marginTop: 2 }}>
            🤖
          </div>
        )}
        <div style={{
          maxWidth: '75%', padding: '12px 16px', borderRadius: 12,
          background: isUser ? 'var(--accent-cyan)' : 'var(--bg-card)',
          color: isUser ? '#0a0e1a' : 'var(--text-primary)',
          border: isUser ? 'none' : '1px solid var(--border)',
          fontSize: 13, lineHeight: 1.65,
          borderTopRightRadius: isUser ? 4 : 12,
          borderTopLeftRadius: isUser ? 12 : 4,
          whiteSpace: 'pre-wrap',
        }}>
          {msg.content.split(/(\*\*[^*]+\*\*)/).map((part, pi) =>
            part.startsWith('**') && part.endsWith('**')
              ? <strong key={pi}>{part.slice(2, -2)}</strong>
              : part
          )}
        </div>
        {isUser && (
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(0,212,255,0.15)', border: '1px solid rgba(0,212,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0, marginLeft: 10, marginTop: 2 }}>
            👤
          </div>
        )}
      </div>
    )
  }

  const riskColor = s => s >= 0.75 ? 'var(--accent-red)' : s >= 0.5 ? 'var(--accent-amber)' : 'var(--accent-green)'
  const statusBadge = s => ({ reviewed: 'badge-green', pending_review: 'badge-amber', flagged: 'badge-red' }[s] || 'badge-gray')
  const statusLabel = s => ({ reviewed: 'Reviewed', pending_review: 'Pending', flagged: 'Flagged' }[s] || s)

  const stdNames = standards ? Object.keys(standards) : Object.keys(STANDARD_COLORS)
  const currentStd = standards?.[selectedStd]
  const c = STANDARD_COLORS[selectedStd] || STANDARD_COLORS['EU AI Act']
  const filteredArticles = (currentStd?.articles || []).filter(a =>
    !stdSearch || a.title.toLowerCase().includes(stdSearch.toLowerCase()) || a.id.toLowerCase().includes(stdSearch.toLowerCase())
  )
  const filteredPolicies = policies.filter(p =>
    !libFilter.search || p.title?.toLowerCase().includes(libFilter.search.toLowerCase()) || p.regulation?.toLowerCase().includes(libFilter.search.toLowerCase())
  )

  return (
    <div>
      {/* ── Page header ── */}
      <div className="page-header" style={{ marginBottom: 16 }}>
        <div>
          <h1 className="page-title">Policy Intelligence</h1>
          <p className="page-subtitle">AI-powered policy answers · Embedded library & standards reference</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--accent-purple)', fontWeight: 600, background: 'rgba(139,92,246,0.1)', padding: '4px 10px', borderRadius: 6 }}>⚡ Claude-Powered</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>{turns} turns</span>
          {messages.length > 0 && (
            <button className="btn btn-secondary" style={{ fontSize: 12 }} onClick={clearChat}>🗑 Clear</button>
          )}
        </div>
      </div>

      {/* ── Primary: Chat + sidebar ── */}
      <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 220px)', minHeight: 480, maxHeight: 720, marginBottom: 20 }}>
        {/* Chat window */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 16px' }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>💬</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>SARO Policy Expert</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.7, maxWidth: 420, margin: '0 auto' }}>
                  Ask about EU AI Act, NIST AI RMF, ISO 42001, or any governance requirement.
                  <br /><br />
                  Expand <strong>Policy Library</strong> or <strong>Standards Explorer</strong> below to browse regulations — click any article to ask AI about it.
                </div>
              </div>
            )}
            {messages.map(renderMessage)}
            {chatLoading && (
              <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(0,212,255,0.15)', border: '1px solid rgba(0,212,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>🤖</div>
                <div style={{ padding: '12px 16px', background: 'var(--bg-card)', borderRadius: '4px 12px 12px 12px', border: '1px solid var(--border)', display: 'flex', gap: 6, alignItems: 'center' }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--accent-cyan)', animation: `pulse 1.2s ${i * 0.2}s infinite` }} />
                  ))}
                </div>
              </div>
            )}
            {chatError && (
              <div style={{ padding: '10px 14px', background: 'rgba(255,61,106,0.08)', border: '1px solid rgba(255,61,106,0.3)', borderRadius: 8, fontSize: 12, color: 'var(--accent-red)', marginBottom: 10 }}>
                ⚠️ {chatError}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div style={{ borderTop: '1px solid var(--border)', padding: '14px 16px', display: 'flex', gap: 10 }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder="Ask about EU AI Act Art. 10, NIST bias requirements, ISO 42001 controls... (Enter to send)"
              style={{ flex: 1, background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', color: 'var(--text-primary)', fontSize: 13, resize: 'none', minHeight: 44, maxHeight: 120, fontFamily: 'inherit', lineHeight: 1.5 }}
              rows={1}
              disabled={chatLoading}
            />
            <button className="btn btn-primary" onClick={() => sendMessage()} disabled={chatLoading || !input.trim()} style={{ alignSelf: 'flex-end', padding: '10px 16px' }}>
              {chatLoading ? <div className="loading-spinner" style={{ width: 14, height: 14 }} /> : '→'}
            </button>
          </div>
        </div>

        {/* Right sidebar: suggested + standards coverage + rate limit */}
        <div style={{ width: 240, display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto' }}>
          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 12 }}>Suggested Questions</div>
            {suggested.map((q, i) => {
              const color = CATEGORY_COLORS[q.category] || 'cyan'
              return (
                <div key={i}
                  style={{ padding: '8px 10px', borderRadius: 7, marginBottom: 6, cursor: 'pointer', border: '1px solid var(--border)', transition: 'all 0.15s' }}
                  onClick={() => sendMessage(q.q)}
                  onMouseEnter={el => { el.currentTarget.style.borderColor = `var(--accent-${color})`; el.currentTarget.style.background = `var(--accent-${color}-dim)` }}
                  onMouseLeave={el => { el.currentTarget.style.borderColor = 'var(--border)'; el.currentTarget.style.background = 'transparent' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: `var(--accent-${color})`, textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 3 }}>{q.category}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{q.q}</div>
                </div>
              )
            })}
          </div>

          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>Standards Covered</div>
            {[
              { name: 'EU AI Act',   articles: 'Art. 5, 9, 10, 11, 13–15', color: 'red' },
              { name: 'NIST AI RMF', articles: 'GOVERN, MAP, MEASURE, MANAGE', color: 'cyan' },
              { name: 'ISO 42001',   articles: 'A.5–A.9 controls', color: 'purple' },
              { name: 'FDA SaMD',    articles: '§1–§5.3 clinical AI', color: 'amber' },
              { name: 'MAS TREx',    articles: 'Fairness, Ethics, Accountability', color: 'green' },
            ].map(s => (
              <div key={s.name} style={{ padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: `var(--accent-${s.color})`, marginBottom: 1 }}>{s.name}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{s.articles}</div>
              </div>
            ))}
          </div>

          <div className="card" style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Rate Limit</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>10 questions / min · {turns} turns</div>
            <div className="progress-bar" style={{ marginTop: 8 }}>
              <div style={{ height: '100%', borderRadius: 3, background: 'var(--accent-cyan)', width: `${Math.min(100, (turns / 10) * 100)}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Secondary: Policy Library (collapsible) ── */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', padding: '4px 0' }}
          onClick={() => setLibraryOpen(o => !o)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 16 }}>📋</span>
            <span style={{ fontWeight: 700, fontSize: 14 }}>Policy Library</span>
            <span className="badge badge-gray" style={{ fontSize: 10 }}>{policies.length || ''}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Searchable · Read-only</span>
            <span style={{ fontSize: 14, color: 'var(--text-muted)', transform: libraryOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
          </div>
        </div>

        {libraryOpen && (
          <div style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 14 }}>
              <input
                className="form-input"
                style={{ flex: 1, minWidth: 200 }}
                placeholder="🔍 Search by title or regulation..."
                value={libFilter.search}
                onChange={e => setLibFilter(f => ({ ...f, search: e.target.value }))}
              />
              <select className="form-select" style={{ width: 'auto', padding: '6px 12px' }}
                value={libFilter.jurisdiction} onChange={e => setLibFilter(f => ({ ...f, jurisdiction: e.target.value }))}>
                {['ALL', 'EU', 'US', 'UK', 'CN', 'SG', 'GLOBAL'].map(j => <option key={j}>{j}</option>)}
              </select>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{filteredPolicies.length} policies</span>
            </div>

            {libLoading ? (
              <div style={{ textAlign: 'center', padding: 24 }}><div className="loading-spinner" /></div>
            ) : filteredPolicies.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <div className="empty-state-text">No policies found — admin uploads policies in Setup Hub</div>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Regulation</th>
                    <th>Jurisdiction</th>
                    <th>Risk</th>
                    <th>Status</th>
                    <th>Ask AI</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPolicies.slice(0, 20).map((p, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 500, fontSize: 13 }}>{p.title}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{p.word_count?.toLocaleString()} words</div>
                      </td>
                      <td style={{ fontSize: 12 }}>{p.regulation}</td>
                      <td><span className="badge badge-cyan">{p.jurisdiction}</span></td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div className="progress-bar" style={{ width: 50 }}>
                            <div className="progress-fill" style={{ width: `${(p.risk_score || 0) * 100}%`, background: riskColor(p.risk_score || 0) }} />
                          </div>
                          <span style={{ fontSize: 11, fontFamily: 'var(--mono)', color: riskColor(p.risk_score || 0), fontWeight: 700 }}>{((p.risk_score || 0) * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td><span className={`badge ${statusBadge(p.status)}`}>{statusLabel(p.status)}</span></td>
                      <td>
                        <button className="btn btn-secondary" style={{ fontSize: 11, padding: '3px 8px' }}
                          onClick={() => { setInput(`Explain ${p.title} — ${p.regulation} requirements and compliance obligations`); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
                          💬 Ask
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* ── Secondary: Standards Explorer (collapsible) ── */}
      <div className="card">
        <div
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', padding: '4px 0' }}
          onClick={() => setStandardsOpen(o => !o)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 16 }}>📖</span>
            <span style={{ fontWeight: 700, fontSize: 14 }}>Standards Explorer</span>
            <span className="badge badge-cyan" style={{ fontSize: 10 }}>6 standards</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Article-level · Click to ask AI</span>
            <span style={{ fontSize: 14, color: 'var(--text-muted)', transform: standardsOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
          </div>
        </div>

        {standardsOpen && (
          <div style={{ marginTop: 16 }}>
            {stdLoading ? (
              <div style={{ textAlign: 'center', padding: 24 }}><div className="loading-spinner" /></div>
            ) : (
              <>
                {/* Standard tab bar */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                  {stdNames.map(s => {
                    const col = STANDARD_COLORS[s] || STANDARD_COLORS['EU AI Act']
                    return (
                      <button key={s}
                        onClick={() => { setSelectedStd(s); setActiveArticle(null); setStdSearch('') }}
                        style={{
                          padding: '7px 14px', borderRadius: 8,
                          border: `1px solid ${selectedStd === s ? col.border : 'var(--border)'}`,
                          background: selectedStd === s ? col.bg : 'transparent',
                          color: selectedStd === s ? 'var(--text-primary)' : 'var(--text-muted)',
                          cursor: 'pointer', fontSize: 12, fontWeight: 500,
                          display: 'flex', alignItems: 'center', gap: 5,
                        }}>
                        {col.emoji} {s}
                      </button>
                    )
                  })}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 16 }}>
                  {/* Left: standard overview + article list */}
                  <div>
                    {currentStd && (
                      <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: 10, padding: 14, marginBottom: 12 }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 13, marginBottom: 4 }}>{currentStd.full_name || selectedStd}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{currentStd.jurisdiction} · Effective: {currentStd.effective}</div>
                        <div style={{ marginTop: 8, padding: '6px 10px', background: 'rgba(0,0,0,0.2)', borderRadius: 6, fontSize: 11, color: '#fbbf24' }}>
                          ⚠️ {currentStd.fines}
                        </div>
                      </div>
                    )}
                    <input
                      style={{ width: '100%', padding: '7px 11px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 7, color: 'var(--text-primary)', fontSize: 12, marginBottom: 10, boxSizing: 'border-box' }}
                      placeholder="🔍 Search articles..."
                      value={stdSearch}
                      onChange={e => setStdSearch(e.target.value)}
                    />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, maxHeight: 360, overflowY: 'auto' }}>
                      {filteredArticles.map(art => (
                        <button key={art.id} onClick={() => setActiveArticle(art)}
                          style={{
                            textAlign: 'left', padding: '8px 12px', borderRadius: 7,
                            border: `1px solid ${activeArticle?.id === art.id ? c.border : 'var(--border)'}`,
                            background: activeArticle?.id === art.id ? c.bg : 'transparent',
                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                          }}>
                          <span style={{ background: (RISK_COLORS[art.risk_level] || '#64748b') + '22', color: RISK_COLORS[art.risk_level] || '#64748b', padding: '1px 6px', borderRadius: 5, fontSize: 10, fontWeight: 600, minWidth: 48, textAlign: 'center' }}>
                            {art.risk_level}
                          </span>
                          <div>
                            <div style={{ color: 'var(--accent-cyan)', fontWeight: 600, fontSize: 11 }}>{art.id}</div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{art.title}</div>
                          </div>
                        </button>
                      ))}
                      {filteredArticles.length === 0 && (
                        <div style={{ color: 'var(--text-muted)', padding: '10px', textAlign: 'center', fontSize: 12 }}>No articles match "{stdSearch}"</div>
                      )}
                    </div>
                  </div>

                  {/* Right: article detail */}
                  <div>
                    {activeArticle ? (
                      <div style={{ background: 'var(--bg-card)', border: `1px solid ${c.border}`, borderRadius: 10, padding: 18 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                          <span style={{ background: (RISK_COLORS[activeArticle.risk_level] || '#64748b') + '22', color: RISK_COLORS[activeArticle.risk_level] || '#64748b', padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700 }}>
                            {activeArticle.risk_level?.toUpperCase()}
                          </span>
                          <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 14 }}>{activeArticle.id}</span>
                          <span style={{ color: 'var(--text-primary)', fontSize: 13 }}>· {activeArticle.title}</span>
                        </div>
                        <div style={{ color: 'var(--text-muted)', fontSize: 12, lineHeight: 1.7, marginBottom: 14 }}>
                          {activeArticle.description || `This article establishes requirements for ${activeArticle.title?.toLowerCase()} under ${selectedStd}. Organizations must ensure full compliance to avoid regulatory enforcement action.`}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
                          <div style={{ background: 'var(--bg-primary)', borderRadius: 7, padding: 10 }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 4 }}>COMPLIANCE BENCHMARK</div>
                            <div style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: 13 }}>≥ 85% required</div>
                          </div>
                          <div style={{ background: 'var(--bg-primary)', borderRadius: 7, padding: 10 }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 4 }}>ASSESSMENT TYPE</div>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: 13 }}>Conformity assessment</div>
                          </div>
                        </div>
                        <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}
                          onClick={() => askAboutArticle(activeArticle, selectedStd)}>
                          💬 Ask AI about {activeArticle.id}
                        </button>
                      </div>
                    ) : (
                      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: 32, marginBottom: 10 }}>👈</div>
                        <div style={{ fontSize: 13 }}>Select an article to view details</div>
                        <div style={{ fontSize: 11, marginTop: 6 }}>Click "Ask AI" to start a conversation about it</div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
