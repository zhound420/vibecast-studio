import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { GenerationStatus } from '@/types'
import { generationApi } from '@/api/generation'

interface GenerationState {
  // State
  currentJobId: string | null
  status: GenerationStatus | 'idle'
  progress: number
  currentChunk: number
  totalChunks: number
  chunkProgress: number
  estimatedTimeRemaining: number | null
  outputPath: string | null
  error: string | null

  // Actions
  startGeneration: (projectId: string) => Promise<void>
  cancelGeneration: () => Promise<void>
  updateProgress: (progress: {
    status: GenerationStatus
    progress: number
    current_chunk: number
    total_chunks: number
    chunk_progress: number
    estimated_time_remaining?: number | null
    error_message?: string | null
  }) => void
  setCompleted: (outputPath: string) => void
  setError: (error: string) => void
  reset: () => void
}

export const useGenerationStore = create<GenerationState>()(
  devtools(
    (set, get) => ({
      currentJobId: null,
      status: 'idle',
      progress: 0,
      currentChunk: 0,
      totalChunks: 0,
      chunkProgress: 0,
      estimatedTimeRemaining: null,
      outputPath: null,
      error: null,

      startGeneration: async (projectId: string) => {
        set({
          status: 'queued',
          progress: 0,
          currentChunk: 0,
          totalChunks: 0,
          chunkProgress: 0,
          error: null,
          outputPath: null,
        })

        try {
          const job = await generationApi.start(projectId)
          set({ currentJobId: job.id })
        } catch (error) {
          set({
            status: 'failed',
            error: error instanceof Error ? error.message : 'Failed to start generation',
          })
        }
      },

      cancelGeneration: async () => {
        const { currentJobId } = get()
        if (!currentJobId) return

        try {
          await generationApi.cancel(currentJobId)
          set({ status: 'cancelled' })
        } catch (error) {
          set({ error: 'Failed to cancel generation' })
        }
      },

      updateProgress: (progress) => {
        set({
          status: progress.status,
          progress: progress.progress,
          currentChunk: progress.current_chunk,
          totalChunks: progress.total_chunks,
          chunkProgress: progress.chunk_progress,
          estimatedTimeRemaining: progress.estimated_time_remaining ?? null,
          error: progress.error_message ?? null,
        })
      },

      setCompleted: (outputPath) => {
        set({
          status: 'completed',
          progress: 100,
          outputPath,
        })
      },

      setError: (error) => {
        set({
          status: 'failed',
          error,
        })
      },

      reset: () => {
        set({
          currentJobId: null,
          status: 'idle',
          progress: 0,
          currentChunk: 0,
          totalChunks: 0,
          chunkProgress: 0,
          estimatedTimeRemaining: null,
          outputPath: null,
          error: null,
        })
      },
    }),
    { name: 'generation-store' }
  )
)
