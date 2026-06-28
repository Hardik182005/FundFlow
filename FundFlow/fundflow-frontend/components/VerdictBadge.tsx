export default function VerdictBadge({ verdict }: { verdict: string }) {
  const styles: Record<string, string> = {
    HOLD: 'bg-[#FFA500] text-white',
    ADD: 'bg-[#0E9F6E] text-white',
    EXIT: 'bg-[#E02424] text-white',
    WATCH: 'bg-[#888888] text-white',
  }
  const v = verdict?.toUpperCase() || 'WATCH'
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide ${styles[v] || styles.WATCH}`}>
      {v}
    </span>
  )
}
