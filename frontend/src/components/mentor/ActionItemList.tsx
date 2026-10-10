"use client";
// Action items on Mentee 360 (REQ-010, API-030). "To verify" = done by the mentee, waiting for the mentor.
// Transitions follow backend §6.6; the server decides, and a 409 refreshes the list.
import { useState } from "react";
import { StatusPill, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type ActionItem = components["schemas"]["ActionItem"];
type Status = ActionItem["status"];

export interface ActionItemListProps {
  items: ActionItem[];
  /** Mentor actions (Verify / Reopen / Drop). False for the HOD's read-only view. */
  canEdit: boolean;
  onChanged: () => void;
}

const ACTIONS: Record<Status, { to: Status; label: string }[]> = {
  done: [
    { to: "verified", label: "Verify" },
    { to: "open", label: "Reopen" },
    { to: "dropped", label: "Drop" },
  ],
  open: [{ to: "dropped", label: "Drop" }],
  verified: [],
  dropped: [],
};

export function ActionItemList({ items, canEdit, onChanged }: ActionItemListProps) {
  const toast = useToast();
  const [busy, setBusy] = useState<string | null>(null);

  async function move(item: ActionItem, to: Status) {
    setBusy(item.id);
    try {
      await api.patch(`/action-items/${item.id}`, { status: to });
      toast.success(to === "verified" ? "Action item verified" : to === "open" ? "Action item reopened" : "Action item dropped");
    } catch (e) {
      toast.error(isApiError(e) && e.code === "INVALID_TRANSITION" ? "This item changed. Refreshing." : "Couldn't update. Try again.");
    } finally {
      setBusy(null);
      onChanged();
    }
  }

  const groups: { title: string; list: ActionItem[] }[] = [
    { title: "To verify", list: items.filter((i) => i.status === "done") },
    { title: "Open", list: items.filter((i) => i.status === "open").sort((a, b) => a.due_date.localeCompare(b.due_date)) },
    { title: "Closed", list: items.filter((i) => i.status === "verified" || i.status === "dropped") },
  ];

  if (items.length === 0) return <p className="text-sm text-gray-600">No action items yet.</p>;

  return (
    <div className="space-y-4">
      {groups
        .filter((g) => g.list.length > 0)
        .map((g) => (
          <div key={g.title}>
            <h3 className="mb-2 text-xs font-black uppercase tracking-widest text-gray-600">
              {g.title} ({g.list.length})
            </h3>
            <ul className="space-y-2">
              {g.list.map((item) => (
                <li key={item.id} className={`rounded-2xl border p-3 ${item.overdue ? "border-red-200 bg-red-50" : "border-gray-200 bg-white"}`}>
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-gray-900">{item.text}</p>
                      <p className="text-xs text-gray-600">
                        Due {formatDate(item.due_date)} · Owner: {item.owner === "mentee" ? "Mentee" : "Mentor"}
                      </p>
                    </div>
                    <StatusPill status={item.overdue ? "overdue" : item.status} />
                  </div>
                  {canEdit && ACTIONS[item.status].length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {ACTIONS[item.status].map((a) => (
                        <button
                          key={a.to}
                          type="button"
                          disabled={busy === item.id}
                          onClick={() => void move(item, a.to)}
                          className={a.to === "verified" ? "btn-primary px-4 py-2 text-xs" : "btn-secondary px-4 py-2 text-xs"}
                        >
                          {a.label}
                          <span className="sr-only"> action item: {item.text}</span>
                        </button>
                      ))}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ))}
    </div>
  );
}
