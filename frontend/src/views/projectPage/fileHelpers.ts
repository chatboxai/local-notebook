import type { FileInfo } from '../../types'

export const IMAGE_TYPES = ['jpg', 'jpeg', 'png']
export const AUDIO_TYPES = ['wav', 'mp3', 'm4a']
export const IMAGE_GENERATION_FILE_TYPES = [...IMAGE_TYPES, 'webp']
export const VIDEO_GENERATION_FILE_TYPES = [...IMAGE_TYPES]

export const MAX_FILE_COUNT = 30

const FILE_SIZE_LIMITS = {
  document: 100 * 1024 * 1024,
  image: 20 * 1024 * 1024,
  audio: 200 * 1024 * 1024,
} as const

export function isImageFile(file: FileInfo): boolean {
  return IMAGE_TYPES.includes(file.file_type?.toLowerCase() || '')
}

export function isAudioFile(file: FileInfo): boolean {
  return AUDIO_TYPES.includes(file.file_type?.toLowerCase() || '')
}

function getFileSizeLimit(file: File): number {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''

  if (['txt', 'docx', 'pdf', 'epub'].includes(ext)) {
    return FILE_SIZE_LIMITS.document
  }
  if (IMAGE_TYPES.includes(ext)) {
    return FILE_SIZE_LIMITS.image
  }
  if (AUDIO_TYPES.includes(ext)) {
    return FILE_SIZE_LIMITS.audio
  }
  return FILE_SIZE_LIMITS.document
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

export function checkFileSize(file: File): { valid: boolean; error?: string } {
  const limit = getFileSizeLimit(file)

  if (file.size > limit) {
    return {
      valid: false,
      error: `"${file.name}" 超过大小限制（最大 ${formatFileSize(limit)}）`
    }
  }
  return { valid: true }
}

export function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    pending: '等待处理',
    processing: '处理中',
    ready: '就绪',
    error: '错误',
    failed: '解析失败'
  }
  return statusMap[status] || status
}
