import { useState } from 'react'
import { Button } from '@/components/common/Button'
import { Key, Save } from 'lucide-react'

export function SettingsPage() {
  const [claudeKey, setClaudeKey] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    // In a real app, this would save to backend/localStorage
    setTimeout(() => {
      setIsSaving(false)
      alert('Settings saved!')
    }, 500)
  }

  return (
    <div className="p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-slate-400 mt-1">Configure your VibeCast Studio</p>
        </div>

        {/* API Keys */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Key className="w-5 h-5 text-slate-400" />
            <h2 className="text-lg font-medium text-white">API Keys</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Claude API Key
              </label>
              <input
                type="password"
                value={claudeKey}
                onChange={(e) => setClaudeKey(e.target.value)}
                placeholder="sk-ant-..."
                className="w-full bg-slate-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="mt-1 text-xs text-slate-500">
                Required for dialogue enhancement feature
              </p>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-medium text-white mb-4">About</h2>
          <div className="text-sm text-slate-400 space-y-2">
            <p><strong className="text-white">VibeCast Studio</strong> v0.1.0</p>
            <p>Powered by Microsoft VibeVoice TTS models</p>
            <p>
              This application generates AI-synthesized audio content.
              All outputs are watermarked and include AI disclaimers.
            </p>
          </div>
        </div>

        {/* Safety Notice */}
        <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-6">
          <h2 className="text-lg font-medium text-yellow-500 mb-2">Safety Notice</h2>
          <p className="text-sm text-yellow-200/70">
            This tool is intended for creating legitimate audio content only.
            Do not use for voice impersonation, deepfakes, or disinformation.
            All generated content is watermarked for traceability.
          </p>
        </div>

        <div className="mt-6 flex justify-end">
          <Button onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-2" />
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  )
}
