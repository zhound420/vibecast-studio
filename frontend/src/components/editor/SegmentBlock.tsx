import { useState } from 'react'
import { useEditorStore } from '@/store/editorStore'
import { Trash2, GripVertical } from 'lucide-react'
import clsx from 'clsx'
import type { Segment } from '@/types'

interface SegmentBlockProps {
  segment: Segment
  index: number
  projectId: string
  isSelected: boolean
  onSelect: () => void
}

const speakerColors = [
  'border-l-blue-500',
  'border-l-green-500',
  'border-l-yellow-500',
  'border-l-red-500',
]

export function SegmentBlock({ segment, index, projectId, isSelected, onSelect }: SegmentBlockProps) {
  const { updateSegment, deleteSegment } = useEditorStore()
  const [localText, setLocalText] = useState(segment.text)

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setLocalText(e.target.value)
  }

  const handleTextBlur = () => {
    if (localText !== segment.text) {
      updateSegment(projectId, segment.id, { text: localText })
    }
  }

  const handleSpeakerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const speakerId = parseInt(e.target.value)
    updateSegment(projectId, segment.id, {
      speaker_id: speakerId,
      speaker_name: `Speaker ${speakerId}`,
    })
  }

  const handleDelete = () => {
    if (confirm('Delete this segment?')) {
      deleteSegment(projectId, segment.id)
    }
  }

  const estimatedSeconds = Math.ceil((localText.split(' ').length || 0) / 2.5)

  return (
    <div
      className={clsx(
        'bg-slate-800 rounded-lg border-l-4 transition-all',
        speakerColors[(segment.speaker_id - 1) % 4],
        isSelected ? 'ring-2 ring-primary-500' : 'hover:bg-slate-750'
      )}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-700">
        <GripVertical className="w-4 h-4 text-slate-500 cursor-grab" />

        <span className="text-slate-500 text-sm font-mono">{index + 1}</span>

        <select
          value={segment.speaker_id}
          onChange={handleSpeakerChange}
          className="bg-slate-700 text-white text-sm px-2 py-1 rounded border-none focus:ring-1 focus:ring-primary-500"
          onClick={(e) => e.stopPropagation()}
        >
          <option value={1}>Speaker 1</option>
          <option value={2}>Speaker 2</option>
          <option value={3}>Speaker 3</option>
          <option value={4}>Speaker 4</option>
        </select>

        <div className="flex-1" />

        <span className="text-slate-500 text-xs">{estimatedSeconds}s</span>

        <button
          onClick={(e) => {
            e.stopPropagation()
            handleDelete()
          }}
          className="p-1 text-slate-500 hover:text-red-500 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-3">
        <textarea
          value={localText}
          onChange={handleTextChange}
          onBlur={handleTextBlur}
          placeholder="Enter dialogue..."
          className="w-full bg-transparent text-white resize-none focus:outline-none min-h-[60px]"
          rows={3}
          onClick={(e) => e.stopPropagation()}
        />
      </div>
    </div>
  )
}
