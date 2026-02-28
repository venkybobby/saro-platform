import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export default function MVP1Ingestion() {
  const [tab, setTab] = useState('ingest')
  const [form, setForm] = useState({ title: '', content: '', jurisdiction: 'EU', doc_type: 'regulation' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [docs, setDocs] = useState([])
  const [forecast, setForecast] = useState(null)
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listDocuments().then(setDocs).catch(() => {})
    api.ingestionStats().then(setStats).catch(() => {})
    api.getForecast('EU').then(setForecast).catch(() => {})
  }, [])

  const handleIngest = async () => {
    if (!form.title || !form.content) {
      setError('Title and content are required')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await api.ingestDocument(form)
      setResult(res)
      setDocs(d => [res, ...d])
      setForm({ title: '', content: '', jurisdiction: 'EU', doc_type: 'regulation' })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const riskColor = (score) => {
    if (score >= 0.7) return 'var(--accent-red)'
    if (score >= 0.4) return 'var(--accent-amber)'
    return 'var(--accent-green)'
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Ingestion & Forecasting</h1>
          <p className="page-subtitle">Ingest regulatory documents, extract entities, score risks, and forecast upcoming changes</p>
        </div>
        <span className="mvp-tag mvp1-tag">◈ MVP1</span>
      </div>

      {stats && (
        <div className="metrics-grid" style={{ marginBottom: 24 }}>
          {[
            { label: 'Total Documents', value: stats.total_documents?.toLocaleString() },
            { label: 'Today', value: stats.documents_today },
            { label: 'Avg Risk Score', value: (stats.avg_risk_score * 100).toFixed(0) + '%' },
            { label: 'High Risk Docs', value: stats.high_risk_docs },
            { label: 'Processing Rate', value: stats.processing_rate },
          ].map(s => (
            <div key={s.label} className="card" style={{ padding: '14px 16px' }}>
              <div className="card-title" style={{ fontSize: 10, marginBottom: 6 }}>{s.label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--accent-cyan)' }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="tabs">
        {['ingest', 'documents', 'forecast'].map(t => (
          <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'ingest' ? '+ Ingest Document' : t === 'documents' ? '📄 Document Library' : '📈 Regulatory Forecast'}
          </div>
        ))}
      </div>

      {tab === 'ingest' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Document Ingest</span></div>
            {error && <div style={{ background: 'var(--accent-red-dim)', color: 'var(--accent-red)', border: '1px solid rgba(255,61,106,0.3)', borderRadius: 6, padding: '10px 14px', marginBottom: 16, fontSize: 13 }}>{error}</div>}
            <div className="form-group">
              <label className="form-label">Document Title</label>
              <input className="form-input" placeholder="EU AI Act Article 9 - Risk Management" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
            </div>
            <div className="grid-2" style={{ marginBottom: 0 }}>
              <div className="form-group">
                <label className="form-label">Jurisdiction</label>
                <select className="form-select" value={form.jurisdiction} onChange={e => setForm(f => ({ ...f, jurisdiction: e.target.value }))}>
                  {['EU', 'US', 'UK', 'CN', 'SG', 'GLOBAL'].map(j => <option key={j}>{j}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Document Type</label>
                <select className="form-select" value={form.doc_type} onChange={e => setForm(f => ({ ...f, doc_type: e.target.value }))}>
                  {['regulation', 'guideline', 'standard', 'whitepaper', 'enforcement'].map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Document Content</label>
              <textarea className="form-textarea" placeholder="Paste regulatory text here... The system will extract entities, identify high-risk clauses, detect bias requirements, and score overall compliance risk." value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
            </div>
            <button className="btn btn-primary" onClick={handleIngest} disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
              {loading ? <><div className="loading-spinner" style={{ width: 14, height: 14 }} /> Processing...</> : '◈ Ingest & Analyze'}
            </button>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Analysis Result</span></div>
            {result ? (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{result.title}</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                    <span className="badge badge-cyan">{result.jurisdiction}</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, padding: '2px 8px', borderRadius: 20, background: `${riskColor(result.risk_score)}22`, color: riskColor(result.risk_score), border: `1px solid ${riskColor(result.risk_score)}44` }}>
                      Risk: {(result.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.7 }}>{result.content_summary}</div>
                </div>

                {result.entities.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Detected Entities</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {result.entities.map((e, i) => <span key={i} className="badge badge-cyan">{e}</span>)}
                    </div>
                  </div>
                )}

                {result.risk_tags.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Risk Tags</div>
                    {result.risk_tags.map((t, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{t.tag}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: 140 }}>
                          <div className="progress-bar" style={{ flex: 1 }}>
                            <div className="progress-fill progress-amber" style={{ width: `${t.probability * 100}%` }} />
                          </div>
                          <span style={{ fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--accent-amber)', width: 35 }}>{(t.probability * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">◈</div>
                <div className="empty-state-text">Ingest a document to see analysis results</div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'documents' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Document Library</span>
            <span className="badge badge-cyan">{docs.length} documents</span>
          </div>
          {docs.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Jurisdiction</th>
                  <th>Entities</th>
                  <th>Risk Score</th>
                  <th>Ingested</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((doc, i) => (
                  <tr key={i}>
                    <td style={{ color: 'var(--text-primary)', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.title}</td>
                    <td><span className="badge badge-cyan">{doc.jurisdiction}</span></td>
                    <td>{doc.entities?.slice(0, 2).join(', ') || '—'}</td>
                    <td>
                      <span style={{ color: riskColor(doc.risk_score), fontFamily: 'var(--mono)', fontWeight: 600 }}>
                        {(doc.risk_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{new Date(doc.ingested_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <div className="empty-state-text">No documents ingested yet. Use the Ingest tab to add documents.</div>
            </div>
          )}
        </div>
      )}

      {tab === 'forecast' && forecast && (
        <div>
          <div style={{ marginBottom: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Model accuracy:</span>
            <span style={{ fontFamily: 'var(--mono)', color: 'var(--accent-green)', fontWeight: 700 }}>{(forecast.model_accuracy * 100).toFixed(0)}%</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {forecast.forecasts?.map((f, i) => (
              <div key={i} className="card" style={{ padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                      <span className="badge badge-cyan">{f.jurisdiction}</span>
                      <span className={`badge ${f.impact === 'high' ? 'badge-red' : 'badge-amber'}`}>{f.impact} impact</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{f.change_type.replace('_', ' ')}</span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{f.regulation}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{f.description}</div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {f.affected_categories.map(c => <span key={c} className="badge badge-gray">{c}</span>)}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', marginLeft: 20 }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 24, fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {(f.probability * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>probability</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                      {new Date(f.predicted_date).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
