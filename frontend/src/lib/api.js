// Runtime config takes priority over build-time env var
// window.SARO_CONFIG is loaded from /public/config.js before React starts
const BASE_URL = (
  window.SARO_CONFIG?.apiUrl ||
  import.meta.env.VITE_API_URL ||
  ''
).replace(/\/$/, '')

console.log('[SARO] API Base URL:', BASE_URL || '⚠️ NOT SET')

async function req(path, options = {}) {
  if (!BASE_URL) {
    throw new Error('API URL not configured. Edit /public/config.js and set apiUrl to your backend URL.')
  }
  const url = `${BASE_URL}${path}`
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      mode: 'cors',
      ...options,
    })
    const text = await res.text()
    if (text.trim().startsWith('<')) {
      throw new Error(`Got HTML instead of JSON — wrong API URL? Currently set to: ${BASE_URL}`)
    }
    const data = JSON.parse(text)
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
    return data
  } catch (e) {
    console.error(`API Error [${path}]:`, e.message)
    throw e
  }
}

export const api = {
  health: () => req('/api/v1/health'),
  dashboard: () => req('/api/v1/dashboard'),
  riskHeatmap: () => req('/api/v1/dashboard/risk-heatmap'),
  ingestDocument: (doc) => req('/api/v1/mvp1/ingest', { method: 'POST', body: JSON.stringify(doc) }),
  listDocuments: (limit = 20) => req(`/api/v1/mvp1/documents?limit=${limit}`),
  getForecast: (jurisdiction = 'EU') => req(`/api/v1/mvp1/forecast?jurisdiction=${jurisdiction}`),
  ingestionStats: () => req('/api/v1/mvp1/stats'),
  runAudit: (data) => req('/api/v1/mvp2/audit', { method: 'POST', body: JSON.stringify(data) }),
  listAudits: () => req('/api/v1/mvp2/audits'),
  complianceMatrix: (j = 'EU') => req(`/api/v1/mvp2/compliance-matrix?jurisdiction=${j}`),
  createTenant: (data) => req('/api/v1/mvp3/tenants', { method: 'POST', body: JSON.stringify(data) }),
  listTenants: () => req('/api/v1/mvp3/tenants'),
  haStatus: () => req('/api/v1/mvp3/ha-status'),
  integrations: () => req('/api/v1/mvp3/integrations'),
  enterpriseDashboard: () => req('/api/v1/mvp3/dashboard/enterprise'),
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
