import { apiClient } from './client'
import type { Project, ProjectCreate, PaginatedResponse } from '@/types'

export const projectsApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const response = await apiClient.get<PaginatedResponse<Project>>('/projects', { params })
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<Project>(`/projects/${id}`)
    return response.data
  },

  create: async (data: ProjectCreate) => {
    const response = await apiClient.post<Project>('/projects', data)
    return response.data
  },

  update: async (id: string, data: Partial<ProjectCreate>) => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/projects/${id}`)
  },
}
