<!--
  Schema.org structured data (JSON-LD) for search-engine and AI-assistant discovery.
  This block makes the repository discoverable as a SoftwareApplication with
  defined properties. Edit the version/date when releasing.
-->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "AI Recommendation Share — Public Coding Protocol",
  "applicationCategory": "ResearchTool",
  "operatingSystem": "Cross-platform",
  "softwareVersion": "1.1.0",
  "datePublished": "2026-11-08",
  "description": "A deterministic, publication-ready coding protocol for classifying brand appearances in AI-generated responses. Measures how frequently brands receive qualified recommendations across buyer-intent questions posed to AI platforms.",
  "url": "https://github.com/modarresi1913/Recommendation-Economy-Pilot",
  "codeRepository": "https://github.com/modarresi1913/Recommendation-Economy-Pilot",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "author": {
    "@type": "Person",
    "name": "Seyed Alireza Alhosseini Almodarresieh"
  },
  "keywords": "LLM, measurement, content analysis, AI visibility, recommendation systems, inter-coder reliability, Krippendorff alpha, coding protocol"
}
</script>

<div align="center">

# AI Recommendation Share (ARS)

### Public Coding Protocol

**A deterministic, publication-ready instrument for measuring brand visibility in AI-generated recommendations.**

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/modarresi1913/Recommendation-Economy-Pilot/releases/tag/v1.1.0)
[![License: CC-BY-4.0](https://img.shields.io/badge/protocol-CC--BY--4.0-green.svg)](./LICENSE)
[![License: MIT](https://img.shields.io/badge/code-MIT-orange.svg)](./LICENSE-CODE)
[![Status: Frozen](https://img.shields.io/badge/status-frozen%20for%20measurement-success.svg)](./PROTOCOL.md#d1-front-matter-and-scope)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![JSON Schema](https://img.shields.io/badge/schema-draft%202020--12-purple.svg)](https://json-schema.org/)

<!-- Zenodo DOI badge — uncomment after archiving:
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.YOUR_DOI.svg)](https://doi.org/10.5281/zenodo.YOUR_DOI)
-->

</div>

---

## Why this exists

As buyers increasingly ask AI platforms — ChatGPT, Claude, Gemini, Perplexity — for product recommendations, brands gain or lose visibility based on what these systems say. **There has been no standardized, reproducible method to measure which brands AI platforms recommend and how strongly.** ARS fills that gap.

> **In one sentence:** ARS is an open coding protocol that classifies every brand appearance in an AI response into one of six classes, so researchers can measure how often each brand receives a *qualified recommendation*.

---

## What it measures

| Metric | Definition | Range |
|---|---|---|
| **Recommendation Incidence** | Count of all qualifying recommendations (C4 + C5) in a response. | 0 to *n* brands per response |
| **Final Choice Incidence** | Count of the single winning recommendation, where one exists. | 0 or 1 per response |

Recommendation Incidence is **not exclusive share** — one response can recommend several brands, so per-brand percentages may sum to more than 100%. The two metrics are recorded separately and never merged.

### The six-class taxonomy

| Code | Class | Definition | Counts toward ARS? |
|:---:|---|---|:---:|
| **C1** | Mention | Brand is named only. | No |
| **C2** | Neutral inclusion | Listed among alternatives, no endorsement or rejection. | No |
| **C3** | Positive consideration | Favorably described, but not recommended for the buyer's stated needs. | No |
| **C4** | Qualified recommendation | Recommended as suitable for the buyer's stated requirements. | **Yes** |
| **C5** | Ranked recommendation | Assigned an explicit priority or rank. | **Yes** |
| **C6** | Rejection or warning | Discouraged or identified as unsuitable. | No |

A **qualified recommendation** (C4/C5) must satisfy three conditions: (1) suitability is communicated, not merely named or described; (2) the recommendation relates to the buyer requirements stated in the question; (3) the response contains enough context to support the classification.

---

## Why you can trust it

| Property | How it's guaranteed | Rule |
|---|---|---|
| **Deterministic** | Every rule is written so two trained coders reach the same code, or the rule is rewritten. | R-DP.1–R-DP.9 |
| **Conservative** | When ambiguous, the protocol never inflates a recommendation (C3 over C4, C4 over C5). | §1.3, Appendix B |
| **Reliable** | Double coding + adjudication + Krippendorff's α ≥ 0.800 target. | R-R.1–R-R.4 |
| **Machine-validatable** | JSON Schema with `if`/`then` constraints + a dataset validator. | D10, `validation/` |
| **Frozen** | Classification rules are locked before measurement; only PATCH changes during a cycle. | R-V.3 |
| **Reproducible** | Semantic versioning, change log, Gold Standard for calibration. | D11, R-R.5 |

### Reliability thresholds

| Krippendorff's α | Interpretation | Action |
|:---:|---|---|
| ≥ 0.800 | Good | Measurement-ready |
| 0.667 – 0.800 | Tentative | Acceptable with caveat |
| < 0.667 | Unacceptable | Remediate before publishing |

---

## Quick start

### Validate a dataset

```bash
pip install jsonschema

python validation/validate.py \
    --responses data/responses.jsonl \
    --annotations data/annotations.jsonl
```

**Exit codes:** `0` clean · `1` errors (or warnings under `--strict`) · `2` I/O failure

The validator enforces 5 error classes (E1–E5) and 3 warning classes (W1–W3). See [`validation/README.md`](./validation/README.md) for the full reference.

### As a human coder

1. **Read** [`PROTOCOL.md`](./PROTOCOL.md) — sections D1–D4 (scope, decision procedure, classification rules, worked examples).
2. **Take the quiz** (D9) — score ≥ 8/10 to be certified.
3. **Calibrate** against the Gold Standard (D7) — reach α ≥ 0.80.
4. **Code** — apply the decision procedure (D2) to every brand–response event; cite rule IDs in every rationale.

### As an LLM-coder operator

1. **Use the fixed system prompt** in D8 at temperature 0.
2. **Calibrate** against the Gold Standard — reach α ≥ 0.85 (R-L.8).
3. **Verify** ≥ 20% of LLM-coded events with a human coder (R-L.5).

---

## Pipeline

The execution order is strict. **Pre-registration must precede the first wave; reliability gates must precede publication of figures.**

```
1. Replace draft questions → questions/README.md
       ↓
2. Pre-register            → preregistration/prereg-draft.md → archive on OSF
       ↓
3. Collect waves           → collection/collect.py --api (or --import-manual)
       ↓
4. Double-code + adjudicate → apply PROTOCOL.md D2–D6
       ↓
5. Reliability gate        → reliability/reliability.py (α ≥ 0.667 to proceed)
       ↓
6. Analyze                 → analysis/ars.py (Wilson CIs, duality) → analysis/glmm.R
       ↓
7. Publish + archive       → GitHub release → Zenodo DOI → cite
```

**Key rule:** ARS figures are not published unless the reliability gate passed for the classes they depend on (C4, C5). See [`analysis/README.md`](./analysis/README.md).

---

## Repository structure

```
Recommendation-Economy-Pilot/
├── PROTOCOL.md                      # Normative protocol (D1–D11, appendices A–B)
├── schema/
│   ├── ars-record.schema.json       # Annotation record schema (with if/then constraints)
│   └── response-record.schema.json  # Response record schema
├── questions/
│   ├── questions.schema.json        # MQC record schema
│   ├── questions-draft.yaml         # 30 draft MQCs (replace before measurement)
│   └── README.md                    # Registry governance
├── collection/
│   ├── collect.py                   # Wave runner (API + manual import modes)
│   ├── wave-01.example.yaml         # Annotated wave config
│   └── README.md                    # Collection docs + pre-reg ordering rule
├── reliability/
│   ├── reliability.py               # Cohen's kappa + Krippendorff's alpha (D7)
│   └── README.md                    # Threshold table + Gold Standard onboarding
├── analysis/
│   ├── ars.py                       # ARS, Final Choice, volatility, Wilson CIs
│   ├── glmm.R                       # Mixed-effects logistic regression
│   └── README.md                    # Pipeline order + reliability gate rule
├── validation/
│   ├── validate.py                  # Dataset validator (E1–E5, W1–W3)
│   └── README.md                    # Validator documentation
├── data/
│   ├── README.md                    # Data dictionary + Zenodo procedure
│   └── adjudications/               # Adjudication records (R-A.9, R-A.10)
├── preregistration/
│   └── prereg-draft.md              # OSF-ready pre-registration (archive before waves)
├── docs/
│   ├── SUMMARY.md                   # One-page executive brief (AEO-optimized)
│   ├── FAQ.md                       # Structured Q&A (schema.org FAQPage)
│   └── CONCEPTS.md                  # Definitional glossary (entity extraction)
├── .github/workflows/validate.yml   # CI: syntax-check + validate on push/PR
├── CITATION.cff                     # CFF 1.2 citation file
├── CHANGELOG.md                     # Versioned change log
├── LICENSE                          # CC-BY-4.0 (protocol text + data)
└── LICENSE-CODE                     # MIT (code: schemas, validator, scripts)
```

---

## Data availability

Responses and annotations are published in `data/` as schema-conformant JSONL:

| File | Contents | Schema |
|---|---|---|
| `data/responses.jsonl` | One record per AI response (full text, model version, self-disclosure, citations) | [`response-record.schema.json`](./schema/response-record.schema.json) |
| `data/annotations.jsonl` | One record per brand–response event (class code, subtype, strength, evidence span, rationale) | [`ars-record.schema.json`](./schema/ars-record.schema.json) |

All datasets are validated with `validation/validate.py` before release.

---

## Documentation

| For… | Read this |
|---|---|
| **A quick overview** | [`docs/SUMMARY.md`](./docs/SUMMARY.md) — executive brief in under 500 words |
| **Common questions** | [`docs/FAQ.md`](./docs/FAQ.md) — 9 structured Q&As with schema.org markup |
| **Term definitions** | [`docs/CONCEPTS.md`](./docs/CONCEPTS.md) — glossary for citation and entity extraction |
| **The full protocol** | [`PROTOCOL.md`](./PROTOCOL.md) — the normative document (D1–D11) |
| **Question registry** | [`questions/README.md`](./questions/README.md) — MQC governance and replacement workflow |
| **Running a wave** | [`collection/README.md`](./collection/README.md) — API/manual modes, failure semantics, pre-reg ordering |
| **Reliability checks** | [`reliability/README.md`](./reliability/README.md) — D7 thresholds, Gold Standard onboarding |
| **Analysis pipeline** | [`analysis/README.md`](./analysis/README.md) — ARS, GLMM, Wilson CIs, reliability gate |
| **Validator usage** | [`validation/README.md`](./validation/README.md) — error/warning codes and exit codes |
| **Data dictionary** | [`data/README.md`](./data/README.md) — file inventory, privacy, Zenodo procedure |
| **Pre-registration** | [`preregistration/prereg-draft.md`](./preregistration/prereg-draft.md) — archive before waves |
| **Version history** | [`CHANGELOG.md`](./CHANGELOG.md) — what changed in each release |

---

## Governance

The classification rules (D2, D3) are **frozen before measurement begins** (R-V.3). During a measurement cycle, only PATCH changes are permitted. MAJOR and MINOR changes are queued for the next cycle and require owner approval (R-V.5).

- **Current version:** 1.1.0
- **Latest release:** [v1.1.0](https://github.com/modarresi1913/Recommendation-Economy-Pilot/releases/tag/v1.1.0)
- **Known ambiguities:** [Appendix B of PROTOCOL.md](./PROTOCOL.md) — 13 unresolved judgment calls with conservative defaults

### Contributing

Proposed changes are submitted as pull requests citing the adjudication incident(s) or reliability finding(s) that motivate them (R-V.6). Before opening a PR, confirm the change's version impact (MAJOR / MINOR / PATCH) per D11.

---

## Citation

```bibtex
@software{ars_coding_protocol_2026,
  author       = {Almodarresieh, Seyed Alireza Alhosseini},
  title        = {AI Recommendation Share — Public Coding Protocol},
  version      = {1.1.0},
  year         = {2026},
  url          = {https://github.com/modarresi1913/Recommendation-Economy-Pilot},
  license      = {CC-BY-4.0}
}
```

See [`CITATION.cff`](./CITATION.cff) for the canonical CFF 1.2 citation. GitHub will auto-generate citation metadata from this file on the repository page.

---

## License

| Component | License | File |
|---|---|---|
| **Protocol text** (`PROTOCOL.md`, `README.md`, `CHANGELOG.md`, `docs/`, `validation/README.md`) | [CC-BY-4.0](./LICENSE) — attribution required | [`LICENSE`](./LICENSE) |
| **Code** (`schema/`, `validation/validate.py`, `CITATION.cff`) | [MIT](./LICENSE-CODE) — copyright 2026 Seyed Alireza Alhosseini Almodarresieh | [`LICENSE-CODE`](./LICENSE-CODE) |

---

<div align="center">

**[Report an issue](https://github.com/modarresi1913/Recommendation-Economy-Pilot/issues)** ·
**[View releases](https://github.com/modarresi1913/Recommendation-Economy-Pilot/releases)** ·
**[Read the protocol](./PROTOCOL.md)**

</div>
