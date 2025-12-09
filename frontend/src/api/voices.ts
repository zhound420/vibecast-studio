import { apiClient } from './client'
import type { Voice } from '@/types'

export const voicesApi = {
  list: async () => {
    const response = await apiClient.get<{ voices: Voice[]; total: number }>('/voices')
    return response.data
  },

  listEmbedded: async () => {
    const response = await apiClient.get<Voice[]>('/voices/embedded')
    return response.data
  },

  get: async (voiceId: string) => {
    const response = await apiClient.get<Voice>(`/voices/${voiceId}`)
    return response.data
  },

  getPreviewUrl: (voiceId: string) => {
    return `/api/v1/voices/${voiceId}/preview`
  },
}
