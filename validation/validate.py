#!/usr/bin/env python3
"""
ARS Coding Protocol — dataset validator.

Validates response and annotation JSONL files against their JSON Schemas and
enforces cross-record constraints that a per-record schema cannot express.

Usage:
    python validation/validate.py \
        --responses data/responses.jsonl \
        --annotations data/annotations.jsonl \
        [--strict]

Exit codes:
    0  — no errors (warnings may be present, unless --strict)
    1  — one or more errors (or warnings under --strict)
    2  — usage error or unrecoverable I/O failure

See validation/README.md for the full list of error (E1-E5) and warning (W1-W3) codes.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.stderr.write(
        "ERROR: the 'jsonschema' package is required. Install with:\n"
        "  pip install jsonschema\n"
    )
    sys.exit(2)


# ── Schema loading ──────────────────────────────────────────────────────────

_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def _load_schema(name: str) -> dict:
    path = _SCHEMA_DIR / name
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


ANNOTATION_SCHEMA = _load_schema("ars-record.schema.json")
RESPONSE_SCHEMA = _load_schema("response-record.schema.json")


# ── JSONL loading ───────────────────────────────────────────────────────────


def _load_jsonl(path: str) -> list[dict]:
    records: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                records.append({
                    "__parse_error__": f"line {lineno}: {exc}",
                    "__lineno__": lineno,
                })
    return records


# ── Finding ──────────────────────────────────────────────────────────────────


class Finding:
    """A single error or warning with structured context."""

    def __init__(
        self,
        code: str,
        message: str,
        response_id: str | None = None,
        brand: str | None = None,
        coder_id: str | None = None,
        detail: str = "",
    ) -> None:
        self.code = code
        self.message = message
        self.response_id = response_id
        self.brand = brand
        self.coder_id = coder_id
        self.detail = detail

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        ctx = []
        if self.response_id is not None:
            ctx.append(f"response_id={self.response_id}")
        if self.brand is not None:
            ctx.append(f"brand={self.brand}")
        if self.coder_id is not None:
            ctx.append(f"coder={self.coder_id}")
        if ctx:
            parts.append("  " + ", ".join(ctx))
        if self.detail:
            parts.append("  detail: " + self.detail)
        return "\n".join(parts)


# ── Validators ────────────────────────────────────────────────────────────────


def check_e1_schema(
    responses: list[dict],
    annotations: list[dict],
) -> list[Finding]:
    """E1: per-record JSON Schema compliance against both schemas."""
    findings: list[Finding] = []

    for i, rec in enumerate(responses):
        if "__parse_error__" in rec:
            findings.append(Finding(
                "E1", "response record is not valid JSON",
                detail=rec["__parse_error__"],
            ))
            continue
        try:
            jsonschema.validate(rec, RESPONSE_SCHEMA)
        except jsonschema.ValidationError as exc:
            rid = rec.get("response_id", f"<line {i+1}>")
            field = " -> ".join(str(p) for p in exc.absolute_path) or "<root>"
            findings.append(Finding(
                "E1", f"response record fails schema validation at '{field}'",
                response_id=rid,
                detail=exc.message,
            ))

    for i, rec in enumerate(annotations):
        if "__parse_error__" in rec:
            findings.append(Finding(
                "E1", "annotation record is not valid JSON",
                detail=rec["__parse_error__"],
            ))
            continue
        try:
            jsonschema.validate(rec, ANNOTATION_SCHEMA)
        except jsonschema.ValidationError as exc:
            rid = rec.get("response_id", f"<line {i+1}>")
            field = " -> ".join(str(p) for p in exc.absolute_path) or "<root>"
            findings.append(Finding(
                "E1", f"annotation record fails schema validation at '{field}'",
                response_id=rid,
                brand=rec.get("brand"),
                coder_id=rec.get("coder_id"),
                detail=exc.message,
            ))

    return findings


def check_e2_final_choice_consistency(
    annotations: list[dict],
) -> list[Finding]:
    """E2: R-FC.5 - within each (response_id, coder_id) group: exactly one
    final_choice=true, or all null."""
    findings: list[Finding] = []
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rec in annotations:
        if "__parse_error__" in rec:
            continue
        key = (rec.get("response_id", ""), rec.get("coder_id", ""))
        groups[key].append(rec)

    for (rid, coder), recs in groups.items():
        true_count = sum(1 for r in recs if r.get("final_choice") is True)
        null_count = sum(1 for r in recs if r.get("final_choice") is None)
        false_count = sum(1 for r in recs if r.get("final_choice") is False)
        total = len(recs)

        if true_count == 0 and null_count == total:
            continue  # all null - valid
        if true_count == 1 and null_count == 0:
            continue  # exactly one true, rest false - valid
        if true_count == 1 and null_count > 0:
            findings.append(Finding(
                "E2",
                f"final_choice inconsistency: one true but {null_count} null(s) in group of {total}",
                response_id=rid, coder_id=coder,
                detail="R-FC.5 requires exactly one true (rest false) OR all null; mixed true+null is invalid.",
            ))
        elif true_count > 1:
            findings.append(Finding(
                "E2",
                f"final_choice inconsistency: {true_count} true values in group of {total}",
                response_id=rid, coder_id=coder,
                detail="R-FC.5 requires exactly one true; multiple winners detected.",
            ))
        elif true_count == 0 and null_count < total:
            findings.append(Finding(
                "E2",
                f"final_choice inconsistency: no true but {null_count} null(s) and {false_count} false in group of {total}",
                response_id=rid, coder_id=coder,
                detail="R-FC.5 requires all null (no winner) or exactly one true; mixed false+null with no true is invalid.",
            ))

    return findings


def check_e3_referential_integrity(
    responses: list[dict],
    annotations: list[dict],
) -> list[Finding]:
    """E3: every response_id in annotations exists in responses; every response
    has at least one annotation."""
    findings: list[Finding] = []

    response_ids = set()
    for rec in responses:
        if "__parse_error__" in rec:
            continue
        rid = rec.get("response_id")
        if rid:
            response_ids.add(rid)

    annotated_ids = set()
    for rec in annotations:
        if "__parse_error__" in rec:
            continue
        rid = rec.get("response_id", "")
        annotated_ids.add(rid)
        if rid and rid not in response_ids:
            findings.append(Finding(
                "E3", "annotation references a response_id not found in responses file",
                response_id=rid,
                brand=rec.get("brand"),
                coder_id=rec.get("coder_id"),
            ))

    for rid in sorted(response_ids - annotated_ids):
        findings.append(Finding(
            "E3", "response has no annotation records (missing from coding round)",
            response_id=rid,
        ))

    return findings


def check_e4_evidence_span(
    responses: list[dict],
    annotations: list[dict],
) -> list[Finding]:
    """E4: evidence_span is a verbatim substring of the response's full_text."""
    findings: list[Finding] = []

    text_by_id: dict[str, str] = {}
    for rec in responses:
        if "__parse_error__" in rec:
            continue
        rid = rec.get("response_id")
        if rid:
            text_by_id[rid] = rec.get("full_text", "")

    for rec in annotations:
        if "__parse_error__" in rec:
            continue
        rid = rec.get("response_id", "")
        span = rec.get("evidence_span", "")
        full = text_by_id.get(rid)
        if full is None:
            # Already flagged by E3; skip to avoid duplicate noise
            continue
        if span not in full:
            findings.append(Finding(
                "E4", "evidence_span is not a verbatim substring of the response full_text",
                response_id=rid,
                brand=rec.get("brand"),
                coder_id=rec.get("coder_id"),
                detail=f"span (first 80 chars): {span[:80]!r}",
            ))

    return findings


