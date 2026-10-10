"use client";
// SCR-14 Notifications (REQ-038, API-037/038) with reminders on top (add-on A3, API-039). Unread items are bold;
// opening one marks it read and follows its link. Bodies never carry note or issue text (SEC-15).
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import RemindersPanel from "@/components/mentor/RemindersPanel";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { features } from "@/lib/features";
import { formatDate, formatRelative } from "@/lib/format";
import { isApiError, type ApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type Notification = components["schemas"]["Notification"];
type Page = components["schemas"]["NotificationPage"];

export default function NotificationsPage() {
  const toast = useToast();
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | undefined>();
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);

  const load = useCallback(async (next: string | null) => {
    setError(undefined);
    if (next) setMore(true);
    else setLoading(true);
    try {
      const res = await api.get<Page>("/me/notifications", { params: { limit: 20, cursor: next ?? undefined } });
      setItems((prev) => (next ? [...prev, ...res.data.items] : res.data.items));
      setUnread(res.data.unread);
      setCursor(res.data.next_cursor);
    } catch (e) {
      setError(isApiError(e) ? e : { status: 0, code: "INTERNAL", errors: [] });
    } finally {
      setLoading(false);
      setMore(false);
    }
  }, []);

  useEffect(() => {
    void load(null);
  }, [load]);

  async function markRead(n: Notification) {
    if (n.read) return;
    try {
      await api.post(`/me/notifications/${n.id}/read`);
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      setUnread((u) => Math.max(0, u - 1));
    } catch {
      toast.error("Couldn't mark as read. Try again.");
    }
  }

  return (
    <>
      <PageHeader title="Notifications" subtitle={loading ? undefined : unread > 0 ? `${unread} unread` : "You're all caught up"} />
      <div className="space-y-6">
        {features.reminders ? <RemindersPanel /> : null}
        {loading ? (
          <LoadingRegion label="Loading notifications">
            <div className="space-y-2">
              <Skeleton block />
              <Skeleton block />
            </div>
          </LoadingRegion>
        ) : error ? (
          <ErrorState error={error} onRetry={() => void load(null)} />
        ) : items.length === 0 ? (
          <EmptyState icon={<Bell size={36} />} message="No notifications yet." />
        ) : (
          <>
            <ul className="space-y-2">
              {items.map((n) => (
                <li key={n.id} className={`card flex flex-wrap items-center justify-between gap-3 p-4 ${n.read ? "" : "border-brand-line bg-brand-tint"}`}>
                  <div className="min-w-0">
                    <Link href={n.link} onClick={() => void markRead(n)} className={`text-sm text-gray-900 hover:underline ${n.read ? "font-medium" : "font-black"}`}>
                      {n.title}
                    </Link>
                    {n.body ? <p className="text-sm text-gray-700">{n.body}</p> : null}
                    <p className="text-xs text-gray-600" title={formatDate(n.created_at)}>
                      {formatRelative(n.created_at)}
                    </p>
                  </div>
                  {n.read ? null : (
                    <button type="button" className="btn-ghost" onClick={() => void markRead(n)}>
                      Mark read
                    </button>
                  )}
                </li>
              ))}
            </ul>
            {cursor ? (
              <button type="button" className="btn-secondary" disabled={more} onClick={() => void load(cursor)}>
                {more ? "Loading…" : "Load more"}
              </button>
            ) : null}
          </>
        )}
      </div>
    </>
  );
}
