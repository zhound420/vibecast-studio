// Project types
export interface Project {
  id: string
  name: string
  description: string | null
  voice_mapping: Record<number, string>
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  voice_mapping?: Record<number, string>
  settings?: Record<string, unknown>
}

// Script types
export interface Segment {
  id: string
  script_id: string
  text: string
  speaker_id: number
  speaker_name: string | null
  voice_id: string | null
  direction: string | null
  order: number
  estimated_duration: number | null
  created_at: string
  updated_at: string
}

export interface Script {
  id: string
  project_id: string
  raw_content: string | null
  speakers: Record<string, string>
  estimated_duration: number | null
  segments: Segment[]
  created_at: string
  updated_at: string
}

// Generation types
export type GenerationStatus =
  | 'queued'
  | 'loading_model'
  | 'generating'
  | 'stitching'
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface GenerationJob {
  id: string
  project_id: string
  status: GenerationStatus
  progress: number
  current_chunk: number
  total_chunks: number
  output_path: string | null
  error_message: string | null
  audio_duration: number | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface GenerationProgress {
  job_id: string
  status: GenerationStatus
  progress: number
  current_chunk: number
  total_chunks: number
  chunk_progress: number
  estimated_time_remaining: number | null
  error_message: string | null
}

// Voice types
export interface Voice {
  id: string
  name: string
  language: string
  gender: 'male' | 'female'
  description: string | null
  has_background_music: boolean
  preview_url: string | null
}

// Template types
export interface Template {
  id: string
  name: string
  description: string | null
  category: string
  voice_mapping: Record<number, string>
  speakers: Record<string, string>
  structure: Record<string, unknown> | null
  settings: Record<string, unknown>
  is_system: boolean
  created_at: string
  updated_at: string
}

// API response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
}
