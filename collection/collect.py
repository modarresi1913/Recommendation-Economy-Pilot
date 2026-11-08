#!/usr/bin/env python3
"""
ARS Collection — wave runner.

Loads a wave config, collects AI responses to the active Market Question Cells
from configured platforms, and writes schema-valid records to
data/responses.jsonl. Failed requests are logged separately and never enter
the ARS denominator (per the protocol's Layer 2: "unknown is not zero").

Usage:
    python collection/collect.py --config collection/wave-01.yaml --api
    python collection/collect.py --config collection/wave-01.yaml --import-manual transcripts/
    python collection/collect.py --config collection/wave-01.yaml --api --dry-run

Environment variables (API mode):
    ARS_PLATFORM_<NAME>_BASE_URL   OpenAI-compatible chat-completion base URL
    ARS_PLATFORM_<NAME>_MODEL      Model identifier to request
    ARS_PLATFORM_<NAME>_API_KEY    API key (NEVER stored in files)
    ARS_PLATFORM_<NAME>_MODEL_VERSION  Optional: override model_version capture

Exit codes:
    0  — wave completed (may include logged failures)
    1  — data/validation errors (schema-invalid output refused)
    2  — usage error or unrecoverable I/O failure
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    sys.stderr.write(
        "ERROR: the 'requests' package is required for --api mode.\n"
        "  pip install requests\n"
    )
    sys.exit(2)

try:
    import jsonschema
except ImportError:
    sys.stderr.write(
        "ERROR: the 'jsonschema' package is required.\n"
        "  pip install jsonschema\n"
    )
    sys.exit(2)

try:
    import yaml
except ImportError:
    yaml = None  # YAML support optional; we provide a fallback


# ── Paths ────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_DIR = _REPO_ROOT / "schema"
_RESPONSE_SCHEMA_PATH = _SCHEMA_DIR / "response-record.schema.json"
_QUESTION_SCHEMA_PATH = _REPO_ROOT / "questions" / "questions.schema.json"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


RESPONSE_SCHEMA = _load_json(_RESPONSE_SCHEMA_PATH)
QUESTION_SCHEMA = _load_json(_QUESTION_SCHEMA_PATH)


# ── YAML loading with fallback ───────────────────────────────────────────────


def _load_yaml(path: Path) -> dict | list:
    if yaml is not None:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    # Minimal fallback: try json
    try:
        return _load_json(path)
    except json.JSONDecodeError:
        sys.stderr.write(
            f"ERROR: cannot parse {path} — install PyYAML or use JSON format.\n"
        )
        sys.exit(2)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_response_record(rec: dict) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    errors = []
    try:
        jsonschema.validate(rec, RESPONSE_SCHEMA)
    except jsonschema.ValidationError as exc:
        field = " -> ".join(str(p) for p in exc.absolute_path) or "<root>"
        errors.append(f"{field}: {exc.message}")
    return errors


def _existing_response_ids(path: Path) -> set[str]:
    """Load existing response_ids for idempotency."""
    ids = set()
    if not path.exists():
        return ids
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if "response_id" in rec:
                    ids.add(rec["response_id"])
            except json.JSONDecodeError:
                continue
    return ids


def _make_response_id(wave: str, platform: str, qid: str, run: int) -> str:
    """Deterministic response_id format: w{wave}-{platform}-q{n}-r{run}."""
    # Sanitize platform for ID safety
    plat = platform.replace(" ", "-").lower()
    return f"w{wave}-{plat}-{qid}-r{run:02d}"


# ── Platform adapters (OpenAI-compatible) ────────────────────────────────────


class PlatformAdapter:
    """OpenAI-compatible chat-completion adapter.

    Platforms exposing /v1/chat/completions work out of the box. For platforms
    with non-standard endpoints, subclass and override _build_payload / _parse_response.
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.base_url = config.get("base_url", "").rstrip("/")
        self.model = config.get("model", "")
        self.model_version = config.get("model_version")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 60)
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.0)  # per R-L.2 deterministic

    def collect(self, question_text: str) -> dict:
        """Return {'full_text': str, 'model_version': str|None, 'citations': list} or raise."""
        if not self.api_key:
            raise RuntimeError(f"no API key configured for platform {self.name}")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": question_text}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        full_text = ""
        choices = data.get("choices", [])
        if choices:
            full_text = choices[0].get("message", {}).get("content", "")

        # Model version: prefer the response's model field, fall back to config
        model_version = data.get("model") or self.model_version or None
        citations = []  # OpenAI-compatible endpoints don't return citations; adapters can override

        return {
            "full_text": full_text,
            "model_version": model_version,
            "citations": citations,
        }


