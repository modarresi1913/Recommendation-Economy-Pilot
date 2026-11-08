# AI Recommendation Share (ARS) — Public Coding Protocol

A deterministic, publication-ready coding protocol for classifying brand appearances in AI-generated responses. Used by human and LLM-assisted coders to measure **AI Recommendation Share (ARS)**: how frequently a brand receives a *qualified recommendation* across a defined set of buyer-intent questions posed to AI platforms.

**Current version: 1.1.0** — Active, frozen for measurement.

<!-- Zenodo DOI badge — uncomment after archiving:
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.YOUR_DOI.svg)](https://doi.org/10.5281/zenodo.YOUR_DOI)
-->

---

## What this repository contains

| Path | Description |
|---|---|
| [`PROTOCOL.md`](./PROTOCOL.md) | The complete coding protocol (sections D1–D11, appendices A–B). This is the normative document. |
| [`schema/ars-record.schema.json`](./schema/ars-record.schema.json) | JSON Schema (draft 2020-12) for one annotation record, with `if`/`then` conditional constraints on `class_code`. |
| [`schema/response-record.schema.json`](./schema/response-record.schema.json) | JSON Schema (draft 2020-12) for one response record (the AI-generated text). |
| [`validation/validate.py`](./validation/validate.py) | Dataset validator — checks schema compliance, R-FC.5 response-level consistency, referential integrity, evidence-span verbatimness, and more. |
| [`validation/README.md`](./validation/README.md) | Validator documentation, error/warning codes, and exit codes. |
| [`CHANGELOG.md`](./CHANGELOG.md) | Versioned change log. |
| [`CITATION.cff`](./CITATION.cff) | CFF 1.2 citation file. |
| [`LICENSE`](./LICENSE) | CC-BY-4.0 (protocol text). |
| [`LICENSE-CODE`](./LICENSE-CODE) | MIT (code: schemas, validator). |

## What ARS measures

ARS measures **recommendation incidence, not exclusive share**. Per-brand percentages may sum to more than 100% because one response can recommend multiple brands. Two incidences are recorded separately and never merged:

- **Recommendation Incidence** — counts all qualifying recommendations (classes C4 + C5) in a response.
- **Final Choice Incidence** — counts only the primary/winning recommendation, where one exists.

## The six-class taxonomy

| Code | Class | Counts toward ARS? |
|---|---|---|
| C1 | Mention | No |
| C2 | Neutral inclusion | No |
| C3 | Positive consideration | No (recorded separately) |
| C4 | Qualified recommendation | **Yes** |
| C5 | Ranked recommendation | **Yes** |
| C6 | Rejection or warning | No |

A **qualified recommendation** (C4 or C5) must satisfy three conditions: (1) the response communicates that the brand is a suitable option, not merely names or describes it; (2) the recommendation relates to the buyer requirements stated in the question (the Market Question Cell); (3) the response contains enough context to support the classification.

## How to use this protocol

### As a human coder
1. Read [`PROTOCOL.md`](./PROTOCOL.md) in full, sections D1–D4.
2. Take the onboarding quiz (D9); score ≥ 8/10 to be certified.
3. Code a calibration set against the Gold Standard (D7); reach α ≥ 0.80 before coding live data.
4. Apply the decision procedure (D2) to every brand–response event. Cite rule IDs in every rationale.

### As an LLM-coder operator
1. Use the fixed system prompt in D8 at temperature 0.
2. Calibrate against the Gold Standard; reach α ≥ 0.85 before any LLM coder is trusted (D8, R-L.8).
3. Verify ≥ 20% of LLM-coded events with a human coder (R-L.5).

### Validating annotation output

Use `validation/validate.py` to check both response and annotation JSONL files:

```bash
pip install jsonschema

python validation/validate.py \
    --responses data/responses.jsonl \
    --annotations data/annotations.jsonl
```

Add `--strict` to treat warnings as errors (recommended for CI or pre-freeze checks).

**Exit codes:** `0` = clean (warnings may be present), `1` = errors (or warnings under `--strict`), `2` = I/O or usage error.

The validator enforces:
- **E1** — per-record JSON Schema compliance (both schemas, including `if`/`then` conditional constraints)
- **E2** — R-FC.5 response-level `final_choice` consistency (exactly one `true` or all `null` per coder)
- **E3** — referential integrity (annotations ↔ responses)
- **E4** — `evidence_span` is a verbatim substring of the response's `full_text`
- **E5** — `final_choice = true` only for C4/C5; no duplicate `(response_id, coder_id, brand)` triples

And warns on:
- **W1** — duplicate `rank_position` (category-winner check)
- **W2** — mixed `protocol_version` across the dataset
- **W3** — missing `model_version` in a response record

See [`validation/README.md`](./validation/README.md) for full details.

## Data availability

Responses and annotations will be published in `data/` as schema-conformant JSONL:
- `data/responses.jsonl` — one record per AI response, conforming to `schema/response-record.schema.json`
- `data/annotations.jsonl` — one record per brand–response event, conforming to `schema/ars-record.schema.json`

All datasets are validated with `validation/validate.py` before release.

## Reliability targets

| Krippendorff's α | Interpretation |
|---|---|
| α ≥ 0.800 | Good; measurement-ready |
| 0.667 ≤ α < 0.800 | Tentative; acceptable with caveat |
| α < 0.667 | Unacceptable; remediate |

## Governance

The classification rules (D2, D3) are **frozen before measurement begins** (R-V.3). During a measurement cycle, only PATCH changes are permitted. MAJOR and MINOR changes are queued for the next cycle and require owner approval (R-V.5).

See [`CHANGELOG.md`](./CHANGELOG.md) for version history and the *Known Ambiguities* appendix (Appendix B of `PROTOCOL.md`) for unresolved judgment calls with their conservative defaults.

## Contributing

Proposed changes are submitted as pull requests citing the adjudication incident(s) or reliability finding(s) that motivate them (R-V.6). Before opening a PR, confirm the change's version impact (MAJOR / MINOR / PATCH) per D11.

## License

- **Protocol text** ([`PROTOCOL.md`](./PROTOCOL.md), [`README.md`](./README.md), [`CHANGELOG.md`](./CHANGELOG.md), [`validation/README.md`](./validation/README.md)): [CC-BY-4.0](./LICENSE) — attribution required.
- **Code** ([`schema/`](./schema/), [`validation/validate.py`](./validation/validate.py), [`CITATION.cff`](./CITATION.cff)): [MIT](./LICENSE-CODE) — copyright 2026 Seyed Alireza Alhosseini Almodarresieh.
