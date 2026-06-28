import type { FileContent } from '@/types'

export interface UploadingFile {
  name: string
  progress: number
  status: 'uploading' | 'success' | 'error'
  error?: string
}

export type SourceViewMode = 'raw' | 'parsed'

export interface AudioTranscriptGroup {
  key: string
  speaker: number | null
  speakerLabel: string
  blocks: FileContent['blocks']
}
