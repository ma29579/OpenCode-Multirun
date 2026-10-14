#!/usr/bin/env python3
"""Statistics for the pilot study: mean, 95% bootstrap interval and a permutation test against the baseline.

    tools/analyze.py results/study-A [results/study-B ...]

Reads <results>/lint.csv of every directory (written by tools/schema_lint.py) and groups the runs by task,
model and scenario. For every group and every rate (db_rate, std_rate, des_rate) it prints the mean with the
interval and the p-value of the difference to the scenario `baseline` (two-sided permutation test, Holm
correction over the scenarios of one task and model). Writes analysis.csv to the first directory.

With few runs per group the interval is narrow by construction and no p-value can be small: two runs against
two runs give at best p = 0.33. Treat the output as effect sizes, not as proof.
"""
from __future__ import annotations

import csv
import itertools
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

METRICS = ("db_rate", "std_rate", "des_rate")
BASELINE = "baseline"
BOOTSTRAPS = 2000
PERMUTATIONS = 10000
EXACT_LIMIT = 14          # up to this many runs in total all permutations are enumerated


def interval(values: list[float], rng: random.Random) -> tuple[float, float]:
    means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(BOOTSTRAPS))
    return means[int(0.025 * BOOTSTRAPS)], means[int(0.975 * BOOTSTRAPS) - 1]


def permutation_p(a: list[float], b: list[float], rng: random.Random) -> float:
    """Two-sided p-value of the difference of the means."""
    pooled, n = a + b, len(a)
    observed = abs(statistics.mean(a) - statistics.mean(b))
    if len(pooled) <= EXACT_LIMIT:
        splits = list(itertools.combinations(range(len(pooled)), n))
    else:
        splits = [tuple(rng.sample(range(len(pooled)), n)) for _ in range(PERMUTATIONS)]
    hits = 0
    for idx in splits:
        left = [pooled[i] for i in idx]
        right = [v for i, v in enumerate(pooled) if i not in idx]
        hits += abs(statistics.mean(left) - statistics.mean(right)) >= observed - 1e-12
    return hits / len(splits)


def holm(p_values: dict[str, float]) -> dict[str, float]:
    adjusted, running = {}, 0.0
    for rank, (key, p) in enumerate(sorted(p_values.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, p * (len(p_values) - rank)))
        adjusted[key] = running
    return adjusted


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dirs = [Path(a) for a in sys.argv[1:]]
    groups: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for d in dirs:
        path = d / "lint.csv"
        if not path.exists():
            sys.exit(f"error: {path} not found (run tools/schema_lint.py first)")
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["applied"] != "1" or row["prompt"] == "review-schema":
                    continue
                key = (row["prompt"], row["model"].split("/")[-1], row["label"])
                for metric in METRICS:
                    if row[metric] != "":
                        groups[key][metric].append(float(row[metric]))

    rng = random.Random(1)
    out_rows = []
    tasks = sorted({(p, m) for p, m, _ in groups})
    for prompt, model in tasks:
        print(f"\n{prompt} / {model}")
        print(f"{'scenario':<20}" + "".join(f"{m[:-5].upper():>26}" for m in METRICS))
        scenarios = sorted({s for p, m, s in groups if (p, m) == (prompt, model)})
        base = groups.get((prompt, model, BASELINE), {})
        stats: dict[str, dict[str, tuple]] = {}
        for metric in METRICS:
            raw = {s: permutation_p(groups[(prompt, model, s)][metric], base[metric], rng)
                   for s in scenarios if s != BASELINE and groups[(prompt, model, s)][metric] and base.get(metric)}
            adjusted = holm(raw)
            for s in scenarios:
                values = groups[(prompt, model, s)][metric]
                if not values:
                    continue
                low, high = interval(values, rng)
                stats.setdefault(s, {})[metric] = (len(values), statistics.mean(values), low, high,
                                                    raw.get(s), adjusted.get(s))
        for s in scenarios:
            cells = []
            for metric in METRICS:
                st = stats.get(s, {}).get(metric)
                if not st:
                    cells.append(f"{'-':>26}")
                    continue
                n, mean, low, high, p, p_adj = st
                flag = "" if p_adj is None else (f" p={p_adj:.2f}" + ("*" if p_adj < 0.05 else ""))
                cells.append(f"{mean:>6.2f} [{low:.2f},{high:.2f}] n={n}{flag}".rjust(26))
                out_rows.append({"prompt": prompt, "model": model, "scenario": s, "metric": metric, "n": n,
                                 "mean": f"{mean:.3f}", "ci_low": f"{low:.3f}", "ci_high": f"{high:.3f}",
                                 "p_vs_baseline": "" if p is None else f"{p:.3f}",
                                 "p_holm": "" if p_adj is None else f"{p_adj:.3f}"})
            print(f"{s:<20}" + "".join(cells))

    target = dirs[0] / "analysis.csv"
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"\nwritten to {target}  (mean [95% bootstrap interval], p: Holm-corrected permutation test vs. baseline, * p < 0.05)")


if __name__ == "__main__":
    main()
