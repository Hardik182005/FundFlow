'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/app/AppShell'
import { getNews } from '@/lib/api'

interface NewsItem { title: string; link?: string; url?: string; summary?: string; published?: string; source?: string }

export default function NewsPage() {
  const [items, setItems] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getNews().then((r) => setItems(r.items || r.news || r || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <AppShell title="News">
      {loading ? <div className="ff-card h-40 animate-pulse" /> : (
        <div className="space-y-3">
          {items.map((n, i) => (
            <a key={i} href={n.link || n.url} target="_blank" rel="noreferrer" className="ff-card block p-4 transition-shadow hover:shadow-md">
              <div className="font-semibold">{n.title}</div>
              {n.summary && <p className="mt-1 text-sm text-textSecondary line-clamp-2">{n.summary}</p>}
              <div className="mt-1 text-xs text-textFaint">{n.source} {n.published}</div>
            </a>
          ))}
          {items.length === 0 && <div className="ff-card p-8 text-center text-textFaint">No news available.</div>}
        </div>
      )}
    </AppShell>
  )
}
