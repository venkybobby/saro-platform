import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''
const get = (path) => fetch(`${BASE}${path}`).then(r => r.json())
const post = (path, body) => fetch(`${BASE}${path}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }).then(r => r.json())

export default function PolicyLibrary() {
  const [tab, setTab] = useState('library')
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ jurisdiction:'ALL', status:'ALL' })
  const [uploadForm, setUploadForm] = useState({ title:'', content:'', jurisdiction:'EU', regulation:'EU AI Act', doc_type:'regulation' })
  const [uploadResult, setUploadResult] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [selected, setSelected] = useState(null)

  useEffect(() => { loadPolicies() }, [filter])

  const loadPolicies = () => {
    setLoading(true)
    get(`/api/v1/policies?jurisdiction=${filter.jurisdiction}&status=${filter.status}`)
      .then(d => setPolicies(d.policies || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const handleUpload = async () => {
    if (!uploadForm.title || !uploadForm.content) return
    setUploading(true)
    try {
      const res = await post('/api/v1/policies/upload', uploadForm)
      setUploadResult(res)
      setPolicies(p => [res, ...p])
      setUploadForm({ title:'', content:'', jurisdiction:'EU', regulation:'EU AI Act', doc_type:'regulation' })
      setTab('library')
    } catch(e) {}
    finally { setUploading(false) }
  }

  const approvePolicy = async (policyId) => {
    await fetch(`${BASE}/api/v1/policies/${policyId}/review`, {
      method:'PUT', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ status:'reviewed' })
    })
    loadPolicies()
  }

  const riskColor = s => s >= 0.75 ? 'var(--accent-red)' : s >= 0.5 ? 'var(--accent-amber)' : 'var(--accent-green)'
  const statusBadge = s => ({ reviewed:'badge-green', pending_review:'badge-amber', flagged:'badge-red' }[s] || 'badge-gray')
  const statusLabel = s => ({ reviewed:'Reviewed', pending_review:'Pending Review', flagged:'Flagged' }[s] || s)

  const DEMO_TEXTS = [
    { label: '⚠️ High-Risk Policy', text: 'This regulation mandates that all AI systems with high-risk classification must implement bias testing, transparency reporting, and human oversight mechanisms. Facial recognition systems are subject to additional restrictions on fundamental rights grounds. Penalties up to €30M apply for non-compliance.' },
    { label: '✅ Standard Guideline', text: 'Organizations should document AI system objectives, data sources, and model architecture. Regular audits of AI performance metrics are recommended. Accountability frameworks should include designated AI governance officers.' },
  ]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Policy Library</h1>
          <p className="page-subtitle">Search, upload, and manage ingested regulatory policies across all jurisdictions</p>
        </div>
        <button className="btn btn-primary" onClick={() => setTab('upload')}>+ Upload Policy</button>
      </div>

      <div className="tabs">
        {[['library','📋 Policy Library'],['upload','+ Upload & Analyze'],['detail','🔍 Policy Detail']].map(([t,l]) => (
          <div key={t} className={`tab ${tab===t?'active':''}`} onClick={() => setTab(t)}>{l}</div>
        ))}
      </div>

      {tab === 'library' && (
        <div>
          <div className="card" style={{ marginBottom:16,padding:'14px 20px' }}>
            <div style={{ display:'flex',gap:12,alignItems:'center',flexWrap:'wrap' }}>
              <span style={{ fontSize:12,color:'var(--text-muted)',fontWeight:600 }}>Filter:</span>
              <select className="form-select" style={{ width:'auto',padding:'6px 12px' }} value={filter.jurisdiction} onChange={e => setFilter(f=>({...f,jurisdiction:e.target.value}))}>
                {['ALL','EU','US','UK','CN','SG','GLOBAL'].map(j => <option key={j}>{j}</option>)}
              </select>
              <select className="form-select" style={{ width:'auto',padding:'6px 12px' }} value={filter.status} onChange={e => setFilter(f=>({...f,status:e.target.value}))}>
                {['ALL','reviewed','pending_review','flagged'].map(s => <option key={s}>{s}</option>)}
              </select>
              <span style={{ fontSize:12,color:'var(--text-muted)',marginLeft:'auto' }}>{policies.length} policies</span>
            </div>
          </div>

          {loading ? (
            <div className="loading-overlay"><div className="loading-spinner" /><span>Loading policies...</span></div>
          ) : (
            <div className="card">
              <table className="data-table">
                <thead><tr><th>Title</th><th>Source</th><th>Jurisdiction</th><th>Risk Score</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {policies.map((p,i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ color:'var(--text-primary)',fontWeight:500,fontSize:13 }}>{p.title}</div>
                        <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2 }}>{p.regulation} · {p.word_count?.toLocaleString()} words</div>
                      </td>
                      <td style={{ fontSize:11,color:'var(--text-muted)' }}>{p.source}</td>
                      <td><span className="badge badge-cyan">{p.jurisdiction}</span></td>
                      <td>
                        <div style={{ display:'flex',alignItems:'center',gap:8 }}>
                          <div className="progress-bar" style={{ width:60 }}>
                            <div className="progress-fill" style={{ width:`${p.risk_score*100}%`,background:riskColor(p.risk_score) }} />
                          </div>
                          <span style={{ fontSize:11,fontFamily:'var(--mono)',color:riskColor(p.risk_score),fontWeight:700 }}>{(p.risk_score*100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td><span className={`badge ${statusBadge(p.status)}`}>{statusLabel(p.status)}</span></td>
                      <td>
                        <div style={{ display:'flex',gap:6 }}>
                          <button className="btn btn-secondary" style={{ fontSize:11,padding:'4px 10px' }} onClick={() => { setSelected(p); setTab('detail') }}>View</button>
                          {p.status === 'pending_review' && <button className="btn btn-secondary" style={{ fontSize:11,padding:'4px 10px',color:'var(--accent-green)',borderColor:'rgba(0,255,136,0.3)' }} onClick={() => approvePolicy(p.policy_id)}>✓ Approve</button>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'upload' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Upload Policy for Analysis</span></div>
            <div className="form-group">
              <label className="form-label">Policy Title</label>
              <input className="form-input" placeholder="EU AI Act Article 9 — Risk Management" value={uploadForm.title} onChange={e => setUploadForm(f=>({...f,title:e.target.value}))} />
            </div>
            <div className="grid-2" style={{ marginBottom:0 }}>
              <div className="form-group">
                <label className="form-label">Jurisdiction</label>
                <select className="form-select" value={uploadForm.jurisdiction} onChange={e => setUploadForm(f=>({...f,jurisdiction:e.target.value}))}>
                  {['EU','US','UK','CN','SG','GLOBAL'].map(j => <option key={j}>{j}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Regulation</label>
                <select className="form-select" value={uploadForm.regulation} onChange={e => setUploadForm(f=>({...f,regulation:e.target.value}))}>
                  {['EU AI Act','GDPR','NIST AI RMF','FDA SaMD','ISO 42001','MAS TREx','UK AI Bill','China AIGC'].map(r => <option key={r}>{r}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Policy Text</label>
              <textarea className="form-textarea" style={{ minHeight:180 }} placeholder="Paste regulatory text, policy document, or guideline content here. The system will detect risk keywords, extract entities, and score compliance impact." value={uploadForm.content} onChange={e => setUploadForm(f=>({...f,content:e.target.value}))} />
            </div>
            <div style={{ marginBottom:12 }}>
              <div style={{ fontSize:11,color:'var(--text-muted)',marginBottom:6 }}>💡 Demo texts:</div>
              {DEMO_TEXTS.map(d => (
                <button key={d.label} className="btn btn-secondary" style={{ fontSize:11,padding:'5px 10px',marginBottom:4,width:'100%',justifyContent:'flex-start' }} onClick={() => setUploadForm(f=>({...f,content:d.text,title:d.label.replace(/[⚠️✅]/g,'').trim()}))}>
                  {d.label}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || !uploadForm.title || !uploadForm.content} style={{ width:'100%',justifyContent:'center' }}>
              {uploading ? <><div className="loading-spinner" style={{width:14,height:14}} /> Analyzing...</> : '📋 Upload & Analyze'}
            </button>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Analysis Result</span></div>
            {uploadResult ? (
              <div>
                <div style={{ display:'flex',gap:8,alignItems:'center',marginBottom:16 }}>
                  <span className={`badge ${statusBadge(uploadResult.status)}`}>{statusLabel(uploadResult.status)}</span>
                  <span style={{ fontFamily:'var(--mono)',fontSize:11,color:'var(--text-muted)' }}>{uploadResult.policy_id}</span>
                </div>
                <div style={{ marginBottom:14,padding:'12px 14px',background:'var(--bg-primary)',borderRadius:8 }}>
                  <div style={{ fontSize:14,fontWeight:600,marginBottom:4 }}>{uploadResult.title}</div>
                  <div style={{ fontSize:12,color:'var(--text-muted)' }}>{uploadResult.regulation} · {uploadResult.jurisdiction} · {uploadResult.word_count} words</div>
                </div>
                <div style={{ marginBottom:14 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Risk Score</div>
                  <div style={{ display:'flex',alignItems:'center',gap:12 }}>
                    <div className="progress-bar" style={{ flex:1 }}>
                      <div className="progress-fill" style={{ width:`${uploadResult.risk_score*100}%`,background:riskColor(uploadResult.risk_score) }} />
                    </div>
                    <span style={{ fontSize:20,fontWeight:800,fontFamily:'var(--mono)',color:riskColor(uploadResult.risk_score) }}>{(uploadResult.risk_score*100).toFixed(0)}%</span>
                  </div>
                </div>
                {uploadResult.risk_tags?.length > 0 && (
                  <div style={{ marginBottom:14 }}>
                    <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Detected Risk Signals</div>
                    {uploadResult.risk_tags.map((t,i) => (
                      <div key={i} style={{ display:'flex',justifyContent:'space-between',alignItems:'center',padding:'6px 0',borderBottom:'1px solid var(--border)' }}>
                        <span style={{ fontSize:12,color:'var(--text-secondary)' }}>{t.tag}</span>
                        <span style={{ fontSize:11,fontFamily:'var(--mono)',color:'var(--accent-amber)',fontWeight:700 }}>{(t.probability*100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                )}
                {uploadResult.content_preview && (
                  <div style={{ padding:'10px 12px',background:'var(--bg-primary)',borderRadius:6,fontSize:11,color:'var(--text-muted)',lineHeight:1.7 }}>
                    {uploadResult.content_preview}
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state"><div className="empty-state-icon">📋</div><div className="empty-state-text">Upload a policy to see risk analysis</div></div>
            )}
          </div>
        </div>
      )}

      {tab === 'detail' && selected && (
        <div className="card">
          <div className="card-header">
            <div>
              <div style={{ fontSize:16,fontWeight:700 }}>{selected.title}</div>
              <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:2,fontFamily:'var(--mono)' }}>{selected.policy_id}</div>
            </div>
            <span className={`badge ${statusBadge(selected.status)}`}>{statusLabel(selected.status)}</span>
          </div>
          <div className="grid-2" style={{ marginBottom:16 }}>
            {[['Regulation',selected.regulation],['Jurisdiction',selected.jurisdiction],['Source',selected.source],['Type',selected.doc_type]].map(([k,v]) => (
              <div key={k} style={{ padding:'10px 0',borderBottom:'1px solid var(--border)' }}>
                <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:4 }}>{k}</div>
                <div style={{ fontSize:13,color:'var(--text-primary)',fontWeight:500 }}>{v}</div>
              </div>
            ))}
          </div>
          <div style={{ display:'flex',gap:12,alignItems:'center',marginBottom:16 }}>
            <span style={{ fontSize:12,color:'var(--text-muted)' }}>Risk Score:</span>
            <div className="progress-bar" style={{ width:120 }}>
              <div className="progress-fill" style={{ width:`${selected.risk_score*100}%`,background:riskColor(selected.risk_score) }} />
            </div>
            <span style={{ fontFamily:'var(--mono)',fontWeight:700,color:riskColor(selected.risk_score) }}>{(selected.risk_score*100).toFixed(0)}%</span>
          </div>
          {selected.status === 'pending_review' && (
            <button className="btn btn-primary" onClick={() => { approvePolicy(selected.policy_id); setSelected({...selected,status:'reviewed'}) }}>✓ Approve Policy</button>
          )}
        </div>
      )}
    </div>
  )
}
