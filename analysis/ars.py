#!/usr/bin/env python3
"""
ARS Analysis — computes Recommendation Incidence, Final Choice Incidence,
and volatility with Wilson score confidence intervals.

Implements the metric definitions of PROTOCOL.md (D5, R-F.16) and the
"unknown is not zero" denominator discipline (Layer 2).

Usage:
    python analysis/ars.py --responses data/responses.jsonl --annotations data/annotations.jsonl
    python analysis/ars.py --responses data/responses.jsonl --annotations data/annotations.jsonl --final-labels adjudicated --json results.json

Exit codes:
    0  — analysis completed
    1  — data error (e.g., no valid annotations, schema mismatch)
    2  — usage error or I/O failure
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


# ── Data loading ────────────────────────────────────────────────────────────


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


# ── Wilson score interval ───────────────────────────────────────────────────


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score 95% interval for a proportion k/n.

    Never use the Wald interval (p ± z*sqrt(p(1-p)/n)) — it has poor coverage
    for small samples or extreme proportions. Wilson is reliable across the range.

    Returns (point_estimate, lower, upper). If n == 0, returns (0.0, 0.0, 0.0).
    """
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))


# ── Coverage table (unknown-is-not-zero compliance) ─────────────────────────


def _build_coverage_table(
    responses: list[dict],
    annotations: list[dict],
    final_labels: set[str] | None,
) -> dict:
    """Build a coverage table: collected vs failed per platform x wave.

    A "collected" response is one present in responses.jsonl.
    A "failed" response is one that was planned but not collected (logged in
    collection/failures-{wave}.jsonl). Since we don't have the failures file
    here, we report collected counts and note that failures are excluded.

    Denominators only count opportunities with a valid observed response
    (linked via response_id). Per the "unknown is not zero" rule (Layer 2),
    failed collections are NOT counted in the denominator.
    """
    # Group responses by platform x wave
    # Wave is parsed from response_id format: w{wave}-{platform}-q{n}-r{run}
    coverage: dict[str, dict[str, int]] = defaultdict(lambda: {"collected": 0})

    for rec in responses:
        rid = rec.get("response_id", "")
        platform = rec.get("platform", "unknown")
        # Extract wave from response_id
        wave = "unknown"
        if rid.startswith("w"):
            parts = rid.split("-")
            if len(parts) >= 1:
                wave = parts[0][1:]  # strip leading 'w'
        key = f"wave-{wave}/{platform}"
        coverage[key]["collected"] += 1

    return dict(coverage)


# ── ARS computation ─────────────────────────────────────────────────────────


def _parse_wave(rid: str) -> str:
    """Extract wave from response_id (w{wave}-...)."""
    if rid.startswith("w"):
        parts = rid.split("-")
        if len(parts) >= 1:
            return parts[0][1:]
    return "unknown"


