"use client";
import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { downloadFile } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import { useToast } from "./Toast";

export interface ExportButtonProps {
  /** API path, e.g. "/evidence/mentoring.xlsx". */
  href: string;
  /** Used only if the response has no Content-Disposition filename. */
  filename: string;
  label: string;
}

export function ExportButton({ href, filename, label }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  async function onClick() {
    setLoading(true);
    try {
      await downloadFile(href, filename);
    } catch (e) {
      const id = isApiError(e) && e.requestId ? ` (request ${e.requestId})` : "";
      toast.error(`Export failed. Try again.${id}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button type="button" onClick={onClick} disabled={loading} className="btn-primary" aria-busy={loading}>
      {loading ? <Loader2 aria-hidden size={16} className="animate-spin" /> : <Download aria-hidden size={16} />}
      {loading ? "Preparing…" : label}
    </button>
  );
}
