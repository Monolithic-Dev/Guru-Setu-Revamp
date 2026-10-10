// Every route of every role (ux-flows §2 and §6), including add-on routes, so this file never changes later.

export type Role = "student" | "faculty" | "hod" | "iqac";

export type NavIcon =
  | "home"
  | "certificate"
  | "mentorship"
  | "bell"
  | "users"
  | "briefcase"
  | "clipboard"
  | "dashboard"
  | "allotment";

export interface NavItem {
  label: string;
  href: string;
  icon: NavIcon;
}

export const ROLE_LABEL: Record<Role, string> = {
  student: "Student",
  faculty: "Faculty",
  hod: "HOD",
  iqac: "IQAC",
};

export const HOME_BY_ROLE: Record<Role, string> = {
  student: "/student",
  faculty: "/faculty",
  hod: "/coordinator",
  iqac: "/coordinator",
};

/** Sidebar / bottom-nav items per role (ux-flows §2). */
export const NAV: Record<Role, NavItem[]> = {
  student: [
    { label: "Home", href: "/student", icon: "home" },
    { label: "Certificates", href: "/student/certificates", icon: "certificate" },
    { label: "My mentorship", href: "/student/mentorship", icon: "mentorship" },
    { label: "Notifications", href: "/notifications", icon: "bell" },
  ],
  faculty: [
    { label: "My mentees", href: "/faculty", icon: "users" },
    { label: "My openings", href: "/faculty/openings", icon: "briefcase" },
    { label: "Reviews", href: "/reviews", icon: "clipboard" },
    { label: "Notifications", href: "/notifications", icon: "bell" },
  ],
  hod: [
    { label: "Dashboard", href: "/coordinator", icon: "dashboard" },
    { label: "Allotment", href: "/coordinator/allotment", icon: "allotment" },
    { label: "Reviews", href: "/reviews", icon: "clipboard" },
    { label: "Notifications", href: "/notifications", icon: "bell" },
  ],
  iqac: [
    { label: "Dashboard", href: "/coordinator", icon: "dashboard" },
    { label: "Notifications", href: "/notifications", icon: "bell" },
  ],
};

/**
 * Route table: which roles may open which screen (ux-flows §6). Patterns use [param] segments.
 * The guard uses this for UX only; the server enforces access.
 */
export const ROUTES: { pattern: string; screen: string; roles: Role[]; addon?: boolean }[] = [
  { pattern: "/login", screen: "SCR-01", roles: ["student", "faculty", "hod", "iqac"] },
  { pattern: "/student", screen: "SCR-02", roles: ["student"] },
  { pattern: "/student/openings/[id]", screen: "SCR-03", roles: ["student"] },
  { pattern: "/student/certificates", screen: "SCR-04", roles: ["student"] },
  { pattern: "/student/mentorship", screen: "SCR-05", roles: ["student"] },
  { pattern: "/faculty", screen: "SCR-06", roles: ["faculty"] },
  { pattern: "/faculty/mentees/[studentId]", screen: "SCR-07", roles: ["faculty", "hod"] },
  { pattern: "/faculty/sessions/new", screen: "SCR-08", roles: ["faculty"] },
  { pattern: "/faculty/openings/[id]", screen: "SCR-09", roles: ["faculty"] },
  { pattern: "/reviews", screen: "SCR-10", roles: ["faculty", "hod"] },
  { pattern: "/coordinator", screen: "SCR-11", roles: ["hod", "iqac"] },
  { pattern: "/coordinator/allotment", screen: "SCR-12", roles: ["hod"] },
  { pattern: "/coordinator/metrics/[metric]", screen: "SCR-13", roles: ["hod", "iqac"], addon: true },
  { pattern: "/notifications", screen: "SCR-14", roles: ["student", "faculty", "hod", "iqac"] },
  { pattern: "/faculty/openings", screen: "SCR-15", roles: ["faculty"] },
  { pattern: "/faculty/openings/new", screen: "SCR-15", roles: ["faculty"], addon: true },
  { pattern: "/faculty-profile/[id]", screen: "SCR-16", roles: ["student"], addon: true },
  { pattern: "/dev/components", screen: "DEV", roles: ["student", "faculty", "hod", "iqac"] },
];

function matches(pattern: string, path: string): boolean {
  const p = pattern.split("/").filter(Boolean);
  const a = path.split("?")[0].split("/").filter(Boolean);
  if (p.length !== a.length) return false;
  return p.every((seg, i) => (seg.startsWith("[") && seg.endsWith("]")) || seg === a[i]);
}

/** Most specific route that matches a pathname (static segments beat [params]). */
export function routeFor(path: string) {
  const hits = ROUTES.filter((r) => matches(r.pattern, path));
  return hits.sort((x, y) => (x.pattern.match(/\[/g)?.length ?? 0) - (y.pattern.match(/\[/g)?.length ?? 0))[0];
}

export function canAccess(role: Role, path: string): boolean {
  const r = routeFor(path);
  return !!r && r.roles.includes(role);
}
