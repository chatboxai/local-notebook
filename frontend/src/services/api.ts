import axios from 'axios'
import type { Project, FileInfo, Session, ToolExecuting, FileContent, Feature, FeatureBlock, ImageFileInfo } from '../types'
import { getToken, clearTokens } from './auth'
import { getModelOutputLanguage, t } from '../i18n'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})


api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})


let lastToastTime = 0
const TOAST_DEBOUNCE = 3000

function showGlobalToast(message: string) {
  const now = Date.now()
  if (now - lastToastTime < TOAST_DEBOUNCE) return
  lastToastTime = now


  window.dispatchEvent(new CustomEvent('global-toast', {
    detail: { message, type: 'warning' }
  }))
}


function is429Error(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false
  const err = error as { response?: { status?: number }; status?: number }
  return err.response?.status === 429 || err.status === 429
}


let isRedirectingToLogin = false


api.interceptors.response.use(
  (response) => response,
  async (error) => {

    if (is429Error(error)) {
      showGlobalToast(t('ui.tooManyRequestsTryAgainLater'))
      return Promise.reject(error)
    }

    if (error.response?.status === 401) {

      const url = error.config?.url || ''
      if (url.includes('/auth/login')) {
        return Promise.reject(error)
      }


      if (isRedirectingToLogin) {
        return new Promise(() => {})
      }

      isRedirectingToLogin = true
      clearTokens()

      setTimeout(() => { isRedirectingToLogin = false }, 3000)
      window.location.href = '/login'
      return new Promise(() => {})
    }

    return Promise.reject(error)
  }
)


export async function login(username: string, password: string) {


  const form = new URLSearchParams({ username, password })
  const response = await axios.post(`${API_BASE}/api/auth/login`, form)
  return response.data
}

export async function getCurrentUser() {
  const response = await api.get('/api/auth/me')
  return response.data
}

export type AdminUserRole = 'user' | 'admin'

export interface AdminUser {
  user_id: string
  username: string
  role: AdminUserRole
  created_at: string
  updated_at: string
}

export interface AdminUserListResponse {
  users: AdminUser[]
  total: number
}

export async function getAdminUsers(): Promise<AdminUserListResponse> {
  const response = await api.get('/api/admin/users')
  return response.data
}

export async function createAdminUser(data: {
  username: string
  password: string
}): Promise<AdminUser> {
  const response = await api.post('/api/admin/users', data)
  return response.data
}

export async function resetAdminUserPassword(userId: string, newPassword: string): Promise<void> {
  await api.post(`/api/admin/users/${userId}/password`, { new_password: newPassword })
}

export interface AdminUsageRow {
  usage_date: string
  user_id: string
  username: string
  model: string
  call_count: number
  input_uncached_tokens: number
  input_cache_read_tokens: number
  input_cache_write_tokens: number
  output_tokens: number
  total_tokens: number
}

export interface AdminUsageTotals {
  call_count: number
  input_uncached_tokens: number
  input_cache_read_tokens: number
  input_cache_write_tokens: number
  output_tokens: number
  total_tokens: number
}

export interface AdminUsageResponse {
  rows: AdminUsageRow[]
  totals: AdminUsageTotals
}

export async function getAdminUsage(params?: {
  start_date?: string
  end_date?: string
  user_id?: string
}): Promise<AdminUsageResponse> {
  const response = await api.get('/api/admin/usage', { params })
  return response.data
}


export async function getProjects(): Promise<Project[]> {
  const response = await api.get('/api/projects')
  return response.data
}

export async function getProject(projectId: string): Promise<Project & { files: FileInfo[] }> {
  const response = await api.get(`/api/projects/${projectId}`)
  return response.data
}

export async function createProject(name: string, description: string = ''): Promise<Project> {
  const response = await api.post('/api/projects', { name, description })
  return response.data
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/api/projects/${projectId}`)
}

export async function updateProject(projectId: string, data: { name?: string; description?: string }): Promise<Project> {
  const response = await api.patch(`/api/projects/${projectId}`, data)
  return response.data
}


export async function getFiles(projectId: string): Promise<FileInfo[]> {
  const response = await api.get(`/api/projects/${projectId}/files`)
  return response.data
}


export type UploadProgressCallback = (progress: number) => void

export async function uploadFile(
  projectId: string,
  file: File,
  onProgress?: UploadProgressCallback,
  outputLanguage?: string
): Promise<FileInfo> {
  const formData = new FormData()
  formData.append('file', file)
  if (outputLanguage) {
    formData.append('output_language', outputLanguage)
  }

  const response = await api.post(`/api/projects/${projectId}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
    onUploadProgress: onProgress ? (progressEvent) => {
      if (progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    } : undefined
  })
  return response.data
}

export async function getFile(fileId: string): Promise<FileInfo> {
  const response = await api.get(`/api/files/${fileId}`)
  return response.data
}

export async function getFileContent(fileId: string): Promise<FileContent> {

  const response = await api.get(`/api/files/${fileId}/content`, { timeout: 60000 })
  return response.data
}


export interface PageInfoItem {
  page: number
  block_count: number
}

export interface FilePageInfo {
  file_id: string
  file_name: string
  file_type: string
  has_pages: boolean
  total_pages: number
  pages: PageInfoItem[]
  segments: Array<{
    segment_id: string
    block_ids: string[]
    summary: string
  }>

