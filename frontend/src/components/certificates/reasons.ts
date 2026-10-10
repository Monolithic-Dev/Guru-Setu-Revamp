// Certificate reason codes → student-facing text (ux-flows §4.2).
import type { components } from "@/lib/types";

export type ReasonCode = components["schemas"]["Certificate"]["reasons"][number];

const COPY: Record<string, string> = {
  name_mismatch: "The name on the certificate doesn't match your profile name.",
  unknown_issuer: "We don't recognise this issuer yet.",
  date_invalid: "The date looks wrong or is missing.",
  incomplete: "Some details couldn't be read.",
  not_a_certificate: "This doesn't look like a certificate.",
  injection_text: "This file needs a manual check.",
  tamper_signal: "This image may have been edited.",
  manual_entry: "Entered manually.",
  extraction_failed: "We couldn't read this file automatically.",
  interrupted: "We couldn't read this file automatically.",
};

const DUPLICATE = "This matches a certificate already on GuruSetu.";

export function reasonText(code: string): string {
  if (code.startsWith("duplicate_")) return DUPLICATE;
  return COPY[code] ?? code.replace(/_/g, " ");
}

/** Unique, readable reason lines (several duplicate_* codes collapse to one line). */
export function reasonLines(codes: readonly string[]): string[] {
  return Array.from(new Set(codes.map(reasonText)));
}

export const MAX_UPLOAD_MB = 10;
export const ACCEPT = ".jpg,.jpeg,.png,.pdf";
export const ACCEPT_TYPES = ["image/jpeg", "image/png", "application/pdf"];

/** Client-side check before upload (FLOW-02). Returns the error copy, or null when the file is fine. */
export function checkFile(file: File): string | null {
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return "File is larger than 10 MB.";
  const ext = file.name.toLowerCase().split(".").pop() ?? "";
  if (!["jpg", "jpeg", "png", "pdf"].includes(ext) && !ACCEPT_TYPES.includes(file.type)) return "Upload a JPG, PNG or PDF.";
  return null;
}

export const LEVELS: components["schemas"]["CertificateLevel"][] = [
  "international", "national", "state", "university", "college", "online", "other", "unknown",
];
export const TYPES: components["schemas"]["CertificateType"][] = [
  "hackathon", "course", "workshop", "competition", "internship", "paper", "sports", "cultural", "other",
];

export const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
