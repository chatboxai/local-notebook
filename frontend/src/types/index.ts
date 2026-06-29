
export type ProjectColor = 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'cyan' | 'pink' | 'brown'


export interface Project {
  id: string
  user_id: string
  name: string
  description: string
  summary: string | null
  color: ProjectColor | null
  file_count: number
  created_at: string
  updated_at: string
}


export interface FileInfo {
  id: string
  project_id: string
  file_name: string
  file_type: string
  status: 'pending' | 'processing' | 'ready' | 'error' | 'failed'
  error_message?: string
  processing_current?: number | null
  processing_total?: number | null
  processing_message?: string | null
  storage_path: string
  created_at: string
  updated_at: string
  
  supports_raw_view?: boolean
  raw_url?: string
}


export interface Session {
  id: string
  project_id: string
  title: string
  message_count: number
  citation_counter: number
  created_at: string
  updated_at: string
  messages?: Message[]
}


export interface TextPart {
  type: 'text'
  content: string
}


export interface SegmentCitationRefPart {
  type: 'citation_ref'
  display_num: number
  file_name: string
  segment_id: string
  summary: string
}


export interface AudioCitationRefPart {
  type: 'citation_ref'
  citation_type: 'audio'
  display_num: number
  file_name: string
  segment_id: string
  summary: string
  time_start?: number
  time_end?: number
  time_range?: string
}


export interface ImageCitationRefPart {
  type: 'citation_ref'
  citation_type: 'image'
  display_num: number
  file_name: string
  file_id: string
  
  image_name?: string
  image_index?: number
  page?: number
}


export interface WebCitationRefPart {
  type: 'citation_ref'
  citation_type: 'web'
  display_num: number
  title: string
  url: string
  snippet: string
  source: string
  published_date: string
  favicon?: string
}

export type CitationRefPart = SegmentCitationRefPart | AudioCitationRefPart | ImageCitationRefPart | WebCitationRefPart

export interface ToolStatusPart {
  type: 'tool_status'
  display: string
  display_key?: string
  display_params?: Record<string, unknown>
  displayKey?: string
  displayParams?: Record<string, unknown>
}


export interface ReasoningPart {
  type: 'reasoning'
  content: string
}

export type ContentPart = TextPart | CitationRefPart | ToolStatusPart | ReasoningPart


export interface ToolExecuting {
  name: string
  display: string
  display_key?: string
  display_params?: Record<string, unknown>
  displayKey?: string
  displayParams?: Record<string, unknown>
  arguments?: Record<string, any>
}


export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'tool' | 'compact_divider'
  content?: string
  content_parts?: ContentPart[]
  reasoning_content?: string
  tool_executing?: ToolExecuting[]
  tool_calls?: any
  created_at: string
  agent_role?: 'default' | 'analysis'
  _error?: string
  has_partial?: boolean
  pending_id_sync?: boolean
}


export interface Citation {
  citation_id: number
  file_id: string
  file_name: string
  block_index: number
  content: string
}


export interface Block {
  block_id: string
  block_type: 'heading' | 'paragraph' | 'list' | 'quote'
  content: string
  page?: number
  extra?: {
    
    speaker?: number
    time_start?: number
    time_end?: number
    time_range?: string
    raw_text?: string
    media_type?: string
    
    is_table?: boolean
    table_html?: string
    table_caption?: string
    table_footnote?: string
    bbox?: number[]
    
    is_image?: boolean
    image_index?: number
    image_name?: string
  }
}


export interface SegmentMapping {
  segment_id: string
  block_ids: string[]
  summary: string
  time_start?: number
  time_end?: number
  time_range?: string
}


export interface FileContent {
  file_id: string
  file_name: string
  summary: string
  keywords: string[]
  blocks: Block[]
  segments: SegmentMapping[]
  audio_meta?: {
    duration_ms: number
    start_ms: number
    speaker_count: number
  }
}


export interface ImageInfo {
  id: string
  image_index: number
  description: string
  vlm_model: string | null
  created_at: string
}


export interface ImageFileInfo {
  file_id: string
  file_name: string
  file_type: string
  images: ImageInfo[]
}


export interface CitationMetadata {
  segment_id?: string
  file_name?: string
  file_id?: string
  summary?: string
  display_num: number
  type?: 'segment' | 'image' | 'pdf_image' | 'web'
  media_type?: 'audio'
  citation_type?: 'audio'
  time_start?: number
  time_end?: number
  time_range?: string
  
  image_name?: string
  image_index?: number
  page?: number
  
  title?: string
  url?: string
  snippet?: string
  source?: string
  published_date?: string
  favicon?: string
}


export interface FeatureAsset {
  id: string
  asset_type: 'image' | 'video' | 'audio'
  file_name: string | null
  mime_type: string | null
  width: number | null
  height: number | null
  duration: number | null
  url: string
  thumbnail_url: string | null
}


export interface FeatureTextPart {
  type: 'text'
  content: string
}

export interface FeatureCitationRefPart {
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
}

export type FeatureContentPart = FeatureTextPart | FeatureCitationRefPart


export interface FeatureTextBlock {
  block_type: 'heading' | 'paragraph' | 'list' | 'quote'
  level?: number
  content_parts: FeatureContentPart[]
  content?: string
  extra?: {
    is_table?: boolean
  }
}

export interface FeatureImageBlock {
  block_type: 'image'
  asset_id: string
  caption: string | null
  asset: FeatureAsset | null
}

export interface FeatureVideoBlock {
  block_type: 'video'
  asset_id: string
  caption: string | null
  asset: FeatureAsset | null
}

export interface FeatureImageGroupBlock {
  block_type: 'image_group'
  asset_ids: string[]
  caption: string | null
  assets: FeatureAsset[]
}

export type FeatureBlock = FeatureTextBlock | FeatureImageBlock | FeatureVideoBlock | FeatureImageGroupBlock


export interface Feature {
  id: string
  project_id: string
  feature_type: string
  title: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  error_message: string | null
  blocks: FeatureBlock[]
  citations: Record<string, CitationMetadata>
  next_citation_display_num?: number
  created_at: string | null
  updated_at: string | null
  started_at: string | null
  finished_at: string | null
}
