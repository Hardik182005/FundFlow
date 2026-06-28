'use client'

import { useCallback, useState } from 'react'
import { Mic, MicOff, X, Loader2, AlertCircle } from 'lucide-react'
import { ConversationProvider, useConversation } from '@elevenlabs/react'

const SUGGESTIONS = [
  'How is my portfolio today?',
  'Which fund is performing best?',
  'Should I add more to SBI Bluechip?',
  "What is today's NAV for Tata Money Market?",
]

const AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID
const AGENT_CONFIGURED = Boolean(AGENT_ID && AGENT_ID !== 'your_elevenlabs_agent_id_here')

const FRIENDLY_ERROR = "Couldn't start voice session — please try again."

/**
 * Inner panel that talks to the ElevenLabs Conversational AI agent.
 * Rendered inside a ConversationProvider so it can use useConversation().
 */
function VoicePanelContent({ onClose }: { onClose: () => void }) {
  const [error, setError] = useState<string | null>(null)
  const [connecting, setConnecting] = useState(false)

  const conversation = useConversation({
    onError: () => setError(FRIENDLY_ERROR),
  })

  const { status, isSpeaking, startSession, endSession, sendUserMessage } = conversation
  const isConnected = status === 'connected'
  const isConnecting = status === 'connecting' || connecting

  const ensureSession = useCallback(async () => {
    setError(null)
    try {
      // Ask for microphone permission up front so we can show a friendly
      // message instead of letting the SDK throw a raw browser error.
      await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setError('Microphone access is needed for voice chat. Please allow microphone permission and try again.')
      return false
    }

    try {
      setConnecting(true)
      await startSession({ agentId: AGENT_ID as string, connectionType: 'webrtc' })
      return true
    } catch {
      setError(FRIENDLY_ERROR)
      return false
    } finally {
      setConnecting(false)
    }
  }, [startSession])

  const handleToggle = useCallback(async () => {
    if (isConnected) {
      try {
        await endSession()
      } catch {
        // Ending a session should never surface an error to the user.
      }
      return
    }
    await ensureSession()
  }, [isConnected, endSession, ensureSession])

  const handleSuggestion = useCallback(
    async (text: string) => {
      setError(null)
      if (!isConnected) {
        const started = await ensureSession()
        if (!started) return
      }
      try {
        sendUserMessage(text)
      } catch {
        setError(FRIENDLY_ERROR)
      }
    },
    [isConnected, ensureSession, sendUserMessage]
  )

  let statusLabel = 'Hi! Ask me anything about your portfolio.'
  if (isConnecting) statusLabel = 'Connecting…'
  else if (isConnected && isSpeaking) statusLabel = 'Speaking…'
  else if (isConnected) statusLabel = "Listening… go ahead, I'm all ears."

  return (
    <div className="p-5">
      {/* Waveform / status */}
      <div className="flex items-center justify-center gap-1 h-12 mb-5">
        {isConnecting ? (
          <Loader2 className="w-5 h-5 text-[#0B0D12] animate-spin" />
        ) : isConnected ? (
          Array.from({ length: 12 }).map((_, i) => (
            <div
              key={i}
              className={`w-1 bg-[#0B0D12] rounded-full ${isSpeaking ? 'animate-pulse' : ''}`}
              style={{
                height: isSpeaking ? `${20 + (i % 4) * 8}px` : '6px',
                animationDelay: `${i * 0.1}s`,
                opacity: isSpeaking ? 1 : 0.35,
              }}
            />
          ))
        ) : (
          <p className="text-[#565B66] text-sm text-center">{statusLabel}</p>
        )}
      </div>

      {isConnecting && (
        <p className="text-[#565B66] text-xs text-center -mt-3 mb-3">{statusLabel}</p>
      )}
      {isConnected && (
        <p className="text-[#565B66] text-xs text-center -mt-3 mb-3">{statusLabel}</p>
      )}

      {error && (
        <div className="mb-3 flex items-start gap-2 bg-[#FFF4F4] border border-[#FFD9D9] text-[#B3261E] text-xs rounded-lg px-3 py-2">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tap to speak */}
      <button
        onClick={handleToggle}
        disabled={isConnecting}
        className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed ${
          isConnected
            ? 'bg-[#E02424] text-white'
            : 'bg-[#0B0D12] text-white hover:bg-[#000000]'
        }`}
      >
        {isConnecting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isConnected ? (
          <MicOff className="w-4 h-4" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
        {isConnecting ? 'Connecting…' : isConnected ? 'Stop' : 'Tap to speak'}
      </button>

      {/* Suggestions */}
      <div className="mt-4 flex flex-col gap-2">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => handleSuggestion(s)}
            className="text-left text-xs text-[#565B66] bg-[#F7F8FA] px-3 py-2 rounded-lg hover:bg-[#0B0D12]/5 hover:text-[#0B0D12] transition-colors border border-[#E7E9EE]"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

/** Shown instead of the live panel while no real ElevenLabs agent is configured. */
function SetupPendingPanel() {
  return (
    <div className="p-5">
      <div className="flex items-center justify-center h-12 mb-5">
        <p className="text-[#565B66] text-sm text-center">
          Hi! Ask me anything about your portfolio.
        </p>
      </div>

      <div className="bg-[#F7F8FA] border border-[#E7E9EE] text-[#565B66] text-sm rounded-xl px-4 py-3 text-center">
        Voice assistant setup in progress — check back soon!
      </div>

      <div className="mt-4 flex flex-col gap-2">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            disabled
            className="text-left text-xs text-[#565B66]/60 bg-[#F7F8FA] px-3 py-2 rounded-lg border border-[#E7E9EE] cursor-not-allowed"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function VoiceAgent() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-[#0B0D12] text-white px-5 py-3.5 rounded-full shadow-xl hover:bg-[#000000] transition-all flex items-center gap-2 font-semibold text-sm hover:shadow-[#0B0D12]/40 hover:shadow-2xl"
      >
        <Mic className="w-4 h-4" />
        Ask FundFlow
      </button>

      {/* Voice panel */}
      {open && (
        <div className="fixed bottom-20 right-6 z-50 w-80 bg-white rounded-2xl shadow-2xl border border-[#E7E9EE] overflow-hidden animate-[fade-in_0.2s_ease-out]">
          <div className="bg-[#0B0D12] px-5 py-4 flex items-center justify-between">
            <div>
              <p className="text-white font-bold text-sm">FundFlow Assistant</p>
              <p className="text-white/70 text-xs">Powered by ElevenLabs AI</p>
            </div>
            <button onClick={() => setOpen(false)} className="text-white/80 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>

          {AGENT_CONFIGURED ? (
            <ConversationProvider>
              <VoicePanelContent onClose={() => setOpen(false)} />
            </ConversationProvider>
          ) : (
            <SetupPendingPanel />
          )}
        </div>
      )}
    </>
  )
}