  blocks?: Array<{
    block_id: string
    page: number
    extra?: {
      is_image?: boolean
      image_index?: number
      image_name?: string
      bbox?: number[]
    }
  }>
}


export interface PageContentBlock {
  block_id: string
  block_type: 'heading' | 'paragraph' | 'list' | 'quote'
  content: string
  page: number
}

export interface FilePageContent {
  file_id: string
  file_name: string
  page: number
  end_page: number
  blocks: PageContentBlock[]
}


export interface BlockLocation {
  page: number
  block_index: number
  exists: boolean
}

export interface BlocksLocationResponse {
  file_id: string
  blocks: Record<string, BlockLocation>
}


export async function getFilePageInfo(fileId: string): Promise<FilePageInfo> {
  const response = await api.get(`/api/files/${fileId}/content/pages`)
  return response.data
}


export async function getFilePage(fileId: string, pageNum: number, range?: string): Promise<FilePageContent> {
  const url = range
    ? `/api/files/${fileId}/content/page/${pageNum}?range=${range}`
    : `/api/files/${fileId}/content/page/${pageNum}`
  const response = await api.get(url)
  return response.data
}


export async function getFilePageRange(fileId: string, startPage: number, endPage: number): Promise<FilePageContent> {
  const response = await api.get(`/api/files/${fileId}/content/page/${startPage}?range=${startPage}-${endPage}`)
  return response.data
}


export async function getBlocksLocation(fileId: string, blockIds: string[]): Promise<BlocksLocationResponse> {
  const response = await api.post(`/api/files/${fileId}/blocks/location`, { block_ids: blockIds })
  return response.data
}

export async function deleteFile(fileId: string): Promise<void> {
  await api.delete(`/api/files/${fileId}`)
}

export async function updateFile(fileId: string, data: { file_name: string }): Promise<FileInfo> {
  const response = await api.put(`/api/files/${fileId}`, data)
  return response.data
}

export async function getFilesStatusBatch(fileIds: string[]): Promise<{
  files: {
    id: string
    status: string
    error_message?: string
    processing_current?: number | null
    processing_total?: number | null
    processing_message?: string | null
  }[]
}> {
  const response = await api.post('/api/files/status/batch', { file_ids: fileIds })
  return response.data
}


export async function getImageInfo(fileId: string): Promise<ImageFileInfo> {
  const response = await api.get(`/api/files/${fileId}/image-info`)
  return response.data
}


export interface SessionsResponse {
  sessions: Session[]
  total: number
  limit: number
  offset: number
}


export interface SessionDetailResponse extends Session {
  total_messages: number
  raw_fetched?: number
  messages_limit: number
  messages_offset: number
}

export async function getSessions(
  projectId: string,
  limit: number = 50,
  offset: number = 0
): Promise<SessionsResponse> {
  const response = await api.get(`/api/projects/${projectId}/sessions`, {
    params: { limit, offset }
  })
  return response.data
}

export async function getSession(
  sessionId: string,
  limit: number = 50,
  offset: number = 0,
  brief: boolean = false
): Promise<SessionDetailResponse> {
  const params: any = { limit, offset }
  if (brief) {
    params.brief = 1
  }
  const response = await api.get(`/api/sessions/${sessionId}`, {
    params
  })
  return response.data
}

export interface CreateSessionResponse extends Session {
  reused: boolean
}

export async function createSession(projectId: string, title: string = t('ui.newChat')): Promise<CreateSessionResponse> {
  const response = await api.post(`/api/projects/${projectId}/sessions`, { title })
  return response.data
}

