"use client";
// Create opening (add-on A9, REQ-030, API-014). P4's SCR-15 shows the link when `features.createOpening` is true.
import { useRouter } from "next/navigation";
import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Plus, X } from "lucide-react";
import { PageHeader, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";

type Opening = components["schemas"]["Opening"];
type OpeningCreate = components["schemas"]["OpeningCreate"];
type Field = keyof OpeningCreate;

export default function NewOpeningPage() {
  const router = useRouter();
  const toast = useToast();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [busy, setBusy] = useState(false);
  // Opening v2 (all optional): capacity, deadline and the eligibility rules, evaluated openly for each student.
  const [positions, setPositions] = useState("1");
  const [deadline, setDeadline] = useState("");
  const [years, setYears] = useState<number[]>([]);
  const [minCgpa, setMinCgpa] = useState("");
  const [strict, setStrict] = useState(false);
  const [mode, setMode] = useState("");
  const [weeks, setWeeks] = useState("");
  const [hours, setHours] = useState("");
  const [preferred, setPreferred] = useState("");

  function addSkill() {
    const s = draft.trim().toLowerCase();
    if (s && !skills.includes(s) && skills.length < 10) {
      setSkills([...skills, s]);
      setErrors((e) => ({ ...e, required_skills: undefined }));
    }
    setDraft("");
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill();
    }
  }

  function validate(): Partial<Record<Field, string>> {
    const e: Partial<Record<Field, string>> = {};
    const t = title.trim();
    if (!t) e.title = "This field is required.";
    else if (t.length < 5 || t.length > 120) e.title = "Title must be 5–120 characters.";
    if (!description.trim()) e.description = "This field is required.";
    else if (description.length > 2000) e.description = "Keep the description under 2000 characters.";
    if (skills.length < 1 || skills.length > 10) e.required_skills = "Add 1 to 10 required skills.";
    return e;
  }

  const focusFirst = (e: Partial<Record<Field, string>>) => {
    const first = (["title", "description", "required_skills"] as Field[]).find((k) => e[k]);
    if (first) document.getElementById(`op-${first}`)?.focus();
  };

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    const e = validate();
    setErrors(e);
    if (Object.values(e).some(Boolean)) return focusFirst(e);
    setBusy(true);
    try {
      const body: OpeningCreate = {
        title: title.trim(),
        description: description.trim(),
        required_skills: skills,
        positions: Number(positions) || 1,
        deadline: deadline || null,
        eligible_years: years,
        min_cgpa: minCgpa === "" ? null : Number(minCgpa),
        eligibility_mode: strict ? "strict" : "advisory",
        mode: (mode || undefined) as OpeningCreate["mode"],
        duration_weeks: weeks === "" ? null : Number(weeks),
        hours_per_week: hours === "" ? null : Number(hours),
        preferred_skills: preferred.split(",").map((x) => x.trim()).filter(Boolean),
      };
      const { data } = await api.post<Opening>("/openings", body);
      toast.success("Opening created.");
      router.push(`/faculty/openings/${data.id}`);
    } catch (err) {
      if (isApiError(err) && err.status === 422 && err.errors.length) {
        const mapped: Partial<Record<Field, string>> = {};
        err.errors.forEach((fe) => (mapped[fe.field.split(/[.[]/)[0] as Field] ??= fe.message));
        setErrors(mapped);
        focusFirst(mapped);
      } else {
        toast.error("Couldn't create the opening. Try again.");
      }
      setBusy(false);
    }
  }

  const err = (k: Field) =>
    errors[k] ? (
      <p id={`op-${k}-error`} role="alert" className="mt-1 text-xs font-bold text-red-700">
        {errors[k]}
      </p>
    ) : null;
  const desc = (k: Field) => (errors[k] ? { "aria-invalid": true, "aria-describedby": `op-${k}-error` } : {});

  return (
    <>
      <PageHeader title="New opening" subtitle="Students see it with their fit score." backHref="/faculty/openings" backLabel="My openings" />
      <form onSubmit={onSubmit} noValidate className="card max-w-3xl space-y-5">
        <div>
          <label htmlFor="op-title" className="label">
            Title
          </label>
          <input
            id="op-title"
            className="input"
            maxLength={120}
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setErrors((x) => ({ ...x, title: undefined }));
            }}
            {...desc("title")}
          />
          {err("title")}
        </div>
        <div>
          <label htmlFor="op-description" className="label">
            Description
          </label>
          <textarea
            id="op-description"
            className="input"
            rows={5}
            maxLength={2000}
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              setErrors((x) => ({ ...x, description: undefined }));
            }}
            {...desc("description")}
          />
          <p className="mt-1 text-right text-xs text-gray-600">{description.length}/2000</p>
          {err("description")}
        </div>
        <div>
          <label htmlFor="op-required_skills" className="label">
            Required skills (1–10)
          </label>
          <div className="flex gap-2">
            <input
              id="op-required_skills"
              className="input"
              value={draft}
              placeholder="Type a skill and press Enter"
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKey}
              {...desc("required_skills")}
            />
            <button type="button" className="btn-secondary" onClick={addSkill} disabled={skills.length >= 10}>
              <Plus aria-hidden size={16} /> Add
            </button>
          </div>
          {err("required_skills")}
          {skills.length > 0 ? (
            <ul className="mt-2 flex flex-wrap gap-2" aria-label="Required skills">
              {skills.map((s) => (
                <li key={s} className="inline-flex items-center gap-1 rounded-full border border-brand-line bg-brand-soft py-1 pl-3 pr-1 text-xs font-bold text-brand">
                  {s}
                  <button type="button" aria-label={`Remove ${s}`} className="rounded-full p-1 hover:bg-white" onClick={() => setSkills(skills.filter((x) => x !== s))}>
                    <X aria-hidden size={12} />
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
        <fieldset className="space-y-4 rounded-2xl border border-gray-200 p-4">
          <legend className="px-1 text-xs font-black uppercase tracking-widest text-gray-600">Who can apply (optional)</legend>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="op-positions" className="label">Positions</label>
              <input id="op-positions" className="input" inputMode="numeric" value={positions} onChange={(e) => setPositions(e.target.value)} />
              <p className="mt-1 text-xs text-gray-600">The opening closes by itself when they are filled.</p>
            </div>
            <div>
              <label htmlFor="op-deadline" className="label">Apply by</label>
              <input id="op-deadline" type="date" className="input" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
            </div>
            <fieldset>
              <legend className="label">Years of study (none ticked = any)</legend>
              <div className="flex flex-wrap gap-3">
                {[1, 2, 3, 4, 5].map((y) => (
                  <label key={y} className="flex min-h-[44px] items-center gap-2 text-sm font-bold text-gray-900">
                    <input type="checkbox" className="h-5 w-5 accent-[#8c1515]" checked={years.includes(y)} onChange={(e) => setYears(e.target.checked ? [...years, y].sort() : years.filter((x) => x !== y))} />
                    Year {y}
                  </label>
                ))}
              </div>
            </fieldset>
            <div>
              <label htmlFor="op-mincgpa" className="label">Minimum CGPA</label>
              <input id="op-mincgpa" className="input" inputMode="decimal" value={minCgpa} onChange={(e) => setMinCgpa(e.target.value)} placeholder="none" />
              <p className="mt-1 text-xs text-gray-600">Students see this rule openly. It is never part of the fit score.</p>
            </div>
            <label className="flex min-h-[44px] items-center gap-3 text-sm font-bold text-gray-900 md:col-span-2">
              <input type="checkbox" className="h-5 w-5 accent-[#8c1515]" checked={strict} onChange={(e) => setStrict(e.target.checked)} />
              Strict: refuse applications from students who do not meet the year, department or CGPA rules (otherwise they only see a warning)
            </label>
            <div>
              <label htmlFor="op-mode" className="label">Mode</label>
              <select id="op-mode" className="input" value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="">Not specified</option>
                <option value="on_campus">On campus</option>
                <option value="hybrid">Hybrid</option>
                <option value="remote">Remote</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="op-weeks" className="label">Weeks</label>
                <input id="op-weeks" className="input" inputMode="numeric" value={weeks} onChange={(e) => setWeeks(e.target.value)} />
              </div>
              <div>
                <label htmlFor="op-hours" className="label">Hours a week</label>
                <input id="op-hours" className="input" inputMode="numeric" value={hours} onChange={(e) => setHours(e.target.value)} />
              </div>
            </div>
            <div className="md:col-span-2">
              <label htmlFor="op-preferred" className="label">Nice-to-have skills</label>
              <input id="op-preferred" className="input" value={preferred} onChange={(e) => setPreferred(e.target.value)} placeholder="separated by commas" />
            </div>
          </div>
        </fieldset>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={() => router.push("/faculty/openings")}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy ? "Creating…" : "Create opening"}
          </button>
        </div>
      </form>
    </>
  );
}
