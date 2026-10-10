"use client";
// Small data hook (ux-flows §8): { data, error, loading, reload }. No global store; the server is the source of truth.
import { useCallback, useEffect, useRef, useState } from "react";
import { fixtureRoutes } from "@/fixtures/p3";
import { api } from "@/lib/api";
import { isApiError, type ApiError } from "@/lib/problem";

/** Sample-data mode for building screens before their endpoint lands. Off unless set at build time. */
export const USE_FIXTURES = process.env.NEXT_PUBLIC_USE_FIXTURES === "1";

function matchFixture(path: string): unknown {
  const parts = path.split("?")[0].split("/").filter(Boolean);
  for (const [pattern, payload] of fixtureRoutes) {
    const p = pattern.split("/").filter(Boolean);
    if (p.length === parts.length && p.every((seg, i) => seg.startsWith("[") || seg === parts[i])) return payload;
  }
  return undefined;
}

export interface UseApiResult<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
  reload: () => Promise<void>;
  setData: (next: T | undefined) => void;
}

export interface UseApiOptions<T> {
  /** Explicit sample payload (used only in sample-data mode), for screens whose payload is not in the P3 registry. */
  fixture?: T;
}

/** Pass `null` as the path to skip the request (for example while a route param is not ready). */
export function useApi<T>(path: string | null, options: UseApiOptions<T> = {}): UseApiResult<T> {
  const sample = USE_FIXTURES && path !== null ? ((options.fixture ?? matchFixture(path)) as T | undefined) : undefined;
  const [data, setData] = useState<T | undefined>(sample);
  const [error, setError] = useState<ApiError | undefined>();
  const [loading, setLoading] = useState<boolean>(path !== null && sample === undefined);
  const latest = useRef(0);

  const load = useCallback(async () => {
    if (sample !== undefined) {
      setData(sample);
      setLoading(false);
      return;
    }
    if (path === null) return;
    const ticket = ++latest.current;
    setLoading(true);
    setError(undefined);
    try {
      const res = await api.get<T>(path);
      if (ticket === latest.current) setData(res.data);
    } catch (e) {
      if (ticket === latest.current) setError(isApiError(e) ? e : { status: 0, code: "INTERNAL", errors: [] });
    } finally {
      if (ticket === latest.current) setLoading(false);
    }
  }, [path, sample]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, error, loading, reload: load, setData };
}
