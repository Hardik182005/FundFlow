// TypeScript types mirroring the backend Pydantic audit schemas.

export type CheckStatus = 'pass' | 'warning' | 'fail' | 'insufficient_data'
export type Verdict = 'TRUSTED' | 'MONITOR' | 'REVIEW' | 'HIGH CONCERN'

export interface SourceEvidence {
  id?: string
  source_type: string
  title: string
  url: string
  excerpt?: string | null
  published_date?: string | null
  reporting_period?: string | null
  scraped_at: string
  anakin_job_id?: string | null
  cached: boolean
  extraction_confidence: number
}

export interface ManagerClaim {
  asset_or_sector: string
  direction: 'increase' | 'decrease' | 'overweight' | 'underweight' | 'maintain' | 'avoid' | 'unknown'
  quoted_text: string
  normalized_claim: string
  confidence: number
  source_evidence_id?: string | null
}

export interface AllocationRecord {
  name: string
  current_weight?: number | null
  previous_weight?: number | null
  delta_percentage_points?: number | null
  classification?: string | null
  source_evidence_ids: string[]
}

export interface ClaimRow {
  statement?: string
  direction?: string
  sector?: string
  previous_weight?: number | null
  current_weight?: number | null
  observed_movement?: number | null
  status?: string
}

export interface AuditCheckResult {
  check_id: string
  name: string
  status: CheckStatus
  score: number
  summary: string
  explanation: string
  findings: string[]
  evidence_ids: string[]
  confidence: number
  methodology: string
  table?: ClaimRow[]
  observed?: Record<string, number>
  mandate?: Record<string, number | null>
  tenure_months?: number
  closest?: { name: string; similarity: number }[]
}

export interface AnakinUsage {
  scraper_calls: number
  wire_calls: number
  search_calls: number
  fresh_calls: number
  cache_hits: number
  estimated_credits: number
  job_ids: string[]
}

export interface FundAuditResult {
  audit_id: string
  scheme_code: string
  fund_name: string
  fund_type: string
  generated_at: string
  trust_score: number
  verdict: Verdict | string
  verdict_explanation: string
  checks: AuditCheckResult[]
  evidence: SourceEvidence[]
  manager_claims: ManagerClaim[]
  allocation_diff: AllocationRecord[]
  anakin_usage: AnakinUsage
  limitations: string[]
  disclaimer: string
  is_demo?: boolean
  status?: string
  wire_reality?: { action_id: string; catalog: string } | null
}

export interface AuditSummary {
  audit_id: string
  scheme_code: string
  fund_name: string
  generated_at: string
  trust_score: number
  verdict: string
}

export interface FundSource {
  scheme_code: string
  fund_name: string
  amc: string
  fund_type?: string
  category?: string
  factsheet_current_url: string
  factsheet_previous_url: string
  manager_commentary_url: string
  sid_url: string
  annual_report_url: string
  manager_profile_url: string
  nfo_document_url?: string | null
}

export interface AnakinUsageReport {
  label: string
  configured_budget: number
  estimated_credits_used: number
  estimated_credits_today: number
  calls_by_operation: Record<string, number>
  cache_hit_rate: number
  recent_calls: Record<string, unknown>[]
}
