'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AppShell from '@/components/app/AppShell'
import { verdictColor } from '@/components/app/StatusBadge'
import { getAuditHistory } from '@/lib/api'
import type { AuditSummary } from '@/lib/types'

export default function AuditHistoryPage() {
  const [audits, setAudits] = useState<AuditSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAuditHistory().then((r) => setAudits(r.audits)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <AppShell title="Audit History">
      {loading ? <div className="ff-card h-40 animate-pulse" /> : audits.length === 0 ? (
        <div className="ff-card p-8 text-center text-textFaint">
          No audits yet. <Link href="/audit" className="text-accent underline">Run your first audit</Link>.
        </div>
      ) : (
        <div className="space-y-3">
          {audits.map((a) => (
            <Link key={a.audit_id} href={`/audit/view?id=${a.audit_id}`} className="ff-card flex items-center justify-between p-4 transition-shadow hover:shadow-md">
              <div>
                <div className="font-semibold">{a.fund_name}</div>
                <div className="text-xs text-textFaint">{a.scheme_code} · {new Date(a.generated_at).toLocaleString()}</div>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono-num text-lg font-semibold">{a.trust_score}</span>
                <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${verdictColor(a.verdict)}`}>{a.verdict}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  )
}
