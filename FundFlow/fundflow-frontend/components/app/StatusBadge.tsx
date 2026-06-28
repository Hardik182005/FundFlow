import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react'
import type { CheckStatus } from '@/lib/types'

const MAP: Record<CheckStatus, { label: string; cls: string; Icon: typeof CheckCircle2 }> = {
  pass: { label: 'Pass', cls: 'bg-gain/10 text-gain', Icon: CheckCircle2 },
  warning: { label: 'Warning', cls: 'bg-warn/10 text-warn', Icon: AlertTriangle },
  fail: { label: 'Fail', cls: 'bg-loss/10 text-loss', Icon: XCircle },
  insufficient_data: { label: 'Insufficient evidence', cls: 'bg-textFaint/10 text-textFaint', Icon: HelpCircle },
}

export default function StatusBadge({ status }: { status: CheckStatus }) {
  const { label, cls, Icon } = MAP[status] || MAP.insufficient_data
  return (
    <span className={`ff-badge ${cls}`}>
      <Icon size={13} /> {label}
    </span>
  )
}

export function verdictColor(verdict: string): string {
  switch (verdict) {
    case 'TRUSTED': return 'bg-gain/10 text-gain border-gain/20'
    case 'MONITOR': return 'bg-warn/10 text-warn border-warn/20'
    case 'REVIEW': return 'bg-warn/10 text-warn border-warn/20'
    case 'HIGH CONCERN': return 'bg-loss/10 text-loss border-loss/20'
    default: return 'bg-textFaint/10 text-textFaint border-cardBorder'
  }
}

export function verdictAction(verdict: string): string {
  switch (verdict) {
    case 'TRUSTED': return 'HOLD / CONSIDER'
    case 'MONITOR': return 'WATCH'
    case 'REVIEW': return 'REVIEW WITH ADVISOR'
    case 'HIGH CONCERN': return 'REASSESS'
    default: return ''
  }
}
