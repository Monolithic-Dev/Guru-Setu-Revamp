"use client";
// SCR-04 Certificates: route stub on fixtures (T1.P3.5). Full flow lands in T2.P3.1 (FLOW-02).
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, StatusPill, TrustBadge } from "@/components/ui";
import type { components } from "@/lib/types";

type Certificate = components["schemas"]["Certificate"];

export default function CertificatesPage() {
  const { data, error, loading, reload } = useApi<Certificate[]>("/me/certificates", { fixture: fixtures.myCertificates });
  const profile = fixtures.studentProfile;

  return (
    <>
      <PageHeader title="Certificates" subtitle="Upload a certificate to turn a claimed skill into a Certified one." />
      <section aria-labelledby="mine" className="space-y-3">
        <h2 id="mine" className="section-title">
          My certificates
        </h2>
        {loading ? (
          <LoadingRegion>
            <Skeleton block />
          </LoadingRegion>
        ) : error ? (
          <ErrorState error={error} onRetry={reload} />
        ) : !data || data.length === 0 ? (
          <EmptyState message="No certificates yet. Upload one to turn claimed skills into Certified." />
        ) : (
          <ul className="space-y-3">
            {data.map((c) => (
              <li key={c.id} className="card flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-black text-gray-900">{c.title ?? "Untitled certificate"}</p>
                  <p className="text-sm text-gray-600">{c.issuer}</p>
                </div>
                <StatusPill status={c.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
      <section aria-labelledby="skills" className="mt-8 space-y-3">
        <h2 id="skills" className="section-title">
          My skills
        </h2>
        <div className="card flex flex-wrap gap-2">
          {profile.skills.map((s) => (
            <span key={s.concept} className="inline-flex items-center gap-1.5 text-sm font-bold text-gray-900">
              {s.concept} <TrustBadge level={s.trust_level} />
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
