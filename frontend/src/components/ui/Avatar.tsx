import { initials } from "@/lib/format";

// Initials only: no external avatar service (offline demo, no external assets).
const SIZES = { sm: "h-8 w-8 text-xs", md: "h-11 w-11 text-sm", lg: "h-16 w-16 text-xl" } as const;

export function Avatar({ name, size = "md", inverted = false }: { name: string; size?: keyof typeof SIZES; inverted?: boolean }) {
  return (
    <span
      aria-hidden
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-black ${SIZES[size]} ${
        inverted ? "border-2 border-white/40 bg-white/15 text-white" : "border border-brand-line bg-brand-soft text-brand"
      }`}
    >
      {initials(name)}
    </span>
  );
}
