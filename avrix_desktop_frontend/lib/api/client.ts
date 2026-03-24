import type {
  AppSettings,
  CurrentDownloadStartRequest,
  CurrentDownloadState,
  ErrorResponse,
  HealthResponse,
  QueueCreateRequest,
  QueueExecutionState,
  QueueItem,
  QueueStartRequest,
  SettingsPatchRequest,
} from "@/lib/api/types"

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

  if (response.status === 204) {
    return undefined as T
  }

  const raw = await response.text()
  if (!raw.trim()) {
    return undefined as T
  }

  return JSON.parse(raw) as T
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

export async function getQueueItems(): Promise<QueueItem[]> {
  return request<QueueItem[]>("/api/v1/queue", { method: "GET" })
}

export async function addQueueItem(payload: QueueCreateRequest): Promise<QueueItem> {
  return request<QueueItem>("/api/v1/queue", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function removeQueueItem(itemId: string): Promise<void> {
  await request<void>(`/api/v1/queue/${itemId}`, { method: "DELETE" })
}

export async function moveQueueItem(itemId: string, direction: "up" | "down"): Promise<QueueItem[]> {
  return request<QueueItem[]>(`/api/v1/queue/${itemId}/move`, {
    method: "POST",
    body: JSON.stringify({ direction }),
  })
}

export async function clearFinishedQueue(): Promise<QueueItem[]> {
  return request<QueueItem[]>("/api/v1/queue/finished", { method: "DELETE" })
}

export async function clearAllQueue(): Promise<void> {
  await request<void>("/api/v1/queue", { method: "DELETE" })
}

export async function getQueueExecutionState(): Promise<QueueExecutionState> {
  return request<QueueExecutionState>("/api/v1/queue/execution", { method: "GET" })
}

export async function startQueueExecution(payload?: QueueStartRequest): Promise<QueueExecutionState> {
  return request<QueueExecutionState>("/api/v1/queue/start", {
    method: "POST",
    body: JSON.stringify({
      retry_failed: payload?.retry_failed ?? true,
      retry_cancelled: payload?.retry_cancelled ?? false,
    }),
  })
}

export async function stopQueueExecution(): Promise<QueueExecutionState> {
  return request<QueueExecutionState>("/api/v1/queue/stop", { method: "POST" })
}

export async function getCurrentDownloadState(): Promise<CurrentDownloadState> {
  return request<CurrentDownloadState>("/api/v1/download/current", { method: "GET" })
}

export async function startCurrentDownload(payload: CurrentDownloadStartRequest): Promise<CurrentDownloadState> {
  return request<CurrentDownloadState>("/api/v1/download/start", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function cancelCurrentDownload(): Promise<CurrentDownloadState> {
  return request<CurrentDownloadState>("/api/v1/download/cancel", { method: "POST" })
}
