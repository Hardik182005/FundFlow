// Voice playback helpers.
//
// Primary path: ElevenLabs TTS audio (a "nice voice") served by the backend.
// Fallback path: the browser's built-in speechSynthesis, so something always
// speaks even if the backend / ElevenLabs key is unavailable.

import { getFundNarration } from './api'

let currentAudio: HTMLAudioElement | null = null

/** Stop any voice that is currently playing (ElevenLabs audio or browser speech). */
export function stopVoice() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.src = ''
    currentAudio = null
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
}

/** Speak plain text using the browser's built-in voice (offline fallback). */
export function speakWithBrowser(text: string) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const utter = new SpeechSynthesisUtterance(text)
  utter.rate = 1.0
  utter.pitch = 1.0
  // Prefer an English (ideally Indian-English) voice if available.
  const voices = window.speechSynthesis.getVoices()
  const preferred =
    voices.find(v => /en-IN/i.test(v.lang)) ||
    voices.find(v => /en-GB/i.test(v.lang)) ||
    voices.find(v => /^en/i.test(v.lang))
  if (preferred) utter.voice = preferred
  window.speechSynthesis.speak(utter)
}

/** Play an MP3 audio Blob; resolves when playback starts, rejects on error. */
function playBlob(blob: Blob): Promise<void> {
  stopVoice()
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  currentAudio = audio
  audio.onended = () => URL.revokeObjectURL(url)
  return audio.play()
}

/**
 * Narrate a fund's analysis out loud. Tries the ElevenLabs "nice voice" first,
 * and falls back to the browser voice if that fails for any reason.
 */
export async function playFundNarration(
  fund: { scheme_code: string; fund_name: string; category?: string; units: number; buy_nav: number },
  fallbackText?: string,
) {
  try {
    const blob = await getFundNarration(fund)
    await playBlob(blob)
    return
  } catch {
    // Fall back to the browser's built-in speech.
    const text =
      fallbackText ||
      `Here is your FundFlow analysis for ${fund.fund_name}. You can read the full detailed report in the PDF.`
    speakWithBrowser(text)
  }
}
