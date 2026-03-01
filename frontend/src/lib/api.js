const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

// Show in console so you can verify during debugging
console.log('[SARO] API Base URL:', BASE_URL || '⚠️ EMPTY - VITE_API_URL not set!')
if (!BASE_URL) {
  console.error('[SARO] VITE_API_URL is not set. All API calls will fail. Set it in Koyeb environment variables and redeploy.')
}

async function req(path, options = {}) {
  const url = `${BASE_URL}${path}`
  if (!BASE_URL) {
    throw new Error('VITE_API_URL not configured — set it in Koyeb environment variables and redeploy')
  }
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      mode: 'cors',
      ...options,
    })
    const text = await res.text()
    // Detect HTML response (means wrong URL or proxied to frontend)
    if (text.trim().startsWith('<')) {
      throw new Error(`Got HTML instead of JSON — VITE_API_URL may be pointing to the frontend. Check Koyeb env vars. URL: ${url}`)
    }
    const data = JSON.parse(text)
    if (!res.ok) {
      throw new Error(data.detail || `HTTP ${res.status}`)
    }
    return data
  } catch (e) {
    console.error(`API Error [${path}]:`, e.message)
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
  enrollCourse: (data) => req('/api/v1/mvp4/training/enroll', { method: 'POST', body: JSON.stringify(data) }),
  gaReadiness: () => req('/api/v1/mvp4/commercial/ga-readiness'),
  getBilling: (tid) => req(`/api/v1/mvp4/commercial/billing/${tid}`),
  onboardCustomer: (data) => req('/api/v1/mvp4/commercial/onboard', { method: 'POST', body: JSON.stringify(data) }),
}
