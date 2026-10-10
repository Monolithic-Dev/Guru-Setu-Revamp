"""EVAL-03: does the hybrid scorer rank better than a keyword baseline?

    python -m scripts.eval_match

Scores nDCG@10 and P@5 for the hybrid scorer and for the Jaccard keyword
baseline that the earlier prototype used, over the relevance labels in
`seed/labels/match_labels.csv` (P4 labels 0/1/2 before seeing any score).

Reporting rule (REQ-026): both numbers are printed as measured. If the hybrid
does not win, that is the result - it is never re-tuned against these labels,
because a scorer tuned on its own test set measures nothing.
"""

from __future__ import annotations

import argparse
import csv
import math
import pathlib
from collections import defaultdict
from typing import Any

from app.core.database import run_read
from app.ml import scorer
from app.ml.embedding import cosine
from app.ml.settings import get_settings
from app.repos import match_repo

LABELS_PATH = pathlib.Path("seed/labels/match_labels.csv")


def load_labels(path: pathlib.Path) -> dict[str, dict[str, int]]:
    """{student_id: {opening_id: relevance}} from the label CSV."""
    if not path.exists():
        raise SystemExit(
            f"{path} not found. P4 produces it in T1.P4.3; EVAL-03 cannot run "
            "without labels, and inventing them would make the number meaningless."
        )
    labels: dict[str, dict[str, int]] = defaultdict(dict)
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            labels[row["student_id"]][row["opening_id"]] = int(row["relevance"])
    return labels


def dcg(relevances: list[int]) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def ndcg_at_k(ranked: list[str], truth: dict[str, int], k: int = 10) -> float:
    gains = [truth.get(oid, 0) for oid in ranked[:k]]
    ideal = sorted(truth.values(), reverse=True)[:k]
    best = dcg(ideal)
    return (dcg(gains) / best) if best else 0.0


def precision_at_k(ranked: list[str], truth: dict[str, int], k: int = 5) -> float:
    if not ranked:
        return 0.0
    hits = sum(1 for oid in ranked[:k] if truth.get(oid, 0) > 0)
    return hits / min(k, len(ranked))


def jaccard_baseline(
    student_skills: set[str], openings: list[dict[str, Any]]
) -> list[str]:
    """The prototype's method: overlap of skill name sets, no trust, no
    similarity, no embeddings."""
    scored = []
    for row in openings:
        required = set(row.get("required") or [])
        union = student_skills | required
        overlap = len(student_skills & required) / len(union) if union else 0.0
        scored.append((overlap, row["opening_id"]))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [oid for _, oid in scored]


def hybrid_ranking(
    tx, student_id: str, openings: list[dict[str, Any]]
) -> list[str]:
    skills, sources = match_repo.student_skills(tx, student_id)
    idf_values = match_repo.idf_table(tx)
    student_vec = match_repo.student_embedding(tx, student_id) or []
    names = {c for row in openings for c in (row.get("required") or [])} | set(skills)
    similar = match_repo.similar_pairs(tx, sorted(names))
    cfg = scorer.FitConfig.from_settings(get_settings())

    scored = []
    for row in openings:
        semantic = cosine(student_vec, list(row.get("embedding") or []))
        fit = scorer.score(
            list(row.get("required") or []), idf_values, skills, similar,
            semantic, cfg, sources,
        )
        scored.append((fit.score, row["opening_id"]))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [oid for _, oid in scored]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default=str(LABELS_PATH))
    parser.add_argument("--out", default="../docs/plan/eval-results.md")
    args = parser.parse_args(argv)

    labels = load_labels(pathlib.Path(args.labels))

    def work(tx):
        openings = match_repo.required_by_open_openings(tx)
        rows = []
        for student_id, truth in sorted(labels.items()):
            hybrid = hybrid_ranking(tx, student_id, openings)
            skills, _ = match_repo.student_skills(tx, student_id)
            base = jaccard_baseline(set(skills), openings)
            rows.append(
                {
                    "student_id": student_id,
                    "hybrid_ndcg": ndcg_at_k(hybrid, truth),
                    "hybrid_p5": precision_at_k(hybrid, truth),
                    "base_ndcg": ndcg_at_k(base, truth),
                    "base_p5": precision_at_k(base, truth),
                }
            )
        return rows

    rows = run_read(work)
    if not rows:
        print("no labelled students found")
        return 1

    def mean(key: str) -> float:
        return sum(r[key] for r in rows) / len(rows)

    hybrid_ndcg, base_ndcg = mean("hybrid_ndcg"), mean("base_ndcg")
    hybrid_p5, base_p5 = mean("hybrid_p5"), mean("base_p5")

    print(f"\nEVAL-03 over {len(rows)} labelled students\n")
    print(f"{'scorer':<22}{'nDCG@10':>10}{'P@5':>10}")
    print(f"{'hybrid (MDL-03)':<22}{hybrid_ndcg:>10.3f}{hybrid_p5:>10.3f}")
    print(f"{'jaccard baseline':<22}{base_ndcg:>10.3f}{base_p5:>10.3f}")
    verdict = "hybrid wins" if hybrid_ndcg > base_ndcg else "baseline is not beaten"
    print(f"\nresult: {verdict} (reported as measured, REQ-026)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