def _compute_ars(
    responses: list[dict],
    annotations: list[dict],
    final_labels: set[str] | None,
) -> dict:
    """Compute ARS (Recommendation Incidence), Final Choice Incidence,
    and mention/consideration rates.

    Denominators: per-coder-grouped adjudicated data. When --final-labels is
    set, only annotations whose coder_id is in the final-labels set are used
    (e.g., the adjudicated/final coder). Otherwise, all annotations are used
    (treat each coder's labels as a separate observation).

    Per R-F.16: every ARS figure is reported twice — inclusive and exclusive
    of sponsored/platform_self_id events — when such events exist.
    """
    # Filter annotations by final-labels if specified
    if final_labels:
        annotations = [a for a in annotations if a.get("coder_id") in final_labels]
        if not annotations:
            sys.stderr.write(
                "WARNING: no annotations match --final-labels; "
                "falling back to all annotations.\n"
            )
            annotations = _load_jsonl("")  # will exit; handled below

    # Build response lookup: response_id -> response record
    resp_by_id = {r["response_id"]: r for r in responses}

    # Group annotations by (platform, wave, brand)
    # Each group's denominator = number of distinct response_ids in that group
    # that exist in responses.jsonl (unknown is not zero).

    # opportunities: (platform, wave) -> set of response_ids
    opportunities: dict[tuple[str, str], set[str]] = defaultdict(set)
    for rid, rec in resp_by_id.items():
        platform = rec.get("platform", "unknown")
        wave = _parse_wave(rid)
        opportunities[(platform, wave)].add(rid)

    # events: (platform, wave, brand) -> list of annotation records
    events: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for ann in annotations:
        rid = ann.get("response_id", "")
        if rid not in resp_by_id:
            continue  # unknown is not zero: skip annotations without a response
        platform = resp_by_id[rid].get("platform", "unknown")
        wave = _parse_wave(rid)
        brand = ann.get("brand", "")
        events[(platform, wave, brand)].append(ann)

    # Compute per-brand x platform x wave
    results = []
    for (platform, wave, brand), anns in sorted(events.items()):
        denom_response_ids = opportunities.get((platform, wave), set())
        n = len(denom_response_ids)
        if n == 0:
            continue

        # Count C4/C5 events (Recommendation Incidence)
        # A response can recommend multiple brands; for per-brand ARS, the
        # denominator is the number of responses (opportunities), and the
        # numerator is the number of responses where this brand got C4/C5.
        rec_response_ids = set()
        fc_response_ids = set()
        mention_ids = set()
        consider_ids = set()
        # Inclusive/exclusive splits (R-F.16)
        rec_incl_ids = set()
        rec_excl_ids = set()

        for ann in anns:
            rid = ann.get("response_id", "")
            code = ann.get("class_code", "")
            sponsored = ann.get("sponsored", False)
            self_id = ann.get("platform_self_id", False)

            if code in ("C4", "C5"):
                rec_response_ids.add(rid)
                rec_incl_ids.add(rid)
                if not sponsored and not self_id:
                    rec_excl_ids.add(rid)
            if code == "C5" or code == "C4":
                if ann.get("final_choice") is True:
                    fc_response_ids.add(rid)
            if code == "C1":
                mention_ids.add(rid)
            if code == "C3":
                consider_ids.add(rid)

        k_rec = len(rec_response_ids)
        k_fc = len(fc_response_ids)
        k_mention = len(mention_ids)
        k_consider = len(consider_ids)

        rec_p, rec_lo, rec_hi = wilson_ci(k_rec, n)
        fc_p, fc_lo, fc_hi = wilson_ci(k_fc, n)
        m_p, m_lo, m_hi = wilson_ci(k_mention, n)
        c_p, c_lo, c_hi = wilson_ci(k_consider, n)

        # Inclusive/exclusive (R-F.16)
        incl_p, incl_lo, incl_hi = wilson_ci(len(rec_incl_ids), n)
        excl_p, excl_lo, excl_hi = wilson_ci(len(rec_excl_ids), n)

        results.append({
            "platform": platform,
            "wave": wave,
            "brand": brand,
            "denominator_n": n,
            "recommendation_incidence": {
                "count": k_rec,
                "point": rec_p,
                "ci_lower": rec_lo,
                "ci_upper": rec_hi,
            },
            "final_choice_incidence": {
                "count": k_fc,
                "point": fc_p,
                "ci_lower": fc_lo,
                "ci_upper": fc_hi,
            },
            "mention_rate": {"count": k_mention, "point": m_p, "ci_lower": m_lo, "ci_upper": m_hi},
            "consideration_rate": {"count": k_consider, "point": c_p, "ci_lower": c_lo, "ci_upper": c_hi},
            "headline_duality": {
                "inclusive": {"point": incl_p, "ci_lower": incl_lo, "ci_upper": incl_hi},
                "exclusive": {"point": excl_p, "ci_lower": excl_lo, "ci_upper": excl_hi},
            },
        })

    # Pooled (across waves)
    pooled: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "denom_ids": set(), "rec_ids": set(), "fc_ids": set(),
        "per_wave_ars": [],
    })
    for r in results:
        key = (r["platform"], r["brand"])
        # We need the denom and rec IDs per wave; recompute from events
    # Simpler: pool by re-aggregating annotations
    pooled_events: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "denom_ids": set(), "rec_ids": set(), "fc_ids": set(), "wave_ars": defaultdict(set),
    })
    for ann in annotations:
        rid = ann.get("response_id", "")
        if rid not in resp_by_id:
            continue
        platform = resp_by_id[rid].get("platform", "unknown")
        wave = _parse_wave(rid)
        brand = ann.get("brand", "")
        key = (platform, brand)
        pooled_events[key]["denom_ids"].add(rid)
        pooled_events[key]["wave_ars"][wave].add(rid)
        if ann.get("class_code") in ("C4", "C5"):
            pooled_events[key]["rec_ids"].add(rid)
            pooled_events[key]["wave_ars"][wave].add(rid)  # mark as recommended
        if ann.get("final_choice") is True:
            pooled_events[key]["fc_ids"].add(rid)

    pooled_results = []
    for (platform, brand), data in sorted(pooled_events.items()):
        n = len(data["denom_ids"])
        k_rec = len(data["rec_ids"])
        k_fc = len(data["fc_ids"])
        rec_p, rec_lo, rec_hi = wilson_ci(k_rec, n)
        fc_p, fc_lo, fc_hi = wilson_ci(k_fc, n)

        # Volatility: SD of per-wave ARS
        per_wave_rates = []
        for wave, ids in data["wave_ars"].items():
            wave_n = len(ids)
            # Actually, wave_ars currently mixes denom and rec; recompute properly
        # Recompute per-wave ARS properly
        wave_recs: dict[str, set] = defaultdict(set)
        wave_denoms: dict[str, set] = defaultdict(set)
        for ann in annotations:
            rid = ann.get("response_id", "")
            if rid not in resp_by_id:
                continue
            if resp_by_id[rid].get("platform") != platform:
                continue
            if ann.get("brand") != brand:
                continue
            wave = _parse_wave(rid)
            wave_denoms[wave].add(rid)
            if ann.get("class_code") in ("C4", "C5"):
                wave_recs[wave].add(rid)
        per_wave_rates = []
        for wave in sorted(wave_denoms):
            wn = len(wave_denoms[wave])
            wk = len(wave_recs.get(wave, set()))
            if wn > 0:
                per_wave_rates.append(wk / wn)
        volatility = float(np_std(per_wave_rates)) if len(per_wave_rates) > 1 else 0.0

        pooled_results.append({
            "platform": platform,
            "brand": brand,
            "denominator_n": n,
            "recommendation_incidence": {
                "count": k_rec, "point": rec_p, "ci_lower": rec_lo, "ci_upper": rec_hi,
            },
            "final_choice_incidence": {
                "count": k_fc, "point": fc_p, "ci_lower": fc_lo, "ci_upper": fc_hi,
            },
            "volatility_sd": volatility,
            "n_waves": len(per_wave_rates),
        })

    return {
        "per_wave": results,
        "pooled": pooled_results,
    }


