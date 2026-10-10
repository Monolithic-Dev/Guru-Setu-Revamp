# Contributing: branches, pull requests, merging
Purpose:      One workflow for four builders: one feature branch each, pull requests only, rebase-and-merge by the lead.
Audience:     P1-P4 and the lead (the person who merges).
Depends on:   docs/phases/parallel-work.md (file ownership), tools/ownership.txt
Status:       Draft v1

---

## 1. Rules (binding)

1. **One feature branch per person**, created from the latest `main` after the scaffold commit (phase-0 T0.P2.0):

   | Person | Branch |
   |---|---|
   | P1 | `feature/p1-ml-fit` |
   | P2 | `feature/p2-backend-core` |
   | P3 | `feature/p3-frontend-mentor` |
   | P4 | `feature/p4-seed-coordinator` |

2. **Never push to `main`. Never merge your own PR.** You only *open* pull requests. The lead reviews and merges.
3. **Open a PR only at a checkpoint** the lead announces (§4), or when your whole work is done. Do not open PRs on your own schedule.
4. **The lead merges with "Rebase and merge" only** (no merge commits, no squash). Every commit on your branch lands on `main` as written, so each commit must stand on its own.
5. **Edit only files you own** (`tools/ownership.txt`). Run `python tools/check_ownership.py P<n>` before every push. If a change needs a file someone else owns, ask the owner in chat.
6. **No secrets and no real data**: never commit `.env`, uploads, `node_modules`, `.next`, exports.

## 2. Commit rules

- Small, working commits. Message format: `T<phase>.<person>.<n> <REQ-ids>: <what changed>`, for example `T2.P1.2 REQ-002: add duplicate checks to verification`.
- No merge commits on your branch. Set once: `git config pull.rebase true`.
- No "wip", "fix", "asdf" commits. If you must fix an earlier commit, use `git commit --fixup <sha>` and, before opening the PR, `git rebase -i --autosquash origin/main`.
- Contract changes (`openapi.yaml`, `schema.cypher`, extraction schema) are their own commit, with the message prefix `CONTRACT:` (parallel-work §5).

## 3. Daily loop

```
git fetch origin
git rebase origin/main                      # stay current; resolve conflicts only in files you own
# ... work, commit small ...
python tools/check_ownership.py P<n>        # must print "ok"
<your tests>                                # pytest -q <your files>, or npm run lint && npx tsc --noEmit
git push --force-with-lease origin feature/p<n>-<name>
```

`--force-with-lease` is allowed on your own feature branch only, never on `main`.

If a rebase conflicts in a file you do not own, stop. You edited something you should not have, or the owner changed a contract. Ask the owner or the lead.

## 4. Checkpoints (when PRs are opened)

Gates need code on `main` (the plan's gates are checked "on `main`"), and the stubs at the seams (parallel-work §4) must reach the other builders. So the lead announces **checkpoints**. At each one, every person opens a PR from their same branch and the lead merges them.

| Checkpoint | Hour | What must be in the PR |
|---|---|---|
| C0 | 0:20 | **Scaffold only**, pushed straight to `main` by P2 (the one allowed direct push; T0.P2.0). Nobody else branches before it. |
| C1 | ~2:30 | All seam stubs with final signatures; `core/`, `deps`, UI kit, seed skeleton |
| G1 | 4:00 | Phase 1 done |
| G2 | 7:00 | Phase 2 done (upload to Certified works; a session saves) |
| G3 | 10:00 | Phase 3 done (core freeze; index §7 passes) |
| Freeze | 12:30 | Add-on A items that passed their gate |
| Final | 14:30 | Bug fixes only; submission tag |

**To open a checkpoint PR:**
1. `git fetch origin && git rebase origin/main`
2. `python tools/check_ownership.py P<n>` prints `ok`; your tests pass.
3. `git push --force-with-lease origin <your branch>`
4. Open a PR into `main`. Title: `P<n> <checkpoint>: <summary>`. Fill in the template. Tag the lead. **Do not merge it.**
5. After the lead merges: `git fetch origin && git rebase origin/main && git push --force-with-lease origin <your branch>`. Git drops your commits that are already on `main`. Keep working on the same branch.

If the team wants only **one** final PR per person, delete this section. The cost: nobody sees anyone else's code until the end, and the seam stubs, G1-G3 and the hour-9:15 dry run cannot happen on `main`.

## 5. Lead checklist (per merge)

1. Confirm the PR touches only that person's files (the ownership check output is in the PR).
2. Merge with **Rebase and merge**. Suggested order at each checkpoint: P2 (core), P1, P3, P4. Files are disjoint, so the order only matters for the seam stubs.
3. On `main`: `docker compose up -d --build`, `docker compose exec backend python -m scripts.seed --reset`, `docker compose exec -e TODAY_OVERRIDE=2026-10-10 backend pytest -q`. `main` must always boot. If it does not, tell the author immediately.
4. Announce "merged, rebase now" in chat.

**GitHub settings to apply once** (manual, repository Settings):
- Branch protection on `main`: require a pull request; block force pushes and deletion; allow admin bypass for the C0 scaffold push.
- Allow **only** "Rebase and merge" (turn off merge commits and squash).
- Turn **off** "Automatically delete head branches" (branches live for the whole build).
- Optional: require the status check once a CI workflow exists (none is planned in this build).

## 6. Status board

Update only your own rows in `docs/phases/status.md`, in your branch, in a separate small commit. On a rebase conflict in that file, keep both sides.
