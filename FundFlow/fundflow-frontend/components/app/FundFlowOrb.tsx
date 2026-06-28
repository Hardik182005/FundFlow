'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { usePathname } from 'next/navigation'
import { Mic, MicOff, X, Loader2, AlertCircle, Send, MessageSquare, AudioLines } from 'lucide-react'
import { ConversationProvider, useConversation } from '@elevenlabs/react'
import { sendAssistantMessage, getSpeech } from '@/lib/api'

const AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID
const AGENT_CONFIGURED = Boolean(AGENT_ID && AGENT_ID !== 'your_elevenlabs_agent_id_here')

type OrbState = 'idle' | 'connecting' | 'listening' | 'thinking' | 'speaking' | 'muted' | 'error'

function suggestionsFor(path: string | null): string[] {
  if (path?.startsWith('/audit/') && path !== '/audit/history') {
    return ['Why did this fund receive a warning?', 'What did the manager say?', 'What actually changed in the holdings?', 'Read this verdict aloud.']
  }
  if (path?.startsWith('/audit')) return ['Which existing funds are similar?', 'How does an audit work?', 'Audit my largest holding.']
  return ['How is my portfolio performing?', 'Which holding has the highest risk?', 'Audit my largest holding.']
}

interface Msg { role: 'user' | 'assistant'; text: string }

export default function FundFlowOrb() {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<'chat' | 'voice'>('chat')
  const pathname = usePathname()
  const auditId = pathname?.startsWith('/audit/') && pathname !== '/audit/history' ? pathname.split('/')[2] : undefined

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Open FundFlow assistant"
        className="fixed bottom-6 right-6 z-50 grid h-14 w-14 place-items-center rounded-full bg-accent text-white shadow-xl transition-transform hover:scale-105 animate-orb-pulse"
      >
        <AudioLines size={22} />
      </button>

      {open && (
        <div className="fixed inset-x-0 bottom-0 z-50 sm:inset-auto sm:bottom-24 sm:right-6">
          <div className="mx-auto w-full max-w-md rounded-t-2xl border border-cardBorder bg-white shadow-2xl sm:w-96 sm:rounded-2xl">
            <div className="flex items-center justify-between border-b border-cardBorder px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-accent text-xs font-bold text-white">F</span>
                <div>
                  <div className="text-sm font-semibold">FundFlow Assistant</div>
                  <div className="text-[10px] text-textFaint">Grounded in your audits</div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => setMode(mode === 'chat' ? 'voice' : 'chat')}
                  className="rounded-lg p-2 text-textSecondary hover:bg-background" aria-label="Toggle mode">
                  {mode === 'chat' ? <Mic size={16} /> : <MessageSquare size={16} />}
                </button>
                <button onClick={() => setOpen(false)} className="rounded-lg p-2 text-textSecondary hover:bg-background" aria-label="Close"><X size={16} /></button>
              </div>
            </div>
            {mode === 'chat'
              ? <ChatPanel auditId={auditId} pathname={pathname} />
              : AGENT_CONFIGURED
                ? <ConversationProvider><VoicePanel /></ConversationProvider>
                : <div className="p-5 text-center text-sm text-textFaint">Voice agent setup in progress. Use chat mode meanwhile.</div>}
          </div>
        </div>
      )}
    </>
  )
}

