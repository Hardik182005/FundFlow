export function formatINR(amount: number): string {
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(2)}Cr`
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(2)}L`
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 }).format(amount)
}

export function formatNAV(nav: number): string {
  return nav.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function getOrCreateUserId(): string {
  if (typeof window === 'undefined') return 'anonymous'
  let id = localStorage.getItem('fundflow_user_id')
  if (!id) {
    id = 'user_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('fundflow_user_id', id)
  }
  return id
}

export function verdictColor(verdict: string): string {
  switch (verdict?.toUpperCase()) {
    case 'ADD': return '#0E9F6E'
    case 'EXIT': return '#E02424'
    case 'HOLD': return '#FFA500'
    case 'WATCH': return '#888888'
    default: return '#888888'
  }
}
