"use client";
// Manual entry for a `failed` certificate (REQ-037, API-008). The result always goes to review.
import { useState, type FormEvent, type KeyboardEvent } from "react";
import { X } from "lucide-react";
import { Dialog, useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { todayIst } from "@/lib/format";
import { isApiError } from "@/lib/problem";
import type { components } from "@/lib/types";
import { LEVELS, TYPES, capitalise } from "./reasons";

type Certificate = components["schemas"]["Certificate"];
type Manual = components["schemas"]["ManualCertificate"];
type Field = keyof Manual;

const REQUIRED = "This field is required.";

export interface ManualCertificateFormProps {
  certificate: Certificate | null;
  onClose: () => void;
  onSaved: (certificate: Certificate) => void;
}

export function ManualCertificateForm({ certificate, onClose, onSaved }: ManualCertificateFormProps) {
  const toast = useToast();
  const [form, setForm] = useState<Manual>({
    holder_name: certificate?.holder_name ?? "",
    title: certificate?.title ?? "",
    issuer: certificate?.issuer ?? "",
    issue_date: certificate?.issue_date ?? "",
    level: certificate?.level ?? "college",
    type: certificate?.type ?? "course",
    skills: certificate?.skills ?? [],
  });
  const [skillDraft, setSkillDraft] = useState("");
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [busy, setBusy] = useState(false);

  const set = <K extends Field>(k: K, v: Manual[K]) => setForm((f) => ({ ...f, [k]: v }));

  function addSkill() {
    const s = skillDraft.trim().toLowerCase();
    if (s && !form.skills.includes(s) && form.skills.length < 8) set("skills", [...form.skills, s]);
    setSkillDraft("");
  }

  function onSkillKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill();
    }
  }

  function validate(): Partial<Record<Field, string>> {
    const errs: Partial<Record<Field, string>> = {};
    (["holder_name", "title", "issuer", "issue_date"] as const).forEach((k) => {
      if (!String(form[k]).trim()) errs[k] = REQUIRED;
    });
    if (form.issue_date && form.issue_date > todayIst()) errs.issue_date = "Date cannot be in the future.";
    if (form.skills.length === 0) errs.skills = "Add at least one skill.";
    return errs;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!certificate) return;
    const errs = validate();
    setErrors(errs);
    const first = Object.keys(errs)[0];
    if (first) {
      document.getElementById(`manual-${first}`)?.focus();
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.put<Certificate>(`/certificates/${certificate.id}/manual`, form);
      toast.success("Details saved. A reviewer will check this certificate.");
      onSaved(data);
    } catch (err) {
      if (isApiError(err) && err.status === 422 && err.errors.length) {
        const mapped: Partial<Record<Field, string>> = {};
        err.errors.forEach((fe) => {
          const key = fe.field.split(/[.[]/)[0] as Field;
          mapped[key] = fe.message;
        });
        setErrors(mapped);
        document.getElementById(`manual-${Object.keys(mapped)[0]}`)?.focus();
      } else {
        toast.error("Couldn't save. Try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  const fieldError = (k: Field) =>
    errors[k] ? (
      <p id={`manual-${k}-error`} role="alert" className="mt-1 text-xs font-bold text-red-700">
        {errors[k]}
      </p>
    ) : null;
  const describe = (k: Field) => (errors[k] ? { "aria-invalid": true, "aria-describedby": `manual-${k}-error` } : {});

  return (
    <Dialog
      open={certificate !== null}
      onClose={onClose}
      title="Enter certificate details"
      description="We couldn't read this file automatically. A reviewer will check what you enter."
      footer={
        <>
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" form="manual-form" className="btn-primary" disabled={busy}>
            {busy ? "Saving…" : "Send for review"}
          </button>
        </>
      }
    >
      <form id="manual-form" onSubmit={onSubmit} noValidate className="grid gap-4 sm:grid-cols-2">
        {(
          [
            ["holder_name", "Name on certificate"],
            ["title", "Title"],
            ["issuer", "Issuer"],
          ] as const
        ).map(([k, label]) => (
          <div key={k} className={k === "title" ? "sm:col-span-2" : ""}>
            <label htmlFor={`manual-${k}`} className="label">
              {label}
            </label>
            <input id={`manual-${k}`} className="input" value={form[k]} onChange={(e) => set(k, e.target.value)} {...describe(k)} />
            {fieldError(k)}
          </div>
        ))}
        <div>
          <label htmlFor="manual-issue_date" className="label">
            Issue date
          </label>
          <input
            id="manual-issue_date"
            type="date"
            max={todayIst()}
            className="input"
            value={form.issue_date}
            onChange={(e) => set("issue_date", e.target.value)}
            {...describe("issue_date")}
          />
          {fieldError("issue_date")}
        </div>
        <div>
          <label htmlFor="manual-level" className="label">
            Level
          </label>
          <select id="manual-level" className="input" value={form.level} onChange={(e) => set("level", e.target.value as Manual["level"])}>
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {capitalise(l)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="manual-type" className="label">
            Type
          </label>
          <select id="manual-type" className="input" value={form.type} onChange={(e) => set("type", e.target.value as Manual["type"])}>
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {capitalise(t)}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="manual-skills" className="label">
            Skills (up to 8)
          </label>
          <div className="flex gap-2">
            <input
              id="manual-skills"
              className="input"
              value={skillDraft}
              placeholder="Type a skill and press Enter"
              onChange={(e) => setSkillDraft(e.target.value)}
              onKeyDown={onSkillKey}
              {...describe("skills")}
            />
            <button type="button" className="btn-secondary" onClick={addSkill} disabled={form.skills.length >= 8}>
              Add
            </button>
          </div>
          {fieldError("skills")}
          {form.skills.length > 0 ? (
            <ul className="mt-2 flex flex-wrap gap-2">
              {form.skills.map((s) => (
                <li key={s} className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 py-1 pl-3 pr-1 text-xs font-bold">
                  {s}
                  <button
                    type="button"
                    aria-label={`Remove ${s}`}
                    className="rounded-full p-1 hover:bg-gray-200"
                    onClick={() => set("skills", form.skills.filter((x) => x !== s))}
                  >
                    <X aria-hidden size={12} />
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </form>
    </Dialog>
  );
}
