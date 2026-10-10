// application/problem+json (backend §3.1) → one error shape for every screen.
import type { AxiosError } from "axios";
import type { components } from "./types";

export type ProblemCode = components["schemas"]["Problem"]["code"] | "NETWORK";

export interface FieldError {
  field: string;
  message: string;
}

export interface ApiError {
  status: number; // 0 for network errors
  code: ProblemCode;
  title?: string;
  detail?: string;
  errors: FieldError[];
  requestId?: string;
}

export function isApiError(e: unknown): e is ApiError {
  return typeof e === "object" && e !== null && "status" in e && "code" in e && "errors" in e;
}

async function readBody(data: unknown): Promise<unknown> {
  // Blob responses (XLSX downloads) carry their problem+json as a Blob.
  if (typeof Blob !== "undefined" && data instanceof Blob) {
    try {
      return JSON.parse(await data.text());
    } catch {
      return undefined;
    }
  }
  return data;
}

const FALLBACK_CODE: Record<number, ProblemCode> = {
  401: "UNAUTHENTICATED",
  403: "FORBIDDEN",
  404: "NOT_FOUND",
  413: "FILE_TOO_LARGE",
  415: "UNSUPPORTED_FILE_TYPE",
  422: "VALIDATION_FAILED",
  429: "RATE_LIMITED",
  503: "DB_UNAVAILABLE",
};

export async function toApiError(err: AxiosError): Promise<ApiError> {
  const res = err.response;
  if (!res) {
    return { status: 0, code: "NETWORK", detail: "You're offline or the server can't be reached.", errors: [] };
  }
  const body = (await readBody(res.data)) as Partial<components["schemas"]["Problem"]> | undefined;
  const header = res.headers?.["x-request-id"];
  return {
    status: res.status,
    code: (body?.code as ProblemCode) ?? FALLBACK_CODE[res.status] ?? "INTERNAL",
    title: body?.title,
    detail: body?.detail,
    errors: body?.errors ?? [],
    requestId: body?.request_id ?? (typeof header === "string" ? header : undefined),
  };
}
