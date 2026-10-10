// Client session in localStorage (ADR-09). UX only: the server enforces every access rule.
import type { Role } from "./nav";

const KEYS = { token: "token", role: "role", userId: "user_id" } as const;
const ROLES: Role[] = ["student", "faculty", "hod", "iqac"];

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export interface Session {
  token: string;
  role: Role;
  userId: string;
}

export function getSession(): Session | null {
  const s = storage();
  const token = s?.getItem(KEYS.token);
  const role = s?.getItem(KEYS.role) as Role | null;
  const userId = s?.getItem(KEYS.userId);
  if (!token || !role || !userId || !ROLES.includes(role)) return null;
  return { token, role, userId };
}

export function getToken(): string | null {
  return storage()?.getItem(KEYS.token) ?? null;
}

export function saveSession(session: Session): void {
  const s = storage();
  s?.setItem(KEYS.token, session.token);
  s?.setItem(KEYS.role, session.role);
  s?.setItem(KEYS.userId, session.userId);
}

export function clearSession(): void {
  const s = storage();
  Object.values(KEYS).forEach((k) => s?.removeItem(k));
}
