export type ErrorCode =
  | "internal_error"
  | "validation_error"
  | "bad_request"
  | "not_found"
  | "service_unavailable"

export interface ErrorDetail {
  field?: string
  message: string
}

export interface ErrorResponse {
  code: ErrorCode
  message: string
  details: ErrorDetail[]
  trace_id: string
}

export interface HealthResponse {
  status: "ok" | "ready" | "not_ready"
  reason?: string
}

export interface ApiResponse<T> {
  data: T
}

export type FormatType = "mp3" | "mp4"
export type Quality = "best" | "2160p" | "1440p" | "1080p" | "720p" | "480p" | "360p" | "240p" | "144p"
export type ThemeMode = "light" | "dark"

export interface AppSettings {
  download_path: string
  format_type: FormatType
  quality: Quality
  last_url: string
  download_subtitles: boolean
  subtitle_languages: string
  embed_thumbnail: boolean
  notifications_enabled: boolean
  max_concurrent_downloads: number
  theme: ThemeMode
}

export interface SettingsPatchRequest {
  download_path?: string
  format_type?: FormatType
  quality?: Quality
  last_url?: string
  download_subtitles?: boolean
  subtitle_languages?: string
  embed_thumbnail?: boolean
  notifications_enabled?: boolean
  max_concurrent_downloads?: number
  theme?: ThemeMode
}

export type QueueStatus = "pending" | "downloading" | "completed" | "failed" | "cancelled"

export interface QueueItem {
  id: string
  url: string
  status: QueueStatus
  format_type: FormatType
  quality: Quality
  progress: number
  download_path: string
  download_subtitles: boolean
  subtitle_languages: string
  embed_thumbnail: boolean
  title?: string | null
  created_at: string
}

export interface QueueCreateRequest {
  url: string
  format_type: FormatType
  quality: Quality
  download_path: string
  download_subtitles?: boolean
  subtitle_languages?: string
  embed_thumbnail?: boolean
}

export interface QueueStartRequest {
  retry_failed?: boolean
  retry_cancelled?: boolean
}

export interface QueueExecutionState {
  running: boolean
  active_item_ids: string[]
  pending_count: number
  max_concurrent: number
}

export type CurrentDownloadStatus = "idle" | "starting" | "downloading" | "completed" | "failed" | "cancelled"

export interface CurrentDownloadState {
  running: boolean
  status: CurrentDownloadStatus
  url: string
  title?: string | null
  thumbnail_url?: string | null
  progress: number
  downloaded_bytes: number
  total_bytes: number
  speed_bps: number
  eta_seconds: number
  error_message?: string | null
}

export interface CurrentDownloadStartRequest {
  url: string
  format_type: FormatType
  quality: Quality
  download_path: string
  download_subtitles?: boolean
  subtitle_languages?: string
  embed_thumbnail?: boolean
}