export async function updateSessionTitle(sessionId: string, title: string): Promise<Session> {
  const response = await api.put(`/api/sessions/${sessionId}`, { title })
  return response.data
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/api/sessions/${sessionId}`)
}


export interface SegmentCitationRef {
  type: 'segment'
  display_num: number
  file_name: string
  segment_id: string
  summary: string
}


export interface AudioCitationRef {
  type: 'audio'
  display_num: number
  file_name: string
  segment_id: string
  summary: string
  time_start?: number
  time_end?: number
  time_range?: string
}


export interface ImageCitationRef {
  type: 'image'
  display_num: number
  file_id: string
  file_name: string

  image_name?: string
  image_index?: number
  page?: number
}


export interface WebCitationRef {
  type: 'web'
  display_num: number
  title: string
  url: string
  snippet: string
  source: string
  published_date: string
  favicon?: string
}

export type CitationRef = SegmentCitationRef | AudioCitationRef | ImageCitationRef | WebCitationRef


export type AgentRole = 'default' | 'analysis'


export interface ChatStreamDoneData {
  agentRole?: AgentRole
  sessionUpdated?: {
    title: string
  }
}

export interface WorkflowStartedData {
  workflow_id: string
  status: string
  display_name?: string
}

export interface ChatStreamCallbacks {
  onContent: (content: string) => void
  onCitationRef?: (citation: CitationRef) => void
  onToolExecuting?: (tools: ToolExecuting[]) => void
  onWorkflowStarted?: (data: WorkflowStartedData) => void
  onCitations?: (citations: any[]) => void
  onReasoning?: (content: string) => void
  onReasoningCitationRef?: (citation: CitationRef) => void
  onCompacting?: () => void
  onCompactDone?: () => void
  onCompactFailed?: (message: string) => void
  onDone: (data: ChatStreamDoneData) => void
  onError: (error: string, hasPartial?: boolean) => void
  onMessageIds?: (userMessageId: string, assistantMessageId: string) => void
}

export function chatStream(
  sessionId: string,
  message: string,
  fileIds: string[] | undefined,
  callbacks: ChatStreamCallbacks,
  enableWebSearch: boolean = false,
  agentRole: AgentRole = 'default'
): () => void {
  const controller = new AbortController()
  const token = getToken()

  fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      file_ids: fileIds,
      enable_web_search: enableWebSearch,
      agent_role: agentRole,
      output_language: getModelOutputLanguage()
    }),
    signal: controller.signal
  })
    .then(async (response) => {
      if (response.status === 401) {
        clearTokens()
        window.location.href = '/login'
        return
      }
      if (response.status === 429) {
        showGlobalToast(t('ui.tooManyRequestsTryAgainLater'))
        callbacks.onError(t('ui.tooManyRequestsTryAgainLater'))
        return
      }
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              switch (data.type) {
                case 'text':
                  callbacks.onContent(data.content)
                  break
                case 'citation_ref':
                  if (data.citation_type === 'web') {

                    callbacks.onCitationRef?.({
                      type: 'web',
                      display_num: data.display_num,
                      title: data.title,
                      url: data.url,
                      snippet: data.snippet,
                      source: data.source || '',
                      published_date: data.published_date || '',
                      favicon: data.favicon || ''
                    })
                  } else if (data.citation_type === 'image') {

                    callbacks.onCitationRef?.({
                      type: 'image',
                      display_num: data.display_num,
                      file_id: data.file_id,
                      file_name: data.file_name,

                      image_name: data.image_name,
                      image_index: data.image_index,
                      page: data.page
                    })
                  } else if (data.citation_type === 'audio') {

                    callbacks.onCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  } else {

                    callbacks.onCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  }
                  break
                case 'tool_executing':
                  callbacks.onToolExecuting?.(data.tools || [])
                  break
                case 'workflow_started':
                  callbacks.onWorkflowStarted?.(data)
                  break
                case 'reasoning':
                  callbacks.onReasoning?.(data.content)
                  break
                case 'reasoning_citation_ref':
                  if (data.citation_type === 'web') {
                    callbacks.onReasoningCitationRef?.({
                      type: 'web',
                      display_num: data.display_num,
                      title: data.title,
                      url: data.url,
                      snippet: data.snippet,
                      source: data.source || '',
                      published_date: data.published_date || '',
                      favicon: data.favicon || ''
                    })
                  } else if (data.citation_type === 'image') {
                    callbacks.onReasoningCitationRef?.({
                      type: 'image',
                      display_num: data.display_num,
                      file_id: data.file_id,
                      file_name: data.file_name,
                      image_name: data.image_name,
                      image_index: data.image_index,
                      page: data.page
                    })
                  } else if (data.citation_type === 'audio') {
                    callbacks.onReasoningCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  } else {
                    callbacks.onReasoningCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  }
                  break
                case 'citations':
                  callbacks.onCitations?.(data.data || data.citations || [])
                  break
                case 'compacting':
                  callbacks.onCompacting?.()
                  break
                case 'compact_done':
                  callbacks.onCompactDone?.()
                  break
                case 'compact_failed':
                  callbacks.onCompactFailed?.(data.message || '')
                  break
                case 'done':
                  callbacks.onDone({
                    agentRole: data.agent_role,
                    sessionUpdated: data.session_updated
                  })
                  break
                case 'message_ids':
                  callbacks.onMessageIds?.(data.user_message_id, data.assistant_message_id)
                  break
                case 'error':
                  callbacks.onError(data.data || data.message, data.has_partial)
                  break
              }
            } catch {

            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        callbacks.onError(error.message)
      }
    })

  return () => controller.abort()
}


export function editMessageAndRegenerate(
  sessionId: string,
  messageId: string,
  content: string,
  fileIds: string[] | undefined,
  callbacks: ChatStreamCallbacks,
  enableWebSearch: boolean = false,
  agentRole: AgentRole = 'default'
): () => void {
  const controller = new AbortController()
  const token = getToken()

  console.log(`📡 [editMessageAndRegenerate] API 调用参数:`, {
    sessionId,
    messageId,
    contentLength: content?.length,
    fileIds,
    enableWebSearch,
    agentRole,
    url: `${API_BASE}/api/chat/${sessionId}/messages/${messageId}/edit`
  })

  fetch(`${API_BASE}/api/chat/${sessionId}/messages/${messageId}/edit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      content,
      file_ids: fileIds,
      enable_web_search: enableWebSearch,
      agent_role: agentRole,
      output_language: getModelOutputLanguage()
    }),
    signal: controller.signal
  })
    .then(async (response) => {
      if (response.status === 401) {
        clearTokens()
        window.location.href = '/login'
        return
      }
      if (response.status === 402) {

        const data = await response.json()
        callbacks.onError(data.error || t('ui.pointsInsufficientRecharge'))
        return
      }
      if (response.status === 429) {
        showGlobalToast(t('ui.tooManyRequestsTryAgainLater'))
        callbacks.onError(t('ui.tooManyRequestsTryAgainLater'))
        return
      }
      if (!response.ok) {

        try {
          const data = await response.json()
          callbacks.onError(data.error || `HTTP error! status: ${response.status}`)
        } catch {
          callbacks.onError(`HTTP error! status: ${response.status}`)
        }
        return
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              switch (data.type) {
                case 'text':
                  callbacks.onContent(data.content)
                  break
                case 'citation_ref':
                  if (data.citation_type === 'web') {
                    callbacks.onCitationRef?.({
                      type: 'web',
                      display_num: data.display_num,
                      title: data.title,
                      url: data.url,
                      snippet: data.snippet,
                      source: data.source || '',
                      published_date: data.published_date || '',
                      favicon: data.favicon || ''
                    })
                  } else if (data.citation_type === 'image') {
                    callbacks.onCitationRef?.({
                      type: 'image',
                      display_num: data.display_num,
                      file_id: data.file_id,
                      file_name: data.file_name,

                      image_name: data.image_name,
                      image_index: data.image_index,
                      page: data.page
                    })
                  } else if (data.citation_type === 'audio') {
                    callbacks.onCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  } else {
                    callbacks.onCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  }
                  break
                case 'tool_executing':
                  callbacks.onToolExecuting?.(data.tools || [])
                  break
                case 'workflow_started':
                  callbacks.onWorkflowStarted?.(data)
                  break
                case 'reasoning':
                  callbacks.onReasoning?.(data.content)
                  break
                case 'reasoning_citation_ref':
                  if (data.citation_type === 'web') {
                    callbacks.onReasoningCitationRef?.({
                      type: 'web',
                      display_num: data.display_num,
                      title: data.title,
                      url: data.url,
                      snippet: data.snippet,
                      source: data.source || '',
                      published_date: data.published_date || '',
                      favicon: data.favicon || ''
                    })
                  } else if (data.citation_type === 'image') {
                    callbacks.onReasoningCitationRef?.({
                      type: 'image',
                      display_num: data.display_num,
                      file_id: data.file_id,
                      file_name: data.file_name,
                      image_name: data.image_name,
                      image_index: data.image_index,
                      page: data.page
                    })
                  } else if (data.citation_type === 'audio') {
                    callbacks.onReasoningCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  } else {
                    callbacks.onReasoningCitationRef?.({
                      type: 'segment',
                      display_num: data.display_num,
                      file_name: data.file_name,
                      segment_id: data.segment_id,
                      summary: data.summary
                    })
                  }
                  break
                case 'citations':
                  callbacks.onCitations?.(data.data || data.citations || [])
                  break
                case 'done':
                  callbacks.onDone({
                    agentRole: data.agent_role,
                    sessionUpdated: data.session_updated
                  })
                  break
                case 'message_ids':
                  callbacks.onMessageIds?.(data.user_message_id, data.assistant_message_id)
                  break
                case 'error':
                  callbacks.onError(data.data || data.message, data.has_partial)
                  break
              }
            } catch {

            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        callbacks.onError(error.message)
      }
    })

  return () => controller.abort()
}


