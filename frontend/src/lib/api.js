const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function req(path, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  } catch (e) {
    console.error(`API Error [${path}]:`, e)
    throw e
  }
}

export const api = {
  // Health
  health: () => req('/api/v1/health'),

  // Dashboard
  dashboard: () => req('/api/v1/dashboard'),
  riskHeatmap: () => req('/api/v1/dashboard/risk-heatmap'),

  // MVP1 - Ingestion
  ingestDocument: (doc) => req('/api/v1/mvp1/ingest', { method: 'POST', body: JSON.stringify(doc) }),
  listDocuments: (limit = 20) => req(`/api/v1/mvp1/documents?limit=${limit}`),
  getForecast: (jurisdiction = 'EU') => req(`/api/v1/mvp1/forecast?jurisdiction=${jurisdiction}`),
  ingestionStats: () => req('/api/v1/mvp1/stats'),

  // MVP2 - Audit
  runAudit: (data) => req('/api/v1/mvp2/audit', { method: 'POST', body: JSON.stringify(data) }),
  listAudits: () => req('/api/v1/mvp2/audits'),
  complianceMatrix: (j = 'EU') => req(`/api/v1/mvp2/compliance-matrix?jurisdiction=${j}`),

  // MVP3 - Enterprise
  createTenant: (data) => req('/api/v1/mvp3/tenants', { method: 'POST', body: JSON.stringify(data) }),
  listTenants: () => req('/api/v1/mvp3/tenants'),
  haStatus: () => req('/api/v1/mvp3/ha-status'),
  integrations: () => req('/api/v1/mvp3/integrations'),
  enterpriseDashboard: () => req('/api/v1/mvp3/dashboard/enterprise'),

  // MVP4 - Agentic
  checkGuardrails: (data) => req('/api/v1/mvp4/guardrails/check', { method: 'POST', body: JSON.stringify(data) }),
  guardrailStats: () => req('/api/v1/mvp4/guardrails/stats'),
  generateReport: (data) => req('/api/v1/mvp4/compliance/generate-report', { method: 'POST', body: JSON.stringify(data) }),
  listRegulations: (j = 'ALL') => req(`/api/v1/mvp4/compliance/regulations?jurisdiction=${j}`),
  listCourses: () => req('/api/v1/mvp4/training/courses'),
  gaReadiness: () => req('/api/v1/mvp4/commercial/ga-readiness'),
  getBilling: (tid) => req(`/api/v1/mvp4/commercial/billing/${tid}`),
}
