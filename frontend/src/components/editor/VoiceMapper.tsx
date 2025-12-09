import { useEffect, useState } from 'react'
import { useEditorStore } from '@/store/editorStore'
import { voicesApi } from '@/api/voices'
import type { Voice } from '@/types'
import { Mic2 } from 'lucide-react'

const speakerColors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500']

export function VoiceMapper() {
  const { segments, voiceMapping, updateVoiceForSpeaker } = useEditorStore()
  const [voices, setVoices] = useState<Voice[]>([])

  // Get unique speaker IDs from segments
  const speakerIds = [...new Set(segments.map((s) => s.speaker_id))].sort()

  useEffect(() => {
    voicesApi.listEmbedded().then(setVoices).catch(console.error)
  }, [])

  if (speakerIds.length === 0) return null

  return (
    <div className="border-t border-slate-700 p-4 bg-slate-800/50">
      <div className="flex items-center gap-2 mb-3">
        <Mic2 className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-300">Voice Mapping</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {speakerIds.map((speakerId) => (
          <div key={speakerId} className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${speakerColors[(speakerId - 1) % 4]}`}
            />
            <span className="text-sm text-slate-400 w-20">Speaker {speakerId}</span>
            <select
              value={voiceMapping[speakerId] || 'en-Carter_man'}
              onChange={(e) => updateVoiceForSpeaker(speakerId, e.target.value)}
              className="flex-1 bg-slate-700 text-white text-sm px-2 py-1.5 rounded border-none focus:ring-1 focus:ring-primary-500"
            >
              {voices.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name} ({voice.language}, {voice.gender})
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  )
}
