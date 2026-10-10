// The only HTTP client (ux-flows §8). Pages never import axios or call fetch directly.
import axios, { AxiosError } from "axios";
import { toApiError } from "./problem";
import { clearSession, getToken } from "./session";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { Accept: "application/json, application/problem+json" },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (err: AxiosError) => {
    const apiError = await toApiError(err);
    // A 401 on login is a wrong password, not an expired session (FLOW-01).
    const isLogin = err.config?.url?.includes("/auth/login");
    if (apiError.status === 401 && !isLogin && typeof window !== "undefined") {
      clearSession();
      if (!window.location.pathname.startsWith("/login")) window.location.assign("/login?expired=1");
    }
    return Promise.reject(apiError);
  },
);

/** Download a binary response (XLSX exports) with the filename from Content-Disposition (ux-flows §8). */
export async function downloadFile(path: string, fallbackName: string): Promise<void> {
  const res = await api.get<Blob>(path, { responseType: "blob" });
  const disposition = String(res.headers["content-disposition"] ?? "");
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
  const name = match ? decodeURIComponent(match[1]) : fallbackName;
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** Fetch a protected file (API-011) as an object URL for <img> / <iframe sandbox> previews (SEC-19). */
export async function fetchObjectUrl(path: string): Promise<{ url: string; type: string }> {
  const res = await api.get<Blob>(path, { responseType: "blob" });
  return { url: URL.createObjectURL(res.data), type: res.data.type };
}
