import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { Segment } from '@/types'
import { scriptsApi } from '@/api/scripts'

interface EditorState {
  // State
  segments: Segment[]
  selectedSegmentId: string | null
  voiceMapping: Record<number, string>
  isDirty: boolean
  isLoading: boolean
  error: string | null

  // Actions
  loadSegments: (projectId: string) => Promise<void>
  setSegments: (segments: Segment[]) => void
  addSegment: (projectId: string, segment: Omit<Segment, 'id' | 'script_id' | 'order' | 'created_at' | 'updated_at'>) => Promise<void>
  updateSegment: (projectId: string, segmentId: string, updates: Partial<Segment>) => Promise<void>
  deleteSegment: (projectId: string, segmentId: string) => Promise<void>
  reorderSegments: (fromIndex: number, toIndex: number) => void
  selectSegment: (segmentId: string | null) => void
  setVoiceMapping: (mapping: Record<number, string>) => void
  updateVoiceForSpeaker: (speakerId: number, voiceId: string) => void
  parseText: (projectId: string, text: string) => Promise<void>
  clearEditor: () => void
}

export const useEditorStore = create<EditorState>()(
  devtools(
    (set, get) => ({
      segments: [],
      selectedSegmentId: null,
      voiceMapping: {
        1: 'en-Carter_man',
        2: 'en-Alice_woman',
        3: 'en-Frank_man',
        4: 'en-Maya_woman',
      },
      isDirty: false,
      isLoading: false,
      error: null,

      loadSegments: async (projectId: string) => {
        set({ isLoading: true, error: null })
        try {
          const segments = await scriptsApi.getSegments(projectId)
          set({ segments, isLoading: false, isDirty: false })
        } catch (error) {
          set({ error: 'Failed to load segments', isLoading: false })
        }
      },

      setSegments: (segments) => set({ segments, isDirty: true }),

      addSegment: async (projectId, segmentData) => {
        set({ isLoading: true })
        try {
          const segment = await scriptsApi.createSegment(projectId, {
            text: segmentData.text,
            speaker_id: segmentData.speaker_id,
            speaker_name: segmentData.speaker_name || undefined,
            voice_id: segmentData.voice_id || undefined,
            direction: segmentData.direction || undefined,
          })
          set((state) => ({
            segments: [...state.segments, segment],
            isLoading: false,
            isDirty: true,
          }))
        } catch (error) {
          set({ error: 'Failed to add segment', isLoading: false })
        }
      },

      updateSegment: async (projectId, segmentId, updates) => {
        try {
          const updated = await scriptsApi.updateSegment(projectId, segmentId, updates)
          set((state) => ({
            segments: state.segments.map((s) => (s.id === segmentId ? updated : s)),
            isDirty: true,
          }))
        } catch (error) {
          set({ error: 'Failed to update segment' })
        }
      },

      deleteSegment: async (projectId, segmentId) => {
        try {
          await scriptsApi.deleteSegment(projectId, segmentId)
          set((state) => ({
            segments: state.segments.filter((s) => s.id !== segmentId),
            selectedSegmentId: state.selectedSegmentId === segmentId ? null : state.selectedSegmentId,
            isDirty: true,
          }))
        } catch (error) {
          set({ error: 'Failed to delete segment' })
        }
      },

      reorderSegments: (fromIndex, toIndex) => {
        set((state) => {
          const newSegments = [...state.segments]
          const [removed] = newSegments.splice(fromIndex, 1)
          newSegments.splice(toIndex, 0, removed)
          // Update order values
          return {
            segments: newSegments.map((s, i) => ({ ...s, order: i })),
            isDirty: true,
          }
        })
      },

      selectSegment: (segmentId) => set({ selectedSegmentId: segmentId }),

      setVoiceMapping: (mapping) => set({ voiceMapping: mapping }),

      updateVoiceForSpeaker: (speakerId, voiceId) => {
        set((state) => ({
          voiceMapping: { ...state.voiceMapping, [speakerId]: voiceId },
          isDirty: true,
        }))
      },

      parseText: async (projectId, text) => {
        set({ isLoading: true, error: null })
        try {
          const segments = await scriptsApi.parse(projectId, text)
          set({ segments, isLoading: false, isDirty: true })
        } catch (error) {
          set({ error: 'Failed to parse text', isLoading: false })
        }
      },

      clearEditor: () => set({
        segments: [],
        selectedSegmentId: null,
        isDirty: false,
        error: null,
      }),
    }),
    { name: 'editor-store' }
  )
)
