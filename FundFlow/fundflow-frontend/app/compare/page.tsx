'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AppShell from '@/components/app/AppShell'
import { verdictColor } from '@/components/app/StatusBadge'
import { getAuditHistory, getFundAudit } from '@/lib/api'
import type { FundAuditResult } from '@/lib/types'

const CHECK_ORDER: [string, string][] = [
  ['manager_said_vs_did', 'Manager Said vs Did'],
  ['style_drift', 'Style Drift'],
  ['manager_tenure', 'Manager Continuity'],
  ['nfo_clone', 'NFO Clone Detector'],
  ['skin_in_game', 'Skin in the Game'],
  ['hidden_churn', 'Churn Transparency'],
]
const STATUS_STYLE: Record<string, string> = {
  pass: 'text-gain', warning: 'text-warn', fail: 'text-loss', insufficient_data: 'text-textFaint',
}
const STATUS_LABEL: Record<string, string> = {
  pass: 'Pass', warning: 'Warning', fail: 'Fail', insufficient_data: 'Insufficient',
}

export default function ComparePage() {
  const [audits, setAudits] = useState<FundAuditResult[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const { audits: summaries } = await getAuditHistory('demo-user')
        const full = await Promise.all(summaries.map((s) => getFundAudit(s.audit_id).catch(() => null)))
        setAudits(full.filter(Boolean) as FundAuditResult[])
      } finally { setLoading(false) }
    })()
  }, [])

  const checkFor = (a: FundAuditResult, id: string) => a.checks.find((c) => c.check_id === id)

  return (
    <AppShell title="Compare">
      <p className="mb-5 text-sm text-textFaint">Side-by-side comparison of the funds you have audited — trust scores and every audit check.</p>

      {loading ? <div className="ff-card h-64 animate-pulse" /> : audits.length === 0 ? (
        <div className="ff-card p-8 text-center text-textFaint">Audit a few funds first to compare them. <Link href="/audit" className="text-accent underline">Run an audit</Link>.</div>
      ) : (
        <div className="ff-card overflow-x-auto">
          <table className="w-full min-w-[680px] text-sm">
            <thead>
              <tr className="border-b border-cardBorder">
                <th className="px-4 py-3 text-left text-xs font-medium text-textFaint">Metric</th>
                {audits.map((a) => (
                  <th key={a.audit_id} className="px-4 py-3 text-left align-top">
                    <Link href={`/audit/view?id=${a.audit_id}`} className="font-semibold hover:text-accent">{a.fund_name}</Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-cardBorder bg-background/50">
                <td className="px-4 py-3 font-medium">Trust Score</td>
                {audits.map((a) => (
                  <td key={a.audit_id} className="px-4 py-3">
                    <span className="font-mono-num text-2xl font-bold">{a.trust_score}</span>
                    <div className="mt-1 h-1.5 w-28 rounded-full bg-cardBorder">
                      <div className="h-1.5 rounded-full bg-accent" style={{ width: `${a.trust_score}%` }} />
                    </div>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-cardBorder">
                <td className="px-4 py-3 font-medium">Verdict</td>
                {audits.map((a) => (
                  <td key={a.audit_id} className="px-4 py-3">
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${verdictColor(a.verdict)}`}>{a.verdict}</span>
                  </td>
                ))}
              </tr>
              {CHECK_ORDER.map(([id, label]) => (
                <tr key={id} className="border-b border-cardBorder last:border-0">
                  <td className="px-4 py-3 font-medium">{label}</td>
                  {audits.map((a) => {
                    const c = checkFor(a, id)
                    return (
                      <td key={a.audit_id} className="px-4 py-3">
                        {c ? (
                          <span className={STATUS_STYLE[c.status]}>
                            {STATUS_LABEL[c.status]}{c.status !== 'insufficient_data' && <span className="ml-1 font-mono-num text-textFaint">({c.score})</span>}
                          </span>
                        ) : <span className="text-textFaint">—</span>}
                      </td>
                    )
                  })}
                </tr>
              ))}
              <tr className="border-t border-cardBorder bg-background/50">
                <td className="px-4 py-3 font-medium">Evidence sources</td>
                {audits.map((a) => (
                  <td key={a.audit_id} className="px-4 py-3 font-mono-num">{a.evidence.length}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  )
}
