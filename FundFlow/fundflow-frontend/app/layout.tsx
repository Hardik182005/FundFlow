import type { Metadata } from 'next'
import './globals.css'
import GoogleTranslate from '@/components/GoogleTranslate'

export const metadata: Metadata = {
  title: 'FundFlow — Track your funds. Trust your funds.',
  description: 'AI-powered mutual-fund manager-accountability audits — powered by Anakin Universal Scraper + Wire.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#F7F8FA] min-h-screen">
        {children}
        <GoogleTranslate />
      </body>
    </html>
  )
}
