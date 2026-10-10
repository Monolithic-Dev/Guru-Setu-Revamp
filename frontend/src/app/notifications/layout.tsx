import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";

// Notifications for every role (SCR-14).
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["student", "faculty", "hod", "iqac"]}>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
