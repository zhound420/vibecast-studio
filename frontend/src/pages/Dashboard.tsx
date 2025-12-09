import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '@/store/projectStore'
import { Button } from '@/components/common/Button'
import { Plus, Folder, Clock, MoreVertical, Trash2 } from 'lucide-react'

export function Dashboard() {
  const navigate = useNavigate()
  const { projects, isLoading, loadProjects, createProject, deleteProject } = useProjectStore()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  const handleCreate = async () => {
    if (!newName.trim()) return
    setIsCreating(true)
    try {
      const project = await createProject(newName.trim())
      setNewName('')
      setShowCreate(false)
      navigate(`/project/${project.id}`)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation()
    if (confirm('Delete this project?')) {
      await deleteProject(projectId)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Projects</h1>
            <p className="text-slate-400 mt-1">Create and manage your audio projects</p>
          </div>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-bold text-white mb-4">Create New Project</h2>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Project name"
                className="w-full bg-slate-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
              <div className="mt-4 flex justify-end gap-2">
                <Button variant="ghost" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} isLoading={isCreating}>
                  Create
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Projects Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16">
            <Folder className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h2 className="text-xl font-medium text-white mb-2">No projects yet</h2>
            <p className="text-slate-400 mb-4">Create your first project to get started</p>
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => navigate(`/project/${project.id}`)}
                className="bg-slate-800 rounded-xl p-4 cursor-pointer hover:bg-slate-750 transition-colors group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                      <Folder className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-medium text-white">{project.name}</h3>
                      <div className="flex items-center gap-1 text-xs text-slate-500 mt-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(project.updated_at)}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, project.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-500 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {project.description && (
                  <p className="text-sm text-slate-400 mt-3 line-clamp-2">{project.description}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
