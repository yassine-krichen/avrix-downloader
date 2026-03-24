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
}
