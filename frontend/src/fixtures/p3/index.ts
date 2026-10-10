// [MOCK] P3 fixtures, used only until each live endpoint lands (phases README rule 2).
// Shapes follow openapi.yaml; values follow the seed personas (backend §10). Remove imports at the gate.
import type { components } from "@/lib/types";
import api003 from "./API-003.json";
import api007 from "./API-007.json";
import api009 from "./API-009.json";
import api013 from "./API-013.json";
import api016 from "./API-016.json";
import api024 from "./API-024.json";
import api025 from "./API-025.json";

type S = components["schemas"];

export const fixtures = {
  studentProfile: api003 as unknown as S["StudentProfile"],
  myCertificates: api007 as unknown as S["Certificate"][],
  reviewQueue: api009 as unknown as S["ReviewItem"][],
  opening: api013 as unknown as S["Opening"],
  candidates: api016 as unknown as S["Candidate"][],
  mentees: api024 as unknown as S["MenteeRow"][],
  menteeOverview: api025 as unknown as S["MenteeOverview"],
};
