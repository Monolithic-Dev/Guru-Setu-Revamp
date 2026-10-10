"use client";
// Upload button with client-side checks (FLOW-02 step 1). The native file input stays the focusable control.
import { useId, useRef, useState } from "react";
import { Loader2, Upload } from "lucide-react";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";
import { ACCEPT, checkFile } from "./reasons";

type Certificate = components["schemas"]["Certificate"];

export interface CertificateUploaderProps {
  onUploaded: (certificate: Certificate) => void;
}

const SERVER_COPY: Record<number, string> = {
  413: "File is larger than 10 MB.",
  415: "Upload a JPG, PNG or PDF.",
  422: "PDF must have at most 5 pages.",
  429: "Too many uploads. Try again later.",
};

export function CertificateUploader({ onUploaded }: CertificateUploaderProps) {
  const inputId = useId();
  const errorId = useId();
  const input = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<"idle" | "uploading">("idle");
  const [error, setError] = useState<string | null>(null);

  async function onFile(file: File | undefined) {
    if (!file) return;
    setError(null);
    const problem = checkFile(file);
    if (problem) {
      setError(problem);
      if (input.current) input.current.value = "";
      return;
    }
    setState("uploading");
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<Certificate>("/certificates", form);
      onUploaded(data);
    } catch (e) {
      if (isApiError(e)) {
        setError(e.detail && e.status === 422 ? e.detail : SERVER_COPY[e.status] ?? "Something went wrong. Try again.");
      } else {
        setError("Something went wrong. Try again.");
      }
    } finally {
      setState("idle");
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div>
      <label
        htmlFor={inputId}
        className={`btn-primary cursor-pointer focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-brand ${
          state === "uploading" ? "pointer-events-none opacity-60" : ""
        }`}
      >
        {state === "uploading" ? <Loader2 aria-hidden size={18} className="animate-spin" /> : <Upload aria-hidden size={18} />}
        {state === "uploading" ? "Uploading…" : "Upload certificate"}
        <input
          ref={input}
          id={inputId}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          disabled={state === "uploading"}
          aria-describedby={error ? errorId : undefined}
          onChange={(e) => void onFile(e.target.files?.[0])}
        />
      </label>
      <p className="mt-2 text-xs font-medium text-gray-600">JPG, PNG or PDF, up to 10 MB.</p>
      {error ? (
        <p id={errorId} role="alert" className="mt-2 text-sm font-bold text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
