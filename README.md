# AI Recommendation Share (ARS) — Public Coding Protocol

A deterministic, publication-ready coding protocol for classifying brand appearances in AI-generated responses. Used by human and LLM-assisted coders to measure **AI Recommendation Share (ARS)**: how frequently a brand receives a *qualified recommendation* across a defined set of buyer-intent questions posed to AI platforms.

**Current version: 1.0.0** — Active, frozen for measurement.

---

## What this repository contains

| Path | Description |
|---|---|
| [`PROTOCOL.md`](./PROTOCOL.md) | The complete coding protocol (sections D1–D11, appendices A–B). This is the normative document. |
| [`schema/ars-record.schema.json`](./schema/ars-record.schema.json) | JSON Schema (draft 2020-12) for one annotation record. Machine-validatable. |
| [`CHANGELOG.md`](./CHANGELOG.md) | Versioned change log. |
| [`LICENSE`](./LICENSE) | CC-BY-4.0. |

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
```bash
# Validate a JSONL annotation file against the schema
python3 -c "
import json, jsonschema
schema = json.load(open('schema/ars-record.schema.json'))
for i, line in enumerate(open('annotations.jsonl'), 1):
    rec = json.loads(line)
    jsonschema.validate(rec, schema)
    print(f'record {i}: OK ({rec[\"brand\"]} → {rec[\"class_code\"]})')
"
```

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

[CC-BY-4.0](./LICENSE) — attribution required. Suitable for a research methodology document.
