"use client";
// Modal dialog with a focus trap; Escape closes; focus returns to the trigger (ux-flows §5).
// On phones it is a bottom sheet, like the earlier GuruSetu filters and detail panels.
import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  /** Wider panel for content such as the Why graph or a student profile. */
  size?: "sm" | "md" | "lg";
}

export function Dialog({ open, onClose, title, description, children, footer, size = "md" }: DialogProps) {
  const panel = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    const trigger = document.activeElement as HTMLElement | null;
    const node = panel.current;
    const first = node?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? node)?.focus();
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeRef.current();
        return;
      }
      if (e.key !== "Tab" || !node) return;
      const items = Array.from(node.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) return;
      const firstEl = items[0];
      const lastEl = items[items.length - 1];
      if (e.shiftKey && document.activeElement === firstEl) {
        e.preventDefault();
        lastEl.focus();
      } else if (!e.shiftKey && document.activeElement === lastEl) {
        e.preventDefault();
        firstEl.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      trigger?.focus?.();
    };
  }, [open]);

  if (!open) return null;
  const width = size === "sm" ? "sm:max-w-md" : size === "lg" ? "sm:max-w-3xl" : "sm:max-w-xl";

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <div className="absolute inset-0 bg-black/50" aria-hidden onClick={onClose} />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        tabIndex={-1}
        className={`relative flex max-h-[90vh] w-full flex-col rounded-t-[2rem] bg-white shadow-2xl outline-none sm:rounded-card ${width}`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-gray-100 p-5">
          <div>
            <h2 id={titleId} className="text-lg font-black text-gray-900">
              {title}
            </h2>
            {description ? (
              <p id={descId} className="mt-1 text-sm text-gray-600">
                {description}
              </p>
            ) : null}
          </div>
          <button type="button" onClick={onClose} className="rounded-full bg-gray-100 p-2 text-gray-700 hover:bg-gray-200" aria-label="Close">
            <X aria-hidden size={18} />
          </button>
        </div>
        <div className="overflow-y-auto p-5">{children}</div>
        {footer ? <div className="flex flex-wrap justify-end gap-2 border-t border-gray-100 p-4">{footer}</div> : null}
      </div>
    </div>
  );
}
