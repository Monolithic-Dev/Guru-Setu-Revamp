"use client";
// Toasts announce with role="status" (ux-flows §5). Mount <ToastProvider> once in the root layout.
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { CheckCircle2, Info, XCircle } from "lucide-react";

type ToastKind = "success" | "error" | "info";
interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastApi {
  show: (message: string, kind?: ToastKind) => void;
  success: (message: string) => void;
  error: (message: string) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const next = useRef(1);

  const show = useCallback((message: string, kind: ToastKind = "info") => {
    const id = next.current++;
    setItems((cur) => [...cur.slice(-2), { id, kind, message }]);
    window.setTimeout(() => setItems((cur) => cur.filter((t) => t.id !== id)), 4500);
  }, []);

  const api = useMemo<ToastApi>(
    () => ({ show, success: (m) => show(m, "success"), error: (m) => show(m, "error") }),
    [show],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        role="status"
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-20 z-[60] flex flex-col items-center gap-2 px-4 md:bottom-6"
      >
        {items.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex max-w-md items-center gap-2 rounded-2xl px-4 py-3 text-sm font-bold shadow-xl ${
              t.kind === "error" ? "bg-red-700 text-white" : t.kind === "success" ? "bg-gray-900 text-white" : "bg-brand text-white"
            }`}
          >
            {t.kind === "error" ? (
              <XCircle aria-hidden size={18} />
            ) : t.kind === "success" ? (
              <CheckCircle2 aria-hidden size={18} className="text-gold" />
            ) : (
              <Info aria-hidden size={18} />
            )}
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}
