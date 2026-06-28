'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import AppShell from '@/components/app/AppShell'
import StatusBadge, { verdictColor, verdictAction } from '@/components/app/StatusBadge'
import { getFundAudit, downloadAuditReport, getAuditNarration } from '@/lib/api'
import { playAudioBlob, stopVoice, speakWithBrowser } from '@/lib/voice'
import type { FundAuditResult, AuditCheckResult } from '@/lib/types'
import { Volume2, Download, FileSearch, Loader2, ChevronDown } from 'lucide-react'

const TABS = ['Summary', 'Manager Claims', 'Allocation Diff', 'Evidence', 'Methodology'] as const
type Tab = typeof TABS[number]

export default function AuditResultPage() {
  return (
    <Suspense fallback={<AppShell title="Audit"><div className="ff-card h-40 animate-pulse" /></AppShell>}>
      <AuditResultInner />
    </Suspense>
  )
}

function AuditResultInner() {
  const auditId = useSearchParams().get('id') || ''
  const [audit, setAudit] = useState<FundAuditResult | null>(null)
  const [tab, setTab] = useState<Tab>('Summary')
  const [error, setError] = useState('')
  const [narrating, setNarrating] = useState(false)

  useEffect(() => {
    getFundAudit(auditId).then(setAudit).catch((e) => setError(e.message))
  }, [auditId])

  async function narrate() {
    if (!audit) return
    // second click while speaking = stop (toggle), never overlap
    if (narrating) { stopVoice(); setNarrating(false); return }
    setNarrating(true)
    try {
      const blob = await getAuditNarration(audit.audit_id)
      await playAudioBlob(blob)
    } catch {
      stopVoice()
      speakWithBrowser(audit.verdict_explanation)
    } finally {
      setNarrating(false)
    }
  }

  async function report() {
    if (!audit) return
    const blob = await downloadAuditReport(audit.audit_id)
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `fundflow-audit-${audit.audit_id}.pdf`
    a.click()
  }

  if (error) return <AppShell title="Audit"><div className="ff-card p-6 text-loss">{error}</div></AppShell>
  if (!audit) return <AppShell title="Audit"><div className="ff-card h-40 animate-pulse" /></AppShell>

  return (
    <AppShell title="Audit Result">
      {audit.is_demo && (
        <div className="mb-4 rounded-xl bg-warn/10 px-4 py-2 text-sm text-warn">Demo audit generated from cached source documents.</div>
      )}

      {/* Header */}
      <div className="ff-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs text-textFaint">{audit.fund_type} · {audit.scheme_code} · {new Date(audit.generated_at).toLocaleString()}</div>
            <h2 className="mt-1 font-display text-2xl font-semibold">{audit.fund_name}</h2>
            <p className="mt-2 max-w-2xl text-sm text-textSecondary">{audit.verdict_explanation}</p>
          </div>
          <div className="text-center">
            <div className="font-mono-num text-4xl font-bold">{audit.trust_score}</div>
            <div className="text-xs text-textFaint">Trust score / 100</div>
            <div className={`mt-2 rounded-full border px-3 py-1 text-xs font-bold ${verdictColor(audit.verdict)}`}>{audit.verdict}</div>
            <div className="mt-1 text-[10px] text-textFaint">{verdictAction(audit.verdict)}</div>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          <button onClick={narrate} className="ff-btn-ghost">{narrating ? <Loader2 className="animate-spin" size={16} /> : <Volume2 size={16} />} Read aloud</button>
          <button onClick={report} className="ff-btn-ghost"><Download size={16} /> Download report</button>
          <button onClick={() => setTab('Evidence')} className="ff-btn-ghost"><FileSearch size={16} /> View evidence</button>
        </div>
      </div>

      {/* Anakin usage strip */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[['Scraper calls', audit.anakin_usage.scraper_calls], ['Wire calls', audit.anakin_usage.wire_calls],
          ['Cache hits', audit.anakin_usage.cache_hits], ['Est. credits', audit.anakin_usage.estimated_credits]].map(([l, v]) => (
          <div key={l as string} className="ff-card p-3">
            <div className="font-mono-num text-xl font-semibold">{v as number}</div>
            <div className="text-xs text-textFaint">{l as string}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="mt-6 flex gap-1 overflow-x-auto border-b border-cardBorder">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`whitespace-nowrap px-4 py-2.5 text-sm font-medium ${tab === t ? 'border-b-2 border-accent text-textPrimary' : 'text-textFaint'}`}>{t}</button>
        ))}
      </div>

      <div className="mt-5">
        {tab === 'Summary' && <Summary audit={audit} />}
        {tab === 'Manager Claims' && <ManagerClaims audit={audit} />}
        {tab === 'Allocation Diff' && <AllocationDiff audit={audit} />}
        {tab === 'Evidence' && <Evidence audit={audit} />}
        {tab === 'Methodology' && <Methodology audit={audit} />}
      </div>

      <p className="mt-8 text-xs text-textFaint">{audit.disclaimer}</p>
    </AppShell>
  )
}