export interface FeatureListItem {
  id: string
  feature_type: string
  display_name?: string
  title: string | null
  prompt?: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}


export async function getProjectFeatures(_projectId: string): Promise<{ features: FeatureListItem[] }> {
  return { features: [] }
}


export async function getFeaturesStatusBatch(featureIds: string[]): Promise<{
  features: Record<string, {
    id: string
    status: string
    error_message: string | null
    display_name?: string
    prompt?: string | null
    title?: string | null
  }>
}> {
  const response = await api.post('/api/features/status/batch', { feature_ids: featureIds })
  return response.data
}


export async function getFeatureContentBatch(featureIds: string[]): Promise<{
  features: Record<string, Feature>
}> {
  const response = await api.post('/api/features/content/batch', { feature_ids: featureIds })
  return response.data
}

export interface FeatureCustomConfig {
  prompt?: string
  file_ids: string[]
  aspect_ratio?: string

  duration?: number
  resolution?: string
  bgm?: boolean
}

export async function generateFeature(
  projectId: string,
  featureType: string,
  customConfig: FeatureCustomConfig
): Promise<{ feature_id: string; status: string }> {
  const response = await api.post('/api/features/generate', {
    project_id: projectId,
    feature_type: featureType,
    custom_config: customConfig
  }, { timeout: 60000 })
  return response.data
}

export async function getFeature(featureId: string): Promise<Feature> {
  const response = await api.get(`/api/features/${featureId}`)
  return response.data
}

export async function getFeatureByType(projectId: string, featureType: string): Promise<{ feature: Feature | null }> {
  const response = await api.get(`/api/features/project/${projectId}/type/${featureType}`)
  return response.data
}


export async function getFeatureListByType(projectId: string, featureType: string): Promise<{
  features: Array<{ id: string; title: string; status: string; created_at: string }>
}> {
  const response = await api.get(`/api/features/project/${projectId}/type/${featureType}/list`)
  return response.data
}

export async function deleteFeature(featureId: string): Promise<void> {
  await api.delete(`/api/features/${featureId}`)
}

