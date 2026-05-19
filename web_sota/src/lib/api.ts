const API_BASE = "";
const DEFAULT_TIMEOUT = 5000;

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
    });
    if (!res.ok) throw new ApiError(`HTTP ${res.status}`, res.status);
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}