def _load_platform_configs(platform_names: list[str]) -> dict[str, PlatformAdapter]:
    """Build adapters from environment variables.

    Convention: ARS_PLATFORM_<NAME>_BASE_URL, _MODEL, _API_KEY, _MODEL_VERSION
    where <NAME> is the platform name uppercased with non-alphanumerics replaced by _.
    """
    adapters = {}
    for name in platform_names:
        env_prefix = "ARS_PLATFORM_" + name.upper().replace("-", "_").replace(" ", "_")
        config = {
            "base_url": os.environ.get(f"{env_prefix}_BASE_URL", ""),
            "model": os.environ.get(f"{env_prefix}_MODEL", ""),
            "api_key": os.environ.get(f"{env_prefix}_API_KEY", ""),
            "model_version": os.environ.get(f"{env_prefix}_MODEL_VERSION"),
            "timeout": int(os.environ.get(f"{env_prefix}_TIMEOUT", "60")),
            "max_tokens": int(os.environ.get(f"{env_prefix}_MAX_TOKENS", "2000")),
            "temperature": float(os.environ.get(f"{env_prefix}_TEMPERATURE", "0.0")),
        }
        adapters[name] = PlatformAdapter(name, config)
    return adapters


# ── Manual import mode ───────────────────────────────────────────────────────


def _import_manual(
    transcripts_dir: Path,
    wave: str,
    platform: str,
    questions: list[dict],
    collection_version: str,
) -> list[tuple[dict, str | None]]:
    """Import pasted/CSV transcripts. Returns list of (record, error) tuples."""
    records = []
    # Expected: one CSV per platform with columns: question_id, run, full_text, [model_version]
    # or one directory of .txt files named {question_id}-r{run}.txt
    results = []

    # CSV mode
    csv_path = transcripts_dir / f"{platform}.csv"
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                qid = row.get("question_id", "")
                run = int(row.get("run", 1))
                full_text = row.get("full_text", "")
                model_version = row.get("model_version") or None
                rid = _make_response_id(wave, platform, qid, run)
                rec = _build_response_record(
                    rid, qid, platform, full_text, model_version,
                    [], collection_channel="web",
                    collection_version=collection_version,
                )
                errors = _validate_response_record(rec)
                if errors:
                    results.append((rec, "; ".join(errors)))
                else:
                    results.append((rec, None))
        return results

    # TXT directory mode
    for txt_path in sorted(transcripts_dir.glob(f"{platform}-*.txt")):
        # filename: {platform}-{question_id}-r{run}.txt
        stem = txt_path.stem  # e.g., openai-crm-q01-r01
        parts = stem.split("-", 2)
        if len(parts) < 3:
            continue
        _, qid, run_part = parts
        run = int(run_part.replace("r", ""))
        full_text = txt_path.read_text(encoding="utf-8")
        rid = _make_response_id(wave, platform, qid, run)
        rec = _build_response_record(
            rid, qid, platform, full_text, None,
            [], collection_channel="web",
            collection_version=collection_version,
        )
        errors = _validate_response_record(rec)
        if errors:
            results.append((rec, "; ".join(errors)))
        else:
            results.append((rec, None))

    return results


# ── Record construction ──────────────────────────────────────────────────────