function CheckCard({ c }: { c: AuditCheckResult }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="ff-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-semibold">{c.name}</div>
          <p className="mt-1 text-sm text-textSecondary">{c.summary}</p>
        </div>
        <div className="text-right">
          <StatusBadge status={c.status} />
          {c.status !== 'insufficient_data' && <div className="mt-1 font-mono-num text-sm">{c.score}</div>}
        </div>
      </div>
      {c.findings.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-textSecondary">
          {c.findings.map((f, i) => <li key={i} className="flex gap-2"><span className="text-textFaint">•</span>{f}</li>)}
        </ul>
      )}
      <button onClick={() => setOpen(!open)} className="mt-3 flex items-center gap-1 text-xs font-medium text-accent">
        <ChevronDown size={14} className={open ? 'rotate-180' : ''} /> How this was calculated
      </button>
      {open && <p className="mt-2 rounded-lg bg-background p-3 text-xs text-textSecondary">{c.methodology}</p>}
    </div>
  )
}

function Summary({ audit }: { audit: FundAuditResult }) {
  return <div className="grid gap-3 md:grid-cols-2">{audit.checks.map((c) => <CheckCard key={c.check_id} c={c} />)}</div>
}

function ManagerClaims({ audit }: { audit: FundAuditResult }) {
  const check = audit.checks.find((c) => c.check_id === 'manager_said_vs_did')
  const rows = check?.table || []
  if (!rows.length) return <p className="text-sm text-textFaint">No manager portfolio-action statements were extracted.</p>
  return (
    <div className="ff-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-background text-left text-xs text-textFaint">
          <tr>{['Manager statement', 'Previous', 'Current', 'Observed', 'Status'].map((h) => <th key={h} className="px-4 py-2.5 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-cardBorder">
              <td className="px-4 py-3 max-w-xs">{r.statement}</td>
              <td className="px-4 py-3 font-mono-num">{r.previous_weight ?? '—'}%</td>
              <td className="px-4 py-3 font-mono-num">{r.current_weight ?? '—'}%</td>
              <td className="px-4 py-3 font-mono-num">{r.observed_movement != null ? `${r.observed_movement > 0 ? '+' : ''}${r.observed_movement} pp` : '—'}</td>
              <td className="px-4 py-3">
                <span className={r.status === 'mismatch' ? 'text-loss' : r.status === 'consistent' ? 'text-gain' : 'text-textFaint'}>
                  {r.status === 'mismatch' ? 'Mismatch' : r.status === 'consistent' ? 'Consistent' : r.status === 'opinion_only' ? 'Opinion only' : 'Insufficient'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function AllocationDiff({ audit }: { audit: FundAuditResult }) {
  if (!audit.allocation_diff.length) return <p className="text-sm text-textFaint">No allocation data available.</p>
  return (
    <div className="ff-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-background text-left text-xs text-textFaint">
          <tr>{['Name', 'Previous', 'Current', 'Delta'].map((h) => <th key={h} className="px-4 py-2.5 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody>
          {audit.allocation_diff.map((a, i) => (
            <tr key={i} className="border-t border-cardBorder">
              <td className="px-4 py-3">{a.name}</td>
              <td className="px-4 py-3 font-mono-num">{a.previous_weight ?? '—'}%</td>
              <td className="px-4 py-3 font-mono-num">{a.current_weight ?? '—'}%</td>
              <td className={`px-4 py-3 font-mono-num ${a.delta_percentage_points == null ? '' : a.delta_percentage_points > 0 ? 'text-gain' : a.delta_percentage_points < 0 ? 'text-loss' : ''}`}>
                {a.delta_percentage_points != null ? `${a.delta_percentage_points > 0 ? '+' : ''}${a.delta_percentage_points} pp` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Evidence({ audit }: { audit: FundAuditResult }) {
  if (!audit.evidence.length) return <p className="text-sm text-textFaint">No evidence sources recorded.</p>
  return (
    <div className="space-y-3">
      {audit.evidence.map((e) => (
        <div key={e.id} className="ff-card p-4">
          <div className="flex flex-wrap items-center gap-2 text-xs text-textFaint">
            <span className="ff-badge bg-background">{e.source_type}</span>
            {e.reporting_period && <span>{e.reporting_period}</span>}
            <span className={e.cached ? 'text-textFaint' : 'text-gain'}>{e.cached ? 'cached' : 'fresh'}</span>
            {e.anakin_job_id && <span>Anakin job: {e.anakin_job_id}</span>}
            <span>conf. {Math.round((e.extraction_confidence || 0) * 100)}%</span>
          </div>
          <div className="mt-1 font-semibold">{e.title}</div>
          {e.excerpt && <p className="mt-1 text-sm text-textSecondary">“{e.excerpt}”</p>}
          {e.url && !e.url.startsWith('anakin-wire://') && (
            <a href={e.url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs font-medium text-accent underline">View source</a>
          )}
        </div>
      ))}
    </div>
  )
}

function Methodology({ audit }: { audit: FundAuditResult }) {
  return (
    <div className="space-y-3">
      {audit.checks.map((c) => (
        <div key={c.check_id} className="ff-card p-4">
          <div className="font-semibold">{c.name}</div>
          <p className="mt-1 text-sm text-textSecondary">{c.explanation}</p>
          <p className="mt-2 rounded-lg bg-background p-3 text-xs text-textSecondary">{c.methodology}</p>
        </div>
      ))}
      {audit.limitations.length > 0 && (
        <div className="ff-card p-4">
          <div className="font-semibold">Limitations</div>
          <ul className="mt-2 space-y-1 text-sm text-textSecondary">
            {audit.limitations.map((l, i) => <li key={i}>• {l}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}