export async function updateFeature(featureId: string, data: { title: string }): Promise<{ id: string; title: string; updated_at: string }> {
  const response = await api.put(`/api/features/${featureId}`, data)
  return response.data
}

export async function exportFeatureToWord(featureId: string): Promise<Blob> {
  const response = await api.post(`/api/features/${featureId}/export`, {}, {
    responseType: 'blob',
    timeout: 120000
  })
  return response.data
}


export interface ImageInfo {
  file_id: string
  file_name: string
  file_type: string
  width: number
  height: number
  format: string
  file_size: number
  description: string
  tags: string[]
  scene_type: string
  style: string
  ocr_text: string
  analysis_status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  preview_url: string
}


export function getImagePreviewUrl(fileId: string): string {
  const token = getToken()
  const query = token ? `?token=${encodeURIComponent(token)}` : ''
  return `${API_BASE}/api/files/${fileId}/preview${query}`
}

export function getAudioPreviewUrl(fileId: string): string {
  const token = getToken()
  const query = token ? `?token=${encodeURIComponent(token)}` : ''
  return `${API_BASE}/api/files/${fileId}/preview${query}`
}

export function getEmbeddedImagePreviewUrl(fileId: string, imageIndex: number): string {
  const token = getToken()
  const query = token ? `?token=${encodeURIComponent(token)}` : ''
  return `${API_BASE}/api/files/${fileId}/images/${imageIndex}/preview${query}`
}


export function getAssetUrl(path: string): string {
  if (!path) return ''

  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }

  return `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`
}


const PDF_CACHE_MAX_SIZE = 5
const PDF_CACHE_TTL = 30 * 60 * 1000


interface PdfCacheItem {
  data: ArrayBuffer
  timestamp: number
  accessTime: number
}


const pdfCache = new Map<string, PdfCacheItem>()


function cleanExpiredPdfCache() {
  const now = Date.now()
  for (const [key, item] of pdfCache.entries()) {
    if (now - item.timestamp > PDF_CACHE_TTL) {
      pdfCache.delete(key)
    }
  }
}


function evictLruPdfCache() {
  if (pdfCache.size < PDF_CACHE_MAX_SIZE) return

  let oldestKey: string | null = null
  let oldestTime = Infinity

  for (const [key, item] of pdfCache.entries()) {
    if (item.accessTime < oldestTime) {
      oldestTime = item.accessTime
      oldestKey = key
    }
  }

  if (oldestKey) {
    pdfCache.delete(oldestKey)
  }
}


export async function getPdfRawData(fileId: string): Promise<ArrayBuffer> {

  cleanExpiredPdfCache()


  const cached = pdfCache.get(fileId)
  if (cached) {

    cached.accessTime = Date.now()

    return cached.data.slice(0)
  }


  const response = await api.get(`/api/files/${fileId}/raw`, {
    responseType: 'arraybuffer'
  })


  evictLruPdfCache()


  const now = Date.now()
  pdfCache.set(fileId, {
    data: (response.data as ArrayBuffer).slice(0),
    timestamp: now,
    accessTime: now
  })

  return response.data
}


export function clearPdfCache(fileId?: string) {
  if (fileId) {
    pdfCache.delete(fileId)
  } else {
    pdfCache.clear()
  }
}


export interface BlockBboxInfo {
  page: number
  bbox: [number, number, number, number] | null
}


export async function getBlocksBbox(
  fileId: string,
  blockIds?: string[]
): Promise<{ file_id: string; file_type: string; blocks: Record<string, BlockBboxInfo> }> {
  const response = await api.post(`/api/files/${fileId}/blocks/bbox`, {
    block_ids: blockIds
  })
  return response.data
}


export interface FoundBlock {
  block_id: string
  content: string
  page: number
  bbox: [number, number, number, number]
}

export interface FindBlockByPositionResponse {
  found: boolean
  block: FoundBlock | null
}

export async function findBlockByPosition(
  fileId: string,
  page: number,
  x: number,
  y: number
): Promise<FindBlockByPositionResponse> {
  const response = await api.post(`/api/files/${fileId}/blocks/find-by-position`, {
    page,
    x,
    y
  })
  return response.data
}


export interface WorkflowProgress {
  total: number
  completed: number
  failed: number
  cancelled?: number
  current_step: string | null
}


export interface WorkflowStep {
  step_index: number
  step_id?: string | null
  depends_on?: string[]
  step_name: string
  feature_id: string | null
  feature_type: string
  display_name: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  title: string | null
  error_message: string | null
}


export type WorkflowStatus = 'pending' | 'processing' | 'cancelling' | 'completed' | 'failed' | 'partial' | 'cancelled'


export interface CreateWorkflowResponse {
  workflow_id: string
  workflow_type: string
  display_name: string
  status: WorkflowStatus
  steps_count: number
  is_finalized?: boolean
}


export interface WorkflowStatusResponse {
  id: string
  status: WorkflowStatus
  progress: WorkflowProgress
}


export interface WorkflowDetail {
  id: string
  workflow_type: string
  display_name: string
  title?: string | null
  status: WorkflowStatus
  progress: WorkflowProgress
  steps: WorkflowStep[]
  created_at: string
  finished_at: string | null
  is_finalized?: boolean
}


