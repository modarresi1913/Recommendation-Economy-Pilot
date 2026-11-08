# Validator (`validation/validate.py`)

Validates ARS response and annotation JSONL files against their JSON Schemas and enforces cross-record constraints that a per-record schema cannot express (notably R-FC.5 response-level `final_choice` consistency).

## Usage

```bash
python validation/validate.py \
    --responses data/responses.jsonl \
    --annotations data/annotations.jsonl \
    [--strict]
```

### Prerequisites

- Python 3.10+
- `jsonschema` package: `pip install jsonschema`

The script loads schemas from `schema/ars-record.schema.json` and `schema/response-record.schema.json` relative to the repository root, so it must be run from within the repository (or the `validation/` directory must remain at its repo-relative path).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | No errors. Warnings may be present (unless `--strict`). |
| 1 | One or more errors, OR warnings when `--strict` is set. |
| 2 | Usage error or unrecoverable I/O failure (file not found, invalid path). |

## Errors (exit 1)

| Code | Check | Rule |
|---|---|---|
| E1 | Per-record JSON Schema compliance — every response record validated against `response-record.schema.json`; every annotation record validated against `ars-record.schema.json` (including the `allOf`/`if`-`then` conditional constraints on `class_code`). | D10, §10.3a |
| E2 | R-FC.5 — within each `(response_id, coder_id)` group: exactly one `final_choice = true` (rest `false`), or all `null`. Mixed `true` + `null`, multiple `true`, or `false` + `null` with no `true` are all errors. | R-FC.5 |
| E3 | Referential integrity — every `response_id` in annotations must exist in the responses file; every response in the responses file must have at least one annotation record (missing from coding round). | D10 |
| E4 | `evidence_span` must be a verbatim substring of the response's `full_text`. | R-F.8 |
| E5 | `final_choice = true` only for C4/C5 events; no duplicate `(response_id, coder_id, brand)` triples. | R-FC.3, R-FC.5 |

## Warnings (exit 0 unless `--strict`)

| Code | Check | Rule |
|---|---|---|
| W1 | Duplicate `rank_position` within a `(response_id, coder_id)` group. Permitted only for category winners (R-F.13); the warning fires when `rationale` does not contain the word "category". | R-F.13 |
| W2 | Mixed `protocol_version` values across the annotation dataset. All records in a measurement cycle should share one version (R-V.3). | R-V.3 |
| W3 | `model_version` is `null` in a response record. Should record the platform's disclosed model identifier. | D10 §10.5 |

## `--strict` flag

When set, warnings are treated as errors — the script exits with code 1 if any warnings are present. Use this in CI or pre-freeze checks to enforce a fully clean dataset.

## Report format

Output is grouped by error and warning codes. Each finding includes:
- The code (e.g., `[E2]`)
- A one-line message
- Context: `response_id`, `brand`, `coder_id` (where applicable)
- A `detail` line with the specific schema path or value

A final summary line reports the total error and warning counts.

## Example session

```bash
$ python validation/validate.py --responses data/responses.jsonl --annotations data/annotations.jsonl

============================================================
ERRORS (2 total)
============================================================

--- E2 (1 occurrences) ---
[E2] final_choice inconsistency: 2 true values in group of 3
  response_id=resp-0007, coder_id=human-coder-04
  detail: R-FC.5 requires exactly one true; multiple winners detected.

--- E4 (1 occurrences) ---
[E4] evidence_span is not a verbatim substring of the response full_text
  response_id=resp-0012, brand=Pipedrive, coder_id=human-coder-02
  detail: span (first 80 chars): 'Pipedrive is the best CRM for startups...'

------------------------------------------------------------
Summary: 2 error(s), 0 warning(s)
------------------------------------------------------------

$ echo $?
1
```
