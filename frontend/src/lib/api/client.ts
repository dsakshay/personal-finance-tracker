import { ApiError } from "./errors";
import { getAuthToken } from "../auth/token";

function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL;
  return (raw && raw.length > 0 ? raw : "http://localhost:8000").replace(/\/$/, "");
}

async function safeParseJson(res: Response): Promise<unknown | null> {
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return null;
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function normalizeErrorPayload(payload: unknown): { error: string; message: string; details?: unknown } {
  if (payload && typeof payload === "object") {
    const p = payload as Record<string, unknown>;
    // Preferred backend format: { error, message, details }
    if (typeof p.error === "string" && typeof p.message === "string") {
      return { error: p.error, message: p.message, details: p.details };
    }
    // FastAPI HTTPException default: { detail: "..." } or { detail: {...} }
    if (typeof p.detail === "string") {
      return { error: "http_error", message: p.detail, details: p };
    }
    // Some validation handlers may return nested details
    if (typeof p.message === "string") {
      return { error: (typeof p.error === "string" ? p.error : "api_error"), message: p.message, details: p.details ?? p };
    }
  }
  return { error: "api_error", message: "Request failed", details: payload };
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit & { skipAuth?: boolean }
): Promise<T> {
  const base = getApiBaseUrl();
  const url = `${base}${path.startsWith("/") ? "" : "/"}${path}`;

  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && init?.body) headers.set("Content-Type", "application/json");

  if (!init?.skipAuth) {
    const token = getAuthToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(url, {
    ...init,
    headers,
  });

  if (!res.ok) {
    const payload = (await safeParseJson(res)) ?? (await res.text().catch(() => null));
    const normalized = normalizeErrorPayload(payload);
    throw new ApiError({
      status: res.status,
      error: normalized.error,
      message: normalized.message,
      details: normalized.details as any,
      raw: payload,
    });
  }

  const json = await safeParseJson(res);
  return json as T;
}