function ChatPanel({ auditId, pathname }: { auditId?: string; pathname: string | null }) {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const convId = useRef<string | undefined>(undefined)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = useCallback(async (text: string) => {
    if (!text.trim() || loading) return
    setMessages((m) => [...m, { role: 'user', text }])
    setInput(''); setLoading(true)
    try {
      const r = await sendAssistantMessage({ message: text, audit_id: auditId, conversation_id: convId.current })
      convId.current = r.conversation_id
      setMessages((m) => [...m, { role: 'assistant', text: r.answer }])
    } catch {
      setMessages((m) => [...m, { role: 'assistant', text: 'The assistant is unavailable right now. Please try again.' }])
    } finally { setLoading(false) }
  }, [auditId, loading])

  async function speak(text: string) {
    try {
      const blob = await getSpeech(text)
      new Audio(URL.createObjectURL(blob)).play()
    } catch {
      speechSynthesis.speak(new SpeechSynthesisUtterance(text))
    }
  }

  return (
    <div className="flex h-[26rem] flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-textFaint">Ask about your portfolio or an audit:</p>
            {suggestionsFor(pathname).map((s) => (
              <button key={s} onClick={() => send(s)} className="block w-full rounded-lg border border-cardBorder bg-background px-3 py-2 text-left text-xs text-textSecondary hover:border-accent/40">{s}</button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm ${m.role === 'user' ? 'bg-accent text-white' : 'bg-background text-textPrimary'}`}>
              {m.text}
              {m.role === 'assistant' && (
                <button onClick={() => speak(m.text)} className="mt-1 block text-[10px] text-textFaint hover:text-accent">🔊 Read aloud</button>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="flex items-center gap-2 text-xs text-textFaint"><Loader2 className="animate-spin" size={14} /> Thinking…</div>}
        <div ref={endRef} />
      </div>
      <form onSubmit={(e) => { e.preventDefault(); send(input) }} className="flex gap-2 border-t border-cardBorder p-3">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask FundFlow…" className="ff-input" />
        <button type="submit" disabled={loading} className="ff-btn-primary px-3"><Send size={16} /></button>
      </form>
    </div>
  )
}

function VoicePanel() {
  const [error, setError] = useState<string | null>(null)
  const [state, setState] = useState<OrbState>('idle')
  const conversation = useConversation({ onError: () => { setError("Couldn't start voice session — please try again."); setState('error') } })
  const { status, isSpeaking, startSession, endSession } = conversation
  const isConnected = status === 'connected'

  useEffect(() => {
    if (status === 'connecting') setState('connecting')
    else if (isConnected) setState(isSpeaking ? 'speaking' : 'listening')
    else setState('idle')
  }, [status, isConnected, isSpeaking])

  // stop session on unmount (prevents duplicate/leaked sessions)
  useEffect(() => () => { if (isConnected) { try { Promise.resolve(endSession()).catch(() => {}) } catch { /* noop */ } } }, [isConnected, endSession])

  const toggle = useCallback(async () => {
    if (isConnected) { try { await Promise.resolve(endSession()) } catch { /* noop */ } return }
    setError(null)
    try { await navigator.mediaDevices.getUserMedia({ audio: true }) }
    catch { setError('Microphone access is needed for voice chat. Please allow it and try again.'); setState('error'); return }
    try { await startSession({ agentId: AGENT_ID as string, connectionType: 'webrtc' }) }
    catch { setError("Couldn't start voice session — please try again."); setState('error') }
  }, [isConnected, endSession, startSession])

  return (
    <div className="p-5">
      <div className="mb-4 flex h-16 items-center justify-center gap-1">
        {state === 'connecting' ? <Loader2 className="animate-spin text-accent" size={22} />
          : isConnected ? Array.from({ length: 14 }).map((_, i) => (
            <div key={i} className="w-1 rounded-full bg-accent" style={{ height: isSpeaking ? `${16 + (i % 4) * 10}px` : '6px', opacity: isSpeaking ? 1 : 0.4, transition: 'height .2s' }} />
          )) : <p className="text-sm text-textFaint">Tap to start a voice conversation.</p>}
      </div>
      <p className="mb-3 text-center text-xs capitalize text-textSecondary">{state}</p>
      {error && <div className="mb-3 flex items-start gap-2 rounded-lg border border-loss/20 bg-loss/5 px-3 py-2 text-xs text-loss"><AlertCircle size={14} className="mt-0.5" />{error}</div>}
      <button onClick={toggle} disabled={state === 'connecting'}
        className={`ff-btn w-full ${isConnected ? 'bg-loss text-white' : 'bg-accent text-white'}`}>
        {state === 'connecting' ? <Loader2 className="animate-spin" size={16} /> : isConnected ? <MicOff size={16} /> : <Mic size={16} />}
        {state === 'connecting' ? 'Connecting…' : isConnected ? 'Stop voice' : 'Start voice'}
      </button>
    </div>
  )
}
