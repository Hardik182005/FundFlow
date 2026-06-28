'use client'
import { useEffect, useState } from 'react'
import { Search, X, TrendingUp, TrendingDown } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'
import AppShell from '@/components/app/AppShell'
import VerdictBadge from '@/components/VerdictBadge'
import { formatNAV } from '@/lib/utils'
import { getNav, getNavHistory, analyzeFund } from '@/lib/api'

// Curated catalog of popular schemes — scheme codes / names / categories / descriptions
// are static metadata. Live NAV, change %, history and 1Y return are fetched from the
// backend (AMFI via mfapi.in) on mount.
const FUND_CATALOG = [
  { code: '135800', name: 'Tata Money Market Fund', amc: 'TATA', category: 'Debt', risk: 'LOW', desc: 'Liquid debt fund with consistent returns. Ideal for short-term parking of funds.' },
  { code: '119598', name: 'SBI Bluechip Fund', amc: 'SBI', category: 'Equity', risk: 'MODERATE', desc: 'Large-cap equity fund with strong track record across market cycles.' },
  { code: '118989', name: 'HDFC Mid-Cap Opportunities', amc: 'HDFC', category: 'Equity', risk: 'HIGH', desc: 'Mid-cap fund targeting high-growth companies. Higher volatility, higher reward.' },
  { code: '122639', name: 'Parag Parikh Flexi Cap', amc: 'PPFAS', category: 'Equity', risk: 'MODERATE', desc: 'Diversified flexi-cap with global exposure. Known for consistent alpha generation.' },
  { code: '120503', name: 'Axis Long Term Equity', amc: 'AXIS', category: 'ELSS', risk: 'HIGH', desc: 'ELSS fund offering 80C tax benefits with 3-year lock-in. Good for tax savers.' },
  { code: '118834', name: 'Mirae Asset Large Cap', amc: 'MIRAE', category: 'Equity', risk: 'MODERATE', desc: 'Index-hugging large-cap fund with competitive expense ratio.' },
  { code: '120468', name: 'Kotak Emerging Equity', amc: 'KOTAK', category: 'Equity', risk: 'HIGH', desc: 'Mid/small cap blend targeting emerging market leaders.' },
  { code: '118778', name: 'Nippon India Small Cap', amc: 'NIPPON', category: 'Equity', risk: 'HIGH', desc: 'Pure small-cap fund. High risk, high reward. For long-term (7Y+) investors only.' },
  { code: '119027', name: 'DSP Midcap Fund', amc: 'DSP', category: 'Equity', risk: 'HIGH', desc: 'Well-managed mid-cap fund with diversified portfolio across sectors.' },
]

const CATEGORIES = ['All', 'Equity', 'Debt', 'ELSS', 'Hybrid']
const RISKS = ['All Risk', 'LOW', 'MODERATE', 'HIGH']

interface FundCatalogEntry {
  code: string
  name: string
  amc: string
  category: string
  risk: string
  desc: string
}

interface NavPoint {
  date: string
  nav: number
}

interface FundLiveData {
  nav: number | null
  navDate: string | null
  change: number | null // day change %, null if not derivable
  oneY: number | null // 1Y return %, null if not derivable
  spark: NavPoint[] // chronological order (oldest -> newest), for sparkline
  loading: boolean
  error: boolean
}

interface AIAnalysisResult {
  metrics: {
    current_nav: number
    buy_nav: number
    units: number
    invested_amount: number
    current_value: number
    gain_loss: number
    gain_loss_pct: number
    one_year_return?: number
    volatility_30d?: number
    expense_ratio?: number
    morningstar_rating?: string
  }
  ai_analysis: {
    verdict: string
    risk_level: string
    risk_explanation: string
    performance_summary: string
    recommendation: string
    key_signals: string[]
    best_for: string
  }
}

const SPARK_DAYS = 90