export interface WorkflowListItem {
  id: string
  workflow_type: string
  display_name: string
  status: WorkflowStatus
  progress: WorkflowProgress
  created_at: string
  finished_at: string | null
  title?: string | null
  is_finalized?: boolean
}


export async function renameWorkflow(workflowId: string, title: string): Promise<WorkflowListItem> {
  const response = await api.put(`/api/workflows/${workflowId}/title`, { title })
  return response.data
}


export async function finalizeWorkflow(workflowId: string): Promise<{ success: boolean, is_finalized: boolean }> {
  const response = await api.put(`/api/workflows/${workflowId}/finalized`, { is_finalized: true })
  return response.data
}


export async function createWorkflow(
  projectId: string,
  title: string,
  customConfig?: {
    prompt?: string
    file_ids?: string[]
    preset_key?: string
    output_language?: string
  }
): Promise<CreateWorkflowResponse> {
  const response = await api.post('/api/workflows/generate', {
    project_id: projectId,
    title,
    custom_config: customConfig
  }, { timeout: 60000 })
  return response.data
}


export async function getWorkflowStatus(workflowId: string): Promise<WorkflowStatusResponse> {
  const response = await api.get(`/api/workflows/${workflowId}/status`)
  return response.data
}


export async function getWorkflowsStatusBatch(workflowIds: string[]): Promise<{
  workflows: Record<string, WorkflowStatusResponse>
}> {
  const response = await api.post('/api/workflows/status/batch', {
    workflow_ids: workflowIds
  })
  return response.data
}


export async function getWorkflowDetail(workflowId: string): Promise<WorkflowDetail> {
  const response = await api.get(`/api/workflows/${workflowId}`)
  return response.data
}


export async function getProjectWorkflows(projectId: string): Promise<{ workflows: WorkflowListItem[] }> {
  const response = await api.get(`/api/workflows/project/${projectId}`)
  return response.data
}


export async function cancelWorkflow(workflowId: string): Promise<WorkflowStatusResponse> {
  const response = await api.post(`/api/workflows/${workflowId}/cancel`)
  return response.data
}


export async function retryWorkflowStep(
  workflowId: string,
  stepIndex: number
): Promise<{ success: boolean; message: string }> {
  const response = await api.post(`/api/workflows/${workflowId}/steps/${stepIndex}/retry`)
  return response.data
}


export async function regenerateWorkflowStep(
  workflowId: string,
  stepIndex: number,
  customConfig?: Record<string, any>
): Promise<{ success: boolean; feature_id: string; step_name: string; previous_status: string }> {
  const body = customConfig ? { custom_config: customConfig } : {}
  const response = await api.post(`/api/workflows/${workflowId}/steps/${stepIndex}/regenerate`, body)
  return response.data
}


export async function getWorkflowStepConfig(
  workflowId: string,
  stepIndex: number
): Promise<{
  workflow_id: string
  step_index: number
  step_name: string
  feature_id: string | null
  feature_type: string
  custom_config?: Record<string, any>
}> {
  const response = await api.get(`/api/workflows/${workflowId}/steps/${stepIndex}/config`)
  return response.data
}


export async function deleteWorkflow(workflowId: string): Promise<void> {
  await api.delete(`/api/workflows/${workflowId}`)
}


export interface FeatureEditCitationRef {
  type: 'citation_ref'
  display_num: number
  citation_id: string
  file_name?: string
  segment_id?: string
  summary?: string
  citation_type?: 'audio' | 'image' | 'web'
  time_start?: number
  time_end?: number
  time_range?: string

  file_id?: string

  title?: string
  url?: string
  snippet?: string
  source?: string
  published_date?: string
}


export interface FeatureEditHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  content_parts?: Array<{ type: 'text'; content: string } | FeatureEditCitationRef>
  tool_executing?: Array<{
    name: string
    display: string
    display_key?: string
    display_params?: Record<string, unknown>
    displayKey?: string
    displayParams?: Record<string, unknown>
  }>
}


export interface EditPreviewContentPart {
  type: 'text' | 'citation_ref'
  content?: string
  display_num?: number
  citation_id?: string
  file_name?: string
  segment_id?: string
  summary?: string
}


export interface FeatureEditCallbacks {
  onStart?: () => void
  onText?: (text: string) => void
  onCitationRef?: (citation: FeatureEditCitationRef) => void
  onToolExecuting?: (tools: ToolExecuting[]) => void
  onEditPreview?: (data: {
    block_index: number
    old_content: string
    new_content: string
    old_content_parts: EditPreviewContentPart[]
    new_content_parts: EditPreviewContentPart[]
  }) => void
  onEditApplied?: (data: { block_index: number; new_content: string; block: FeatureBlock; success: boolean; error?: string }) => void
  onDone?: (data: {
    session_id: string
    history: FeatureEditHistoryMessage[]
    citations?: Record<string, any>
    next_citation_display_num?: number
  }) => void
  onError?: (error: string) => void
}


