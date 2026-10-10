import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";

// Faculty area (SCR-06..09, SCR-15). The HOD may open Mentee 360 (SCR-07); lib/nav narrows it per route.
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["faculty", "hod"]}>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
