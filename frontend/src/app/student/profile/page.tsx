"use client";
// SCR-17 Student profile (plan section 3): the one place a student edits what the matcher knows about them.
// Trust is never typed: the badge on a skill comes from the server (certificates and endorsements only), and a
// self-reported CGPA is labelled as such. Saves per tab, so a half-finished profile is fine.
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { FileText, Plus, Trash2, Upload } from "lucide-react";
import { ErrorState, LoadingRegion, PageHeader, Skeleton, TrustBadge, useToast } from "@/components/ui";
import { useApi } from "@/hooks/useApi";
import { api, fetchObjectUrl } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type MyProfile = components["schemas"]["MyProfile"];
type Suggestions = components["schemas"]["ResumeSuggestions"];
type Concept = components["schemas"]["ConceptSuggestion"];
type Level = components["schemas"]["SkillLevel"];
type Programme = components["schemas"]["Programme"];

const TABS = ["Basics", "Skills", "Projects", "Resume", "Preferences"] as const;
type Tab = (typeof TABS)[number];
const PROGRAMMES: { value: Programme; label: string }[] = [
  { value: "btech", label: "B.Tech" },
  { value: "mtech", label: "M.Tech" },
  { value: "phd", label: "PhD" },
  { value: "other", label: "Other" },
];
const LEVELS: { value: Level; label: string }[] = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];
const PREFERENCES = ["research", "tooling", "data", "writing", "teaching assistant"];

interface ProjectDraft {
  title: string;
  description: string;
  link: string;
  skills: string;
}

function Field({ id, label, hint, children }: { id: string; label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="label">
        {label}
      </label>
      {children}
      {hint ? <p className="mt-1 text-xs text-gray-600">{hint}</p> : null}
    </div>
  );
}

