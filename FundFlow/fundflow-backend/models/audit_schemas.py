"""Pydantic models for FundFlow Audit and the Anakin integration."""
from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ----------------------- Anakin client DTOs -----------------------

class AnakinJobSubmission(BaseModel):
    job_id: str
    status: str = "submitted"
    source_url: Optional[str] = None


class AnakinScrapeResult(BaseModel):
    source_url: Optional[str] = None
    job_id: Optional[str] = None
    status: str = "unknown"          # completed | failed | timeout | error
    duration_seconds: Optional[float] = None
    cached: bool = False
    markdown: Optional[str] = None
    generated_json: Optional[dict] = None
    error: Optional[str] = None
    used_browser: bool = False


class WireAction(BaseModel):
    action_id: str
    catalog: Optional[str] = None
    name: str
    description: Optional[str] = None
    param_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    credits_per_call: Optional[float] = None


class WireCatalog(BaseModel):
    slug: str
    actions: List[WireAction] = Field(default_factory=list)


class WireJobSubmission(BaseModel):
    job_id: str
    status: str = "submitted"
    action_id: Optional[str] = None


class WireJobResult(BaseModel):
    job_id: Optional[str] = None
    action_id: Optional[str] = None
    status: str = "unknown"
    duration_seconds: Optional[float] = None
    data: Optional[dict] = None
    error: Optional[str] = None


# ----------------------- Audit domain models -----------------------

class SourceEvidence(BaseModel):
    id: Optional[str] = None
    source_type: str
    title: str
    url: str
    excerpt: Optional[str] = None
    published_date: Optional[str] = None
    reporting_period: Optional[str] = None
    scraped_at: str
    anakin_job_id: Optional[str] = None
    cached: bool = False
    extraction_confidence: float = 0.0


class ManagerClaim(BaseModel):
    asset_or_sector: str
    direction: Literal[
        "increase", "decrease", "overweight",
        "underweight", "maintain", "avoid", "unknown"
    ]
    quoted_text: str
    normalized_claim: str
    confidence: float
    source_evidence_id: Optional[str] = None


class AllocationRecord(BaseModel):
    name: str
    current_weight: Optional[float] = None
    previous_weight: Optional[float] = None
    delta_percentage_points: Optional[float] = None
    classification: Optional[str] = None
    source_evidence_ids: List[str] = Field(default_factory=list)


class AuditCheckResult(BaseModel):
    check_id: str
    name: str
    status: Literal["pass", "warning", "fail", "insufficient_data"]
    score: float
    summary: str
    explanation: str
    findings: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    methodology: str = ""


class AnakinUsage(BaseModel):
    scraper_calls: int = 0
    wire_calls: int = 0
    search_calls: int = 0
    fresh_calls: int = 0
    cache_hits: int = 0
    estimated_credits: int = 0
    job_ids: List[str] = Field(default_factory=list)


class FundAuditResult(BaseModel):
    audit_id: str
    scheme_code: str
    fund_name: str
    fund_type: str = "equity"
    generated_at: str
    trust_score: float
    verdict: str
    verdict_explanation: str
    checks: List[AuditCheckResult] = Field(default_factory=list)
    evidence: List[SourceEvidence] = Field(default_factory=list)
    manager_claims: List[ManagerClaim] = Field(default_factory=list)
    allocation_diff: List[AllocationRecord] = Field(default_factory=list)
    anakin_usage: dict = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "This is an AI-assisted document and portfolio consistency audit, not "
        "investment advice. Verify source documents and consult a SEBI-registered "
        "investment adviser before making financial decisions."
    )
    is_demo: bool = False


# ----------------------- Request models -----------------------

class CustomSources(BaseModel):
    factsheet_current_url: Optional[str] = None
    factsheet_previous_url: Optional[str] = None
    manager_commentary_url: Optional[str] = None
    sid_url: Optional[str] = None
    annual_report_url: Optional[str] = None
    manager_profile_url: Optional[str] = None
    nfo_document_url: Optional[str] = None


class RunAuditRequest(BaseModel):
    user_id: str = "demo-user"
    scheme_code: str
    fund_name: str
    audit_type: Literal["full", "nfo"] = "full"
    force_refresh: bool = False
    custom_sources: Optional[CustomSources] = None


class FundSource(BaseModel):
    scheme_code: str
    fund_name: str = ""
    amc: str = ""
    factsheet_current_url: str = ""
    factsheet_previous_url: str = ""
    manager_commentary_url: str = ""
    sid_url: str = ""
    annual_report_url: str = ""
    manager_profile_url: str = ""
    nfo_document_url: Optional[str] = None
