"use client";
// Unread count from API-037, polled every 30 s while the tab is visible (ux-flows §8).
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { api } from "@/lib/api";
import type { components } from "@/lib/types";

type NotificationPage = components["schemas"]["NotificationPage"];

export function NotificationBell() {
  const [unread, setUnread] = useState(0);

  const poll = useCallback(async () => {
    if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
    try {
      const res = await api.get<NotificationPage>("/me/notifications", { params: { limit: 1 } });
      setUnread(res.data.unread);
    } catch {
      // The bell is decorative when the API is down; the page shows its own error state.
    }
  }, []);

  useEffect(() => {
    void poll();
    const id = window.setInterval(poll, 30_000);
    const onVisible = () => void poll();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [poll]);

  return (
    <Link
      href="/notifications"
      aria-label={`Notifications, ${unread} unread`}
      className="relative inline-flex h-11 w-11 items-center justify-center rounded-full text-white hover:bg-white/10"
    >
      <Bell aria-hidden size={22} />
      {unread > 0 ? (
        <span
          aria-hidden
          className="absolute right-1 top-1 flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-brand bg-gold px-1 text-[10px] font-black text-gold-ink"
        >
          {unread > 9 ? "9+" : unread}
        </span>
      ) : null}
    </Link>
  );
}
