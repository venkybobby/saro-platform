/**
 * AI Policy Chat Agent (FR-02, FR-INNOV-01..03)
 * Claude-powered interactive policy explanations.
 * Context: EU AI Act, NIST AI RMF, ISO 42001, FDA SaMD, MAS TREx
 * Rate limited: 10 requests/minute
 */
import { useState, useEffect, useRef } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const post = (p, b) => fetch(`${BASE}${p}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b) }).then(r => r.json())
const get  = (p) => fetch(`${BASE}${p}`).then(r => r.json())

const SESSION_ID = `chat-${Date.now()}-${Math.random().toString(36).slice(2,8)}`

const CATEGORY_COLORS = {
  'EU AI Act':   'red',
  'NIST AI RMF': 'cyan',
  'ISO 42001':   'purple',
  'FDA SaMD':    'amber',
  'MAS TREx':    'green',
  'Compliance':  'amber',
  'SARO':        'cyan',
}

export default function PolicyChat({ onNavigate }) {
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [suggested, setSuggested] = useState([])
  const [error, setError]         = useState('')
  const [turns, setTurns]         = useState(0)
  const bottomRef = useRef(null)

  useEffect(() => {
    get('/api/v1/policy-chat/suggested').then(d => setSuggested(d.questions || [])).catch(() => {})
    // Load session history if exists
    get(`/api/v1/policy-chat/history?session_id=${SESSION_ID}`)
      .then(d => {
        if (d.history?.length > 0) {
          setMessages(d.history.map(m => ({ role:m.role, content:m.content })))
          setTurns(d.turns)
        }
      }).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior:'smooth' })
  }, [messages, loading])

  const sendMessage = async (query = null) => {
    const text = (query || input).trim()
    if (!text) return
    setInput('')
    setError('')
    setMessages(m => [...m, { role:'user', content:text }])
    setLoading(true)
    try {
      const data = await post('/api/v1/policy-chat/ask', { query: text, session_id: SESSION_ID })
      setMessages(m => [...m, { role:'assistant', content:data.answer }])
      setTurns(data.turn)
    } catch(e) {
      const msg = e.message?.includes('429') ? 'Rate limit — max 10 questions/minute' : 'Policy agent unavailable — check API connection'
      setError(msg)
      setMessages(m => m.slice(0,-1))   // remove user msg on error
    } finally { setLoading(false) }
  }

  const clearChat = async () => {
    await post('/api/v1/policy-chat/clear', { session_id: SESSION_ID }).catch(() => {})
    setMessages([]); setTurns(0); setError('')
  }

  const renderMessage = (msg, i) => {
    const isUser = msg.role === 'user'
    return (
      <div key={i} style={{ display:'flex',justifyContent:isUser?'flex-end':'flex-start',marginBottom:14 }}>
        {!isUser && (
          <div style={{ width:32,height:32,borderRadius:'50%',background:'rgba(0,212,255,0.15)',border:'1px solid rgba(0,212,255,0.3)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14,flexShrink:0,marginRight:10,marginTop:2 }}>
            🤖
          </div>
        )}
        <div style={{
          maxWidth:'75%',padding:'12px 16px',borderRadius:12,
          background: isUser ? 'var(--accent-cyan)' : 'var(--bg-card)',
          color: isUser ? '#0a0e1a' : 'var(--text-primary)',
          border: isUser ? 'none' : '1px solid var(--border)',
          fontSize:13,lineHeight:1.65,
          borderTopRightRadius: isUser ? 4 : 12,
          borderTopLeftRadius:  isUser ? 12 : 4,
          whiteSpace:'pre-wrap',
        }}>
          {/* Render **bold** markdown-style */}
          {msg.content.split(/(\*\*[^*]+\*\*)/).map((part, pi) =>
            part.startsWith('**') && part.endsWith('**')
              ? <strong key={pi}>{part.slice(2,-2)}</strong>
              : part
          )}
        </div>
        {isUser && (
          <div style={{ width:32,height:32,borderRadius:'50%',background:'rgba(0,212,255,0.15)',border:'1px solid rgba(0,212,255,0.3)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14,flexShrink:0,marginLeft:10,marginTop:2 }}>
            👤
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ display:'flex',flexDirection:'column',height:'calc(100vh - 120px)',maxHeight:900 }}>
      <div className="page-header" style={{ marginBottom:0,paddingBottom:16 }}>
        <div>
          <h1 className="page-title">AI Policy Chat Agent</h1>
          <p className="page-subtitle">Ask any AI governance question — EU AI Act, NIST AI RMF, ISO 42001, FDA SaMD, MAS TREx</p>
        </div>
        <div style={{ display:'flex',gap:10,alignItems:'center' }}>
          <span style={{ fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>{turns} turns</span>
          {messages.length > 0 && (
            <button className="btn btn-secondary" style={{ fontSize:12 }} onClick={clearChat}>
              🗑 Clear
            </button>
          )}
          <span style={{ fontSize:11,color:'var(--accent-purple)',fontWeight:600,background:'rgba(139,92,246,0.1)',padding:'4px 10px',borderRadius:6 }}>⚡ Claude-Powered</span>
        </div>
      </div>

      <div style={{ display:'flex',flex:1,gap:16,overflow:'hidden',marginTop:16 }}>
        {/* Chat window */}
        <div style={{ flex:1,display:'flex',flexDirection:'column',background:'var(--bg-card)',borderRadius:12,border:'1px solid var(--border)',overflow:'hidden' }}>
          {/* Messages area */}
          <div style={{ flex:1,overflowY:'auto',padding:'20px 16px' }}>
            {messages.length === 0 && (
              <div style={{ textAlign:'center',padding:'60px 20px' }}>
                <div style={{ fontSize:40,marginBottom:12 }}>💬</div>
                <div style={{ fontSize:16,fontWeight:700,color:'var(--text-primary)',marginBottom:8 }}>SARO Policy Expert</div>
                <div style={{ fontSize:13,color:'var(--text-muted)',lineHeight:1.7,maxWidth:400,margin:'0 auto' }}>
                  Ask me anything about AI governance regulations, compliance requirements, or how SARO helps you meet them.
                  <br /><br />
                  Try one of the suggested questions →
                </div>
              </div>
            )}
            {messages.map(renderMessage)}
            {loading && (
              <div style={{ display:'flex',gap:10,marginBottom:14 }}>
                <div style={{ width:32,height:32,borderRadius:'50%',background:'rgba(0,212,255,0.15)',border:'1px solid rgba(0,212,255,0.3)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14,flexShrink:0 }}>🤖</div>
                <div style={{ padding:'12px 16px',background:'var(--bg-card)',borderRadius:'4px 12px 12px 12px',border:'1px solid var(--border)',display:'flex',gap:6,alignItems:'center' }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{ width:7,height:7,borderRadius:'50%',background:'var(--accent-cyan)',animation:`pulse 1.2s ${i*0.2}s infinite` }} />
                  ))}
                </div>
              </div>
            )}
            {error && (
              <div style={{ padding:'10px 14px',background:'rgba(255,61,106,0.08)',border:'1px solid rgba(255,61,106,0.3)',borderRadius:8,fontSize:12,color:'var(--accent-red)',marginBottom:10 }}>
                ⚠️ {error}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input area */}
          <div style={{ borderTop:'1px solid var(--border)',padding:'14px 16px',display:'flex',gap:10 }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder="Ask about EU AI Act Art. 10, NIST bias requirements, ISO 42001 controls... (Enter to send)"
              style={{ flex:1,background:'var(--bg-primary)',border:'1px solid var(--border)',borderRadius:8,padding:'10px 12px',color:'var(--text-primary)',fontSize:13,resize:'none',minHeight:44,maxHeight:120,fontFamily:'inherit',lineHeight:1.5 }}
              rows={1}
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={() => sendMessage()} disabled={loading || !input.trim()}
              style={{ alignSelf:'flex-end',padding:'10px 16px' }}>
              {loading ? <div className="loading-spinner" style={{width:14,height:14}} /> : '→'}
            </button>
          </div>
        </div>

        {/* Suggested questions sidebar */}
        <div style={{ width:260,display:'flex',flexDirection:'column',gap:12,overflow:'auto' }}>
          <div className="card" style={{ padding:'14px 16px' }}>
            <div style={{ fontSize:12,fontWeight:700,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:12 }}>Suggested Questions</div>
            {suggested.map((q, i) => {
              const color = CATEGORY_COLORS[q.category] || 'cyan'
              return (
                <div key={i}
                  style={{ padding:'8px 10px',borderRadius:7,marginBottom:6,cursor:'pointer',border:'1px solid var(--border)',transition:'all 0.15s' }}
                  onClick={() => sendMessage(q.q)}
                  onMouseEnter={el => { el.currentTarget.style.borderColor = `var(--accent-${color})`; el.currentTarget.style.background = `var(--accent-${color}-dim)` }}
                  onMouseLeave={el => { el.currentTarget.style.borderColor = 'var(--border)'; el.currentTarget.style.background = 'transparent' }}>
                  <div style={{ fontSize:10,fontWeight:700,color:`var(--accent-${color})`,textTransform:'uppercase',letterSpacing:'0.4px',marginBottom:3 }}>{q.category}</div>
                  <div style={{ fontSize:11,color:'var(--text-secondary)',lineHeight:1.5 }}>{q.q}</div>
                </div>
              )
            })}
          </div>

          <div className="card" style={{ padding:'14px 16px' }}>
            <div style={{ fontSize:12,fontWeight:700,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:10 }}>Standards Covered</div>
            {[
              { name:'EU AI Act', articles:'Art. 5, 9, 10, 11, 13, 14, 15, 22, 52', color:'red' },
              { name:'NIST AI RMF', articles:'GOVERN, MAP, MEASURE, MANAGE', color:'cyan' },
              { name:'ISO 42001', articles:'A.5–A.9 controls', color:'purple' },
              { name:'FDA SaMD', articles:'§1–§5.3 clinical AI', color:'amber' },
              { name:'MAS TREx', articles:'Fairness, Ethics, Accountability', color:'green' },
            ].map(s => (
              <div key={s.name} style={{ padding:'6px 0',borderBottom:'1px solid var(--border)' }}>
                <div style={{ fontSize:11,fontWeight:700,color:`var(--accent-${s.color})`,marginBottom:1 }}>{s.name}</div>
                <div style={{ fontSize:10,color:'var(--text-muted)' }}>{s.articles}</div>
              </div>
            ))}
          </div>

          <div className="card" style={{ padding:'14px 16px' }}>
            <div style={{ fontSize:12,fontWeight:700,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Rate Limit</div>
            <div style={{ fontSize:12,color:'var(--text-secondary)' }}>10 questions / minute · {turns} turns this session</div>
            <div className="progress-bar" style={{ marginTop:8 }}>
              <div style={{ height:'100%',borderRadius:3,background:'var(--accent-cyan)',width:`${Math.min(100,(turns/10)*100)}%` }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
