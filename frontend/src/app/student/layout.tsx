import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";

// Student area (SCR-02..05).
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["student"]}>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
