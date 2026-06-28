'use client'
import { useEffect, useState } from 'react'

const STATS = [
  { value: '10,000+', label: 'Active Schemes Tracked' },
  { value: 'Daily', label: 'NAV Refresh from AMFI' },
  { value: '4.2s', label: 'Avg Analysis Time' },
  { value: '4', label: 'AI Models in Stack' },
]

export default function StatsBar() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 300)
    return () => clearTimeout(t)
  }, [])

  return (
    <section className="py-16 px-6 max-w-7xl mx-auto">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
        {STATS.map((s, i) => (
          <div
            key={i}
            className={`text-center transition-all duration-700 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
            style={{ transitionDelay: `${i * 100}ms` }}
          >
            <div className="text-4xl lg:text-5xl font-extrabold text-[#0A0A0A] font-mono mb-2">{s.value}</div>
            <div className="text-sm text-[#565B66] font-medium uppercase tracking-wide">{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
