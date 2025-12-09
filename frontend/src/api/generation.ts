import { apiClient } from './client'
import type { GenerationJob } from '@/types'

export const generationApi = {
  start: async (projectId: string, options?: {
    voice_mapping?: Record<number, string>
    options?: Record<string, unknown>
  }) => {
    const response = await apiClient.post<GenerationJob>('/generation/start', {
      project_id: projectId,
      ...options,
    })
    return response.data
  },

  getStatus: async (jobId: string) => {
    const response = await apiClient.get<GenerationJob>(`/generation/${jobId}`)
    return response.data
  },

  cancel: async (jobId: string) => {
    const response = await apiClient.post<GenerationJob>(`/generation/${jobId}/cancel`)
    return response.data
  },

  getQueueStatus: async () => {
    const response = await apiClient.get<{
      position: number
      estimated_wait: number | null
      active_jobs: number
      queued_jobs: number
    }>('/generation/queue/status')
    return response.data
  },

  preview: async (text: string, voiceId: string) => {
    const response = await apiClient.post<{
      status: string
      message: string
    }>('/generation/preview', {
      text,
      voice_id: voiceId,
    })
    return response.data
  },
}
