'use client'

import { useEffect } from 'react'
import { Info, X } from 'lucide-react'

interface ToastProps {
  message: string
  onClose: () => void
  duration?: number
}

export default function Toast({ message, onClose, duration = 4000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [onClose, duration])

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] animate-[fade-in_0.2s_ease-out]">
      <div className="flex items-center gap-3 bg-[#0A0A0A] text-white text-sm font-medium pl-4 pr-3 py-3 rounded-xl shadow-2xl max-w-sm">
        <Info className="w-4 h-4 text-[#0B0D12] shrink-0" />
        <span className="flex-1">{message}</span>
        <button onClick={onClose} className="text-white/60 hover:text-white shrink-0">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
