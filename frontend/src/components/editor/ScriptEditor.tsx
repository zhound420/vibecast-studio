import { useEffect } from 'react'
import { useEditorStore } from '@/store/editorStore'
import { SegmentBlock } from './SegmentBlock'
import { EditorToolbar } from './EditorToolbar'
import { VoiceMapper } from './VoiceMapper'
import { Plus } from 'lucide-react'
import { Button } from '@/components/common/Button'

interface ScriptEditorProps {
  projectId: string
}

export function ScriptEditor({ projectId }: ScriptEditorProps) {
  const { segments, selectedSegmentId, selectSegment, loadSegments, addSegment, isLoading } = useEditorStore()

  useEffect(() => {
    loadSegments(projectId)
  }, [projectId, loadSegments])

  const handleAddSegment = async () => {
    await addSegment(projectId, {
      text: '',
      speaker_id: 1,
      speaker_name: 'Speaker 1',
      voice_id: null,
      direction: null,
      estimated_duration: null,
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <EditorToolbar projectId={projectId} />

      <div className="flex-1 overflow-auto p-4">
        {segments.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-slate-400 mb-4">No segments yet. Add content to get started.</p>
            <Button onClick={handleAddSegment}>
              <Plus className="w-4 h-4 mr-2" />
              Add Segment
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {segments.map((segment, index) => (
              <SegmentBlock
                key={segment.id}
                segment={segment}
                index={index}
                projectId={projectId}
                isSelected={segment.id === selectedSegmentId}
                onSelect={() => selectSegment(segment.id)}
              />
            ))}
            <div className="pt-4">
              <Button variant="ghost" onClick={handleAddSegment} className="w-full border border-dashed border-slate-600">
                <Plus className="w-4 h-4 mr-2" />
                Add Segment
              </Button>
            </div>
          </div>
        )}
      </div>

      <VoiceMapper />
    </div>
  )
}
