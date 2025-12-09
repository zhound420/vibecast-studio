import { apiClient } from './client'
import type { Script, Segment } from '@/types'

export const scriptsApi = {
  get: async (projectId: string) => {
    const response = await apiClient.get<Script>(`/scripts/${projectId}`)
    return response.data
  },

  update: async (projectId: string, data: { raw_content?: string; speakers?: Record<string, string> }) => {
    const response = await apiClient.put<Script>(`/scripts/${projectId}`, data)
    return response.data
  },

  getSegments: async (projectId: string) => {
    const response = await apiClient.get<Segment[]>(`/scripts/${projectId}/segments`)
    return response.data
  },

  createSegment: async (projectId: string, data: {
    text: string
    speaker_id: number
    speaker_name?: string
    voice_id?: string
    direction?: string
    order?: number
  }) => {
    const response = await apiClient.post<Segment>(`/scripts/${projectId}/segments`, data)
    return response.data
  },

  updateSegment: async (projectId: string, segmentId: string, data: Partial<{
    text: string
    speaker_id: number
    speaker_name: string
    voice_id: string
    direction: string
    order: number
  }>) => {
    const response = await apiClient.put<Segment>(`/scripts/${projectId}/segments/${segmentId}`, data)
    return response.data
  },

  deleteSegment: async (projectId: string, segmentId: string) => {
    await apiClient.delete(`/scripts/${projectId}/segments/${segmentId}`)
  },

  parse: async (projectId: string, text: string, format: string = 'auto') => {
    const response = await apiClient.post<Segment[]>(`/scripts/${projectId}/parse`, { text, format })
    return response.data
  },

  enhance: async (projectId: string, data: {
    text: string
    style?: string
    target_speakers?: number
    speaker_names?: string[]
  }) => {
    const response = await apiClient.post<{ enhanced_text: string }>(`/scripts/${projectId}/enhance`, data)
    return response.data
  },
}
