"use client";
// SCR-13 Click-to-source (add-on A1, REQ-019, API-034): the exact rows behind a dashboard number.
// IQAC rows carry pseudonyms ("Student 01"); the server never sends names or ids to IQAC.
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { isApiError, type ApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type Records = components["schemas"]["MetricRecords"];
type Row = Record<string, unknown>;

const TITLE: Record<string, string> = {
  compliance: "Compliance: allotted students and their meetings",
  issues_raised: "Issues raised this term",
  issues_resolved: "Issues resolved this term",
  overdue_actions: "Overdue action items",
  achievements: "Verified achievements this academic year",
  needs_attention: "Students needing attention",
  pending_reviews: "Certificates waiting for review",
};
const HIDDEN = new Set(["student_id"]);
const PAGE = 20;

function cell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.map(String).join(", ").replace(/_/g, " ");
  return String(value).replace(/_/g, " ");
}

export default function MetricRecordsPage() {
  const { metric } = useParams<{ metric: string }>();
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | undefined>();
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);

  const load = useCallback(
    async (next: string | null) => {
      setError(undefined);
      if (next) setMore(true);
      else setLoading(true);
      try {
        const res = await api.get<Records>(`/dept/metrics/${metric}/records`, { params: { limit: PAGE, cursor: next ?? undefined } });
        setRows((prev) => (next ? [...prev, ...res.data.items] : res.data.items));
        setTotal(res.data.total);
        setCursor(res.data.next_cursor);
      } catch (e) {
        setError(isApiError(e) ? e : { status: 0, code: "INTERNAL", errors: [] });
      } finally {
        setLoading(false);
        setMore(false);
      }
    },
    [metric],
  );

  useEffect(() => {
    void load(null);
  }, [load]);

  const columns = rows.length > 0 ? Object.keys(rows[0]).filter((k) => !HIDDEN.has(k)) : [];

  return (
    <>
      <PageHeader title={TITLE[metric] ?? "Records"} subtitle={loading ? undefined : `${total} record${total === 1 ? "" : "s"}, matching the dashboard number`} backHref="/coordinator" backLabel="Dashboard" />
      {loading ? (
        <LoadingRegion label="Loading records">
          <Skeleton block />
        </LoadingRegion>
      ) : error ? (
        <ErrorState error={error} onRetry={() => void load(null)} homeHref="/coordinator" />
      ) : rows.length === 0 ? (
        <EmptyState message="No records behind this number." />
      ) : (
        <div className="space-y-3">
          <div className="card overflow-x-auto p-0">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="border-b border-gray-100 text-xs font-black uppercase tracking-wider text-gray-600">
                <tr>
                  {columns.map((c) => (
                    <th key={c} scope="col" className="px-4 py-3">
                      {c.replace(/_/g, " ")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-gray-50 last:border-0">
                    {columns.map((c) => (
                      <td key={c} className="px-4 py-2.5 text-gray-800">
                        {cell(r[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cursor ? (
            <button type="button" className="btn-secondary" disabled={more} onClick={() => void load(cursor)}>
              {more ? "Loading…" : "Load more"}
            </button>
          ) : null}
        </div>
      )}
    </>
  );
}
