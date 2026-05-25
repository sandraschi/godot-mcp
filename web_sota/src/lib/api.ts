/** Empty in Vite dev (proxy); absolute URL in Tauri production build. */
export const API_BASE = import.meta.env.DEV ? "" : "http://127.0.0.1:10993";
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

export async function apiFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number },
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT, ...fetchOptions } = options ?? {};
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
    });
    if (!res.ok) throw new ApiError(`HTTP ${res.status}`, res.status);
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}
