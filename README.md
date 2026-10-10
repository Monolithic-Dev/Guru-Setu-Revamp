# GuruSetu: Verified Mentorship Graph

**Mentoring built on proof.** A student's verified achievements find the right research guide. Every mentoring session is recorded and tracked in about two minutes. The college gets its accreditation evidence as a by-product.

Built for the **Genesis Hackathon, Campus Problems track**. This extends GuruSetu, an earlier prototype by members of our team (see [Disclosure](#disclosure)).

> **Status:** specification complete, implementation starting. The `backend/` and `frontend/` folders are added at hour 0 of the build. All data is synthetic.

---

## The problem

- **Skills are self-claimed.** Anyone can type "PyTorch" on a profile, and faculty find research students by word of mouth.
- **Mentoring runs on paper.** Each faculty mentor looks after 10–20 students and must meet them at least twice a semester, recorded in signed registers. Nobody can see which mentee hasn't been met, or what was promised last time.
- **Evidence is compiled by hand.** Before every NAAC cycle, departments spend weeks rebuilding mentor ratios, issues raised and resolved, and student achievements.

## What it does

| Module | What happens |
|---|---|
| **Verify** | A student uploads a certificate. An LLM extracts the fields. Deterministic checks (duplicate hash, name match, known issuer, valid date) decide whether it is **Certified** or goes to a faculty review queue. |
| **Match** | **Fit Check** for every research opening gives an explained score from verified skills, plus what is proven, only claimed, or missing. Students apply; faculty see ranked applicants. |
| **Mentor** | The HOD allots mentors. Mentors log individual or group sessions with attendance, topics, private notes, action items and issues. Mentees confirm attendance digitally. |
| **Track** | The mentor home flags who needs attention, and why (not met in 45+ days, overdue action, stale issue). **Mentee 360** shows skills, academics and the whole mentoring timeline on one page. |
| **Evidence** | HOD and IQAC dashboards show coverage, meeting compliance and issue resolution live. A one-click **draft** XLSX evidence pack contains aggregates only and **never** private notes. |

## Tech stack

FastAPI (Python 3.12) · Neo4j 5 (graph + vector index) · Next.js 14 + Tailwind · `all-MiniLM-L6-v2` embeddings · Claude (vision extraction, structured output) · Docker Compose.

The demo also runs **fully offline** (`LLM_PROVIDER=none`), using cached extractions and manual entry.

## Quick start

> Requires Docker with Compose v2. These commands work once `backend/` and `frontend/` are in the repo.

```bash
cp docs/10-devops/env.example .env        # set NEO4J_PASSWORD and JWT_SECRET_KEY
                                          # add ANTHROPIC_API_KEY, or set LLM_PROVIDER=none
docker compose up -d --build
docker compose exec backend python -m scripts.seed --reset
```

Open http://localhost:3000. The demo accounts are synthetic, and every password is `Demo@123`:

| Role | Email |
|---|---|
| Student | `aarav@demo.gurusetu` |
| Faculty mentor | `meera@demo.gurusetu` |
| HOD | `suresh@demo.gurusetu` |
| IQAC | `kavya@demo.gurusetu` |

Run the tests with `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q`. Every other command is in [environments-and-deployment.md](docs/10-devops/environments-and-deployment.md).

## Documentation

The specification pack is the source of truth for the build:

| Start here | |
|---|---|
| [docs/00-index.md](docs/00-index.md) | Document map, ID registry, assumptions, end-to-end scenario |
| [AGENTS.md](AGENTS.md) | Rules and read order for coding agents (Claude Code, Cursor) |
| [Product requirements](docs/01-product/prd.md) | Requirements with acceptance criteria, non-goals, primary flow |
| [Architecture](docs/02-architecture/architecture.md) | Components, decisions, project structure |
| [Backend](docs/04-backend/backend.md) · [OpenAPI](docs/04-backend/openapi.yaml) · [Graph schema](docs/04-backend/schema.cypher) | Data model, API, business rules |
| [AI system](docs/06-ai/ai-system.md) | Extraction, verification, fit scoring, evaluation |
| [Frontend & UX](docs/05-frontend/ux-flows.md) | Screens, flows, components |
| [Security & privacy](docs/08-security/security-and-privacy.md) | Access rules, privacy matrix, threat model |
| [Test strategy](docs/11-quality/test-strategy.md) | Tests, failure modes, QA checklist |
| [Phase plan](docs/phases/README.md) · [Status](docs/phases/status.md) | Hour-by-hour tasks per person, gates, add-ons, freeze |
| [Team plan](docs/plan/prd-v2-and-15h-plan.md) | Demo story, disclosure, pitch material |

## Principles

- **Fit, never rank.** Scores describe one student against one opening. There are no leaderboards and no ratings of faculty.
- **Private by default.** Session notes are visible only to the mentor who wrote them, and are excluded from every dashboard and export.
- **Honest labels.** The UI marks what is Certified versus Claimed, what is a DRAFT, and what is sample data. Accreditation criterion codes are drafts until checked against the official NAAC manual.
- **Synthetic data only.** No real student data is stored or demoed.

## Disclosure

This project extends **GuruSetu**, an earlier prototype by members of our team, exhibited at TechFair 2026.

For Genesis we are building the following as new work:
- certificate verification and the trust ladder;
- explainable Fit Check matching;
- the digital mentor-mentee system (allotment, session logs, action items, issues, tracking);
- the coordinator dashboards and draft evidence export;
- security fixes to the original code.

The earlier prototype's matching was keyword-based.

## License

[Apache License 2.0](LICENSE)
