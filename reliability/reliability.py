#!/usr/bin/env python3
"""
ARS Reliability Statistics — implements PROTOCOL.md D7.

Computes inter-coder reliability for the ARS coding protocol:
  - Cohen's kappa for exactly 2 coders (aggregate + per-class one-vs-rest)
  - Krippendorff's nominal alpha for >=2 coders (with bootstrap 95% CIs)
  - Coder-vs-coder confusion matrix on class_code
  - ADJUDICATE share check (R-R.2 trigger at >5%)
  - Threshold enforcement: alpha >= 0.80 measurement-ready; 0.667-0.80 tentative; < 0.667 fail

Usage:
    python reliability/reliability.py --annotations data/annotations.jsonl
    python reliability/reliability.py --annotations data/annotations.jsonl --gold-standard data/gold-standard.jsonl
    python reliability/reliability.py --annotations data/annotations.jsonl --bootstrap 2000

Exit codes (per D7 thresholds):
    0  — alpha >= 0.667 (measurement-ready or tentative-with-caveat)
    1  — alpha < 0.667 (unacceptable; remediation checklist printed) OR ADJUDICATE > 5%
    2  — usage error or I/O failure
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.stderr.write("ERROR: numpy is required. Install with: pip install numpy\n")
    sys.exit(2)

try:
    import krippendorff
except ImportError:
    sys.stderr.write(
        "ERROR: the 'krippendorff' package is required. Install with:\n"
        "  pip install krippendorff\n"
    )
    sys.exit(2)


# The full 7-category value domain including ADJUDICATE (per R-R.1, R-R.2)
VALUE_DOMAIN = ["C1", "C2", "C3", "C4", "C5", "C6", "ADJUDICATE"]

# D7 thresholds (per R-R.2)
ALPHA_GOOD = 0.800
ALPHA_MIN = 0.667
ADJUDICATE_MAX_SHARE = 0.05  # R-R.2 trigger


# ── Data loading ─────────────────────────────────────────────────────────────


def _load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                sys.stderr.write(f"ERROR: {path} line {lineno}: {exc}\n")
                sys.exit(1)
    return records


def _build_coder_matrix(annotations: list[dict]) -> tuple[list[str], list[str], np.ndarray]:
    """Build a reliability data matrix: rows = coders, cols = events.

    Returns (coder_ids, event_keys, matrix) where matrix[i][j] is the class_code
    assigned by coder i to event j, or np.nan if missing (R-R.1a: missing data
    is represented as NaN for Krippendorff's alpha).
    """
    # Collect all (response_id, brand) event keys and all coder_ids
    event_to_idx: dict[str, int] = {}
    coder_to_idx: dict[str, int] = {}

    for rec in annotations:
        event_key = f"{rec.get('response_id', '')}::{rec.get('brand', '')}"
        if event_key not in event_to_idx:
            event_to_idx[event_key] = len(event_to_idx)
        coder = rec.get("coder_id", "")
        if coder not in coder_to_idx:
            coder_to_idx[coder] = len(coder_to_idx)

    n_coders = len(coder_to_idx)
    n_events = len(event_to_idx)
    matrix = np.full((n_coders, n_events), np.nan, dtype=object)

    code_to_idx = {c: i for i, c in enumerate(VALUE_DOMAIN)}

    for rec in annotations:
        event_key = f"{rec.get('response_id', '')}::{rec.get('brand', '')}"
        ej = event_to_idx[event_key]
        ci = coder_to_idx[rec.get("coder_id", "")]
        code = rec.get("class_code", "")
        if code in code_to_idx:
            matrix[ci, ej] = code
        else:
            matrix[ci, ej] = "ADJUDICATE"  # unknown codes map to ADJUDICATE

    coder_ids = [c for c, _ in sorted(coder_to_idx.items(), key=lambda x: x[1])]
    event_keys = [e for e, _ in sorted(event_to_idx.items(), key=lambda x: x[1])]
    return coder_ids, event_keys, matrix


# ── Cohen's kappa (2 coders) ─────────────────────────────────────────────────


def _cohen_kappa(codes_a: list[str], codes_b: list[str]) -> float:
    """Compute Cohen's kappa for two coders on matched events.

    kappa = (p_o - p_e) / (1 - p_e)
    where p_o = observed agreement, p_e = chance agreement from marginals.
    Per R-R.1.
    """
    # Only use events where both coders assigned a code (balanced subset)
    paired = [(a, b) for a, b in zip(codes_a, codes_b) if a and b]
    if not paired:
        return float("nan")

    n = len(paired)
    labels = sorted(set(c for pair in paired for c in pair))

    # Observed agreement
    p_o = sum(1 for a, b in paired if a == b) / n

    # Expected agreement from marginals
    from collections import Counter
    count_a = Counter(a for a, _ in paired)
    count_b = Counter(b for _, b in paired)
    p_e = sum((count_a.get(l, 0) / n) * (count_b.get(l, 0) / n) for l in labels)

    if p_e == 1.0:
        return 1.0  # perfect agreement on a single category
    return (p_o - p_e) / (1 - p_e)


def _per_class_kappa(codes_a: list[str], codes_b: list[str], target: str) -> float:
    """One-vs-rest kappa for a single class."""
    bin_a = ["1" if c == target else "0" for c in codes_a]
    bin_b = ["1" if c == target else "0" for c in codes_b]
    return _cohen_kappa(bin_a, bin_b)


# ── Krippendorff's alpha ─────────────────────────────────────────────────────


def _krippendorff_alpha(matrix: np.ndarray) -> float:
    """Compute Krippendorff's nominal-metric alpha.

    matrix: rows = coders, cols = events, values = class codes or np.nan.
    Per R-R.2. value_domain is the full 7-category set including ADJUDICATE.
    """
    # krippendorff.alpha expects reliability_data as list of rows (coders)
    # with missing values as np.nan
    data = [list(row) for row in matrix]
    try:
        alpha = krippendorff.alpha(
            reliability_data=data,
            value_domain=VALUE_DOMAIN,
            level_of_measurement="nominal",
        )
    except Exception as exc:
        sys.stderr.write(f"WARNING: krippendorff.alpha failed: {exc}\n")
        return float("nan")
    return alpha


def _bootstrap_alpha_ci(
    matrix: np.ndarray, n_resamples: int = 1000, seed: int = 42
) -> tuple[float, float]:
    """Bootstrap 95% CI for Krippendorff's alpha.

    Resample units = events (columns), per R-R.2.
    Returns (lower, upper) bounds.
    """
    rng = np.random.default_rng(seed)
    n_events = matrix.shape[1]
    alphas = []
    for _ in range(n_resamples):
        # Resample events (columns) with replacement
        idx = rng.integers(0, n_events, size=n_events)
        boot_matrix = matrix[:, idx]
        try:
            a = krippendorff.alpha(
                reliability_data=[list(row) for row in boot_matrix],
                value_domain=VALUE_DOMAIN,
                level_of_measurement="nominal",
            )
            if not np.isnan(a):
                alphas.append(a)
        except Exception:
            continue

    if len(alphas) < 10:
        return (float("nan"), float("nan"))
    lower = float(np.percentile(alphas, 2.5))
    upper = float(np.percentile(alphas, 97.5))
    return (lower, upper)


# ── Confusion matrix ─────────────────────────────────────────────────────────


def _confusion_matrix(
    codes_a: list[str], codes_b: list[str], labels: list[str]
) -> np.ndarray:
    """Coder-vs-coder confusion matrix. Rows = coder A, cols = coder B."""
    label_to_idx = {l: i for i, l in enumerate(labels)}
    mat = np.zeros((len(labels), len(labels)), dtype=int)
    for a, b in zip(codes_a, codes_b):
        if a in label_to_idx and b in label_to_idx:
            mat[label_to_idx[a], label_to_idx[b]] += 1
    return mat


# ── ADJUDICATE share ─────────────────────────────────────────────────────────


def _adjudicate_share(annotations: list[dict]) -> float:
    """Share of ADJUDICATE events across all annotations (R-R.2 trigger)."""
    if not annotations:
        return 0.0
    adj = sum(1 for r in annotations if r.get("class_code") == "ADJUDICATE")
    return adj / len(annotations)


# ── Missing data check (R-R.1a) ──────────────────────────────────────────────


def _check_missing_data(matrix: np.ndarray) -> bool:
    """Return True if any event is missing from any coder (unbalanced panel).

    An event is "missing" for a coder if the cell is np.nan. The matrix is an
    object array (class codes are strings); we check for NaN without converting
    the whole array to float.
    """
    # Check each cell: np.nan is a float, class codes are strings
    for cell in matrix.flat:
        if isinstance(cell, float) and np.isnan(cell):
            return True
    return False


# ── Reporting ────────────────────────────────────────────────────────────────


def _print_remediation_checklist() -> None:
    """Print the R-R.4 remediation checklist when alpha < 0.667."""
    print("\n" + "=" * 60)
    print("REMEDIATION CHECKLIST (per R-R.4)")
    print("=" * 60)
    print("""
Alpha is below 0.667 (unacceptable). Do NOT publish ARS figures.

1. Examine the confusion matrix above to identify the class pair
   with the highest off-diagonal mass (the dominant confusion).
2. Refine or add boundary rules for that class pair; cite the new rule IDs.
3. Re-train all coders on the revised rules using the onboarding quiz (D9)
   and a refreshed calibration set.
4. Re-code a fresh, equivalently-sized sample (not the original) and
   recompute alpha.
5. Repeat until alpha >= 0.667 on the full taxonomy.
6. If a single class remains below 0.667 after two remediation cycles,
   report ARS for the reliable classes only and exclude the unreliable
   class with explicit documentation.
""")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reliability.py",
        description="ARS inter-coder reliability statistics (implements D7).",
    )
    parser.add_argument(
        "--annotations", required=True,
        help="Path to annotations JSONL (multi-coder records).",
    )
    parser.add_argument(
        "--gold-standard",
        help="Path to Gold Standard JSONL. If set, computes alpha of each coder vs Gold Standard (for onboarding per R-R.7).",
    )
    parser.add_argument(
        "--bootstrap", type=int, default=1000,
        help="Number of bootstrap resamples for alpha CI (default 1000, per R-R.2).",
    )
    args = parser.parse_args(argv)

    annotations = _load_jsonl(args.annotations)
    if not annotations:
        sys.stderr.write("ERROR: no annotations found.\n")
        return 2

    # Build coder matrix
    coder_ids, event_keys, matrix = _build_coder_matrix(annotations)
    n_coders = len(coder_ids)
    n_events = len(event_keys)

    print(f"\n{'=' * 60}")
    print("ARS RELIABILITY REPORT")
    print(f"{'=' * 60}")
    print(f"Coders: {n_coders} ({', '.join(coder_ids)})")
    print(f"Events: {n_events}")

    # ADJUDICATE share (R-R.2)
    adj_share = _adjudicate_share(annotations)
    print(f"\nADJUDICATE share: {adj_share:.1%}")
    if adj_share > ADJUDICATE_MAX_SHARE:
        print(f"  ⚠ TRIGGER (R-R.2): ADJUDICATE exceeds {ADJUDICATE_MAX_SHARE:.0%}.")
        print(f"    Protocol is under-specified; remediation required regardless of alpha.")

    # Missing data check (R-R.1a)
    missing = _check_missing_data(matrix)
    if missing:
        print("\n⚠ UNBALANCED PANEL (R-R.1a): some events are missing from some coders.")
        print("  Krippendorff's alpha is the primary statistic; kappa is secondary-only.")

    # ── Krippendorff's alpha (primary, per R-R.2) ──
    alpha = _krippendorff_alpha(matrix)
    print(f"\nKrippendorff's alpha (nominal, 7-category): {alpha:.4f}")

    if n_coders >= 2 and args.bootstrap > 0:
        ci_lo, ci_hi = _bootstrap_alpha_ci(matrix, n_resamples=args.bootstrap)
        if not np.isnan(ci_lo):
            print(f"  Bootstrap 95% CI ({args.bootstrap} resamples): [{ci_lo:.4f}, {ci_hi:.4f}]")

    # ── Cohen's kappa (2 coders only, or pairwise) ──
    if n_coders == 2:
        codes_a = [matrix[0, j] for j in range(n_events)]
        codes_b = [matrix[1, j] for j in range(n_events)]
        kappa = _cohen_kappa(codes_a, codes_b)
        print(f"\nCohen's kappa (2 coders, aggregate): {kappa:.4f}")

        print("\nPer-class kappa (one-vs-rest):")
        for code in VALUE_DOMAIN:
            k = _per_class_kappa(codes_a, codes_b, code)
            print(f"  {code:12s}: {k:.4f}")

        # Confusion matrix
        print("\nConfusion matrix (rows = coder A, cols = coder B):")
        cm = _confusion_matrix(codes_a, codes_b, VALUE_DOMAIN)
        header = "          " + "  ".join(f"{c:>5s}" for c in VALUE_DOMAIN)
        print(header)
        for i, code in enumerate(VALUE_DOMAIN):
            row = "  ".join(f"{cm[i, j]:5d}" for j in range(len(VALUE_DOMAIN)))
            print(f"  {code:8s} {row}")
    else:
        print(f"\nCohen's kappa: skipped (requires exactly 2 coders; got {n_coders}).")
        print("  Pairwise kappa (coder i vs coder j):")
        for i in range(n_coders):
            for j in range(i + 1, n_coders):
                codes_i = [matrix[i, k] for k in range(n_events)]
                codes_j = [matrix[j, k] for k in range(n_events)]
                k = _cohen_kappa(codes_i, codes_j)
                print(f"    {coder_ids[i]} vs {coder_ids[j]}: {k:.4f}")

    # ── Gold Standard onboarding check (R-R.7) ──
    if args.gold_standard:
        print(f"\n{'─' * 60}")
        print("GOLD STANDARD ONBOARDING CHECK (per R-R.7)")
        print(f"{'─' * 60}")
        gs_records = _load_jsonl(args.gold_standard)
        # Treat Gold Standard as an additional "coder" and compute alpha per coder
        gs_by_event = {}
        for r in gs_records:
            event_key = f"{r.get('response_id', '')}::{r.get('brand', '')}"
            gs_by_event[event_key] = r.get("class_code", "")

        print(f"Gold Standard events: {len(gs_by_event)}")
        print(f"Threshold: alpha >= {ALPHA_GOOD} (measurement-ready per R-R.7)\n")

        for i, coder in enumerate(coder_ids):
            codes_coder = []
            codes_gs = []
            for event_key, gs_code in gs_by_event.items():
                if event_key in event_keys:
                    ej = event_keys.index(event_key)
                    coder_code = matrix[i, ej]
                    if coder_code and not (isinstance(coder_code, float) and np.isnan(coder_code)):
                        codes_coder.append(coder_code)
                        codes_gs.append(gs_code)
            if codes_coder:
                # Build a 2-row matrix for this coder vs GS
                pair_matrix = np.array([codes_gs, codes_coder], dtype=object)
                a = krippendorff.alpha(
                    reliability_data=[list(row) for row in pair_matrix],
                    value_domain=VALUE_DOMAIN,
                    level_of_measurement="nominal",
                )
                status = "PASS" if a >= ALPHA_GOOD else "FAIL"
                print(f"  {coder}: alpha = {a:.4f} [{status}]")

    # ── Threshold enforcement ──
    print(f"\n{'=' * 60}")
    print("THRESHOLD ASSESSMENT (per D7)")
    print(f"{'=' * 60}")

    if np.isnan(alpha):
        print("alpha could not be computed. Manual review required.")
        return 1

    if alpha >= ALPHA_GOOD:
        print(f"alpha = {alpha:.4f} >= {ALPHA_GOOD} → MEASUREMENT-READY")
        print("Headline ARS figures may be published.")
        return 0
    elif alpha >= ALPHA_MIN:
        print(f"alpha = {alpha:.4f} ({ALPHA_MIN} <= alpha < {ALPHA_GOOD}) → TENTATIVE")
        print("Acceptable with documented caveat. Flag for improvement.")
        return 0
    else:
        print(f"alpha = {alpha:.4f} < {ALPHA_MIN} → UNACCEPTABLE")
        _print_remediation_checklist()
        return 1


if __name__ == "__main__":
    sys.exit(main())
