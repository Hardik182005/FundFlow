from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class NavEntry(BaseModel):
    date: str
    nav: float

class FundMeta(BaseModel):
    scheme_code: str
    scheme_name: str
    nav: float
    nav_date: str
    category: Optional[str] = None
    amc: Optional[str] = None

class SearchResult(BaseModel):
    schemeCode: str
    schemeName: str

class Holding(BaseModel):
    scheme_code: str
    fund_name: str
    units: float
    buy_nav: float
    investment_date: Optional[str] = None

class PortfolioSaveRequest(BaseModel):
    holdings: List[Holding]

class HoldingValuation(BaseModel):
    scheme_code: str
    fund_name: str
    amc: Optional[str] = None
    category: Optional[str] = None
    units: float
    buy_nav: float
    current_nav: float
    nav_date: str
    invested_amount: float
    current_value: float
    gain_loss: float
    gain_loss_pct: float

class PortfolioValuation(BaseModel):
    user_id: str
    holdings: List[HoldingValuation]
    total_invested: float
    total_current_value: float
    total_gain_loss: float
    total_gain_loss_pct: float
    as_of_date: str

class AnalysisFundRequest(BaseModel):
    scheme_code: str
    fund_name: str
    category: Optional[str] = None
    units: float
    buy_nav: float

class AIAnalysis(BaseModel):
    verdict: str  # HOLD | ADD | EXIT | WATCH
    risk_level: str  # LOW | MODERATE | HIGH
    risk_explanation: str
    performance_summary: str
    recommendation: str
    key_signals: List[str]
    best_for: str

class FundMetrics(BaseModel):
    current_nav: float
    buy_nav: float
    units: float
    invested_amount: float
    current_value: float
    gain_loss: float
    gain_loss_pct: float
    one_year_return: Optional[float] = None
    volatility_30d: Optional[float] = None
    expense_ratio: Optional[float] = None
    morningstar_rating: Optional[str] = None

class AnalysisResponse(BaseModel):
    metrics: FundMetrics
    ai_analysis: AIAnalysis

class CompareRequest(BaseModel):
    scheme_codes: List[str]

class NewsArticle(BaseModel):
    title: str
    link: str
    summary: str
    source: str
    published: str

class VoiceSummaryRequest(BaseModel):
    user_id: str

class VoiceSummaryResponse(BaseModel):
    script: str

class TTSRequest(BaseModel):
    text: str
