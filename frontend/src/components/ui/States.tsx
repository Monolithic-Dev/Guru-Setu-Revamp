"use client";
// Data-view states (ux-flows §4.1) with the exact copy.
import Link from "next/link";
import type { ReactNode } from "react";
import { Inbox, Lock, RefreshCw, SearchX, WifiOff } from "lucide-react";
import type { ApiError } from "@/lib/problem";

export interface EmptyStateProps {
  message: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export function EmptyState({ message, action, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-gray-300 bg-white px-6 py-10 text-center">
      <div className="mb-3 text-gray-400" aria-hidden>
        {icon ?? <Inbox size={36} />}
      </div>
      <p className="max-w-sm text-sm font-bold text-gray-700">{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export interface ErrorStateProps {
  error: ApiError;
  onRetry?: () => void;
  /** Where "home" is for the not-found link (defaults to "/"). */
  homeHref?: string;
  /** Inline variant for one failed section of a page (partial state). */
  inline?: boolean;
}

export function ErrorState({ error, onRetry, homeHref = "/", inline = false }: ErrorStateProps) {
  const box = inline
    ? "rounded-2xl border border-red-200 bg-red-50 p-4"
    : "flex flex-col items-center rounded-card border border-red-200 bg-white px-6 py-10 text-center";

  if (error.status === 404) {
    return (
      <div role="alert" className={box}>
        <SearchX aria-hidden className="mb-2 text-gray-500" size={32} />
        <p className="text-sm font-bold text-gray-800">This page isn&apos;t available.</p>
        <Link href={homeHref} className="mt-3 text-sm font-black text-brand underline underline-offset-2">
          Go home
        </Link>
      </div>
    );
  }
  if (error.status === 403) {
    return (
      <div role="alert" className={box}>
        <Lock aria-hidden className="mb-2 text-gray-500" size={32} />
        <p className="text-sm font-bold text-gray-800">You don&apos;t have access to this.</p>
      </div>
    );
  }
  return (
    <div role="alert" className={box}>
      {error.status === 0 ? (
        <WifiOff aria-hidden className="mb-2 text-red-700" size={28} />
      ) : null}
      <p className="text-sm font-bold text-red-800">
        {error.code === "DB_UNAVAILABLE"
          ? "Service is starting, try again in a moment."
          : "Something went wrong. Try again."}
      </p>
      {onRetry ? (
        <button type="button" onClick={onRetry} className="btn-secondary mt-3">
          <RefreshCw aria-hidden size={16} /> Retry
        </button>
      ) : null}
      {error.requestId ? (
        <p className="mt-2 text-[11px] text-gray-600">Request ID: {error.requestId}</p>
      ) : null}
    </div>
  );
}

export interface SkeletonProps {
  /** Number of text lines, or use `block` for a card-shaped placeholder. */
  lines?: number;
  block?: boolean;
  className?: string;
}

export function Skeleton({ lines = 3, block = false, className = "" }: SkeletonProps) {
  if (block) {
    return <div aria-hidden className={`h-28 animate-pulse rounded-card bg-gray-200 ${className}`} />;
  }
  return (
    <div aria-hidden className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className="h-3 animate-pulse rounded-full bg-gray-200" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </div>
  );
}

/** Screen-reader text while a view loads; pair with skeleton blocks. */
export function LoadingRegion({ children, label = "Loading" }: { children: ReactNode; label?: string }) {
  return (
    <div role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}
