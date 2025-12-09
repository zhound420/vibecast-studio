import { useEffect, useState } from 'react'
import { voicesApi } from '@/api/voices'
import type { Voice } from '@/types'
import { Mic2, Play, Pause } from 'lucide-react'
import { Button } from '@/components/common/Button'

export function VoicesPage() {
  const [voices, setVoices] = useState<Voice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [playingVoice, setPlayingVoice] = useState<string | null>(null)

  useEffect(() => {
    voicesApi.listEmbedded()
      .then(setVoices)
      .catch(console.error)
      .finally(() => setIsLoading(false))
  }, [])

  const languageNames: Record<string, string> = {
    en: 'English',
    zh: 'Chinese',
    in: 'Indian English',
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Voices</h1>
          <p className="text-slate-400 mt-1">
            {voices.length} embedded voices available from VibeVoice
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {voices.map((voice) => (
            <div
              key={voice.id}
              className="bg-slate-800 rounded-xl p-4 hover:bg-slate-750 transition-colors"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-primary-600/20 rounded-full flex items-center justify-center">
                  <Mic2 className="w-6 h-6 text-primary-500" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-white">{voice.name}</h3>
                  <p className="text-sm text-slate-400">
                    {languageNames[voice.language] || voice.language} · {voice.gender}
                  </p>
                  {voice.has_background_music && (
                    <span className="inline-block mt-1 text-xs bg-purple-900/50 text-purple-300 px-2 py-0.5 rounded">
                      Includes BGM
                    </span>
                  )}
                </div>
              </div>

              {voice.description && (
                <p className="mt-3 text-sm text-slate-500">{voice.description}</p>
              )}

              <div className="mt-4">
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full"
                  disabled
                >
                  <Play className="w-4 h-4 mr-2" />
                  Preview
                </Button>
              </div>

              <div className="mt-2 text-xs text-slate-600 font-mono">
                {voice.id}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
