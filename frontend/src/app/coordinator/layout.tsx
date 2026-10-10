import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";

// Coordinator area for HOD and IQAC (SCR-11..13, A-03).
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["hod", "iqac"]}>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
