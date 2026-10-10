import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";

// Faculty track record for students (SCR-16, stretch).
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["student"]}>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
