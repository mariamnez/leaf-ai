// apps/web/src/app/lib/api.ts

// Public base URL for the FastAPI backend.
// You can override it via .env.local -> NEXT_PUBLIC_API_URL="http://127.0.0.1:8010"
export const API_URL: string = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8010"
).replace(/\/+$/, ""); // strip trailing slash just in case

// Join base + path safely (ensure the path starts with "/")
function joinUrl(base: string, path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * Simple JSON GET helper
 * Usage: const data = await getJSON<MyType>("/api/sales/kpi")
 */
export async function getJSON<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = joinUrl(API_URL, path);

  const res = await fetch(url, {
    cache: "no-store",
    ...init,
  });

  if (!res.ok) {
    // Try to include backend error text for easier debugging
    const txt = await res.text().catch(() => "");
    throw new Error(`API ${url} -> ${res.status}${txt ? `: ${txt}` : ""}`);
  }
  return res.json() as Promise<T>;
}
