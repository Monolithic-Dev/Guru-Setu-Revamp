"use client";
// Session feedback (G3/B6, REQ-034, API-042): a present attendee rates a session. A second submission replaces the
// first. Only the student ever reads it, and the API does not send it back, so "sent" is local to this page.
import { useState } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { useToast } from "@/components/ui";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/problem";

type Rating = "helpful" | "not_helpful";
const COMMENT_MAX = 300;

export function SessionFeedback({ sessionId, label }: { sessionId: string; label: string }) {
  const toast = useToast();
  const [rating, setRating] = useState<Rating | null>(null);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<Rating | null>(null);
  const [error, setError] = useState<string | null>(null);
  const id = `fb-${sessionId}`;

  async function send() {
    if (!rating) return setError("Choose Helpful or Not helpful.");
    setBusy(true);
    setError(null);
    try {
      await api.post(`/sessions/${sessionId}/feedback`, { feedback: rating, comment: comment.trim() || null });
      setSent(rating);
      toast.success(sent ? "Feedback updated." : "Thanks for the feedback.");
    } catch (e) {
      setError(isApiError(e) && e.code === "NOT_PRESENT" ? "You were marked absent for this session." : "Couldn't send. Try again.");
    } finally {
      setBusy(false);
    }
  }

  const choice = (value: Rating, text: string, Icon: typeof ThumbsUp) => (
    <button
      type="button"
      aria-pressed={rating === value}
      onClick={() => setRating(value)}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-bold ${
        rating === value ? "border-brand bg-brand text-white" : "border-gray-300 bg-white text-gray-800 hover:border-brand"
      }`}
    >
      <Icon aria-hidden size={14} /> {text}
    </button>
  );

  return (
    <fieldset className="w-full space-y-2 rounded-2xl border border-brand-line bg-brand-tint p-3">
      <legend className="px-1 text-xs font-black uppercase tracking-widest text-brand">Was this session useful? · {label}</legend>
      <div className="flex flex-wrap gap-2">
        {choice("helpful", "Helpful", ThumbsUp)}
        {choice("not_helpful", "Not helpful", ThumbsDown)}
      </div>
      <div>
        <label htmlFor={`${id}-comment`} className="label">
          Comment <span className="font-normal normal-case text-gray-600">(optional, not shown to your mentor)</span>
        </label>
        <textarea
          id={`${id}-comment`}
          className="input min-h-[64px]"
          maxLength={COMMENT_MAX}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          aria-describedby={`${id}-count`}
        />
        <p id={`${id}-count`} className="mt-1 text-right text-xs text-gray-600">
          {comment.length}/{COMMENT_MAX}
        </p>
      </div>
      {error ? (
        <p role="alert" className="text-xs font-bold text-red-700">
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className="btn-primary" disabled={busy} onClick={() => void send()}>
          {busy ? "Sending…" : sent ? "Update feedback" : "Send feedback"}
        </button>
        {sent ? (
          <p role="status" className="text-xs font-bold text-green-800">
            Sent: {sent === "helpful" ? "Helpful" : "Not helpful"}. Sending again replaces it.
          </p>
        ) : null}
      </div>
    </fieldset>
  );
}
