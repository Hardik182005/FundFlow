// Replicates resolveMfuFund from app/dashboard/page.tsx against the live backend
// to validate matching on real MFU-statement-style names.
const API = 'https://fundflow-backend-m477e5mida-el.a.run.app'

const MFU_NOISE_WORDS = /\b(fund|plan|option|scheme|growth|regular|direct|idcw|dividend|reinvestment|payout|bonus)\b/gi
const tokens = s => s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(Boolean)

function score(original, candidate) {
  const o = new Set(tokens(original))
  const c = new Set(tokens(candidate))
  let overlap = 0
  o.forEach(t => { if (c.has(t)) overlap++ })
  let s = overlap / Math.max(o.size, 1) - (c.size - overlap) * 0.05
  if (/\bdirect\b/i.test(original) === /\bdirect\b/i.test(candidate)) s += 0.5
  const wantsGrowth = !/\b(idcw|dividend|payout|bonus)\b/i.test(original)
  const candGrowth = /\bgrowth\b/i.test(candidate) && !/\b(idcw|dividend|payout|bonus)\b/i.test(candidate)
  if (wantsGrowth === candGrowth) s += 0.5
  return s
}

async function resolve(name) {
  const cleaned = name.replace(/-/g, ' ').replace(/\s+/g, ' ').trim()
  const significant = cleaned.replace(MFU_NOISE_WORDS, ' ').replace(/\s+/g, ' ').trim()
  const w = significant.split(' ')
  const queries = [cleaned, significant, w.slice(0, 4).join(' '), w.slice(0, 3).join(' '), w.slice(0, 2).join(' ')]
  const seen = new Set()
  for (const q of queries) {
    const key = q.trim().toLowerCase()
    if (key.length < 3 || seen.has(key)) continue
    seen.add(key)
    const res = await fetch(`${API}/api/nav/search?q=${encodeURIComponent(q.trim())}`).then(r => r.json()).catch(() => [])
    if (Array.isArray(res) && res.length > 0) {
      return res.map(r => ({ code: String(r.schemeCode), name: r.schemeName, s: score(name, r.schemeName) }))
        .sort((a, b) => b.s - a.s)[0]
    }
  }
  return null
}

const rows = [
  'Parag Parikh Flexi Cap Fund Regular Growth',
  'SBI Bluechip Fund Regular Growth',
  'HDFC Mid-Cap Opportunities Fund Regular Growth',
  'Tata Money Market Fund Regular Growth',
  'Axis Long Term Equity Fund Direct Growth',
]
for (const r of rows) {
  const m = await resolve(r)
  console.log(m ? `MATCH  '${r}'\n  -> [${m.code}] ${m.name} (score ${m.s.toFixed(2)})` : `NOMATCH '${r}'`)
}