function Completeness({ data }: { data: MyProfile["completeness"] }) {
  return (
    <section aria-labelledby="comp-title" className="card space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 id="comp-title" className="section-title">
          Profile completeness
        </h2>
        <span className="text-lg font-black text-gray-900">{data.percent}%</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={data.percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Profile completeness"
        className="h-2.5 rounded-full bg-gray-100"
      >
        <div className="h-2.5 rounded-full bg-brand" style={{ width: `${data.percent}%` }} />
      </div>
      {data.next_action ? <p className="text-sm font-medium text-gray-700">Next: {data.next_action}.</p> : <p className="text-sm font-medium text-green-800">Your profile is complete.</p>}
    </section>
  );
}

export default function StudentProfilePage() {
  const toast = useToast();
  const { data, error, loading, reload } = useApi<MyProfile>("/me/profile");
  const [tab, setTab] = useState<Tab>("Basics");
  const [busy, setBusy] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Basics
  const [programme, setProgramme] = useState<Programme | "">("");
  const [year, setYear] = useState(3);
  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");
  const [interests, setInterests] = useState("");
  const [links, setLinks] = useState("");
  const [hours, setHours] = useState("");
  const [from, setFrom] = useState("");
  const [cgpa, setCgpa] = useState("");
  // Skills
  const [claimed, setClaimed] = useState<string[]>([]);
  const [levels, setLevels] = useState<Record<string, Level | "">>({});
  const [draft, setDraft] = useState("");
  const [options, setOptions] = useState<Concept[]>([]);
  // Projects, preferences, resume
  const [projects, setProjects] = useState<ProjectDraft[]>([]);
  const [prefs, setPrefs] = useState<string[]>([]);
  const [suggest, setSuggest] = useState<Suggestions | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const file = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!data) return;
    setProgramme(data.programme ?? "");
    setYear(data.year);
    setHeadline(data.headline ?? "");
    setBio(data.bio ?? "");
    setInterests(data.interests.join(", "));
    setLinks(data.links.join("\n"));
    setHours(data.availability_hours == null ? "" : String(data.availability_hours));
    setFrom(data.available_from ?? "");
    setCgpa(data.cgpa.self_reported == null ? "" : String(data.cgpa.self_reported));
    setClaimed(data.skills.filter((s) => s.claimed).map((s) => s.concept));
    setLevels(Object.fromEntries(data.skills.map((s) => [s.concept, s.level ?? ""])));
    setProjects(
      data.projects.map((p) => ({ title: p.title, description: p.description ?? "", link: p.link ?? "", skills: p.skills.join(", ") })),
    );
    setPrefs(data.preferences);
  }, [data]);

  useEffect(() => {
    const q = draft.trim();
    if (q.length < 1) {
      setOptions([]);
      return;
    }
    const id = window.setTimeout(() => {
      api
        .get<Concept[]>("/concepts", { params: { q } })
        .then((r) => setOptions(r.data))
        .catch(() => setOptions([]));
    }, 200);
    return () => window.clearTimeout(id);
  }, [draft]);

  async function save(body: Record<string, unknown>, done: string) {
    setBusy(true);
    setFieldErrors({});
    try {
      await api.patch("/me/profile", body);
      toast.success(done);
      await reload();
    } catch (e) {
      if (isApiError(e) && e.status === 422) {
        setFieldErrors(Object.fromEntries(e.errors.map((x) => [x.field.split(".")[0], x.message])));
        toast.error("Check the highlighted fields.");
      } else {
        toast.error("Couldn't save. Try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  const split = (text: string, sep: RegExp) => text.split(sep).map((x) => x.trim()).filter(Boolean);

  function saveBasics() {
    void save(
      {
        programme: programme || null,
        year,
        headline: headline.trim() || null,
        bio: bio.trim() || null,
        interests: split(interests, /,/),
        links: split(links, /\n/),
        availability_hours: hours === "" ? null : Number(hours),
        available_from: from || null,
        self_reported_cgpa: cgpa === "" ? null : Number(cgpa),
      },
      "Basics saved",
    );
  }

  function addSkill(name: string) {
    const n = name.trim().toLowerCase();
    if (n && !claimed.includes(n) && claimed.length < 30) setClaimed([...claimed, n]);
    setDraft("");
    setOptions([]);
  }

  function saveSkills() {
    const lv: Record<string, Level> = {};
    for (const name of claimed.concat(data?.skills.filter((s) => !s.claimed).map((s) => s.concept) ?? [])) {
      const level = levels[name];
      if (level) lv[name] = level;
    }
    void save({ claimed_skills: claimed, skill_levels: lv }, "Skills saved");
  }

  function saveProjects() {
    void save(
      {
        projects: projects
          .filter((p) => p.title.trim())
          .map((p) => ({
            title: p.title.trim(),
            description: p.description.trim() || null,
            link: p.link.trim() || null,
            skills: split(p.skills, /,/),
          })),
      },
      "Projects saved",
    );
  }

  async function upload(f: File | undefined) {
    if (!f) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", f);
      await api.post("/me/resume", form);
      toast.success("Resume uploaded");
      setSuggest(null);
      await reload();
    } catch (e) {
      const code = isApiError(e) ? e.code : "";
      toast.error(
        code === "UNSUPPORTED_FILE_TYPE" ? "Upload a PDF file." : code === "FILE_TOO_LARGE" ? "That file is too large (5 MB at most)." : code === "VALIDATION_FAILED" ? "The resume can have at most 4 pages." : code === "RATE_LIMITED" ? "Too many uploads. Try again later." : "Couldn't upload. Try again.",
      );
    } finally {
      setBusy(false);
      if (file.current) file.current.value = "";
    }
  }

  async function viewResume() {
    if (!data) return;
    const { url } = await fetchObjectUrl(`/students/${data.user_id}/resume/file`);
    window.open(url, "_blank", "noopener");
  }

  async function findSkills() {
    setBusy(true);
    try {
      const res = await api.post<Suggestions>("/me/resume/suggestions");
      setSuggest(res.data);
      setPicked(res.data.skills.filter((s) => !s.already_claimed).map((s) => s.concept));
    } catch {
      toast.error("Couldn't read the resume. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function applySuggestions() {
    setBusy(true);
    try {
      await api.post("/me/resume/suggestions/apply", { skills: picked });
      toast.success("Added as claimed skills. Certify them to verify.");
      setSuggest(null);
      await reload();
    } catch {
      toast.error("Couldn't add those. Try again.");
    } finally {
      setBusy(false);
    }
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
        {error ? <ErrorState error={error} onRetry={reload} homeHref="/student" /> : null}
      </>
    );
  }

  const err = (k: string) => (fieldErrors[k] ? <p role="alert" className="mt-1 text-xs font-bold text-red-700">{fieldErrors[k]}</p> : null);
  const cg = data.cgpa;

  return (
    <>
      <PageHeader
        title="Profile"
        subtitle={`${data.name} · ${data.roll_no} · ${data.dept_code}`}
        actions={<Link href="/student/certificates" className="btn-secondary">Certify a skill</Link>}
      />
      <div className="space-y-6">
        <Completeness data={data.completeness} />

        <div role="tablist" aria-label="Profile sections" className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t}
              role="tab"
              id={`tab-${t}`}
              aria-selected={tab === t}
              aria-controls={`panel-${t}`}
              type="button"
              onClick={() => setTab(t)}
              className={`min-h-[44px] rounded-full border px-4 text-sm font-black ${tab === t ? "border-brand bg-brand text-white" : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"}`}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === "Basics" ? (
          <section role="tabpanel" id="panel-Basics" aria-labelledby="tab-Basics" className="card grid gap-4 md:grid-cols-2">
            <Field id="dept" label="Department" hint="Set by the department; it can't be changed here.">
              <input id="dept" className="input" value={data.dept_code} readOnly />
            </Field>
            <Field id="programme" label="Programme">
              <select id="programme" className="input" value={programme} onChange={(e) => setProgramme(e.target.value as Programme | "")}>
                <option value="">Not set</option>
                {PROGRAMMES.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </Field>
            <Field id="year" label="Year of study">
              <select id="year" className="input" value={year} onChange={(e) => setYear(Number(e.target.value))}>
                {[1, 2, 3, 4, 5].map((y) => (
                  <option key={y} value={y}>Year {y}</option>
                ))}
              </select>
              {err("year")}
            </Field>
            <Field
              id="cgpa"
              label="CGPA (self-reported)"
              hint={
                cg.record != null
                  ? `Your department record shows ${cg.record} (${cg.record_term}). The record is used for eligibility; this value is only a fallback.`
                  : "No department record yet, so openings use this value and label it self-reported."
              }
            >
              <input id="cgpa" className="input" inputMode="decimal" value={cgpa} onChange={(e) => setCgpa(e.target.value)} placeholder="for example 8.2" />
              {err("self_reported_cgpa")}
            </Field>
            <div className="md:col-span-2">
              <Field id="headline" label="Headline" hint="One line about you (up to 120 characters).">
                <input id="headline" className="input" maxLength={120} value={headline} onChange={(e) => setHeadline(e.target.value)} />
              </Field>
            </div>
            <div className="md:col-span-2">
              <Field id="bio" label="Bio (up to 500 characters)">
                <textarea id="bio" className="input" rows={3} maxLength={500} value={bio} onChange={(e) => setBio(e.target.value)} />
              </Field>
            </div>
            <Field id="interests" label="Interests" hint="Up to 10, separated by commas.">
              <input id="interests" className="input" value={interests} onChange={(e) => setInterests(e.target.value)} />
              {err("interests")}
            </Field>
            <Field id="links" label="Links" hint="One https link per line (GitHub, portfolio). Up to 5.">
              <textarea id="links" className="input" rows={3} value={links} onChange={(e) => setLinks(e.target.value)} />
              {err("links")}
            </Field>
            <Field id="hours" label="Hours per week you can give">
              <input id="hours" className="input" inputMode="numeric" value={hours} onChange={(e) => setHours(e.target.value)} />
              {err("availability_hours")}
            </Field>
            <Field id="from" label="Available from">
              <input id="from" type="date" className="input" value={from} onChange={(e) => setFrom(e.target.value)} />
            </Field>
            <div className="md:col-span-2">
              <button type="button" className="btn-primary" disabled={busy} onClick={saveBasics}>Save basics</button>
            </div>
          </section>
        ) : null}

        {tab === "Skills" ? (
          <section role="tabpanel" id="panel-Skills" aria-labelledby="tab-Skills" className="card space-y-4">
            <p className="text-sm text-gray-700">
              Add what you know. A skill you add is <strong>claimed</strong>. It becomes <strong>certified</strong> only when a certificate proves it, and the level you pick is your own estimate and never changes that.
            </p>
            <div className="flex flex-wrap gap-2">
              <div className="min-w-[220px] flex-1">
                <label htmlFor="skill-draft" className="label">Add a skill</label>
                <input
                  id="skill-draft"
                  className="input"
                  list="skill-options"
                  value={draft}
                  maxLength={40}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill(draft);
                    }
                  }}
                />
                <datalist id="skill-options">
                  {options.map((o) => (
                    <option key={o.name} value={o.name}>{o.matched_alias ? `via ${o.matched_alias}` : undefined}</option>
                  ))}
                </datalist>
              </div>
              <button type="button" className="btn-secondary self-end" onClick={() => addSkill(draft)}>
                <Plus aria-hidden size={16} /> Add
              </button>
            </div>
            {claimed.length >= 30 ? <p className="text-xs font-bold text-amber-800">You have reached 30 skills.</p> : null}
            <ul className="space-y-2">
              {Array.from(new Set(claimed.concat(data.skills.filter((s) => !s.claimed).map((s) => s.concept)))).map((name) => {
                const held = data.skills.find((s) => s.concept === name);
                const isClaimed = claimed.includes(name);
                return (
                  <li key={name} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-gray-200 bg-white p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-black text-gray-900">{name}</span>
                      <TrustBadge level={(held?.trust_level ?? 0) as 0 | 1 | 2} source={held?.sources[0]?.title} />
                      {!held || held.trust_level === 0 ? (
                        <Link href="/student/certificates" className="text-xs font-bold text-brand underline">Certify this</Link>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      <label htmlFor={`lvl-${name}`} className="sr-only">Your level in {name}</label>
                      <select id={`lvl-${name}`} className="input !w-auto !py-1.5" value={levels[name] ?? ""} onChange={(e) => setLevels({ ...levels, [name]: e.target.value as Level | "" })}>
                        <option value="">Level</option>
                        {LEVELS.map((l) => (
                          <option key={l.value} value={l.value}>{l.label}</option>
                        ))}
                      </select>
                      {isClaimed ? (
                        <button type="button" className="btn-ghost" aria-label={`Remove ${name}`} onClick={() => setClaimed(claimed.filter((c) => c !== name))}>
                          <Trash2 aria-hidden size={16} />
                        </button>
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ul>
            {err("skill_levels")}
            <button type="button" className="btn-primary" disabled={busy} onClick={saveSkills}>Save skills</button>
          </section>
        ) : null}

        {tab === "Projects" ? (
          <section role="tabpanel" id="panel-Projects" aria-labelledby="tab-Projects" className="card space-y-4">
            {projects.length === 0 ? <p className="text-sm text-gray-600">No projects yet. Add up to 10.</p> : null}
            {projects.map((p, i) => (
              <fieldset key={i} className="space-y-2 rounded-2xl border border-gray-200 p-3">
                <legend className="px-1 text-xs font-black uppercase tracking-widest text-gray-600">Project {i + 1}</legend>
                <input aria-label={`Project ${i + 1} title`} className="input" placeholder="Title" maxLength={100} value={p.title} onChange={(e) => setProjects(projects.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))} />
                <textarea aria-label={`Project ${i + 1} description`} className="input" rows={2} placeholder="What it does (up to 300 characters)" maxLength={300} value={p.description} onChange={(e) => setProjects(projects.map((x, j) => (j === i ? { ...x, description: e.target.value } : x)))} />
                <input aria-label={`Project ${i + 1} link`} className="input" placeholder="https link (optional)" value={p.link} onChange={(e) => setProjects(projects.map((x, j) => (j === i ? { ...x, link: e.target.value } : x)))} />
                <input aria-label={`Project ${i + 1} skills`} className="input" placeholder="Skills used, separated by commas" value={p.skills} onChange={(e) => setProjects(projects.map((x, j) => (j === i ? { ...x, skills: e.target.value } : x)))} />
                <button type="button" className="btn-ghost" onClick={() => setProjects(projects.filter((_, j) => j !== i))}>
                  <Trash2 aria-hidden size={16} /> Remove project
                </button>
              </fieldset>
            ))}
            {err("projects")}
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" disabled={projects.length >= 10} onClick={() => setProjects([...projects, { title: "", description: "", link: "", skills: "" }])}>
                <Plus aria-hidden size={16} /> Add a project
              </button>
              <button type="button" className="btn-primary" disabled={busy} onClick={saveProjects}>Save projects</button>
            </div>
          </section>
        ) : null}

        {tab === "Resume" ? (
          <section role="tabpanel" id="panel-Resume" aria-labelledby="tab-Resume" className="card space-y-4">
            <p className="text-sm text-gray-700">
              One PDF, up to 5 MB and 4 pages. Your mentors, your HOD and faculty you apply to can open it; nobody else can.
            </p>
            {data.resume ? (
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-gray-200 p-3">
                <span className="inline-flex items-center gap-2 text-sm font-bold text-gray-900">
                  <FileText aria-hidden size={18} /> Uploaded {formatDate(data.resume.uploaded_at)} · {data.resume.pages} page{data.resume.pages === 1 ? "" : "s"}
                </span>
                <button type="button" className="btn-ghost" onClick={() => void viewResume()}>View</button>
              </div>
            ) : (
              <p className="text-sm text-gray-600">No resume uploaded yet.</p>
            )}
            <div>
              <label htmlFor="resume-file" className="label">{data.resume ? "Replace resume" : "Upload resume"}</label>
              <input id="resume-file" ref={file} type="file" accept="application/pdf" className="block text-sm" onChange={(e) => void upload(e.target.files?.[0])} />
            </div>
            {data.resume ? (
              <div className="space-y-3 border-t border-gray-100 pt-4">
                <button type="button" className="btn-secondary" disabled={busy} onClick={() => void findSkills()}>
                  <Upload aria-hidden size={16} /> Find skills in my resume
                </button>
                {suggest ? (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-700">{suggest.note}</p>
                    {suggest.skills.length === 0 ? null : (
                      <ul className="space-y-1">
                        {suggest.skills.map((s) => (
                          <li key={s.concept}>
                            <label className="flex min-h-[44px] items-center gap-3 text-sm font-bold text-gray-900">
                              <input
                                type="checkbox"
                                className="h-5 w-5 accent-[#8c1515]"
                                disabled={s.already_claimed}
                                checked={s.already_claimed || picked.includes(s.concept)}
                                onChange={(e) => setPicked(e.target.checked ? [...picked, s.concept] : picked.filter((x) => x !== s.concept))}
                              />
                              {s.concept}
                              {s.already_claimed ? <span className="text-xs font-medium text-gray-600">already on your profile</span> : null}
                            </label>
                          </li>
                        ))}
                      </ul>
                    )}
                    {picked.length > 0 ? (
                      <button type="button" className="btn-primary" disabled={busy} onClick={() => void applySuggestions()}>
                        Add {picked.length} as claimed
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ) : null}
          </section>
        ) : null}

        {tab === "Preferences" ? (
          <section role="tabpanel" id="panel-Preferences" aria-labelledby="tab-Preferences" className="card space-y-4">
            <fieldset>
              <legend className="label">What kind of work are you after?</legend>
              <div className="flex flex-wrap gap-3">
                {PREFERENCES.map((p) => (
                  <label key={p} className="flex min-h-[44px] items-center gap-2 text-sm font-bold text-gray-900">
                    <input type="checkbox" className="h-5 w-5 accent-[#8c1515]" checked={prefs.includes(p)} onChange={(e) => setPrefs(e.target.checked ? [...prefs, p] : prefs.filter((x) => x !== p))} />
                    {p}
                  </label>
                ))}
              </div>
            </fieldset>
            <button type="button" className="btn-primary" disabled={busy} onClick={() => void save({ preferences: prefs }, "Preferences saved")}>
              Save preferences
            </button>
          </section>
        ) : null}
      </div>
    </>
  );
}
