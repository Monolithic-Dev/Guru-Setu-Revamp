"""Check that a branch only touches files its owner may edit.

Usage:
  python tools/check_ownership.py P2               # files changed vs origin/main, as P2
  python tools/check_ownership.py P2 --base main   # compare against another base
  python tools/check_ownership.py --who backend/app/ml/scorer.py
  python tools/check_ownership.py --list P4        # tracked files owned by P4

Rules come from tools/ownership.txt (last match wins). Exit code 1 if any changed
file belongs to someone else. ALL files are allowed for everyone; GEN files are
allowed but flagged: only change them by re-running their generator.
"""
import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_FILE = ROOT / "tools" / "ownership.txt"


def load_rules():
    rules = []
    for line in RULES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pattern, owner = line.split()
            rules.append((pattern, owner))
    return rules


def matches(pattern, path):
    if pattern.endswith("/"):
        return path.startswith(pattern)
    if "*" in pattern:
        escaped = pattern.replace("[", "[[]")  # Next.js [id] folders are literal
        return fnmatch.fnmatchcase(path, escaped)
    return path == pattern


def owner_of(path, rules):
    owner = None
    for pattern, who in rules:
        if matches(pattern, path):
            owner = who
    return owner


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("me", nargs="?", help="P1, P2, P3 or P4")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--who")
    ap.add_argument("--list")
    args = ap.parse_args()
    rules = load_rules()

    if args.who:
        print(owner_of(args.who.replace("\\", "/"), rules))
        return 0
    if args.list:
        for path in git("ls-files").splitlines():
            if owner_of(path, rules) == args.list:
                print(path)
        return 0
    if not args.me:
        ap.error("give your owner id, e.g. P2")

    changed = set(git("diff", "--name-only", f"{args.base}...HEAD").splitlines())
    changed |= set(git("diff", "--name-only").splitlines())             # unstaged
    changed |= set(git("diff", "--name-only", "--cached").splitlines())  # staged
    foreign, generated = [], []
    for path in sorted(p for p in changed if p):
        who = owner_of(path, rules)
        if who in (args.me, "ALL"):
            continue
        (generated if who == "GEN" else foreign).append((path, who))

    for path, _ in generated:
        print(f"note  {path}: generated file; make sure you only re-ran its generator")
    for path, who in foreign:
        print(f"BLOCK {path}: owned by {who}; ask {who} to make this change")
    if foreign:
        return 1
    print(f"ok    {len(changed)} changed file(s), all owned by {args.me} (or shared)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
