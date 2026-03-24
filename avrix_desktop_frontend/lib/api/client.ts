import type { AppSettings, ErrorResponse, HealthResponse, SettingsPatchRequest } from "@/lib/api/types"

const DEFAULT_BASE_URL = "http://127.0.0.1:8000"

function resolveBaseUrl(): string {
  const fromWindow =
    typeof window !== "undefined"
      ? (window as Window & { __AVRIX_BACKEND_URL?: string }).__AVRIX_BACKEND_URL
      : undefined

  return fromWindow || process.env.NEXT_PUBLIC_AVRIX_BACKEND_URL || DEFAULT_BASE_URL
}

async function parseError(response: Response): Promise<ErrorResponse> {
  try {
    return (await response.json()) as ErrorResponse
  } catch {
    return {
      code: "internal_error",
      message: "Unable to parse backend error",
      details: [],
      trace_id: "unknown",
    }
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${resolveBaseUrl()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    throw await parseError(response)
  }

  return (await response.json()) as T
}

export async function pingBackend(): Promise<HealthResponse> {
  return request<HealthResponse>("/health/live", { method: "GET" })
}

export async function getSettings(): Promise<AppSettings> {
  return request<AppSettings>("/api/v1/settings", { method: "GET" })
}

export async function updateSettings(payload: SettingsPatchRequest): Promise<AppSettings> {
  return request<AppSettings>("/api/v1/settings", {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}
