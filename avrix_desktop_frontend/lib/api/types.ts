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
