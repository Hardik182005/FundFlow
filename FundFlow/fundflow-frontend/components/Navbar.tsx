'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Navbar() {
  const pathname = usePathname()
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#F7F8FA]/95 backdrop-blur border-b border-[#E7E9EE]">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-[#0B0D12] rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">F</span>
          </div>
          <span className="font-bold text-xl text-[#0A0A0A]">FundFlow</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {[
            { href: '/', label: 'Home' },
            { href: '/#features', label: 'Features' },
            { href: '/#how-it-works', label: 'How it works' },
            { href: '/dashboard', label: 'Portfolio' },
            { href: '/explore', label: 'Explore' },
          ].map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`text-sm font-medium transition-colors ${
                pathname === href ? 'text-[#0B0D12]' : 'text-[#565B66] hover:text-[#0A0A0A]'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button className="text-sm font-medium text-[#565B66] hover:text-[#0A0A0A] px-4 py-2">
            Login
          </button>
          <Link
            href="/dashboard"
            className="bg-[#0B0D12] text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-[#000000] transition-colors"
          >
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  )
}