export default function ExplorePage() {
  const [query, setQuery] = useState('')
  const [catFilter, setCatFilter] = useState('All')
  const [riskFilter, setRiskFilter] = useState('All Risk')
  const [selectedFund, setSelectedFund] = useState<FundCatalogEntry | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<AIAnalysisResult | null>(null)

  const [liveData, setLiveData] = useState<Record<string, FundLiveData>>(() =>
    Object.fromEntries(
      FUND_CATALOG.map((f) => [
        f.code,
        { nav: null, navDate: null, change: null, oneY: null, spark: [], loading: true, error: false },
      ])
    )
  )

  // Fetch live NAV + history for every fund in the catalog on mount.
  useEffect(() => {
    let cancelled = false

    FUND_CATALOG.forEach(async (fund) => {
      try {
        const [navRes, historyRes] = await Promise.all([
          getNav(fund.code).catch(() => null),
          getNavHistory(fund.code, 365).catch(() => [] as NavPoint[]),
        ])

        if (cancelled) return

        // History from backend is newest-first (mfapi.in order).
        const history: NavPoint[] = Array.isArray(historyRes) ? historyRes : []

        let change: number | null = null
        if (history.length >= 2) {
          const latest = history[0].nav
          const prev = history[1].nav
          if (prev) change = ((latest - prev) / prev) * 100
        }

        let oneY: number | null = null
        if (history.length >= 2) {
          const newest = history[0].nav
          const oldest = history[history.length - 1].nav
          if (oldest) oneY = ((newest - oldest) / oldest) * 100
        }

        // Sparkline: last SPARK_DAYS points, chronological (oldest -> newest).
        const spark = history.slice(0, SPARK_DAYS).slice().reverse()

        const nav = navRes?.nav ?? (history.length > 0 ? history[0].nav : null)
        const navDate = navRes?.nav_date ?? (history.length > 0 ? history[0].date : null)

        setLiveData((prev) => ({
          ...prev,
          [fund.code]: {
            nav,
            navDate,
            change,
            oneY,
            spark,
            loading: false,
            error: nav === null && spark.length === 0,
          },
        }))
      } catch {
        if (cancelled) return
        setLiveData((prev) => ({
          ...prev,
          [fund.code]: { ...prev[fund.code], loading: false, error: true },
        }))
      }
    })

    return () => {
      cancelled = true
    }
  }, [])

  const filtered = FUND_CATALOG.filter((f) => {
    const matchQuery = f.name.toLowerCase().includes(query.toLowerCase()) || f.amc.toLowerCase().includes(query.toLowerCase())
    const matchCat = catFilter === 'All' || f.category === catFilter
    const matchRisk = riskFilter === 'All Risk' || f.risk === riskFilter
    return matchQuery && matchCat && matchRisk
  })

  const handleAnalyze = async (fund: FundCatalogEntry) => {
    setSelectedFund(fund)
    setAnalysis(null)
    setAnalysisError(null)
    setAnalyzing(true)

    try {
      const live = liveData[fund.code]
      const currentNav = live?.nav

      if (currentNav == null) {
        throw new Error('NAV unavailable')
      }

      const result = await analyzeFund({
        scheme_code: fund.code,
        fund_name: fund.name,
        category: fund.category,
        units: 1,
        buy_nav: currentNav,
      })
      setAnalysis(result)
    } catch {
      setAnalysisError("We couldn't load AI analysis for this fund right now. Please try again in a moment.")
    } finally {
      setAnalyzing(false)
    }
  }

  const closeDrawer = () => {
    setSelectedFund(null)
    setAnalysis(null)
    setAnalysisError(null)
    setAnalyzing(false)
  }

  return (
    <AppShell title="Explore Funds">
      <main className="pb-8">
        {/* Hero search */}
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-extrabold text-[#0A0A0A] mb-3">Explore Mutual Funds</h1>
          <p className="text-lg text-[#565B66] mb-8">Search any of 14,000+ schemes. Real NAV from AMFI.</p>
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#565B66]" />
            <input
              type="text"
              placeholder="Search any mutual fund in India..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-12 pr-5 py-4 text-base border-2 border-[#E7E9EE] rounded-2xl focus:outline-none focus:border-[#0B0D12] bg-white shadow-sm"
            />
            {query && (
              <button onClick={() => setQuery('')} className="absolute right-4 top-1/2 -translate-y-1/2 text-[#565B66]">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-8 items-center">
          <div className="flex gap-2 flex-wrap">
            {CATEGORIES.map((c) => (
              <button key={c} onClick={() => setCatFilter(c)}
                className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${catFilter === c ? 'bg-[#0B0D12] text-white' : 'bg-white border border-[#E7E9EE] text-[#565B66] hover:border-[#0B0D12] hover:text-[#0B0D12]'}`}>
                {c}
              </button>
            ))}
          </div>
          <div className="hidden sm:block h-6 w-px bg-[#E7E9EE] mx-1" />
          <div className="flex gap-2 flex-wrap">
            {RISKS.map((r) => (
              <button key={r} onClick={() => setRiskFilter(r)}
                className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${riskFilter === r ? 'bg-[#0A0A0A] text-white' : 'bg-white border border-[#E7E9EE] text-[#565B66] hover:border-[#0A0A0A] hover:text-[#0A0A0A]'}`}>
                {r === 'All Risk' ? 'All Risk' : r.charAt(0) + r.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
          <p className="ml-auto text-sm text-[#565B66]">{filtered.length} funds</p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((fund) => {
            const live = liveData[fund.code]
            const isLoading = !live || live.loading
            const hasNav = live && live.nav != null
            const isPositive = (live?.change ?? 0) >= 0

            return (
              <div key={fund.code} className="bg-white rounded-2xl border border-[#E7E9EE] p-5 hover:shadow-lg hover:border-[#0B0D12]/20 transition-all group">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-[#0B0D12] bg-[#0B0D12]/10 px-2 py-0.5 rounded-full">{fund.amc}</span>
                    <h3 className="font-bold text-[#0A0A0A] mt-1.5 text-sm leading-tight">{fund.name}</h3>
                    <p className="text-xs text-[#565B66] mt-0.5">{fund.category} · Risk: {fund.risk.charAt(0) + fund.risk.slice(1).toLowerCase()}</p>
                  </div>
                </div>

                {/* NAV + chart */}
                {isLoading ? (
                  <div className="mb-3 space-y-2">
                    <div className="skeleton h-7 w-24 rounded" />
                    <div className="skeleton h-3 w-16 rounded" />
                  </div>
                ) : (
                  <div className="flex items-end justify-between mb-3">
                    <div>
                      {hasNav ? (
                        <p className="text-2xl font-mono font-bold text-[#0A0A0A]">₹{formatNAV(live.nav as number)}</p>
                      ) : (
                        <p className="text-sm text-[#565B66]">NAV unavailable</p>
                      )}
                      {live.change != null ? (
                        <div className="flex items-center gap-1 mt-0.5">
                          {isPositive
                            ? <TrendingUp className="w-3.5 h-3.5 text-[#0E9F6E]" />
                            : <TrendingDown className="w-3.5 h-3.5 text-[#E02424]" />}
                          <span className={`text-sm font-semibold ${isPositive ? 'text-[#0E9F6E]' : 'text-[#E02424]'}`}>
                            {isPositive ? '+' : ''}{live.change.toFixed(2)}%
                          </span>
                          <span className="text-xs text-[#565B66]">latest</span>
                        </div>
                      ) : (
                        <span className="text-xs text-[#565B66] mt-0.5 inline-block">Change unavailable</span>
                      )}
                    </div>
                    {live.spark.length > 1 && (
                      <div className="w-24 h-12">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={live.spark}>
                            <Line type="monotone" dataKey="nav" stroke={isPositive ? '#0E9F6E' : '#E02424'} strokeWidth={1.5} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                )}

                {/* 1Y return */}
                <div className="flex items-center justify-between mb-4 pt-3 border-t border-[#E7E9EE]">
                  <span className="text-xs text-[#565B66]">1Y Return</span>
                  {isLoading ? (
                    <div className="skeleton h-4 w-12 rounded" />
                  ) : live.oneY != null ? (
                    <span className={`text-sm font-mono font-bold ${live.oneY >= 0 ? 'text-[#0E9F6E]' : 'text-[#E02424]'}`}>
                      {live.oneY >= 0 ? '+' : ''}{live.oneY.toFixed(2)}%
                    </span>
                  ) : (
                    <span className="text-xs text-[#565B66]">N/A</span>
                  )}
                </div>

                {/* Analyze button */}
                <button
                  onClick={() => handleAnalyze(fund)}
                  disabled={isLoading || !hasNav}
                  className="w-full py-2.5 bg-[#0B0D12] text-white rounded-xl text-sm font-semibold hover:bg-[#000000] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Analyze Fund →
                </button>
              </div>
            )
          })}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-20">
            <p className="text-[#565B66] text-lg">No funds found for "{query}"</p>
            <p className="text-sm text-[#888] mt-2">Try a different name or clear filters</p>
          </div>
        )}
      </main>

      {/* Analysis drawer */}
      {selectedFund && (
        <div className="fixed inset-0 z-50 flex">
          <div className="flex-1 bg-black/40" onClick={closeDrawer} />
          <div className="w-full max-w-md bg-white h-full overflow-y-auto shadow-2xl">
            <div className="sticky top-0 bg-white border-b border-[#E7E9EE] px-6 py-4 flex items-center justify-between z-10">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-[#0B0D12]">{selectedFund.amc}</span>
                <h2 className="font-bold text-[#0A0A0A] text-base mt-0.5">{selectedFund.name}</h2>
              </div>
              <button onClick={closeDrawer} className="p-2 hover:bg-[#F7F8FA] rounded-lg transition-colors">
                <X className="w-5 h-5 text-[#565B66]" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Tags */}
              <div className="flex gap-2 flex-wrap items-center">
                <span className="text-xs font-semibold border border-[#E7E9EE] px-2 py-1 rounded-full text-[#565B66]">{selectedFund.category}</span>
                <span className="text-xs font-semibold border border-[#E7E9EE] px-2 py-1 rounded-full text-[#565B66]">Risk: {selectedFund.risk.charAt(0) + selectedFund.risk.slice(1).toLowerCase()}</span>
                {analysis && <VerdictBadge verdict={analysis.ai_analysis.verdict} />}
              </div>

              {/* Sparkline */}
              {(() => {
                const live = liveData[selectedFund.code]
                const isPositive = (live?.change ?? 0) >= 0
                return (
                  <div className="bg-[#F7F8FA] rounded-xl p-4">
                    <div className="flex justify-between items-end mb-3">
                      <div>
                        {live && live.nav != null ? (
                          <p className="text-2xl font-mono font-bold text-[#0A0A0A]">₹{formatNAV(live.nav)}</p>
                        ) : (
                          <p className="text-sm text-[#565B66]">NAV unavailable</p>
                        )}
                        {live && live.change != null ? (
                          <span className={`text-sm font-semibold ${isPositive ? 'text-[#0E9F6E]' : 'text-[#E02424]'}`}>
                            {isPositive ? '▲' : '▼'} {Math.abs(live.change).toFixed(2)}% latest
                          </span>
                        ) : (
                          <span className="text-xs text-[#565B66]">Change unavailable</span>
                        )}
                      </div>
                      <span className="text-xs text-[#565B66]">AMFI · {live?.navDate || 'live'}</span>
                    </div>
                    <div className="h-28">
                      {live && live.spark.length > 1 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={live.spark}>
                            <Line type="monotone" dataKey="nav" stroke="#0B0D12" strokeWidth={2} dot={false} />
                            <Tooltip formatter={(v: number) => [`₹${formatNAV(v)}`, 'NAV']} labelFormatter={(l) => l} />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-xs text-[#565B66]">
                          {live?.loading ? 'Loading chart…' : 'History unavailable'}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })()}

              {/* Metrics */}
              {(() => {
                const live = liveData[selectedFund.code]
                return (
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Current NAV', value: live?.nav != null ? `₹${formatNAV(live.nav)}` : 'N/A' },
                      { label: '1Y Return', value: live?.oneY != null ? `${live.oneY >= 0 ? '+' : ''}${live.oneY.toFixed(2)}%` : 'N/A' },
                      { label: 'Category', value: selectedFund.category },
                      { label: 'Risk Level', value: selectedFund.risk.charAt(0) + selectedFund.risk.slice(1).toLowerCase() },
                    ].map((m, i) => (
                      <div key={i} className="bg-[#F7F8FA] rounded-xl p-3">
                        <p className="text-xs text-[#565B66] mb-1">{m.label}</p>
                        <p className="font-mono font-bold text-sm text-[#0A0A0A]">{m.value}</p>
                      </div>
                    ))}
                  </div>
                )
              })()}

              {/* Description */}
              <div className="bg-white border border-[#E7E9EE] rounded-xl p-4">
                <p className="text-xs font-bold uppercase tracking-widest text-[#565B66] mb-2">About this Fund</p>
                <p className="text-sm text-[#0A0A0A] leading-relaxed">{selectedFund.desc}</p>
              </div>

              {/* AI Analysis */}
              <div className="bg-[#0A0A0A] rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#0B0D12]">AI Verdict</span>
                  {analysis && <VerdictBadge verdict={analysis.ai_analysis.verdict} />}
                </div>
                {analyzing ? (
                  <div className="space-y-2">
                    <div className="skeleton h-4 rounded w-full" style={{ background: 'linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%)', backgroundSize: '200% 100%' }} />
                    <div className="skeleton h-4 rounded w-5/6" style={{ background: 'linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%)', backgroundSize: '200% 100%' }} />
                    <div className="skeleton h-4 rounded w-4/6" style={{ background: 'linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%)', backgroundSize: '200% 100%' }} />
                  </div>
                ) : analysisError ? (
                  <p className="text-sm text-[#E02424] leading-relaxed">{analysisError}</p>
                ) : analysis ? (
                  <>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <span className="text-xs font-semibold px-2 py-1 rounded-full bg-white/10 text-white">
                        Risk: {analysis.ai_analysis.risk_level.charAt(0) + analysis.ai_analysis.risk_level.slice(1).toLowerCase()}
                      </span>
                    </div>
                    <p className="text-white text-sm leading-relaxed mb-3">{analysis.ai_analysis.performance_summary}</p>
                    <p className="text-[#888] text-xs leading-relaxed mb-3">{analysis.ai_analysis.risk_explanation}</p>
                    <div className="bg-white/5 rounded-lg p-3 mb-3">
                      <p className="text-xs font-bold uppercase tracking-widest text-[#0B0D12] mb-1">Recommendation</p>
                      <p className="text-white text-sm leading-relaxed">{analysis.ai_analysis.recommendation}</p>
                    </div>
                    {analysis.ai_analysis.key_signals?.length > 0 && (
                      <div className="space-y-1.5 mb-3">
                        {analysis.ai_analysis.key_signals.map((s, i) => (
                          <div key={i} className="flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#0B0D12] mt-1.5 flex-shrink-0" />
                            <span className="text-xs text-[#888]">{s}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {analysis.ai_analysis.best_for && (
                      <p className="text-xs text-[#888] leading-relaxed">
                        <span className="font-bold uppercase tracking-widest text-[#0B0D12]">Best for: </span>
                        {analysis.ai_analysis.best_for}
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-[#888] leading-relaxed">Analysis unavailable.</p>
                )}
              </div>

              {/* Add to portfolio */}
              <a href="/dashboard" className="block w-full py-3.5 bg-[#0B0D12] text-white rounded-xl text-sm font-semibold hover:bg-[#000000] transition-colors text-center">
                Add to My Portfolio →
              </a>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