def _build_response_record(
    response_id: str,
    question_id: str,
    platform: str,
    full_text: str,
    model_version: str | None,
    citations: list,
    collection_channel: str = "api",
    collection_version: str = "1.0.0",
    self_disclosure: dict | None = None,
) -> dict:
    """Build a schema-valid response record."""
    if self_disclosure is None:
        self_disclosure = {"present": False, "verbatim": None, "vendor": None}

    # Normalize citations to {url, title} objects
    norm_citations = []
    for c in citations:
        if isinstance(c, dict):
            norm_citations.append({
                "url": c.get("url", ""),
                "title": c.get("title"),
            })
        elif isinstance(c, str):
            norm_citations.append({"url": c, "title": None})

    return {
        "response_id": response_id,
        "question_id": question_id,
        "platform": platform,
        "model_version": model_version,
        "language": "en",
        "timestamp_collected": _utc_now(),
        "full_text": full_text,
        "citations": norm_citations,
        "sponsored_block_present": False,  # default; manual review sets true
        "self_disclosure": self_disclosure,
        "collection_channel": collection_channel,
        "collection_version": collection_version,
    }


# ── Wave runner ──────────────────────────────────────────────────────────────


def run_wave(
    config: dict,
    mode: str,
    transcripts_dir: Path | None,
    dry_run: bool,
    output_path: Path,
) -> int:
    wave = config.get("wave", "01")
    questions_path = Path(config.get("questions_path", "questions/questions-draft.yaml"))
    platforms = config.get("platforms", [])
    runs_per_question = config.get("runs_per_question", 10)
    delay_range = config.get("delay_range_seconds", [1, 5])
    collection_version = config.get("collection_version", "1.0.0")
    failures_path = _REPO_ROOT / "collection" / f"failures-{wave}.jsonl"

    # Load questions
    if not questions_path.is_absolute():
        questions_path = _REPO_ROOT / questions_path
    all_questions = _load_yaml(questions_path)
    active_questions = [q for q in all_questions if q.get("status") == "active"]
    if not active_questions:
        sys.stderr.write(
            f"WARNING: no 'active' questions found in {questions_path}.\n"
            f"  All questions are likely 'draft'. Replace draft questions with "
            f"active ones before running a wave (see questions/README.md).\n"
        )
        if not dry_run:
            sys.stderr.write("Refusing to collect against draft questions.\n")
            return 1

    print(f"Wave {wave}: {len(active_questions)} active questions x "
          f"{len(platforms)} platforms x {runs_per_question} runs", file=sys.stderr)

    # Idempotency: load existing response_ids
    existing_ids = _existing_response_ids(output_path)
    print(f"Idempotency: {len(existing_ids)} response_ids already present.", file=sys.stderr)

    # Build adapters or prepare for manual import
    adapters = {}
    if mode == "api":
        adapters = _load_platform_configs(platforms)
        missing = [p for p in platforms if not adapters[p].api_key]
        if missing and not dry_run:
            sys.stderr.write(
                f"ERROR: no API key for platforms: {missing}.\n"
                f"  Set ARS_PLATFORM_<NAME>_API_KEY environment variables.\n"
            )
            return 2

    # Prepare output
    collected = 0
    failed = 0
    skipped = 0
    failures = []

    total_planned = len(active_questions) * len(platforms) * runs_per_question

    for q in active_questions:
        qid = q["question_id"]
        qtext = q["question_text"]

        for platform in platforms:
            for run in range(1, runs_per_question + 1):
                rid = _make_response_id(wave, platform, qid, run)

                if rid in existing_ids:
                    skipped += 1
                    continue

                if dry_run:
                    print(f"[dry-run] would collect {rid}", file=sys.stderr)
                    collected += 1
                    continue

                # ── Collect ──
                try:
                    if mode == "api":
                        adapter = adapters[platform]
                        result = adapter.collect(qtext)
                        rec = _build_response_record(
                            rid, qid, platform,
                            result["full_text"],
                            result["model_version"],
                            result["citations"],
                            collection_channel="api",
                            collection_version=collection_version,
                        )
                    else:  # import-manual
                        # Manual import is handled in bulk per platform; skip here
                        continue

                    # Validate before writing (fail fast)
                    errors = _validate_response_record(rec)
                    if errors:
                        raise ValueError(
                            f"schema validation failed: {'; '.join(errors)}"
                        )

                    # Append to output
                    with open(output_path, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    collected += 1

                except Exception as exc:
                    failed += 1
                    failure = {
                        "response_id": rid,
                        "question_id": qid,
                        "platform": platform,
                        "run": run,
                        "wave": wave,
                        "error": str(exc),
                        "timestamp": _utc_now(),
                    }
                    failures.append(failure)
                    with open(failures_path, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(failure, ensure_ascii=False) + "\n")
                    print(f"  FAILED {rid}: {exc}", file=sys.stderr)

                # Inter-run delay with jitter
                delay = random.uniform(delay_range[0], delay_range[1])
                time.sleep(delay)

    # Manual import mode (bulk per platform)
    if mode == "import-manual" and transcripts_dir is not None:
        for platform in platforms:
            results = _import_manual(
                transcripts_dir, wave, platform, active_questions, collection_version
            )
            for rec, error in results:
                rid = rec["response_id"]
                if rid in existing_ids:
                    skipped += 1
                    continue
                if dry_run:
                    print(f"[dry-run] would import {rid}", file=sys.stderr)
                    collected += 1
                    continue
                if error:
                    failed += 1
                    failure = {
                        "response_id": rid,
                        "question_id": rec.get("question_id", ""),
                        "platform": platform,
                        "wave": wave,
                        "error": error,
                        "timestamp": _utc_now(),
                    }
                    failures.append(failure)
                    with open(failures_path, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(failure, ensure_ascii=False) + "\n")
                    print(f"  FAILED {rid}: {error}", file=sys.stderr)
                    continue
                with open(output_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                collected += 1

    # ── Summary ──
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"Wave {wave} summary:", file=sys.stderr)
    print(f"  Total planned:  {total_planned}", file=sys.stderr)
    print(f"  Collected:      {collected}", file=sys.stderr)
    print(f"  Skipped (exist): {skipped}", file=sys.stderr)
    print(f"  Failed:         {failed}", file=sys.stderr)
    if total_planned > 0:
        print(f"  Failure rate:   {failed / (collected + failed) * 100:.1f}%", file=sys.stderr)
    print(f"  Failures logged: {failures_path}", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)

    # Per-platform failure rates
    if failures:
        plat_counts: dict[str, int] = {}
        for f in failures:
            plat_counts[f["platform"]] = plat_counts.get(f["platform"], 0) + 1
        print("\nPer-platform failures:", file=sys.stderr)
        for p, c in sorted(plat_counts.items()):
            print(f"  {p}: {c}", file=sys.stderr)

    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collect.py",
        description="ARS wave collection runner.",
    )
    parser.add_argument(
        "--config", required=True,
        help="Path to wave config YAML (e.g., collection/wave-01.yaml)",
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--api", action="store_true",
        help="Collect via OpenAI-compatible API endpoints.",
    )
    mode_group.add_argument(
        "--import-manual", metavar="DIR",
        help="Import pasted/CSV transcripts from DIR (for platforms without usable APIs).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Plan and print what would be collected; write nothing.",
    )
    parser.add_argument(
        "--output", default="data/responses.jsonl",
        help="Output path (default: data/responses.jsonl).",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = _REPO_ROOT / config_path
    if not config_path.exists():
        sys.stderr.write(f"ERROR: config not found: {config_path}\n")
        return 2

    config = _load_yaml(config_path)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = _REPO_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    transcripts_dir = None
    if args.import_manual:
        transcripts_dir = Path(args.import_manual)
        if not transcripts_dir.is_absolute():
            transcripts_dir = _REPO_ROOT / transcripts_dir
        if not transcripts_dir.exists():
            sys.stderr.write(f"ERROR: transcripts directory not found: {transcripts_dir}\n")
            return 2

    mode = "api" if args.api else "import-manual"
    return run_wave(config, mode, transcripts_dir, args.dry_run, output_path)


if __name__ == "__main__":
    sys.exit(main())