def check_e5_final_choice_and_duplicates(
    annotations: list[dict],
) -> list[Finding]:
    """E5: final_choice=true only for C4/C5 events; no duplicate
    (response_id, coder_id, brand) triples."""
    findings: list[Finding] = []
    seen: set[tuple[str, str, str]] = set()

    for rec in annotations:
        if "__parse_error__" in rec:
            continue
        rid = rec.get("response_id", "")
        coder = rec.get("coder_id", "")
        brand = rec.get("brand", "")
        code = rec.get("class_code", "")
        fc = rec.get("final_choice")

        if fc is True and code not in ("C4", "C5"):
            findings.append(Finding(
                "E5", f"final_choice=true is only permitted for C4/C5 events (got {code})",
                response_id=rid, brand=brand, coder_id=coder,
            ))

        key = (rid, coder, brand)
        if key in seen:
            findings.append(Finding(
                "E5", "duplicate (response_id, coder_id, brand) triple",
                response_id=rid, brand=brand, coder_id=coder,
            ))
        else:
            seen.add(key)

    return findings


def check_w1_duplicate_rank(
    annotations: list[dict],
) -> list[Finding]:
    """W1: duplicate rank_position within a (response_id, coder_id) group.
    Permitted only for category winners per R-F.13; require the category name
    to appear in rationale."""
    findings: list[Finding] = []
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rec in annotations:
        if "__parse_error__" in rec:
            continue
        key = (rec.get("response_id", ""), rec.get("coder_id", ""))
        groups[key].append(rec)

    for (rid, coder), recs in groups.items():
        rank_map: dict[int, list[dict]] = defaultdict(list)
        for r in recs:
            rp = r.get("rank_position")
            if rp is not None and r.get("class_code") == "C5":
                rank_map[rp].append(r)
        for rp, dupes in rank_map.items():
            if len(dupes) > 1:
                # W1 fires only if NO record in the duplicate set mentions
                # "category" in its rationale — meaning the duplicate is
                # unexplained. If at least one record names a category, the
                # duplicate is the permitted category-winner case (R-F.13).
                any_has_category = any(
                    "categor" in r.get("rationale", "").lower() for r in dupes
                )
                if not any_has_category:
                    for r in dupes:
                        findings.append(Finding(
                            "W1",
                            f"duplicate rank_position={rp} in group with no "
                            "category-winner rationale; permitted only for "
                            "category winners (R-F.13) - at least one record's "
                            "rationale must name the category",
                            response_id=rid,
                            brand=r.get("brand"),
                            coder_id=coder,
                        ))

    return findings


