'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AppShell from '@/components/app/AppShell'
import { verdictColor } from '@/components/app/StatusBadge'
import { getAuditHistory } from '@/lib/api'
import type { AuditSummary } from '@/lib/types'

export default function ComparePage() {
  const [audits, setAudits] = useState<AuditSummary[]>([])
  useEffect(() => { getAuditHistory().then((r) => setAudits(r.audits)).catch(() => {}) }, [])

  return (
    <AppShell title="Compare">
      <p className="mb-4 text-sm text-textFaint">Compare trust scores across funds you have audited.</p>
      {audits.length === 0 ? (
        <div className="ff-card p-8 text-center text-textFaint">Audit a few funds first to compare them.</div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {audits.map((a) => (
            <Link key={a.audit_id} href={`/audit/view?id=${a.audit_id}`} className="ff-card p-4 transition-shadow hover:shadow-md">
              <div className="text-sm font-semibold leading-tight">{a.fund_name}</div>
              <div className="mt-3 flex items-end justify-between">
                <span className="font-mono-num text-3xl font-bold">{a.trust_score}</span>
                <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${verdictColor(a.verdict)}`}>{a.verdict}</span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-background">
                <div className="h-2 rounded-full bg-accent" style={{ width: `${a.trust_score}%` }} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  )
}
