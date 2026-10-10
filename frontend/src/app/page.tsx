"use client";
// "/" sends a signed-in user to their role home, everyone else to /login (FLOW-01).
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { HOME_BY_ROLE } from "@/lib/nav";
import { getSession } from "@/lib/session";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const session = getSession();
    router.replace(session ? HOME_BY_ROLE[session.role] : "/login");
  }, [router]);
  return (
    <main role="status" aria-live="polite" className="flex min-h-screen items-center justify-center bg-canvas">
      <span className="text-sm font-bold text-gray-600">Loading…</span>
    </main>
  );
}