def check_w2_mixed_versions(
    annotations: list[dict],
) -> list[Finding]:
    """W2: mixed protocol_version values across the annotation dataset."""
    findings: list[Finding] = []
    versions: dict[str, list[dict]] = defaultdict(list)
    for rec in annotations:
        if "__parse_error__" in rec:
            continue
        v = rec.get("protocol_version", "<missing>")
        versions[v].append(rec)

    if len(versions) > 1:
        summary = ", ".join(
            f"{v} ({len(recs)} records)" for v, recs in sorted(versions.items())
        )
        findings.append(Finding(
            "W2", f"mixed protocol_version values across dataset: {summary}",
            detail="All records in a measurement cycle should share one protocol_version (R-V.3).",
        ))

    return findings


def check_w3_missing_model_version(
    responses: list[dict],
) -> list[Finding]:
    """W3: missing model_version in a response record."""
    findings: list[Finding] = []
    for rec in responses:
        if "__parse_error__" in rec:
            continue
        if rec.get("model_version") is None:
            findings.append(Finding(
                "W3", "response record has null model_version",
                response_id=rec.get("response_id"),
                detail="model_version should record the platform's disclosed model identifier (D10, section 10.5).",
            ))

    return findings


# ── Reporting ────────────────────────────────────────────────────────────────


def _print_grouped(label: str, findings: list[Finding]) -> None:
    if not findings:
        return
    by_code: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_code[f.code].append(f)
    print(f"\n{'=' * 60}")
    print(f"{label} ({len(findings)} total)")
    print(f"{'=' * 60}")
    for code in sorted(by_code):
        group = by_code[code]
        print(f"\n--- {code} ({len(group)} occurrences) ---")
        for f in group:
            print(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description="Validate ARS response and annotation JSONL files.",
    )
    parser.add_argument(
        "--responses", required=True,
        help="Path to data/responses.jsonl",
    )
    parser.add_argument(
        "--annotations", required=True,
        help="Path to data/annotations.jsonl",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors (exit 1 if any warnings).",
    )
    args = parser.parse_args(argv)

    # ── Load ──
    try:
        responses = _load_jsonl(args.responses)
    except OSError as exc:
        sys.stderr.write(f"ERROR: cannot read responses file: {exc}\n")
        return 2
    try:
        annotations = _load_jsonl(args.annotations)
    except OSError as exc:
        sys.stderr.write(f"ERROR: cannot read annotations file: {exc}\n")
        return 2

    # ── Run all checks ──
    errors: list[Finding] = []
    warnings: list[Finding] = []

    # E1 must run first; subsequent checks skip records that failed to parse
    e1 = check_e1_schema(responses, annotations)
    errors.extend(e1)

    errors.extend(check_e3_referential_integrity(responses, annotations))
    errors.extend(check_e2_final_choice_consistency(annotations))
    errors.extend(check_e4_evidence_span(responses, annotations))
    errors.extend(check_e5_final_choice_and_duplicates(annotations))

    warnings.extend(check_w1_duplicate_rank(annotations))
    warnings.extend(check_w2_mixed_versions(annotations))
    warnings.extend(check_w3_missing_model_version(responses))

    # ── Report ──
    if errors:
        _print_grouped("ERRORS", errors)
    if warnings:
        _print_grouped("WARNINGS", warnings)

    print(f"\n{'-' * 60}")
    print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    if args.strict and warnings:
        print("(--strict: warnings treated as errors)")
    print(f"{'-' * 60}")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
