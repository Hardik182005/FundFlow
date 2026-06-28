'use client'

import { useEffect } from 'react'

/**
 * Google Website Translate widget — lets a visitor translate the whole site into
 * Hindi and other Indian languages (and beyond). Renders a small language picker
 * pinned bottom-left. The injected top banner is hidden via globals.css.
 */
export default function GoogleTranslate() {
  useEffect(() => {
    if (document.getElementById('google-translate-script')) return
    ;(window as unknown as { googleTranslateElementInit: () => void }).googleTranslateElementInit = () => {
      const g = (window as unknown as { google?: { translate?: { TranslateElement: new (o: object, id: string) => void } } }).google
      if (g?.translate) {
        new g.translate.TranslateElement(
          { pageLanguage: 'en', includedLanguages: 'en,hi,mr,gu,ta,te,kn,bn,pa,ml,or', autoDisplay: false },
          'google_translate_element',
        )
      }
    }
    const s = document.createElement('script')
    s.id = 'google-translate-script'
    s.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'
    document.body.appendChild(s)
  }, [])

  return (
    <div
      id="google_translate_element"
      className="fixed bottom-4 left-4 z-40 rounded-lg border border-cardBorder bg-white/90 px-2 py-1 shadow-sm backdrop-blur"
      aria-label="Translate this site"
    />
  )
}
