import { useGenerationStore } from '@/store/generationStore'
import { useEditorStore } from '@/store/editorStore'
import { Button } from '@/components/common/Button'
import { ProgressBar } from '@/components/common/ProgressBar'
import { Play, Square, Download, AlertCircle, CheckCircle } from 'lucide-react'

interface GenerationPanelProps {
  projectId: string
}

export function GenerationPanel({ projectId }: GenerationPanelProps) {
  const { segments } = useEditorStore()
  const {
    status,
    progress,
    currentChunk,
    totalChunks,
    error,
    outputPath,
    startGeneration,
    cancelGeneration,
    reset,
  } = useGenerationStore()

  const isIdle = status === 'idle'
  const isRunning = ['queued', 'loading_model', 'generating', 'stitching'].includes(status)
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  const handleStart = () => {
    if (segments.length === 0) {
      alert('Add some content first')
      return
    }
    startGeneration(projectId)
  }

  const handleDownload = () => {
    if (outputPath) {
      window.open(`/api/v1/export/job/${projectId}/download`, '_blank')
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'queued':
        return 'Waiting in queue...'
      case 'loading_model':
        return 'Loading AI model...'
      case 'generating':
        return `Generating chunk ${currentChunk + 1} of ${totalChunks}...`
      case 'stitching':
        return 'Stitching audio segments...'
      case 'completed':
        return 'Generation complete!'
      case 'failed':
        return 'Generation failed'
      case 'cancelled':
        return 'Generation cancelled'
      default:
        return 'Ready to generate'
    }
  }

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-white">Generate Audio</h3>
        {(isCompleted || isFailed) && (
          <Button variant="ghost" size="sm" onClick={reset}>
            Start Over
          </Button>
        )}
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 mb-4">
        {isRunning && (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
        )}
        {isCompleted && <CheckCircle className="w-4 h-4 text-green-500" />}
        {isFailed && <AlertCircle className="w-4 h-4 text-red-500" />}
        <span className="text-sm text-slate-300">{getStatusText()}</span>
      </div>

      {/* Progress */}
      {isRunning && (
        <div className="mb-4">
          <ProgressBar progress={progress} showLabel />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {isIdle && (
          <Button onClick={handleStart} disabled={segments.length === 0}>
            <Play className="w-4 h-4 mr-2" />
            Generate Audio
          </Button>
        )}

        {isRunning && (
          <Button variant="danger" onClick={cancelGeneration}>
            <Square className="w-4 h-4 mr-2" />
            Cancel
          </Button>
        )}

        {isCompleted && outputPath && (
          <Button onClick={handleDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download Audio
          </Button>
        )}
      </div>

      {/* Info */}
      <div className="mt-4 text-xs text-slate-500">
        <p>Estimated generation time depends on content length.</p>
        <p>~90 minutes of audio can take 10-20 minutes to generate.</p>
      </div>
    </div>
  )
}
