"""Build the committed extraction cache (T2.P1.3).

    python -m scripts.build_extraction_cache seed/certificates seed/demo_uploads

Calls MDL-01 once per file and writes `extraction_cache/<sha256>.json`. The
cache is committed so the demo runs with the network off (NFR-04, TEST-52).

Throttling matters here. The Groq free tier allows 8,000 tokens per minute and
one certificate costs about 2,200, so roughly three files per minute. Without
pacing, a 29-file run would spend most of its time being rate-limited, so the
script waits between calls and backs off on a 429.

Honesty rule (ai-system 2.4): EVAL-01 is scored on *raw* model output. This
script records what the model actually said in `--report`; corrections to the
cache are made afterwards, by hand, and noted in the label CSV's
`cache_corrected` column.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

from app.ml import extraction

MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
}

# ~2,200 tokens per call against an 8,000 token/minute budget leaves room for
# three calls a minute; 21 s between calls keeps a safety margin.
DEFAULT_DELAY_S = 21.0
MAX_429_RETRIES = 3


def media_type_of(path: pathlib.Path) -> str | None:
    return MEDIA_TYPES.get(path.suffix.lower())


def collect(dirs: list[str]) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for raw in dirs:
        root = pathlib.Path(raw)
        if not root.exists():
            print(f"  ! {root} does not exist, skipping", file=sys.stderr)
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and media_type_of(path):
                files.append(path)
    return files


def extract_with_backoff(data: bytes, media_type: str, delay: float):
    """One file, retrying a rate-limit response with increasing waits."""
    for attempt in range(1, MAX_429_RETRIES + 1):
        result = extraction.call_groq(data, media_type)
        if isinstance(result, extraction.Extraction):
            return result
        detail = (result.detail or "").lower()
        if "ratelimit" not in detail and "429" not in detail:
            return result
        wait = delay * attempt
        print(f"      rate limited, waiting {wait:.0f}s (attempt {attempt})")
        time.sleep(wait)
    return extraction.ExtractionFailed(detail="rate limited after retries")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dirs", nargs="+", help="directories of certificate files")
    parser.add_argument("--force", action="store_true",
                        help="re-call the model for files already cached")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_S,
                        help="seconds to wait between calls (free-tier pacing)")
    parser.add_argument("--report", default="",
                        help="write raw model output here for EVAL-01 scoring")
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after N uncached files (useful for a dry run)")
    args = parser.parse_args(argv)

    files = collect(args.dirs)
    if not files:
        print("no files found", file=sys.stderr)
        return 1

    print(f"{len(files)} file(s) found")
    raw_report: dict[str, dict] = {}
    cached = called = failed = 0

    for path in files:
        data = path.read_bytes()
        digest = extraction.sha256_hex(data)
        media_type = media_type_of(path) or "image/png"

        if not args.force and extraction.cache_path(digest).exists():
            print(f"  = {path.name} (cached)")
            cached += 1
            continue

        if args.limit and called >= args.limit:
            print(f"  . {path.name} (limit reached)")
            continue

        if called:
            time.sleep(args.delay)

        print(f"  > {path.name} ... ", end="", flush=True)
        result = extract_with_backoff(data, media_type, args.delay)
        called += 1

        if isinstance(result, extraction.Extraction):
            extraction.write_cache(digest, result)
            raw_report[path.name] = result.model_dump(exclude={"source"})
            print("ok")
        else:
            failed += 1
            print(f"FAILED ({result.detail})")

    if args.report and raw_report:
        out = pathlib.Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(raw_report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"raw output written to {out} (score EVAL-01 against this, not the cache)")

    print(f"\ncached: {cached}  called: {called}  failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
