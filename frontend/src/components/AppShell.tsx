"use client";
// App shell (ux-flows §2, §5): maroon header with name, role, bell and log out; sidebar ≥ 768 px
// (icons only until 1280 px), bottom nav below 768 px. Styled after the earlier GuruSetu side menu.
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import {
  Bell,
  Briefcase,
  Compass,
  ClipboardCheck,
  FileBadge,
  Handshake,
  Home,
  LayoutDashboard,
  LogOut,
  UserPlus,
  UserRound,
  Users,
  WifiOff,
  type LucideIcon,
} from "lucide-react";
import { useApi } from "@/hooks/useApi";
import { NAV, ROLE_LABEL, type NavIcon, type Role } from "@/lib/nav";
import { clearSession, getSession } from "@/lib/session";
import type { components } from "@/lib/types";
import { Avatar } from "./ui";
import { NotificationBell } from "./NotificationBell";

type Me = components["schemas"]["Me"];

const ICONS: Record<NavIcon, LucideIcon> = {
  home: Home,
  certificate: FileBadge,
  mentorship: Handshake,
  bell: Bell,
  users: Users,
  briefcase: Briefcase,
  clipboard: ClipboardCheck,
  dashboard: LayoutDashboard,
  allotment: UserPlus,
  profile: UserRound,
  guides: Compass,
};

function isActive(href: string, pathname: string): boolean {
  if (href === pathname) return true;
  // Home items ("/student", "/faculty", "/coordinator") are active only on themselves, except
  // detail pages that belong to them (Mentee 360, session form) which are reached from the home list.
  if (["/student", "/coordinator"].includes(href)) return false;
  if (href === "/faculty") return pathname.startsWith("/faculty/mentees") || pathname.startsWith("/faculty/sessions");
  return pathname.startsWith(`${href}/`);
}

function useOnline(): boolean {
  const [online, setOnline] = useState(true);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  return online;
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const online = useOnline();
  const [role, setRole] = useState<Role | null>(null);
  const { data: me } = useApi<Me>("/me");

  useEffect(() => setRole(getSession()?.role ?? null), []);

  function logout() {
    clearSession();
    router.replace("/login");
  }

  if (!role) return null;
  const items = NAV[role];
  const name = me?.name ?? "";

  return (
    <div className="min-h-screen bg-canvas md:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-[70] focus:rounded-xl focus:bg-white focus:px-4 focus:py-2 focus:font-bold focus:text-brand">
        Skip to content
      </a>

      {/* Sidebar (≥ 768 px): maroon profile block over a white menu, as in the earlier GuruSetu drawer. */}
      <aside className="sticky top-0 hidden h-screen shrink-0 flex-col border-r border-gray-200 bg-white md:flex md:w-20 xl:w-64">
        <div className="flex flex-col items-center gap-2 bg-brand px-3 pb-6 pt-8 text-center text-white xl:px-6">
          <Avatar name={name || ROLE_LABEL[role]} size="lg" inverted />
          <div className="hidden xl:block">
            <p className="text-lg font-black leading-tight">{name || " "}</p>
            <p className="text-xs font-medium text-white/80">
              {ROLE_LABEL[role]}
              {me?.dept_code ? ` · ${me.dept_code}` : ""}
            </p>
          </div>
        </div>
        <nav aria-label="Main" className="flex-1 space-y-1 p-3">
          {items.map((item) => {
            const Icon = ICONS[item.icon];
            const active = isActive(item.href, pathname);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                title={item.label}
                className={`flex min-h-[44px] items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold transition-colors md:justify-center xl:justify-start ${
                  active ? "bg-brand text-white shadow-md" : "text-gray-700 hover:bg-brand-tint hover:text-brand"
                }`}
              >
                <Icon aria-hidden size={20} strokeWidth={2.25} />
                <span className="md:sr-only xl:not-sr-only">{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-gray-100 p-3">
          <button
            type="button"
            onClick={logout}
            className="flex min-h-[44px] w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-black uppercase tracking-wider text-brand hover:bg-brand-tint md:justify-center xl:justify-start"
          >
            <LogOut aria-hidden size={20} />
            <span className="md:sr-only xl:not-sr-only">Log out</span>
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        {/* Header: the maroon band from the earlier GuruSetu screens. */}
        <header className="sticky top-0 z-30 bg-brand text-white shadow-md">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 md:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <span className="text-xl font-black tracking-tight">GuruSetu</span>
              <span className="hidden truncate border-l border-white/30 pl-3 text-sm font-bold text-white/90 sm:inline">
                {name}
                <span className="ml-2 rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest">
                  {ROLE_LABEL[role]}
                </span>
              </span>
            </div>
            <div className="flex items-center gap-1">
              <NotificationBell />
              <button
                type="button"
                onClick={logout}
                className="inline-flex h-11 items-center gap-2 rounded-full px-3 text-xs font-black uppercase tracking-widest text-white hover:bg-white/10 md:hidden"
              >
                <LogOut aria-hidden size={18} />
                Log out
              </button>
            </div>
          </div>
        </header>

        {!online ? (
          <div role="alert" className="flex items-center justify-center gap-2 bg-amber-100 px-4 py-2 text-sm font-bold text-amber-900">
            <WifiOff aria-hidden size={16} />
            You&apos;re offline. Changes will fail until you reconnect.
          </div>
        ) : null}

        <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-6 md:px-8 md:pb-10">
          {children}
        </main>
      </div>

      {/* Bottom nav (< 768 px). */}
      <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white md:hidden">
        <ul className="flex justify-around">
          {items.map((item) => {
            const Icon = ICONS[item.icon];
            const active = isActive(item.href, pathname);
            return (
              <li key={item.href} className="flex-1">
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex min-h-[56px] flex-col items-center justify-center gap-0.5 px-1 text-[10px] font-black uppercase tracking-wide ${
                    active ? "text-brand" : "text-gray-600"
                  }`}
                >
                  <Icon aria-hidden size={20} strokeWidth={active ? 2.75 : 2} />
                  <span className="truncate">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