export async function featureEditChat(
  featureId: string,
  message: string,
  callbacks: FeatureEditCallbacks,
  sessionId?: string | null
): Promise<void> {
  const token = getToken()


  const requestBody: { message: string; session_id?: string } = { message }
  if (sessionId) {
    requestBody.session_id = sessionId
  }

  const response = await fetch(`${API_BASE}/api/features/${featureId}/edit/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(requestBody)
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No response body')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') {
          return
        }

        try {
          const event = JSON.parse(data)
          switch (event.type) {
            case 'start':
              callbacks.onStart?.()
              break
            case 'text':
              callbacks.onText?.(event.content)
              break
            case 'citation_ref':

              callbacks.onCitationRef?.(event as FeatureEditCitationRef)
              break
            case 'tool_executing':
              callbacks.onToolExecuting?.(event.tools || [])
              break
            case 'edit_preview':
              callbacks.onEditPreview?.(event)
              break
            case 'edit_applied':
              callbacks.onEditApplied?.(event)
              break
            case 'done':
              callbacks.onDone?.(event)
              break
            case 'error':
              callbacks.onError?.(event.message)
              break
          }
        } catch (e) {
          console.error('Parse SSE error:', e)
        }
      }
    }
  }
}


export interface WorkflowCitation {
  display_num: number
  file_name: string
  file_id?: string
  segment_id: string
  summary?: string
  start_page?: number
  content?: string
  type?: 'image' | 'pdf_image' | 'web' | 'segment'
  media_type?: 'audio'
  citation_type?: 'audio'
  time_start?: number
  time_end?: number
  time_range?: string
  image_name?: string
  image_index?: number
  page?: number
}


export interface WorkflowContentFeature {
  id: string
  project_id: string
  feature_type: string
  step_index: number
  step_id?: string | null
  depends_on?: string[]
  step_name: string
  title: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  error_message?: string
  blocks: FeatureBlock[]
  citations: Record<string, WorkflowCitation>
}


export interface WorkflowContentResponse {
  workflow_id: string
  citations: Record<string, WorkflowCitation>
  features: WorkflowContentFeature[]
}


export interface WorkflowContentStep {
  step_index: number
  step_name: string
  feature: {
    id: string
    feature_type: string
    title: string
    generation_report: string
  }
  blocks: FeatureBlock[]
}

export interface WorkflowContent {
  workflow: {
    id: string
    workflow_type: string
    title: string
    project_id: string
    status: string
    citations: Record<string, WorkflowCitation>
    next_citation_display_num: number
  }
  steps: WorkflowContentStep[]
}


export async function getWorkflowContent(workflowId: string): Promise<WorkflowContentResponse> {
  const response = await api.get(`/api/workflows/${workflowId}/content`)
  return response.data
}


export async function getWorkflowEditContext(workflowId: string): Promise<WorkflowContent> {
  const response = await api.get(`/api/workflows/${workflowId}/edit/context`)
  return response.data
}


export interface WorkflowEditCallbacks {
  onStart?: () => void
  onText?: (text: string) => void
  onCitationRef?: (citation: FeatureEditCitationRef) => void
  onToolExecuting?: (tools: ToolExecuting[]) => void
  onEditPreview?: (data: {
    step_index: number
    step_name: string
    block_index: number
    old_content: string
    new_content: string
    old_content_parts: EditPreviewContentPart[]
    new_content_parts: EditPreviewContentPart[]
  }) => void
  onEditApplied?: (data: {
    step_index: number
    step_name: string
    block_index: number
    success: boolean
    new_content: string
    block: FeatureBlock
    error?: string
  }) => void
  onDone?: (data: {
    session_id: string
    history: FeatureEditHistoryMessage[]
    citations: Record<string, WorkflowCitation>
    next_citation_display_num: number
  }) => void
  onError?: (error: string) => void
}


export async function workflowEditChat(
  workflowId: string,
  message: string,
  callbacks: WorkflowEditCallbacks,
  sessionId?: string | null
): Promise<void> {
  const token = getToken()


  const requestBody: { message: string; session_id?: string } = { message }
  if (sessionId) {
    requestBody.session_id = sessionId
  }

  const response = await fetch(`${API_BASE}/api/workflows/${workflowId}/edit/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(requestBody)
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No response body')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') {
          return
        }

        try {
          const event = JSON.parse(data)
          switch (event.type) {
            case 'start':
              callbacks.onStart?.()
              break
            case 'text':
              callbacks.onText?.(event.content)
              break
            case 'citation_ref':
              callbacks.onCitationRef?.(event as FeatureEditCitationRef)
              break
            case 'tool_executing':
              callbacks.onToolExecuting?.(event.tools || [])
              break
            case 'edit_preview':

              callbacks.onEditPreview?.(event)
              break
            case 'edit_applied':

              callbacks.onEditApplied?.(event)
              break
            case 'done':

              callbacks.onDone?.(event)
              break
            case 'error':
              callbacks.onError?.(event.message)
              break
          }
        } catch (e) {
          console.error('Parse SSE error:', e)
        }
      }
    }
  }
}


export interface EditSession {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}


export interface EditSessionsResponse {
  sessions: EditSession[]
  total: number
}


export interface FeatureEditChange {
  block_index: number
  old_content: string
  new_content: string
  reason?: string
  success: boolean
  error_message?: string | null
  is_outdated?: boolean
}


export interface WorkflowEditChange extends FeatureEditChange {
  step_index: number
  step_name: string
}


