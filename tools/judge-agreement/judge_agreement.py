#!/usr/bin/env python3
"""judge-agreement: check whether an automated grader (for example an LLM-as-judge) agrees with humans.

Before trusting a model-graded metric, compare its labels with a blind human-labeled sample.
This tool reports raw agreement, Cohen's kappa with a bootstrap confidence interval,
a confusion matrix, and per-label precision and recall, and says plainly whether the
grader is reliable enough to use.

Usage:
    python judge_agreement.py labels.csv --human human --model model
    python judge_agreement.py labels.csv --human human --model model --boot 5000 --seed 7

The CSV needs one row per item with a human label column and a model label column.
Labels can be any strings ("correct"/"incorrect", "1"/"0", "A"/"B"/"C").
Only the Python standard library is used.
"""
import argparse
import csv
import random
import sys
from collections import Counter

# Landis and Koch (1977) bands, the most commonly cited interpretation of kappa.
BANDS = [(0.0, "no better than chance"), (0.20, "slight"), (0.40, "fair"),
         (0.60, "moderate"), (0.80, "substantial"), (1.01, "almost perfect")]


def cohen_kappa(a, b):
    """Cohen's kappa for two equal-length label lists."""
    n = len(a)
    if n == 0:
        raise ValueError("no items")
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def bootstrap_ci(a, b, reps, seed, alpha=0.05):
    rng = random.Random(seed)
    n = len(a)
    stats = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        stats.append(cohen_kappa([a[i] for i in idx], [b[i] for i in idx]))
    stats.sort()
    lo = stats[int((alpha / 2) * reps)]
    hi = stats[min(reps - 1, int((1 - alpha / 2) * reps))]
    return lo, hi


def band(k):
    if k <= 0:
        return BANDS[0][1]
    for upper, name in BANDS[1:]:
        if k < upper:
            return name
    return BANDS[-1][1]


def load(path, hcol, mcol):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit("error: the CSV has no rows")
    for col in (hcol, mcol):
        if col not in rows[0]:
            raise SystemExit(f"error: column '{col}' not found; columns are {list(rows[0])}")
    pairs = [(r[hcol].strip(), r[mcol].strip()) for r in rows if r[hcol].strip() and r[mcol].strip()]
    skipped = len(rows) - len(pairs)
    return [p[0] for p in pairs], [p[1] for p in pairs], skipped


def report(h, m, reps, seed, threshold):
    n = len(h)
    labels = sorted(set(h) | set(m))
    agree = sum(x == y for x, y in zip(h, m)) / n
    k = cohen_kappa(h, m)
    lo, hi = bootstrap_ci(h, m, reps, seed)

    out = [f"items compared      {n}",
           f"raw agreement       {agree:.1%}",
           f"Cohen's kappa       {k:.3f}  (95% bootstrap CI {lo:.3f} to {hi:.3f}; {band(k)})",
           "",
           "confusion matrix (rows = human, columns = model)"]
    width = max(8, max(len(x) for x in labels) + 2)
    out.append(" " * width + "".join(f"{x:>{width}}" for x in labels))
    for r in labels:
        out.append(f"{r:<{width}}" + "".join(f"{sum(1 for a, b in zip(h, m) if a == r and b == c):>{width}}" for c in labels))
    out += ["", "per label (human labels as ground truth)"]
    for lab in labels:
        tp = sum(1 for a, b in zip(h, m) if a == lab and b == lab)
        pred = sum(1 for b in m if b == lab)
        true = sum(1 for a in h if a == lab)
        prec = tp / pred if pred else float("nan")
        rec = tp / true if true else float("nan")
        out.append(f"  {lab:<{width}} precision {prec:.2f}   recall {rec:.2f}   human count {true}")
    out.append("")
    if lo >= threshold:
        out.append(f"verdict: usable. The lower bound of kappa ({lo:.3f}) is at or above {threshold}.")
    else:
        out.append(f"verdict: do not trust this grader yet. The lower bound of kappa ({lo:.3f}) is below {threshold}. "
                   "Inspect the disagreements, tighten the grading instructions, and re-check on fresh labels.")
    return "\n".join(out), k, lo


def main(argv=None):
    ap = argparse.ArgumentParser(description="Measure agreement between an automated grader and human labels.")
    ap.add_argument("csv")
    ap.add_argument("--human", default="human", help="column with human labels (default: human)")
    ap.add_argument("--model", default="model", help="column with grader labels (default: model)")
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap resamples (default: 2000)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threshold", type=float, default=0.6,
                    help="minimum acceptable lower bound for kappa (default: 0.6, 'substantial')")
    args = ap.parse_args(argv)
    h, m, skipped = load(args.csv, args.human, args.model)
    if len(h) < 2:
        raise SystemExit("error: need at least two labeled items")
    text, _, _ = report(h, m, args.boot, args.seed, args.threshold)
    if skipped:
        text = f"skipped {skipped} row(s) with a missing label\n" + text
    print(text)


if __name__ == "__main__":
    sys.exit(main())
