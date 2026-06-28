'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/app/AppShell'
import { getFundSources, estimateAudit, runFundAudit } from '@/lib/api'
import type { FundSource } from '@/lib/types'
import { ShieldCheck, FileText, Loader2, Sparkles } from 'lucide-react'

const STAGES = [
  'Locating source documents',
  'Retrieving documents through Anakin',
  'Extracting manager statements',
  'Comparing portfolio allocations',
  'Checking mandate consistency',
  'Reviewing manager continuity',
  'Generating evidence-linked verdict',
]

export default function AuditPage() {
  const router = useRouter()
  const [funds, setFunds] = useState<FundSource[]>([])
  const [selected, setSelected] = useState<FundSource | null>(null)
  const [estimate, setEstimate] = useState<{ fresh_scrapes: number; cached_documents: number; wire_actions: number; estimated_credits: number } | null>(null)
  const [running, setRunning] = useState(false)
  const [stage, setStage] = useState(0)
  const [error, setError] = useState('')
  const [custom, setCustom] = useState({ factsheet_current_url: '', factsheet_previous_url: '', manager_commentary_url: '', sid_url: '' })
  const [useCustom, setUseCustom] = useState(false)

  useEffect(() => {
    getFundSources().then((r) => setFunds(r.funds)).catch(() => setError('Could not load funds.'))
  }, [])

  async function pick(f: FundSource) {
    setSelected(f); setEstimate(null); setError('')
    try { setEstimate(await estimateAudit(f.scheme_code)) } catch { /* ignore */ }
  }

  useEffect(() => {
    if (!running) return
    setStage(0)
    const t = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 9000)
    return () => clearInterval(t)
  }, [running])

  async function run() {
    if (!selected && !useCustom) return
    setRunning(true); setError('')
    try {
      const payload = useCustom
        ? { scheme_code: `custom-${Date.now()}`, fund_name: 'Custom audit', custom_sources: custom }
        : { scheme_code: selected!.scheme_code, fund_name: selected!.fund_name }
      const result = await runFundAudit(payload)
      router.push(`/audit/view?id=${result.audit_id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The audit could not be completed.')
      setRunning(false)
    }
  }

  if (running) {
    return (
      <AppShell title="Running Audit">
        <div className="mx-auto max-w-lg pt-10">
          <div className="ff-card p-6">
            <div className="mb-4 flex items-center gap-2 font-display text-lg font-semibold">
              <Sparkles className="text-accent" size={20} /> Auditing {selected?.fund_name || 'fund'}
            </div>
            <ol className="space-y-3">
              {STAGES.map((s, i) => (
                <li key={s} className="flex items-center gap-3 text-sm">
                  {i < stage ? <span className="text-gain">✓</span>
                    : i === stage ? <Loader2 className="animate-spin text-accent" size={16} />
                    : <span className="h-4 w-4 rounded-full border border-cardBorder" />}
                  <span className={i <= stage ? 'text-textPrimary' : 'text-textFaint'}>{s}</span>
                </li>
              ))}
            </ol>
            <p className="mt-5 text-xs text-textFaint">Live audits go through Anakin Universal Scraper and Wire. This can take up to ~90 seconds.</p>
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell title="Audit a Fund">
      <div className="mb-6 max-w-2xl">
        <h2 className="font-display text-2xl font-semibold">Audit a mutual fund</h2>
        <p className="mt-1 text-textSecondary">Check whether the fund manager is keeping their promises — using evidence retrieved through Anakin.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex gap-2">
            <button className={`ff-btn ${!useCustom ? 'ff-btn-primary' : 'ff-btn-ghost'}`} onClick={() => setUseCustom(false)}>Supported funds</button>
            <button className={`ff-btn ${useCustom ? 'ff-btn-primary' : 'ff-btn-ghost'}`} onClick={() => setUseCustom(true)}>Custom source URLs</button>
          </div>

          {!useCustom ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {funds.map((f) => (
                <button key={f.scheme_code} onClick={() => pick(f)}
                  className={`ff-card p-4 text-left transition-shadow hover:shadow-md ${selected?.scheme_code === f.scheme_code ? 'ring-2 ring-accent' : ''}`}>
                  <div className="text-xs text-textFaint">{f.amc}</div>
                  <div className="mt-1 font-semibold leading-tight">{f.fund_name}</div>
                  <div className="mt-2 text-xs text-textSecondary">{f.category} · {f.scheme_code}</div>
                </button>
              ))}
              {funds.length === 0 && <p className="text-sm text-textFaint">Loading supported funds…</p>}
            </div>
          ) : (
            <div className="ff-card space-y-3 p-4">
              {([['factsheet_current_url', 'Current factsheet URL'], ['factsheet_previous_url', 'Previous factsheet URL'], ['manager_commentary_url', 'Manager commentary URL'], ['sid_url', 'SID URL']] as const).map(([k, label]) => (
                <div key={k}>
                  <label className="text-xs font-medium text-textSecondary">{label}</label>
                  <input className="ff-input mt-1" placeholder="https://…" value={custom[k]}
                    onChange={(e) => setCustom({ ...custom, [k]: e.target.value })} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="ff-card p-4">
            <div className="mb-2 flex items-center gap-2 font-semibold"><FileText size={16} /> Estimated Anakin usage</div>
            {estimate ? (
              <ul className="space-y-1.5 text-sm">
                <li className="flex justify-between"><span className="text-textSecondary">Fresh Anakin credits</span><span className="font-mono-num font-semibold">{estimate.estimated_credits}</span></li>
                <li className="flex justify-between"><span className="text-textSecondary">Documents cached</span><span className="font-mono-num">{estimate.cached_documents}</span></li>
                <li className="flex justify-between"><span className="text-textSecondary">Wire actions available</span><span className="font-mono-num">{estimate.wire_actions}</span></li>
              </ul>
            ) : (
              <p className="text-sm text-textFaint">{useCustom ? 'Estimate runs after submission.' : 'Select a fund to estimate.'}</p>
            )}
          </div>

          {error && <div className="ff-card border-loss/30 bg-loss/5 p-3 text-sm text-loss">{error}</div>}

          <button onClick={run} disabled={!selected && !useCustom} className="ff-btn-primary w-full">
            <ShieldCheck size={16} /> Run Audit
          </button>
          <p className="text-[11px] text-textFaint">A completed audit attempts at least one Anakin Wire action and shows full source evidence.</p>
        </div>
      </div>
    </AppShell>
  )
}