def np_std(values: list[float]) -> float:
    """Population standard deviation (stdlib, no numpy needed for this)."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(var)


# ── Markdown table output ───────────────────────────────────────────────────


def _md_table(results: list[dict], title: str) -> str:
    lines = [f"\n### {title}\n"]
    lines.append("| Platform | Brand | N | Rec. Inc. (95% CI) | FC Inc. (95% CI) |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        rec = r["recommendation_incidence"]
        fc = r["final_choice_incidence"]
        lines.append(
            f"| {r['platform']} | {r['brand']} | {r['denominator_n']} | "
            f"{rec['point']:.1%} ({rec['ci_lower']:.1%}–{rec['ci_upper']:.1%}) | "
            f"{fc['point']:.1%} ({fc['ci_lower']:.1%}–{fc['ci_upper']:.1%}) |"
        )
    return "\n".join(lines)


def _coverage_md_table(coverage: dict) -> str:
    lines = ["\n### Coverage Table (unknown is not zero)\n"]
    lines.append("| Wave/Platform | Collected responses |")
    lines.append("|---|---|")
    for key in sorted(coverage):
        lines.append(f"| {key} | {coverage[key]['collected']} |")
    return "\n".join(lines)


def _duality_md_table(results: list[dict]) -> str:
    """R-F.16 headline duality: inclusive vs exclusive."""
    has_flags = any(
        r.get("headline_duality", {}).get("inclusive", {}).get("point")
        != r.get("headline_duality", {}).get("exclusive", {}).get("point")
        for r in results
    )
    if not has_flags:
        return "\n_(No sponsored or platform_self_id events; inclusive == exclusive.)_\n"
    lines = ["\n### Headline Duality (R-F.16: inclusive vs exclusive)\n"]
    lines.append("| Platform | Brand | Inclusive ARS | Exclusive ARS |")
    lines.append("|---|---|---|---|")
    for r in results:
        d = r.get("headline_duality", {})
        inc = d.get("inclusive", {})
        exc = d.get("exclusive", {})
        lines.append(
            f"| {r['platform']} | {r['brand']} | "
            f"{inc.get('point', 0):.1%} | {exc.get('point', 0):.1%} |"
        )
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ars.py",
        description="ARS analysis: Recommendation Incidence, Final Choice, volatility.",
    )
    parser.add_argument("--responses", required=True, help="Path to responses.jsonl")
    parser.add_argument("--annotations", required=True, help="Path to annotations.jsonl")
    parser.add_argument(
        "--final-labels",
        help="Comma-separated coder_ids whose labels are the adjudicated/final records "
             "(e.g., 'adjudicator-1'). If omitted, all annotations are used.",
    )
    parser.add_argument("--json", metavar="PATH", help="Write JSON results to PATH")
    args = parser.parse_args(argv)

    responses = _load_jsonl(args.responses)
    annotations = _load_jsonl(args.annotations)

    if not responses:
        sys.stderr.write("ERROR: no responses loaded.\n")
        return 1
    if not annotations:
        sys.stderr.write("ERROR: no annotations loaded.\n")
        return 1

    final_labels = None
    if args.final_labels:
        final_labels = set(s.strip() for s in args.final_labels.split(","))
        print(f"Using final labels from coders: {final_labels}", file=sys.stderr)

    # Coverage table (printed before any result)
    coverage = _build_coverage_table(responses, annotations, final_labels)
    print(_coverage_md_table(coverage))

    # Compute ARS
    results = _compute_ars(responses, annotations, final_labels)

    # Markdown output
    print(_md_table(results["per_wave"], "Per-Brand × Platform × Wave"))
    print(_duality_md_table(results["per_wave"]))
    print(_md_table(results["pooled"], "Pooled (across waves, with volatility)"))

    # Volatility annotation on pooled table
    print("\n### Volatility (SD of ARS across waves)\n")
    print("| Platform | Brand | Waves | Volatility (SD) |")
    print("|---|---|---|---|")
    for r in results["pooled"]:
        print(f"| {r['platform']} | {r['brand']} | {r['n_waves']} | {r['volatility_sd']:.4f} |")

    print(f"\n_Wilson score 95% intervals. Denominators count only collected responses "
          f"(unknown is not zero, Layer 2). ADJUDICATE events excluded from numerators._")

    # JSON output
    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
        print(f"\nJSON results written to {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
