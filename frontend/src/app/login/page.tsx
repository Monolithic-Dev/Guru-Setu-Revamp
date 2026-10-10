"use client";
// SCR-01 Login (FLOW-01, REQ-031). Styled after the earlier GuruSetu login screen.
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useRef, useState, type FormEvent } from "react";
import { ChevronRight, Eye, EyeOff, Lock, Mail } from "lucide-react";
import { api } from "@/lib/api";
import { HOME_BY_ROLE } from "@/lib/nav";
import { isApiError } from "@/lib/problem";
import { saveSession } from "@/lib/session";
import type { components } from "@/lib/types";

type TokenResponse = components["schemas"]["TokenResponse"];

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const expired = params.get("expired") === "1";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    const errs: typeof fieldErrors = {};
    if (!email.trim()) errs.email = "Enter your email.";
    if (!password) errs.password = "Enter your password.";
    setFieldErrors(errs);
    if (errs.email) return emailRef.current?.focus();
    if (errs.password) return passwordRef.current?.focus();

    setBusy(true);
    try {
      const { data } = await api.post<TokenResponse>("/auth/login", { email: email.trim(), password });
      saveSession({ token: data.access_token, role: data.role, userId: data.user_id });
      router.replace(HOME_BY_ROLE[data.role]);
    } catch (err) {
      if (isApiError(err) && err.status === 401) {
        setFormError("Email or password is incorrect.");
        passwordRef.current?.focus();
      } else if (isApiError(err) && err.status === 429) {
        setFormError("Too many attempts. Try again in a minute.");
      } else if (isApiError(err) && err.status === 0) {
        setFormError("You're offline or the server can't be reached.");
      } else {
        setFormError("Something went wrong. Try again.");
      }
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col bg-white">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-12">
        <div className="mb-10 text-center">
          <h1 className="text-5xl font-black tracking-tight text-brand">GuruSetu</h1>
          <p className="mt-3 text-xs font-bold uppercase tracking-[0.25em] text-gray-600">
            Mentoring built on proof
          </p>
        </div>

        {expired ? (
          <div role="alert" className="mb-5 rounded-2xl border border-gold-line bg-gold-soft px-4 py-3 text-sm font-bold text-gold-ink">
            Session expired, please log in again.
          </div>
        ) : null}

        <form onSubmit={onSubmit} noValidate className="space-y-5">
          <div>
            <label htmlFor="email" className="label">
              Email
            </label>
            <div className="relative">
              <Mail aria-hidden size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-brand" />
              <input
                ref={emailRef}
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@demo.gurusetu"
                aria-invalid={!!fieldErrors.email}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 py-4 pl-12 pr-4 text-sm font-bold text-gray-900 placeholder-gray-500 outline-none focus:border-brand focus:bg-white focus:ring-2 focus:ring-brand/20"
              />
            </div>
            {fieldErrors.email ? (
              <p id="email-error" role="alert" className="mt-1 text-xs font-bold text-red-700">
                {fieldErrors.email}
              </p>
            ) : null}
          </div>

          <div>
            <label htmlFor="password" className="label">
              Password
            </label>
            <div className="relative">
              <Lock aria-hidden size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-brand" />
              <input
                ref={passwordRef}
                id="password"
                type={show ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={!!fieldErrors.password || !!formError}
                aria-describedby={fieldErrors.password ? "password-error" : formError ? "form-error" : undefined}
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 py-4 pl-12 pr-14 text-sm font-bold text-gray-900 outline-none focus:border-brand focus:bg-white focus:ring-2 focus:ring-brand/20"
              />
              <button
                type="button"
                onClick={() => setShow((s) => !s)}
                aria-label={show ? "Hide password" : "Show password"}
                aria-pressed={show}
                className="absolute right-2 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full text-brand hover:bg-brand-tint"
              >
                {show ? <EyeOff aria-hidden size={20} /> : <Eye aria-hidden size={20} />}
              </button>
            </div>
            {fieldErrors.password ? (
              <p id="password-error" role="alert" className="mt-1 text-xs font-bold text-red-700">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>

          {formError ? (
            <p id="form-error" role="alert" className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-800">
              {formError}
            </p>
          ) : null}

          <button type="submit" disabled={busy} className="btn-primary w-full py-4">
            {busy ? "Logging in…" : "Log in"}
            {!busy ? (
              <span aria-hidden className="rounded-full border border-white/30 bg-white/20 p-1">
                <ChevronRight size={16} strokeWidth={3} />
              </span>
            ) : null}
          </button>
        </form>

        <p className="mt-10 text-center text-xs font-medium text-gray-600">
          Demo accounts only. All data is synthetic (Sample data).
        </p>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
