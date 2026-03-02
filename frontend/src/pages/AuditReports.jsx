import { useState, useEffect } from 'react'

const BASE = window.SARO_CONFIG?.apiUrl || ''

export default function AuditReports() {
  const [reports, setReports] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BASE}/api/v1/audit-reports`)
      .then(r => r.json())
      .then(d => setReports(d.reports || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const riskColor = s => s >= 0.8 ? 'var(--accent-green)' : s >= 0.65 ? 'var(--accent-amber)' : 'var(--accent-red)'

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Reports</h1>
          <p className="page-subtitle">Standards-aligned compliance reports — EU AI Act, NIST AI RMF, ISO 42001 · Evidence chain included</p>
        </div>
      </div>

      <div style={{ fontSize:13,color:'var(--text-muted)',marginBottom:20,padding:'12px 16px',background:'var(--bg-card)',borderRadius:8,border:'1px solid var(--border)' }}>
        💡 Generate reports from the <strong style={{ color:'var(--text-primary)' }}>Audit & Compliance</strong> page — run an audit, then click <strong style={{ color:'var(--text-primary)' }}>Standards Report</strong>. Reports appear here automatically.
      </div>

      {loading ? (
        <div className="loading-overlay"><div className="loading-spinner" /></div>
      ) : reports.length === 0 ? (
        <div className="empty-state" style={{ padding:80 }}>
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-text">No reports yet</div>
          <div style={{ fontSize:12,color:'var(--text-muted)',marginTop:8 }}>Go to Audit & Compliance → Run Audit → Standards Report</div>
        </div>
      ) : (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><span className="card-title">Generated Reports</span><span className="badge badge-cyan">{reports.length}</span></div>
            {reports.map((r,i) => (
              <div key={i} style={{ padding:'12px 0',borderBottom:'1px solid var(--border)',cursor:'pointer' }} onClick={() => setSelected(r)}>
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:4 }}>
                  <div style={{ fontSize:13,fontWeight:600,color:selected?.report_id===r.report_id?'var(--accent-cyan)':'var(--text-primary)' }}>{r.model_name}</div>
                  <span style={{ fontFamily:'var(--mono)',fontSize:18,fontWeight:800,color:riskColor(r.executive_summary?.overall_compliance_score) }}>{(r.executive_summary?.overall_compliance_score*100).toFixed(0)}%</span>
                </div>
                <div style={{ display:'flex',gap:6,flexWrap:'wrap' }}>
                  <span className="badge badge-cyan">{r.standard}</span>
                  <span className="badge badge-gray">{r.jurisdiction}</span>
                  <span className={`badge ${r.ready_for_submission?'badge-green':'badge-amber'}`}>{r.ready_for_submission?'Ready':'Review Required'}</span>
                </div>
                <div style={{ fontSize:11,color:'var(--text-muted)',marginTop:4,fontFamily:'var(--mono)' }}>{r.report_id} · {new Date(r.generated_at).toLocaleDateString()}</div>
              </div>
            ))}
          </div>

          <div className="card">
            {selected ? (
              <div>
                <div className="card-header">
                  <div>
                    <div style={{ fontSize:15,fontWeight:700 }}>{selected.model_name}</div>
                    <div style={{ fontSize:11,color:'var(--text-muted)',fontFamily:'var(--mono)' }}>{selected.report_id}</div>
                  </div>
                  <span className={`badge ${selected.ready_for_submission?'badge-green':'badge-amber'}`}>{selected.ready_for_submission?'✓ Ready':'Review Required'}</span>
                </div>

                <div className="grid-2" style={{ marginBottom:16 }}>
                  {[
                    {label:'Compliance',value:`${(selected.executive_summary?.overall_compliance_score*100).toFixed(0)}%`,color:'green'},
                    {label:'Mitigation',value:`${selected.executive_summary?.mitigation_percent}%`,color:'cyan'},
                    {label:'Fine Avoided',value:`$${selected.executive_summary?.estimated_fine_avoided_usd?.toLocaleString()}`,color:'amber'},
                    {label:'Gaps',value:selected.gaps_identified,color:'red'},
                  ].map(m => (
                    <div key={m.label} style={{ padding:'10px 14px',background:'var(--bg-primary)',borderRadius:8,textAlign:'center' }}>
                      <div style={{ fontSize:10,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:4 }}>{m.label}</div>
                      <div style={{ fontSize:18,fontWeight:800,fontFamily:'var(--mono)',color:`var(--accent-${m.color})` }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                <div style={{ marginBottom:16 }}>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Standards Mapping — {selected.standard}</div>
                  {selected.standards_mapping?.map((m,i) => (
                    <div key={i} style={{ padding:'8px 0',borderBottom:'1px solid var(--border)' }}>
                      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:3 }}>
                        <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                          <span className="badge badge-cyan" style={{ fontSize:10 }}>{m.article}</span>
                          <span style={{ fontSize:12,fontWeight:600,color:'var(--text-primary)' }}>{m.finding_category}</span>
                        </div>
                        <div style={{ display:'flex',gap:6,alignItems:'center' }}>
                          <span style={{ fontSize:11,fontFamily:'var(--mono)',color:m.compliance_score>=0.75?'var(--accent-green)':'var(--accent-amber)',fontWeight:700 }}>{(m.compliance_score*100).toFixed(0)}%</span>
                          <span className={`badge ${m.status==='compliant'?'badge-green':'badge-amber'}`} style={{ fontSize:10 }}>{m.status?.replace('_',' ')}</span>
                        </div>
                      </div>
                      <div style={{ fontSize:11,color:'var(--text-muted)' }}>{m.requirement}</div>
                    </div>
                  ))}
                </div>

                <div>
                  <div style={{ fontSize:11,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:8 }}>Evidence Chain</div>
                  {selected.evidence_chain?.map((e,i) => (
                    <div key={i} style={{ display:'flex',gap:8,padding:'6px 0',borderBottom:'1px solid var(--border)',fontSize:12,alignItems:'center' }}>
                      <span className={`badge ${e.type==='output'?'badge-green':e.type==='findings'?'badge-amber':'badge-gray'}`} style={{ fontSize:10,flexShrink:0 }}>{e.type}</span>
                      <span style={{ color:'var(--text-secondary)' }}>{e.event}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state"><div className="empty-state-icon">📊</div><div className="empty-state-text">Select a report to view details</div></div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
