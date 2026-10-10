import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";

// Certificate review queue (SCR-10).
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["faculty", "hod"]}>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
