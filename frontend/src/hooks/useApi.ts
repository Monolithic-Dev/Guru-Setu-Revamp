"use client";
// Small data hook (ux-flows §8): { data, error, loading, reload }. No global store; the server is the source of truth.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { isApiError, type ApiError } from "@/lib/problem";

export interface UseApiResult<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
  reload: () => Promise<void>;
  setData: (next: T | undefined) => void;
}

export interface UseApiOptions<T> {
  /**
   * Fixture payload used until the real endpoint lands (phases README rule 2). While set, no request is made.
   * Remove the fixture import at the gate; `grep -rn "fixtures/" src/app` must be empty for P0 routes.
   */
  fixture?: T;
}

/** Pass `null` as the path to skip the request (for example while a route param is not ready). */
export function useApi<T>(path: string | null, options: UseApiOptions<T> = {}): UseApiResult<T> {
  const { fixture } = options;
  const [data, setData] = useState<T | undefined>(fixture);
  const [error, setError] = useState<ApiError | undefined>();
  const [loading, setLoading] = useState<boolean>(path !== null && fixture === undefined);
  const latest = useRef(0);

  const load = useCallback(async () => {
    if (fixture !== undefined) {
      setData(fixture);
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
      if (ticket === latest.current) {
        setError(isApiError(e) ? e : { status: 0, code: "INTERNAL", errors: [] });
      }
    } finally {
      if (ticket === latest.current) setLoading(false);
    }
  }, [path, fixture]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, error, loading, reload: load, setData };
}
