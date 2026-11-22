// Default to the deployed Vercel backend; VITE_API_BASE_URL still overrides (e.g. localhost dev).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://adaptive-ai-backend-nine.vercel.app';
const API_KEY = import.meta.env.VITE_API_KEY || '';
const REQUEST_TIMEOUT_MS = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 60000);

export class ApiError extends Error {
  status: number;
  code: string;
  retryable: boolean;

  constructor(message: string, status: number, code = 'API_ERROR', retryable = false) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryable = retryable;
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers,
    });

    const data = await res.json().catch(() => null);

    if (!res.ok) {
      if (res.status === 429) {
        throw new ApiError('Rate limit reached. Please wait a moment and try again.', 429, 'RATE_LIMITED', true);
      }
      const errMsg = data?.detail || data?.error?.message || `Request failed with status ${res.status}`;
      throw new ApiError(String(errMsg), res.status, `HTTP_${res.status}`, res.status >= 500);
    }

    return data as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('The request timed out. Please retry.', 408, 'TIMEOUT', true);
    }
    throw new ApiError('Cannot reach the Adaptive AI backend at ' + API_BASE_URL, 0, 'NETWORK_ERROR', true);
  } finally {
    window.clearTimeout(timeoutId);
  }
}
