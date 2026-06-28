const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export async function searchFunds(query: string) {
  const res = await fetch(`${API_BASE}/api/nav/search?q=${encodeURIComponent(query)}`)
  if (!res.ok) throw new Error('Search failed')
  return res.json()
}

export async function getNav(schemeCode: string) {
  const res = await fetch(`${API_BASE}/api/nav/${schemeCode}`)
  if (!res.ok) throw new Error('NAV fetch failed')
  return res.json()
}

export async function getNavHistory(schemeCode: string, days = 365) {
  const res = await fetch(`${API_BASE}/api/nav/${schemeCode}/history?days=${days}`)
  if (!res.ok) throw new Error('History fetch failed')
  return res.json()
}

export async function getPortfolioValuation(userId: string) {
  const res = await fetch(`${API_BASE}/api/portfolio/${userId}/valuation`)
  if (!res.ok) throw new Error('Portfolio fetch failed')
  return res.json()
}

export async function savePortfolio(userId: string, holdings: unknown[]) {
  const res = await fetch(`${API_BASE}/api/portfolio/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ holdings }),
  })
  if (!res.ok) throw new Error('Save failed')
  return res.json()
}

export async function analyzeFund(data: {
  scheme_code: string; fund_name: string; category?: string; units: number; buy_nav: number
}) {
  const res = await fetch(`${API_BASE}/api/analysis/fund`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Analysis failed')
  return res.json()
}

export async function compareFunds(schemeCodes: string[]) {
  const res = await fetch(`${API_BASE}/api/analysis/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scheme_codes: schemeCodes }),
  })
  if (!res.ok) throw new Error('Compare failed')
  return res.json()
}

export async function getNews() {
  const res = await fetch(`${API_BASE}/api/news`)
  if (!res.ok) throw new Error('News fetch failed')
  return res.json()
}

export async function refreshNavCache() {
  const res = await fetch(`${API_BASE}/api/nav/refresh`, { method: 'POST' })
  if (!res.ok) throw new Error('NAV refresh failed')
  return res.json()
}

export async function getFundReportPdf(data: {
  scheme_code: string; fund_name: string; category?: string; units: number; buy_nav: number
}) {
  const res = await fetch(`${API_BASE}/api/analysis/fund/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Report generation failed')
  return res.blob()
}

// Returns an MP3 audio Blob narrating the fund's analysis (ElevenLabs TTS).
export async function getFundNarration(data: {
  scheme_code: string; fund_name: string; category?: string; units: number; buy_nav: number
}) {
  const res = await fetch(`${API_BASE}/api/voice/fund-narration`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Narration unavailable')
  return res.blob()
}

// Generic text-to-speech: returns an MP3 audio Blob for any text.
export async function getSpeech(text: string) {
  const res = await fetch(`${API_BASE}/api/voice/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error('Speech unavailable')
  return res.blob()
}

// ============================================================
// FundFlow Audit API
// ============================================================
import type {
  FundAuditResult, AuditSummary, FundSource, AnakinUsageReport,
} from './types'

export interface RunAuditPayload {
  user_id?: string
  scheme_code: string
  fund_name: string
  audit_type?: 'full' | 'nfo'
  force_refresh?: boolean
  custom_sources?: Record<string, string | null>
}

export async function runFundAudit(payload: RunAuditPayload): Promise<FundAuditResult> {
  const res = await fetch(`${API_BASE}/api/audit/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'demo-user', audit_type: 'full', force_refresh: false, ...payload }),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error((detail as { detail?: string }).detail || 'The audit could not be completed.')
  }
  return res.json()
}

export async function getFundAudit(auditId: string): Promise<FundAuditResult> {
  const res = await fetch(`${API_BASE}/api/audit/${auditId}`)
  if (!res.ok) throw new Error('Audit not found.')
  return res.json()
}

export async function getLatestFundAudit(schemeCode: string, userId = 'demo-user'): Promise<FundAuditResult> {
  const res = await fetch(`${API_BASE}/api/audit/fund/${schemeCode}/latest?user_id=${userId}`)
  if (!res.ok) throw new Error('No audit found for this fund yet.')
  return res.json()
}

export async function getAuditHistory(userId = 'demo-user'): Promise<{ audits: AuditSummary[] }> {
  const res = await fetch(`${API_BASE}/api/audit/user/${userId}`)
  if (!res.ok) throw new Error('Could not load audit history.')
  return res.json()
}

export async function estimateAudit(schemeCode: string, forceRefresh = false) {
  const res = await fetch(`${API_BASE}/api/audit/estimate/${schemeCode}?force_refresh=${forceRefresh}`)
  if (!res.ok) throw new Error('Could not estimate audit cost.')
  return res.json()
}

export async function refreshAudit(auditId: string): Promise<FundAuditResult> {
  const res = await fetch(`${API_BASE}/api/audit/${auditId}/refresh`, { method: 'POST' })
  if (!res.ok) throw new Error('Refresh failed.')
  return res.json()
}

export async function downloadAuditReport(auditId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/audit/${auditId}/report`, { method: 'POST' })
  if (!res.ok) throw new Error('Report generation failed.')
  return res.blob()
}

export async function getAuditNarration(auditId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/voice/audit-narration`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ audit_id: auditId }),
  })
  if (!res.ok) throw new Error('Narration unavailable')
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) throw new Error('audio-unavailable')
  return res.blob()
}

export async function sendAssistantMessage(payload: {
  user_id?: string; message: string; audit_id?: string; conversation_id?: string
}) {
  const res = await fetch(`${API_BASE}/api/assistant/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'demo-user', ...payload }),
  })
  if (!res.ok) throw new Error('Assistant unavailable.')
  return res.json()
}

export async function getAnakinUsage(): Promise<AnakinUsageReport> {
  const res = await fetch(`${API_BASE}/api/anakin/usage`)
  if (!res.ok) throw new Error('Usage unavailable.')
  return res.json()
}

export async function discoverWireActions() {
  const res = await fetch(`${API_BASE}/api/anakin/discover-wire-actions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
  })
  if (!res.ok) throw new Error('Discovery failed.')
  return res.json()
}

export async function getWireActions() {
  const res = await fetch(`${API_BASE}/api/anakin/wire-actions`)
  if (!res.ok) throw new Error('Could not load Wire actions.')
  return res.json()
}

export async function getFundSources(): Promise<{ funds: FundSource[] }> {
  const res = await fetch(`${API_BASE}/api/sources/funds`)
  if (!res.ok) throw new Error('Could not load fund sources.')
  return res.json()
}

export async function updateFundSources(schemeCode: string, data: FundSource): Promise<FundSource> {
  const res = await fetch(`${API_BASE}/api/sources/funds/${schemeCode}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Could not save fund sources.')
  return res.json()
}

export async function validateFundSource(url: string) {
  const res = await fetch(`${API_BASE}/api/sources/validate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }),
  })
  if (!res.ok) throw new Error('Validation failed.')
  return res.json()
}
