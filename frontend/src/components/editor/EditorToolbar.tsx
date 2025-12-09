import { useState } from 'react'
import { useEditorStore } from '@/store/editorStore'
import { Button } from '@/components/common/Button'
import { FileText, Sparkles, Upload } from 'lucide-react'

interface EditorToolbarProps {
  projectId: string
}

export function EditorToolbar({ projectId }: EditorToolbarProps) {
  const { parseText, segments } = useEditorStore()
  const [showImport, setShowImport] = useState(false)
  const [importText, setImportText] = useState('')
  const [isImporting, setIsImporting] = useState(false)

  const handleImport = async () => {
    if (!importText.trim()) return
    setIsImporting(true)
    try {
      await parseText(projectId, importText)
      setImportText('')
      setShowImport(false)
    } finally {
      setIsImporting(false)
    }
  }

  const totalDuration = segments.reduce((acc, seg) => {
    const words = seg.text.split(' ').length
    return acc + Math.ceil(words / 2.5)
  }, 0)

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="border-b border-slate-700 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowImport(!showImport)}
          >
            <Upload className="w-4 h-4 mr-2" />
            Import Text
          </Button>

          <Button variant="ghost" size="sm" disabled>
            <Sparkles className="w-4 h-4 mr-2" />
            Enhance with Claude
          </Button>
        </div>

        <div className="flex items-center gap-4 text-sm text-slate-400">
          <span>{segments.length} segments</span>
          <span>~{formatDuration(totalDuration)} duration</span>
        </div>
      </div>

      {showImport && (
        <div className="mt-4 p-4 bg-slate-800 rounded-lg">
          <textarea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder="Paste your script here...&#10;&#10;Supported formats:&#10;[1] Speaker one dialogue&#10;[2] Speaker two dialogue&#10;&#10;Or:&#10;Speaker Name: Their dialogue"
            className="w-full bg-slate-700 text-white rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows={8}
          />
          <div className="mt-3 flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setShowImport(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleImport} isLoading={isImporting}>
              <FileText className="w-4 h-4 mr-2" />
              Parse & Import
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
