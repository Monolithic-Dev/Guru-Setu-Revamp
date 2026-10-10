"use client";
// SCR-18 Faculty profile (plan section 5): research areas, expertise, subjects taught, qualifications and capacity.
// This is what students and the matcher see: research areas shape each opening's text, capacity gates applications,
// and the guide directory orders faculty by the topics they share with a student. Lists are saved in full.
import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { ErrorState, LoadingRegion, PageHeader, Skeleton, useToast } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import { getSession } from "@/lib/session";
import type { components } from "@/lib/types";

type FacultyProfile = components["schemas"]["FacultyProfile"];

const TABS = ["Research and expertise", "Subjects", "Qualifications", "Capacity"] as const;
type Tab = (typeof TABS)[number];

interface CourseDraft {
  code: string;
  title: string;
  term_id: string;
  topics: string;
}
interface QualDraft {
  degree: string;
  institution: string;
  year: string;
}

const split = (text: string) => text.split(",").map((x) => x.trim()).filter(Boolean);

export default function FacultyProfilePage() {
  const toast = useToast();
  const { data, error, loading, reload } = useApi<FacultyProfile>("/me/faculty-profile");
  const [tab, setTab] = useState<Tab>("Research and expertise");
  const [busy, setBusy] = useState(false);
  const [areas, setAreas] = useState<{ concept: string; primary: boolean }[]>([]);
  const [areaDraft, setAreaDraft] = useState("");
  const [expertise, setExpertise] = useState("");
  const [courses, setCourses] = useState<CourseDraft[]>([]);
  const [quals, setQuals] = useState<QualDraft[]>([]);
  const [max, setMax] = useState("");
  const [accepting, setAccepting] = useState(true);
  const [hours, setHours] = useState("");
  const [links, setLinks] = useState("");
  const [pubs, setPubs] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;
    setAreas(data.research_areas.map((a) => ({ concept: a.concept, primary: Boolean(a.primary) })));
    setExpertise(data.expertise.join(", "));
    setCourses(data.courses.map((c) => ({ code: c.code, title: c.title, term_id: c.term_id ?? "", topics: (c.topics ?? []).join(", ") })));
    setQuals(data.qualifications.map((q) => ({ degree: q.degree, institution: q.institution, year: q.year == null ? "" : String(q.year) })));
    setMax(data.max_guided_students == null ? "" : String(data.max_guided_students));
    setAccepting(data.accepting_guides);
    setHours(data.office_hours ?? "");
    setLinks(data.links.join("\n"));
    setPubs(data.publications.join("\n"));
  }, [data]);

  async function save(body: Record<string, unknown>, done: string) {
    setBusy(true);
    setFieldError(null);
    try {
      await api.patch("/me/faculty-profile", body);
      toast.success(done);
      await reload();
    } catch (e) {
      if (isApiError(e) && e.status === 422) {
        setFieldError(e.errors[0]?.message ?? "Check the values and try again.");
        toast.error("Check the highlighted fields.");
      } else {
        toast.error("Couldn't save. Try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  function addArea() {
    const name = areaDraft.trim().toLowerCase();
    if (name && !areas.some((a) => a.concept === name) && areas.length < 10) setAreas([...areas, { concept: name, primary: false }]);
    setAreaDraft("");
  }

  if (loading) {
    return (
      <>
        <PageHeader title="Profile" />
        <LoadingRegion label="Loading your profile">
          <Skeleton block />
        </LoadingRegion>
      </>
    );
  }
  if (error || !data) {
    return (
      <>
        <PageHeader title="Profile" />
        {error ? <ErrorState error={error} onRetry={reload} homeHref="/faculty" /> : null}
      </>
    );
  }

  const me = getSession()?.userId;
  return (
    <>
      <PageHeader
        title="Profile"
        subtitle={`${data.name} · ${data.designation} · ${data.dept_code}`}
        actions={me ? <Link href={`/faculty-profile/${me}`} className="btn-secondary">See how students see it</Link> : undefined}
      />
      <div className="space-y-6">
        <div role="tablist" aria-label="Profile sections" className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t}
              role="tab"
              id={`ftab-${t}`}
              aria-selected={tab === t}
              aria-controls={`fpanel-${t}`}
              type="button"
              onClick={() => setTab(t)}
              className={`min-h-[44px] rounded-full border px-4 text-sm font-black ${tab === t ? "border-brand bg-brand text-white" : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"}`}
            >
              {t}
            </button>
          ))}
        </div>
        {fieldError ? <p role="alert" className="text-sm font-bold text-red-700">{fieldError}</p> : null}

        {tab === "Research and expertise" ? (
          <section role="tabpanel" id="fpanel-Research and expertise" aria-labelledby="ftab-Research and expertise" className="card space-y-4">
            <p className="text-sm text-gray-700">Research areas are the strongest signal for matching students to you. Mark at most one as your primary area.</p>
            <div className="flex flex-wrap gap-2">
              <div className="min-w-[220px] flex-1">
                <label htmlFor="area-draft" className="label">Add a research area</label>
                <input id="area-draft" className="input" value={areaDraft} maxLength={40} onChange={(e) => setAreaDraft(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addArea(); } }} />
              </div>
              <button type="button" className="btn-secondary self-end" onClick={addArea}><Plus aria-hidden size={16} /> Add</button>
            </div>
            <ul className="space-y-2">
              {areas.map((a) => (
                <li key={a.concept} className="flex items-center justify-between gap-2 rounded-2xl border border-gray-200 p-3">
                  <span className="text-sm font-black text-gray-900">{a.concept}</span>
                  <span className="flex items-center gap-3">
                    <label className="flex min-h-[44px] items-center gap-2 text-sm font-bold text-gray-700">
                      <input type="radio" name="primary-area" className="h-5 w-5 accent-[#8c1515]" checked={a.primary} onChange={() => setAreas(areas.map((x) => ({ ...x, primary: x.concept === a.concept })))} />
                      Primary
                    </label>
                    <button type="button" className="btn-ghost" aria-label={`Remove ${a.concept}`} onClick={() => setAreas(areas.filter((x) => x.concept !== a.concept))}><Trash2 aria-hidden size={16} /></button>
                  </span>
                </li>
              ))}
            </ul>
            <div>
              <label htmlFor="expertise" className="label">Expertise</label>
              <input id="expertise" className="input" value={expertise} onChange={(e) => setExpertise(e.target.value)} />
              <p className="mt-1 text-xs text-gray-600">Skills you can teach or supervise, separated by commas (up to 15).</p>
            </div>
            <button type="button" className="btn-primary" disabled={busy} onClick={() => void save({ research_areas: areas, expertise: split(expertise) }, "Research and expertise saved")}>Save</button>
          </section>
        ) : null}

        {tab === "Subjects" ? (
          <section role="tabpanel" id="fpanel-Subjects" aria-labelledby="ftab-Subjects" className="card space-y-4">
            <p className="text-sm text-gray-700">What you teach tells students what they will already know when they work with you.</p>
            {courses.map((c, i) => (
              <fieldset key={i} className="grid gap-2 rounded-2xl border border-gray-200 p-3 md:grid-cols-2">
                <legend className="px-1 text-xs font-black uppercase tracking-widest text-gray-600">Subject {i + 1}</legend>
                <input aria-label={`Subject ${i + 1} code`} className="input" placeholder="Code, for example CS401" maxLength={20} value={c.code} onChange={(e) => setCourses(courses.map((x, j) => (j === i ? { ...x, code: e.target.value } : x)))} />
                <input aria-label={`Subject ${i + 1} title`} className="input" placeholder="Title" maxLength={100} value={c.title} onChange={(e) => setCourses(courses.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))} />
                <input aria-label={`Subject ${i + 1} term`} className="input" placeholder="Term, for example 2026-ODD" maxLength={20} value={c.term_id} onChange={(e) => setCourses(courses.map((x, j) => (j === i ? { ...x, term_id: e.target.value } : x)))} />
                <input aria-label={`Subject ${i + 1} topics`} className="input" placeholder="Topics, separated by commas" value={c.topics} onChange={(e) => setCourses(courses.map((x, j) => (j === i ? { ...x, topics: e.target.value } : x)))} />
                <button type="button" className="btn-ghost md:col-span-2" onClick={() => setCourses(courses.filter((_, j) => j !== i))}><Trash2 aria-hidden size={16} /> Remove subject</button>
              </fieldset>
            ))}
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" disabled={courses.length >= 15} onClick={() => setCourses([...courses, { code: "", title: "", term_id: "", topics: "" }])}><Plus aria-hidden size={16} /> Add a subject</button>
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() => void save({ courses: courses.filter((c) => c.code.trim() && c.title.trim()).map((c) => ({ code: c.code.trim(), title: c.title.trim(), term_id: c.term_id.trim() || null, topics: split(c.topics) })) }, "Subjects saved")}
              >
                Save subjects
              </button>
            </div>
          </section>
        ) : null}

        {tab === "Qualifications" ? (
          <section role="tabpanel" id="fpanel-Qualifications" aria-labelledby="ftab-Qualifications" className="card space-y-4">
            <p className="text-sm text-gray-700">Self-reported. A qualification is listed as stated, not as verified.</p>
            {quals.map((q, i) => (
              <fieldset key={i} className="grid gap-2 rounded-2xl border border-gray-200 p-3 md:grid-cols-3">
                <legend className="px-1 text-xs font-black uppercase tracking-widest text-gray-600">Qualification {i + 1}</legend>
                <input aria-label={`Qualification ${i + 1} degree`} className="input" placeholder="Degree" value={q.degree} onChange={(e) => setQuals(quals.map((x, j) => (j === i ? { ...x, degree: e.target.value } : x)))} />
                <input aria-label={`Qualification ${i + 1} institution`} className="input" placeholder="Institution" value={q.institution} onChange={(e) => setQuals(quals.map((x, j) => (j === i ? { ...x, institution: e.target.value } : x)))} />
                <input aria-label={`Qualification ${i + 1} year`} className="input" placeholder="Year" inputMode="numeric" value={q.year} onChange={(e) => setQuals(quals.map((x, j) => (j === i ? { ...x, year: e.target.value } : x)))} />
                <button type="button" className="btn-ghost md:col-span-3" onClick={() => setQuals(quals.filter((_, j) => j !== i))}><Trash2 aria-hidden size={16} /> Remove</button>
              </fieldset>
            ))}
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" disabled={quals.length >= 5} onClick={() => setQuals([...quals, { degree: "", institution: "", year: "" }])}><Plus aria-hidden size={16} /> Add</button>
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() => void save({ qualifications: quals.filter((q) => q.degree.trim() && q.institution.trim()).map((q) => ({ degree: q.degree.trim(), institution: q.institution.trim(), year: q.year ? Number(q.year) : null })) }, "Qualifications saved")}
              >
                Save qualifications
              </button>
            </div>
          </section>
        ) : null}

        {tab === "Capacity" ? (
          <section role="tabpanel" id="fpanel-Capacity" aria-labelledby="ftab-Capacity" className="card grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2 text-sm text-gray-700">
              You currently guide <strong>{data.guided_students ?? 0}</strong> student{data.guided_students === 1 ? "" : "s"}. When you reach your limit or switch intake off, your openings show as unavailable.
            </div>
            <div>
              <label htmlFor="cap" className="label">Most students you can guide</label>
              <input id="cap" className="input" inputMode="numeric" value={max} onChange={(e) => setMax(e.target.value)} />
            </div>
            <label className="flex min-h-[44px] items-center gap-3 self-end text-sm font-bold text-gray-900">
              <input type="checkbox" className="h-5 w-5 accent-[#8c1515]" checked={accepting} onChange={(e) => setAccepting(e.target.checked)} />
              I am taking new guided students
            </label>
            <div className="md:col-span-2">
              <label htmlFor="oh" className="label">Office hours</label>
              <input id="oh" className="input" maxLength={200} value={hours} onChange={(e) => setHours(e.target.value)} />
            </div>
            <div>
              <label htmlFor="flinks" className="label">Links</label>
              <textarea id="flinks" className="input" rows={3} value={links} onChange={(e) => setLinks(e.target.value)} />
              <p className="mt-1 text-xs text-gray-600">One https link per line, up to 5.</p>
            </div>
            <div>
              <label htmlFor="pubs" className="label">Selected publications</label>
              <textarea id="pubs" className="input" rows={3} value={pubs} onChange={(e) => setPubs(e.target.value)} />
              <p className="mt-1 text-xs text-gray-600">One title per line, up to 10. Listed as self-reported.</p>
            </div>
            <div className="md:col-span-2">
              <button
                type="button"
                className="btn-primary"
                disabled={busy}
                onClick={() =>
                  void save(
                    {
                      max_guided_students: max === "" ? 0 : Number(max),
                      accepting_guides: accepting,
                      office_hours: hours.trim() || null,
                      links: links.split("\n").map((x) => x.trim()).filter(Boolean),
                      publications: pubs.split("\n").map((x) => x.trim()).filter(Boolean),
                    },
                    "Capacity saved",
                  )
                }
              >
                Save capacity
              </button>
            </div>
          </section>
        ) : null}
      </div>
    </>
  );
}
