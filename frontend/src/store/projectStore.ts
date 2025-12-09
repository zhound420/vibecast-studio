import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { Project } from '@/types'
import { projectsApi } from '@/api/projects'

interface ProjectState {
  // State
  projects: Project[]
  currentProject: Project | null
  isLoading: boolean
  error: string | null

  // Actions
  loadProjects: () => Promise<void>
  loadProject: (id: string) => Promise<void>
  createProject: (name: string, description?: string) => Promise<Project>
  updateProject: (id: string, updates: Partial<Project>) => Promise<void>
  deleteProject: (id: string) => Promise<void>
  setCurrentProject: (project: Project | null) => void
  clearError: () => void
}

export const useProjectStore = create<ProjectState>()(
  devtools(
    (set, get) => ({
      projects: [],
      currentProject: null,
      isLoading: false,
      error: null,

      loadProjects: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await projectsApi.list()
          set({ projects: response.items, isLoading: false })
        } catch (error) {
          set({ error: 'Failed to load projects', isLoading: false })
        }
      },

      loadProject: async (id: string) => {
        set({ isLoading: true, error: null })
        try {
          const project = await projectsApi.get(id)
          set({ currentProject: project, isLoading: false })
        } catch (error) {
          set({ error: 'Failed to load project', isLoading: false })
        }
      },

      createProject: async (name: string, description?: string) => {
        set({ isLoading: true, error: null })
        try {
          const project = await projectsApi.create({ name, description })
          set((state) => ({
            projects: [project, ...state.projects],
            isLoading: false,
          }))
          return project
        } catch (error) {
          set({ error: 'Failed to create project', isLoading: false })
          throw error
        }
      },

      updateProject: async (id: string, updates: Partial<Project>) => {
        try {
          const updated = await projectsApi.update(id, updates)
          set((state) => ({
            projects: state.projects.map((p) => (p.id === id ? updated : p)),
            currentProject: state.currentProject?.id === id ? updated : state.currentProject,
          }))
        } catch (error) {
          set({ error: 'Failed to update project' })
        }
      },

      deleteProject: async (id: string) => {
        try {
          await projectsApi.delete(id)
          set((state) => ({
            projects: state.projects.filter((p) => p.id !== id),
            currentProject: state.currentProject?.id === id ? null : state.currentProject,
          }))
        } catch (error) {
          set({ error: 'Failed to delete project' })
        }
      },

      setCurrentProject: (project) => set({ currentProject: project }),
      clearError: () => set({ error: null }),
    }),
    { name: 'project-store' }
  )
)
