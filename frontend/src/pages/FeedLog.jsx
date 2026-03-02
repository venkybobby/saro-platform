import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''

export default function FeedLog({ onNavigate }) {
  const [feeds, setFeeds] = useState([])
  const [meta, setMeta] = useState({})
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [approvingId, setApprovingId] = useState(null)

  useEffect(() => { loadFeed() }, [filter])

  const loadFeed = () => {
    setLoading(true)
    fetch(`${BASE}/api/v1/feed-log?jurisdiction=${filter}`)
      .then(r => r.json())
      .then(d => { setFeeds(d.feeds || []); setMeta(d) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const approve = async (feedId) => {
    setApprovingId(feedId)
    await fetch(`${BASE}/api/v1/feed-log/${feedId}/approve`, { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}' })
    setFeeds(prev => prev.map(f => f.feed_id === feedId ? {...f, status:'reviewed', is_new:false} : f))
    setApprovingId(null)
  }

  const impactColor = i => ({ critical:'var(--accent-red)', high:'var(--accent-amber)', medium:'var(--accent-cyan)', low:'var(--accent-green)' }[i] || 'var(--text-muted)')
  const statusBadge = s => ({ reviewed:'badge-green', pending_review:'badge-amber', flagged:'badge-red' }[s] || 'badge-gray')

  const newCount = feeds.filter(f => f.is_new).length

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Regulatory Feed</h1>
          <p className="page-subtitle">Live regulatory intelligence feed — new entries auto-tagged, reviewed, and pushed to policy library</p>
        </div>
        {newCount > 0 && <span className="badge badge-amber" style={{ fontSize:13,padding:'6px 14px' }}>{newCount} new items</span>}
      </div>

      <div className="metrics-grid-4" style={{ marginBottom:24 }}>
        {[
          { label:'Total Feeds', value:meta.total || feeds.length, color:'cyan' },
          { label:'New Items', value:meta.new_count || newCount, color:'amber' },
          { label:'Last Polled', value:meta.last_polled ? new Date(meta.last_polled).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '—', color:'green' },
          { label:'Next Poll', value:meta.next_poll ? new Date(meta.next_poll).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '—', color:'purple' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding:'14px 16px' }}>
            <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:6 }}>{m.label}</div>
            <div style={{ fontSize:18,fontWeight:700,fontFamily:'var(--mono)',color:`var(--accent-${m.color})` }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom:16,padding:'12px 20px' }}>
        <div style={{ display:'flex',gap:8,alignItems:'center',flexWrap:'wrap' }}>
          <span style={{ fontSize:12,color:'var(--text-muted)',fontWeight:600 }}>Jurisdiction:</span>
          {['ALL','EU','US','UK','SG','GLOBAL'].map(j => (
            <button key={j} className={`btn ${filter===j?'btn-primary':'btn-secondary'}`} style={{ padding:'5px 14px',fontSize:12 }} onClick={() => setFilter(j)}>{j}</button>
          ))}
          <button className="btn btn-secondary" style={{ marginLeft:'auto',fontSize:12 }} onClick={loadFeed}>↻ Refresh</button>
        </div>
      </div>

      {loading ? (
        <div className="loading-overlay"><div className="loading-spinner" /><span>Loading feed...</span></div>
      ) : (
        <div style={{ display:'flex',flexDirection:'column',gap:12 }}>
          {feeds.map((f, i) => (
            <div key={i} className="card" style={{ padding:'16px 20px',borderLeft:`3px solid ${f.is_new ? impactColor(f.impact) : 'var(--border)'}` }}>
              <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:12 }}>
                <div style={{ flex:1 }}>
                  <div style={{ display:'flex',gap:8,alignItems:'center',marginBottom:8,flexWrap:'wrap' }}>
                    {f.is_new && <span style={{ fontSize:10,fontWeight:700,color:'var(--accent-amber)',background:'rgba(255,184,0,0.12)',padding:'2px 8px',borderRadius:20 }}>NEW</span>}
                    <span className="badge badge-cyan">{f.jurisdiction}</span>
                    <span className="badge badge-gray">{f.regulation}</span>
                    <span style={{ fontSize:11,color:impactColor(f.impact),fontWeight:700,textTransform:'uppercase' }}>{f.impact} impact</span>
                  </div>
                  <div style={{ fontSize:14,fontWeight:600,color:'var(--text-primary)',marginBottom:6 }}>{f.headline}</div>
                  <div style={{ fontSize:11,color:'var(--text-muted)' }}>
                    Source: {f.feed} · Fetched: {f.fetched_at ? new Date(f.fetched_at).toLocaleString() : '—'}
                    {f.risk_score && <span style={{ marginLeft:8,color:'var(--accent-amber)',fontFamily:'var(--mono)' }}>Risk: {(f.risk_score*100).toFixed(0)}%</span>}
                  </div>
                </div>
                <div style={{ display:'flex',flexDirection:'column',gap:8,alignItems:'flex-end' }}>
                  <span className={`badge ${statusBadge(f.status)}`}>{f.status?.replace('_',' ')}</span>
                  {f.status !== 'reviewed' && (
                    <button className="btn btn-secondary" style={{ fontSize:11,padding:'4px 12px',color:'var(--accent-green)',borderColor:'rgba(0,255,136,0.3)' }}
                      onClick={() => approve(f.feed_id)} disabled={approvingId === f.feed_id}>
                      {approvingId === f.feed_id ? '...' : '✓ Approve'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          {feeds.length === 0 && (
            <div className="empty-state"><div className="empty-state-icon">📡</div><div className="empty-state-text">No feed entries for selected jurisdiction</div></div>
          )}
        </div>
      )}
    </div>
  )
}
