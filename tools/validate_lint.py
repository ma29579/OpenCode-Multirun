#!/usr/bin/env python3
"""Validates the linter with a blind manual rating.

    tools/validate_lint.py sample results/study-A [results/study-B ...]
    tools/validate_lint.py agree  results/study-A

`sample` draws checks of the linter (up to three satisfied and three violated ones per rule) from the
runs of the given studies and writes two files to the first directory:

  rating-sample.csv  what the raters see: rule, object, path of the workspace and of the patch; neither the
                     verdict nor model and scenario
  rating-key.csv     the verdict of the linter plus model and scenario (keep it away from the raters)

Every rater fills the column rater_1 (and a second person rater_2) with 1 = the rule is satisfied for the
object, 0 = it is violated, - = the rule does not apply. `agree` compares the ratings with the linter:
percent agreement, Cohen's kappa linter vs. rater, rater vs. rater, and lists the disagreements.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PER_RULE = 3              # satisfied and violated checks drawn per rule
SEED = 1
SAMPLE_FIELDS = ("id", "rule", "rule_text", "task", "workspace", "patch", "scope", "object",
                 "rater_1", "rater_2", "comment")
RULE_LINE = re.compile(r"^- \*\*(?P<id>[A-Z]+-\d+) (?P<rest>.*)$")


def rule_texts() -> dict[str, str]:
    out = {}
    for path in (ROOT / "sample_guidelines").glob("*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            m = RULE_LINE.match(line)
            if m:
                out[m["id"]] = m["rest"].replace("**", "").strip()
    return out


def sample(dirs: list[Path]) -> None:
    pool: dict[str, list[dict]] = defaultdict(list)
    for d in dirs:
        with (d / "lint.csv").open(newline="", encoding="utf-8") as fh:
            runs = [r for r in csv.DictReader(fh) if r["applied"] == "1" and r["touched"] not in ("", "0")]
        for run in runs:
            run_dir = Path(run["run_dir"])
            items = json.loads((run_dir / "lint.json").read_text(encoding="utf-8")).get("items", [])
            for item in items:
                pool[item["rule"]].append({**item, "run": run})
    rng = random.Random(SEED)
    texts = rule_texts()
    rows, key = [], []
    for rule in sorted(pool):
        for ok in (True, False):
            candidates = [i for i in pool[rule] if i["ok"] == ok]
            for item in rng.sample(candidates, min(PER_RULE, len(candidates))):
                run = item["run"]
                rows.append({"rule": rule, "rule_text": texts.get(rule, ""), "task": run["prompt"],
                             "model": run["model"], "scenario": run["label"],
                             "workspace": str(Path(run["run_dir"]) / "workspace"),
                             "patch": str(Path(run["run_dir"]) / "changes.patch"),
                             "scope": item["scope"], "object": item["obj"], "ok": int(item["ok"])})
    rng.shuffle(rows)  # the order must not reveal the rule or the verdict
    out = dirs[0]
    with (out / "rating-sample.csv").open("w", newline="", encoding="utf-8") as fh_s, \
            (out / "rating-key.csv").open("w", newline="", encoding="utf-8") as fh_k:
        writer = csv.DictWriter(fh_s, fieldnames=SAMPLE_FIELDS, restval="", extrasaction="ignore")
        writer_k = csv.writer(fh_k)
        writer.writeheader()
        writer_k.writerow(("id", "linter_ok", "model", "scenario"))
        for n, row in enumerate(rows, 1):
            row["id"] = n
            writer.writerow(row)
            writer_k.writerow((n, row["ok"], row["model"], row["scenario"]))
    print(f"{len(rows)} checks of {len(pool)} rules written to {out}/rating-sample.csv (verdicts: rating-key.csv)")


def kappa(pairs: list[tuple[int, int]]) -> str:
    n = len(pairs)
    if n == 0:
        return "n/a"
    observed = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return "n/a" if expected == 1 else f"{(observed - expected) / (1 - expected):.2f}"


def rating(value: str) -> int | None:
    return {"1": 1, "0": 0}.get(value.strip())


def compare(name: str, pairs: list[tuple[int, int]]) -> None:
    if not pairs:
        print(f"{name}: no common ratings")
        return
    agree = sum(a == b for a, b in pairs) / len(pairs)
    print(f"{name}: n = {len(pairs)}, agreement {agree:.0%}, kappa {kappa(pairs)}")


def agree(directory: Path) -> None:
    with (directory / "rating-sample.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with (directory / "rating-key.csv").open(newline="", encoding="utf-8") as fh:
        linter = {r["id"]: int(r["linter_ok"]) for r in csv.DictReader(fh)}
    r1 = {r["id"]: rating(r["rater_1"]) for r in rows}
    r2 = {r["id"]: rating(r["rater_2"]) for r in rows}
    print(f"{sum(v is not None for v in r1.values())} checks rated by rater 1, "
          f"{sum(v is not None for v in r2.values())} by rater 2, {len(rows)} in the sample\n")
    compare("linter vs rater 1", [(linter[i], v) for i, v in r1.items() if v is not None])
    compare("linter vs rater 2", [(linter[i], v) for i, v in r2.items() if v is not None])
    compare("rater 1 vs rater 2", [(r1[i], r2[i]) for i in r1 if r1[i] is not None and r2[i] is not None])
    consensus = {i: (r1[i] if r2[i] is None or r1[i] == r2[i] else None) for i in r1 if r1[i] is not None}
    compare("linter vs consensus", [(linter[i], v) for i, v in consensus.items() if v is not None])
    wrong = Counter()
    print("\ndisagreements (linter vs consensus):")
    for row in rows:
        v = consensus.get(row["id"])
        if v is not None and v != linter[row["id"]]:
            wrong[row["rule"]] += 1
            print(f"  #{row['id']} {row['rule']} {row['object']}: linter {linter[row['id']]}, rater {v}  {row['comment']}")
    if wrong:
        print("\nper rule:", ", ".join(f"{r} {n}" for r, n in sorted(wrong.items())))
    else:
        print("  none")


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in ("sample", "agree"):
        sys.exit(__doc__)
    paths = [Path(a) for a in sys.argv[2:]]
    sample(paths) if sys.argv[1] == "sample" else agree(paths[0])


if __name__ == "__main__":
    main()