export interface EditSessionMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  content_parts?: Array<{
    type: 'text' | 'citation_ref'
    content?: string
    display_num?: number
    citation_id?: string
    file_name?: string
    segment_id?: string
    summary?: string
  }>
  tool_calls?: Array<{
    id: string
    name: string
    arguments: Record<string, any>
  }>
  tool_executing?: Array<{
    name: string
    display: string
    display_key?: string
    display_params?: Record<string, unknown>
    displayKey?: string
    displayParams?: Record<string, unknown>
  }>
  tool_call_id?: string
  name?: string
  citations?: Record<string, any>
  changes?: FeatureEditChange[] | WorkflowEditChange[]
  created_at: string
}


export interface EditSessionDetailResponse {
  session: EditSession
  messages: EditSessionMessage[]
}


export async function getFeatureEditSessions(
  featureId: string,
  limit: number = 20,
  offset: number = 0
): Promise<EditSessionsResponse> {
  const response = await api.get(`/api/features/${featureId}/edit/sessions`, {
    params: { limit, offset }
  })
  return response.data
}


export async function getFeatureEditSessionDetail(
  featureId: string,
  sessionId: string
): Promise<EditSessionDetailResponse> {
  const response = await api.get(`/api/features/${featureId}/edit/sessions/${sessionId}`)
  return response.data
}


export async function getWorkflowEditSessions(
  workflowId: string,
  limit: number = 20,
  offset: number = 0
): Promise<EditSessionsResponse> {
  const response = await api.get(`/api/workflows/${workflowId}/edit/sessions`, {
    params: { limit, offset }
  })
  return response.data
}


export async function getWorkflowEditSessionDetail(
  workflowId: string,
  sessionId: string
): Promise<EditSessionDetailResponse> {
  const response = await api.get(`/api/workflows/${workflowId}/edit/sessions/${sessionId}`)
  return response.data
}


export type CitationStyle = 'inline' | 'endnote'


export async function exportWorkflowToWord(
  workflowId: string,
  options: {
    include_citations?: boolean
    citation_style?: CitationStyle
  } = {}
): Promise<{ blob: Blob; filename: string }> {
  const response = await api.post(
    `/api/workflows/${workflowId}/export`,
    {
      include_citations: options.include_citations ?? true,
      citation_style: options.citation_style ?? 'inline'
    },
    {
      responseType: 'blob',
      timeout: 120000
    }
  )


  const contentDisposition = response.headers['content-disposition']
  let filename = 'workflow.docx'
  if (contentDisposition) {

    const utf8Match = contentDisposition.match(/filename\*=UTF-8''(.+?)(?:;|$)/i)
    if (utf8Match && utf8Match[1]) {
      filename = decodeURIComponent(utf8Match[1])
    } else {

      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '')
        try {
          filename = decodeURIComponent(filename)
        } catch {
        }
      }
    }
  }

  return {
    blob: response.data,
    filename
  }
}

export async function exportChatMessagesToWord(
  sessionId: string,
  userMessageIds: string[] | null = null,
  includeCitations: boolean = true
): Promise<{ blob: Blob; filename: string }> {
  const response = await api.post(
    `/api/sessions/${sessionId}/export`,
    {
      user_message_ids: userMessageIds,
      include_citations: includeCitations
    },
    {
      responseType: 'blob',
      timeout: 120000
    }
  )

  const contentDisposition = response.headers['content-disposition']
  let filename = 'chat_export.docx'
  if (contentDisposition) {
    const utf8Match = contentDisposition.match(/filename\*=UTF-8''(.+?)(?:;|$)/i)
    if (utf8Match && utf8Match[1]) {
      filename = decodeURIComponent(utf8Match[1])
    } else {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '')
        try {
          filename = decodeURIComponent(filename)
        } catch {
        }
      }
    }
  }

  return {
    blob: response.data,
    filename
  }
}


export interface SettingsMap {
  bailian_api_key?: string
  llm_source?: string
  llm_bailian_model?: string
  llm_api_key?: string
  llm_base_url?: string
  llm_model?: string
  llm_api_format?: string
  easy_task_llm?: string
  easy_task_llm_verified?: string
  vlm_source?: string
  vlm_bailian_model?: string
  vlm_api_key?: string
  vlm_base_url?: string
  vlm_model?: string
  embedding_source?: string
  embedding_bailian_model?: string
  embedding_model?: string
  embedding_api_key?: string
  embedding_base_url?: string
  mineru_source?: string
  mineru_base_url?: string
  mineru_api_key?: string
  funasr_base_url?: string
  funasr_verified?: string
  bocha_api_key?: string
  [key: string]: string | undefined
}

export interface PreflightResult {
  ready: boolean
  llm_ready: boolean
  embedding_ready: boolean
  missing: string[]
}

export async function checkPreflight(): Promise<PreflightResult> {
  const response = await api.get('/api/settings/preflight')
  return response.data
}

export async function getSettings(): Promise<SettingsMap> {
  const response = await api.get('/api/settings')
  return response.data.settings
}

export async function updateSettings(settings: Partial<SettingsMap>, force = false): Promise<SettingsMap> {
  const response = await api.patch('/api/settings', { settings, force })
  return response.data.settings
}

export async function getSettingRaw(key: string): Promise<string | null> {
  const response = await api.get(`/api/settings/${key}`)
  return response.data.value
}
