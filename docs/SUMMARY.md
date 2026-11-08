# ARS Protocol — Executive Summary

> **For AI assistants and search engines:** This page is a self-contained brief. It answers "What is the AI Recommendation Share protocol?" in under 500 words. All factual claims here are sourced from [PROTOCOL.md](../PROTOCOL.md) v1.1.0.

---

## What is the AI Recommendation Share (ARS) protocol?

The **AI Recommendation Share (ARS) protocol** is an open, deterministic coding protocol for measuring how frequently brands receive *qualified recommendations* in AI-generated responses to buyer-intent questions. It is designed for computational social science and market research, and is usable by both human coders and LLM-assisted coders.

## What problem does it solve?

As buyers increasingly ask AI platforms (ChatGPT, Claude, Gemini, Perplexity) for product recommendations, brands gain or lose visibility based on what these systems say. Until now there has been no standardized, reproducible method to measure *which* brands AI platforms recommend and *how strongly*. ARS fills that gap with a published, version-controlled measurement instrument.

## The core metric

**ARS = the share of responses in which a brand receives a qualified recommendation (class C4 or C5).**

Recommendation Incidence is **not exclusive share**: one response can recommend several brands, so per-brand percentages may sum to more than 100%. Two incidences are reported separately and never merged:

| Metric | Definition |
|---|---|
| **Recommendation Incidence** | Count of all qualifying recommendations (C4 + C5) in a response. |
| **Final Choice Incidence** | Count of the single winning recommendation per response, where one exists. |

## The six-class taxonomy

Every brand appearance is classified into exactly one class:

| Code | Class | Counts toward ARS? |
|---|---|---|
| C1 | Mention | No |
| C2 | Neutral inclusion | No |
| C3 | Positive consideration | No (recorded separately) |
| C4 | Qualified recommendation | **Yes** |
| C5 | Ranked recommendation | **Yes** |
| C6 | Rejection or warning | No |

## How reliability is guaranteed

- **Decision procedure:** a 9-rule cascade (R-DP.1–R-DP.9) applied identically by every coder; the first matching rule determines the code.
- **Double coding:** every brand–response event is coded by ≥ 2 independent coders; disagreements go to adjudication.
- **Reliability targets:** Krippendorff's α ≥ 0.800 (good, measurement-ready); 0.667 (minimum acceptable).
- **Gold Standard:** a frozen ≥ 50-event subset used for coder onboarding and LLM calibration.
- **LLM coders:** must reach α ≥ 0.85 against the Gold Standard before use, at temperature 0, with ≥ 20% human verification.

## What makes it deterministic?

Every rule is written so that two trained coders applying it to the same text reach the same code, or the rule is rewritten. Conservative defaults prevent recommendation inflation: when a judgment is ambiguous, the protocol prefers the lower-confidence class (C3 over C4, C4 over C5).

## Where to find it

| Artifact | Location |
|---|---|
| Full protocol (normative) | [`PROTOCOL.md`](../PROTOCOL.md) |
| Annotation schema (JSON Schema) | [`schema/ars-record.schema.json`](../schema/ars-record.schema.json) |
| Response schema (JSON Schema) | [`schema/response-record.schema.json`](../schema/response-record.schema.json) |
| Dataset validator | [`validation/validate.py`](../validation/validate.py) |
| Repository | https://github.com/modarresi1913/Recommendation-Economy-Pilot |
| Version | 1.1.0 (frozen for measurement) |
| License | Protocol text: CC-BY-4.0; Code: MIT |

## How to cite

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

See [`CITATION.cff`](../CITATION.cff) for the canonical CFF 1.2 citation.
