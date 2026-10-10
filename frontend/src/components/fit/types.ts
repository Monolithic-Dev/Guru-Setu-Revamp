/**
 * Shapes the fit components consume. Owner: P1.
 *
 * These mirror the `Fit`, `FitChip` and `SkillGap` schemas in openapi.yaml.
 * Once `lib/types.ts` is generated (GEN, from the same contract), these can be
 * replaced by imports from it; they are written out here so the components
 * compile before that file exists.
 */

export type FitVerdict = "ready" | "close" | "not_yet";

export type ChipKind = "matched" | "claimed_only" | "near" | "missing";

export interface ChipSource {
  evidence_id: string;
  title: string;
}

export interface FitChip {
  concept: string;
  kind: ChipKind;
  trust_level: number | null;
  via?: string | null;
  similarity?: number | null;
  source?: ChipSource | null;
}

export interface FitComponents {
  semantic: number;
  skill: number;
  concept: number;
}

export interface FitGain {
  concept: string;
  score_if_certified: number;
}

export interface Fit {
  opening_id: string;
  student_id: string;
  score: number;
  components: FitComponents;
  weights: FitComponents;
  verdict: FitVerdict;
  verdict_text: string;
  chips: FitChip[];
  gains: FitGain[];
  note?: string | null;
}

export interface SkillGap {
  concept: string;
  openings_unlocked: number;
  total_gain: number;
}

export type ApplicationStatus =
  | "pending"
  | "shortlisted"
  | "accepted"
  | "rejected"
  | "completed";
