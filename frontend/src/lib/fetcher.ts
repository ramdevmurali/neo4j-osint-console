export type FetchOptions = RequestInit & { timeoutMs?: number };

export async function fetchWithTimeout(url: string, options: FetchOptions = {}) {
  const { timeoutMs, ...init } = options;
  if (!timeoutMs) {
    return fetch(url, init);
  }
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

export async function fetchJson<T = unknown>(url: string, options: FetchOptions = {}) {
  const response = await fetchWithTimeout(url, options);
  const text = await response.text();
  let data: T | unknown;
  try {
    data = JSON.parse(text) as T;
  } catch {
    data = text;
  }
  return { response, data };
}
