"use client";
// Route guard (architecture §9): no token or a role not allowed on this route → /login.
// UX only; the server enforces every access rule.
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { canAccess, type Role } from "@/lib/nav";
import { getSession } from "@/lib/session";

export interface AuthGuardProps {
  /** Roles allowed anywhere under this layout; the route table in lib/nav narrows it per screen. */
  allowedRoles: Role[];
  children: ReactNode;
}

export function AuthGuard({ allowedRoles, children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    if (!allowedRoles.includes(session.role) || !canAccess(session.role, pathname)) {
      router.replace("/login");
      return;
    }
    setAllowed(true);
  }, [allowedRoles, pathname, router]);

  if (!allowed) {
    return (
      <div role="status" aria-live="polite" className="flex min-h-screen items-center justify-center bg-canvas">
        <span className="text-sm font-bold text-gray-600">Loading…</span>
      </div>
    );
  }
  return <>{children}</>;
}
