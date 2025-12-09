import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useProjectStore } from '@/store/projectStore'
import { useEditorStore } from '@/store/editorStore'
import { ScriptEditor } from '@/components/editor/ScriptEditor'
import { GenerationPanel } from '@/components/generation/GenerationPanel'
import { ChevronLeft } from 'lucide-react'

export function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { currentProject, loadProject, isLoading } = useProjectStore()
  const { clearEditor } = useEditorStore()

  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
    }
    return () => {
      clearEditor()
    }
  }, [projectId, loadProject, clearEditor])

  if (isLoading || !currentProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-slate-700 px-6 py-4 bg-slate-800/50">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="text-slate-400 hover:text-white transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white">{currentProject.name}</h1>
            {currentProject.description && (
              <p className="text-sm text-slate-400">{currentProject.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Editor */}
        <div className="flex-1 overflow-hidden">
          <ScriptEditor projectId={projectId!} />
        </div>

        {/* Right Panel */}
        <div className="w-80 border-l border-slate-700 p-4 overflow-auto bg-slate-900/50">
          <GenerationPanel projectId={projectId!} />
        </div>
      </div>
    </div>
  )
}
