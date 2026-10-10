"use client";
// SCR-04 Certificates (FLOW-02; REQ-001, 002, 003, 037): upload, live status, manual entry, my skills with trust.
import { useCallback, useEffect, useRef, useState } from "react";
import { FileBadge } from "lucide-react";
import { CertificateCard } from "@/components/certificates/CertificateCard";
import { CertificateUploader } from "@/components/certificates/CertificateUploader";
import { ManualCertificateForm } from "@/components/certificates/ManualCertificateForm";
import { EmptyState, ErrorState, LoadingRegion, PageHeader, Skeleton, TrustBadge, useToast } from "@/components/ui";
import { fixtures } from "@/fixtures/p3";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

type Certificate = components["schemas"]["Certificate"];
type StudentProfile = components["schemas"]["StudentProfile"];

const POLL_MS = 2000;
const POLL_LIMIT_MS = 30_000;

function certifiedToast(c: Certificate): string {
  const [first, ...rest] = c.skills;
  if (!first) return `'${c.title ?? "Certificate"}' is now Verified`;
  const name = first.charAt(0).toUpperCase() + first.slice(1);
  return rest.length === 0 ? `${name} is now Certified` : `${name} and ${rest.length} more skill${rest.length > 1 ? "s" : ""} are now Certified`;
}

export default function CertificatesPage() {
  const toast = useToast();
  const [userId, setUserId] = useState<string | null>(null);
  useEffect(() => setUserId(getSession()?.userId ?? null), []);

  const certs = useApi<Certificate[]>("/me/certificates", { fixture: fixtures.myCertificates });
  const profile = useApi<StudentProfile>(userId ? `/students/${userId}` : null, { fixture: fixtures.studentProfile });

  const [stillWorking, setStillWorking] = useState<Set<string>>(new Set());
  const [manual, setManual] = useState<Certificate | null>(null);
  const polling = useRef<Set<string>>(new Set());
  const listRef = useRef<Certificate[]>([]);
  listRef.current = certs.data ?? [];
  const setCerts = certs.setData;
  const reloadProfile = profile.reload;

  const upsert = useCallback(
    (c: Certificate) => {
      const cur = listRef.current;
      const next = cur.some((x) => x.id === c.id) ? cur.map((x) => (x.id === c.id ? c : x)) : [c, ...cur];
      listRef.current = next;
      setCerts(next);
    },
    [setCerts],
  );

  const poll = useCallback(
    async (id: string) => {
      if (polling.current.has(id)) return;
      polling.current.add(id);
      const started = Date.now();
      try {
        while (Date.now() - started < POLL_LIMIT_MS) {
          await new Promise((r) => setTimeout(r, POLL_MS));
          const { data } = await api.get<Certificate>(`/certificates/${id}`);
          if (data.status !== "processing") {
            upsert(data);
            if (data.status === "certified") {
              toast.success(certifiedToast(data));
              void reloadProfile();
            }
            return;
          }
        }
        setStillWorking((s) => new Set(s).add(id));
      } catch {
        // Polling is best effort; the notification arrives later (FM-11).
        setStillWorking((s) => new Set(s).add(id));
      } finally {
        polling.current.delete(id);
      }
    },
    [reloadProfile, toast, upsert],
  );

  // Resume polling for cards that were still processing when the page loaded.
  useEffect(() => {
    (certs.data ?? []).filter((c) => c.status === "processing" && !stillWorking.has(c.id)).forEach((c) => void poll(c.id));
  }, [certs.data, poll, stillWorking]);

  function onUploaded(c: Certificate) {
    upsert(c);
    if (c.status === "processing") void poll(c.id);
  }

  return (
    <>
      <PageHeader
        title="Certificates"
        subtitle="Upload a certificate to turn a claimed skill into a Certified one."
        actions={<CertificateUploader onUploaded={onUploaded} />}
      />

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_340px]">
        <section aria-labelledby="mine" className="space-y-3">
          <h2 id="mine" className="section-title">
            My certificates
          </h2>
          {certs.loading ? (
            <LoadingRegion label="Loading certificates">
              <div className="space-y-3">
                <Skeleton block />
                <Skeleton block />
              </div>
            </LoadingRegion>
          ) : certs.error ? (
            <ErrorState error={certs.error} onRetry={certs.reload} homeHref="/student" />
          ) : !certs.data || certs.data.length === 0 ? (
            <EmptyState
              icon={<FileBadge size={36} />}
              message="No certificates yet. Upload one to turn claimed skills into Certified."
              action={<CertificateUploader onUploaded={onUploaded} />}
            />
          ) : (
            <ul className="space-y-3">
              {certs.data.map((c) => (
                <li key={c.id}>
                  <CertificateCard certificate={c} stillWorking={stillWorking.has(c.id)} onManual={setManual} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <aside aria-labelledby="skills" className="space-y-3">
          <h2 id="skills" className="section-title">
            My skills
          </h2>
          <div className="card">
            {profile.loading ? (
              <LoadingRegion label="Loading skills">
                <Skeleton lines={4} />
              </LoadingRegion>
            ) : profile.error ? (
              <ErrorState inline error={profile.error} onRetry={profile.reload} />
            ) : !profile.data || profile.data.skills.length === 0 ? (
              <p className="text-sm text-gray-600">No skills yet. Add claimed skills to your profile, then prove them here.</p>
            ) : (
              <ul className="space-y-3">
                {profile.data.skills.map((s) => (
                  <li key={s.concept} className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-black text-gray-900">{s.concept}</span>
                    <TrustBadge
                      level={s.trust_level}
                      source={s.trust_level === 2 ? s.endorsed_by?.[0] : s.sources[0]?.title}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </div>

      {manual ? (
        <ManualCertificateForm
          key={manual.id}
          certificate={manual}
          onClose={() => setManual(null)}
          onSaved={(c) => {
            upsert(c);
            setManual(null);
          }}
        />
      ) : null}
    </>
  );
}
