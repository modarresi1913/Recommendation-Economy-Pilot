# Collection Infrastructure

This directory contains the **wave runner** — the script that collects AI responses to the active Market Question Cells from configured platforms.

## Files

| File | Description |
|---|---|
| [`collect.py`](./collect.py) | Wave runner: collects responses via API or imports manual transcripts. |
| [`wave-01.example.yaml`](./wave-01.example.yaml) | Annotated example wave configuration. |

## ⚠️ Pre-registration ordering rule

**Waves must not start until the pre-registration (Phase F) is archived.** The coding protocol froze only the *coding* rules (D2, D3), not the *sampling* plan. The sampling plan — which questions, which platforms, how many runs, what cadence — is frozen by the pre-registration. Collecting data before pre-registration creates an unreviewable sampling choice.

Order of operations:
1. Replace draft questions with active questions (`questions/README.md`).
2. Archive the pre-registration (`preregistration/prereg-draft.md` → OSF or equivalent).
3. Configure and run waves (this directory).
4. Double-code, adjudicate, run the reliability gate (`reliability/`).
5. Analyze and publish (`analysis/`).

## Running a wave

### API mode

```bash
# 1. Set environment variables (NEVER put keys in files)
export ARS_PLATFORM_OPENAI_BASE_URL=https://api.openai.com
export ARS_PLATFORM_OPENAI_MODEL=gpt-4o
export ARS_PLATFORM_OPENAI_API_KEY=sk-...

export ARS_PLATFORM_ANTHROPIC_BASE_URL=https://api.anthropic.com
export ARS_PLATFORM_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
export ARS_PLATFORM_ANTHROPIC_API_KEY=sk-ant-...
# ... (one set per platform)

# 2. Dry-run first (plans without collecting)
python collection/collect.py --config collection/wave-01.yaml --api --dry-run

# 3. Real run
python collection/collect.py --config collection/wave-01.yaml --api
```

### Manual import mode (for platforms without usable APIs)

```bash
# Place CSV files as transcripts/{platform}.csv with columns:
# question_id, run, full_text, model_version (optional)
# Or TXT files as transcripts/{platform}-{question_id}-r{run}.txt

python collection/collect.py --config collection/wave-01.yaml --import-manual transcripts/
```

## API keys rule

**API keys are read from environment variables only. Never from files.** A `.env` file is gitignored (see `.gitignore`). If you use a `.env` file locally, source it before running:

```bash
set -a; source .env; set +a
python collection/collect.py --config collection/wave-01.yaml --api
```

Do not commit `.env`. Do not echo keys to stdout or stderr.

## Failure semantics (unknown is not zero)

A failed API request is logged to `collection/failures-{wave}.jsonl` and is **NOT** written to `data/responses.jsonl`. Failed collections never enter the ARS denominator — a failed request is not a negative recommendation (Layer 2 of the protocol's collection rules). The run summary prints per-platform failure rates.

The `analysis/ars.py` script honors this by linking annotations to responses via `response_id`; responses that were never collected have no annotations and are excluded from denominators.

## Idempotency

The wave runner is idempotent: it skips `response_id`s already present in the output file. Re-running a wave after a partial failure resumes from where it left off. Use `--dry-run` to preview without collecting.

## Schema-valid output

Every record written to `data/responses.jsonl` is validated against `schema/response-record.schema.json` **before** it is appended. If a record fails validation, it is refused (fail fast), and the error is logged to the failures file. This prevents schema-invalid data from entering the dataset.

## Platform ToS note

Use only **permitted interfaces** for collection: official APIs, authorized integrations, or web UIs where the platform's Terms of Service permit research use. Do not use scrapers or automated UI testing against platforms that prohibit them. The protocol's Layer 2 (observatory/marketplace separation) requires that the researcher act as an observer using disclosed, authorized interfaces, not as a marketplace participant manipulating rankings.

If a platform's ToS prohibits automated collection, use `--import-manual` with transcripts collected through the platform's web UI under their permitted usage, recording `collection_channel: "web"`.

## Extension point for new platforms

The `PlatformAdapter` class in `collect.py` implements the OpenAI-compatible `/v1/chat/completions` interface. For platforms with non-standard endpoints, subclass `PlatformAdapter` and override `_build_payload` / `_parse_response` (see the class docstring). Register the adapter in `_load_platform_configs`.
