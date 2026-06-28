'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import {
  LayoutDashboard, Wallet, ShieldCheck, History, GitCompare,
  Compass, FileSearch, Newspaper, Activity, Settings, Menu, X,
} from 'lucide-react'
import FundFlowOrb from './FundFlowOrb'

const NAV = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Portfolio', href: '/portfolio', icon: Wallet },
  { label: 'Audit Funds', href: '/audit', icon: ShieldCheck },
  { label: 'Audit History', href: '/audit/history', icon: History },
  { label: 'Compare', href: '/compare', icon: GitCompare },
  { label: 'Explore', href: '/explore', icon: Compass },
  { label: 'Evidence', href: '/evidence', icon: FileSearch },
  { label: 'News', href: '/news', icon: Newspaper },
  { label: 'Anakin Usage', href: '/settings/usage', icon: Activity },
  { label: 'Settings', href: '/settings', icon: Settings },
]

export default function AppShell({ children, title }: { children: React.ReactNode; title?: string }) {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  const isActive = (href: string) =>
    href === '/dashboard' ? pathname === href : pathname?.startsWith(href)

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar (desktop) */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-cardBorder bg-white lg:flex">
        <SidebarInner isActive={isActive} />
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-white shadow-xl">
            <div className="flex justify-end p-3">
              <button onClick={() => setOpen(false)} aria-label="Close menu"><X size={20} /></button>
            </div>
            <SidebarInner isActive={isActive} onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-cardBorder bg-white/80 px-4 py-3 backdrop-blur md:px-8">
          <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={22} /></button>
          <h1 className="font-display text-lg font-semibold">{title || 'FundFlow'}</h1>
          <div className="ml-auto">
            <Link href="/audit" className="ff-btn-primary text-xs">Audit a Fund</Link>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6 md:px-8">{children}</main>
      </div>
      <FundFlowOrb />
    </div>
  )
}

function SidebarInner({ isActive, onNavigate }: { isActive: (h: string) => boolean | undefined; onNavigate?: () => void }) {
  return (
    <>
      <Link href="/" className="flex items-center gap-2 px-5 py-5" onClick={onNavigate}>
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-sm font-bold text-white">F</span>
        <div>
          <div className="font-display text-base font-semibold leading-none">FundFlow</div>
          <div className="text-[10px] text-textFaint">Track. Trust.</div>
        </div>
      </Link>
      <nav className="flex-1 space-y-0.5 px-3">
        {NAV.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
              isActive(href) ? 'bg-accent text-white' : 'text-textSecondary hover:bg-background hover:text-textPrimary'
            }`}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-4 text-[10px] text-textFaint">
        AI-assisted audit, not investment advice.
      </div>
    </>
  )
}
