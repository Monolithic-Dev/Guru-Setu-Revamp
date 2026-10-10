// [MOCK] P3 sample payloads, served by useApi only when NEXT_PUBLIC_USE_FIXTURES=1 (phases README rule 2).
// Shapes follow openapi.yaml; values follow the seed personas (backend §10). Pages never import this file,
// so `grep -rn "fixtures/" src/app` stays empty (G3) and going live is a build flag, not a code change.
import type { components } from "@/lib/types";
import api007 from "./API-007.json";
import api009 from "./API-009.json";
import api012 from "./API-012.json";
import api013 from "./API-013.json";
import api016 from "./API-016.json";
import api020 from "./API-020.json";
import api024 from "./API-024.json";
import api025 from "./API-025.json";
import api039 from "./API-039.json";

type S = components["schemas"];

export const fixtures = {
  myCertificates: api007 as unknown as S["Certificate"][],
  reviewQueue: api009 as unknown as S["ReviewItem"][],
  openings: api012 as unknown as S["OpeningSummary"][],
  opening: api013 as unknown as S["Opening"],
  candidates: api016 as unknown as S["Candidate"][],
  why: api020 as unknown as S["WhyGraph"],
  mentees: api024 as unknown as S["MenteeRow"][],
  menteeOverview: api025 as unknown as S["MenteeOverview"],
  reminders: api039 as unknown as S["Reminder"][],
};

/** GET path patterns ([param] = one segment) → sample payload. First match wins. */
export const fixtureRoutes: [string, unknown][] = [
  ["/me/certificates", fixtures.myCertificates],
  ["/me/mentees", fixtures.mentees],
  ["/me/reminders", fixtures.reminders],
  ["/reviews/certificates", fixtures.reviewQueue],
  ["/mentees/[id]/overview", fixtures.menteeOverview],
  ["/openings", fixtures.openings],
  ["/openings/[id]/candidates", fixtures.candidates],
  ["/openings/[id]/why", fixtures.why],
  ["/openings/[id]", fixtures.opening],
];
