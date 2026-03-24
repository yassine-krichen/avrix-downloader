import type { ErrorResponse, HealthResponse } from "@/lib/api/types"

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

export async function pingBackend(): Promise<HealthResponse> {
  const response = await fetch(`${resolveBaseUrl()}/health/live`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    throw await parseError(response)
  }

  return (await response.json()) as HealthResponse
}
