# Changelog

All notable changes to the AI Recommendation Share (ARS) Public Coding Protocol are documented here.
Versioning follows [Semantic Versioning](https://semver.org/). See `PROTOCOL.md` §D11 for the full versioning policy and change-log template.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-11-08

### Added
- Initial release of the ARS Public Coding Protocol (sections D1–D11, appendices A–B).
- Decision procedure (D2): nine-rule cascade R-DP.1–R-DP.9 with Mermaid flowchart.
- Classification rules (D3): full inclusion/exclusion/boundary rule sets for C1–C6 (R-C1 through R-C6).
- Twenty-five worked examples (D4), nineteen of them deliberately borderline.
- Captured-field rules (D5): subtype, recommendation strength, Final Choice determination (R-FC.1–R-FC.5), evidence-span quoting, rank position, platform self-identification and sponsorship metadata.
- Adjudication procedure (D6): double/triple coding, blind re-code, recusal (R-A.5a), documentation requirements.
- Reliability evaluation (D7): Cohen's κ (two coders) and Krippendorff's α (≥3 coders), per-class and aggregate reporting, α ≥ 0.80 target / 0.667 minimum, remediation procedure, Gold Standard subset (≥50 events).
- LLM-assisted coding rules (D8): fixed system prompt, temperature 0, human verification sample, α ≥ 0.85 calibration threshold with justification.
- Ten-item coder onboarding quiz with answer key (D9).
- JSONL annotation schema (D10) with standalone JSON Schema file at `schema/ars-record.schema.json`.
- Versioning and governance (D11): semantic versioning, freeze-before-measurement rule, change-log template, initial change log.
- Glossary (Appendix A) and Known Ambiguities register (Appendix B, KA-1 through KA-12).

### Rationale
- Baseline protocol frozen for measurement. Incorporates determinism fixes from the Pass-2 self-audit: operative-stance test (R-DP.3), explicit/implicit marker inventories (R-C4.2, R-C4.3), Final-Choice rule renumbering (R-FC.1–R-FC.5), C5-subtype-is-always-explicit (R-F.1a), comparative-is-not-a-rank (R-C5.8), out-of-category recommendations (R-C4.10), ADJUDICATE reliability handling (R-R.1, R-R.2), missing-data → use alpha (R-R.1a), adjudicator recusal (R-A.5a), Gold Standard post-adjudication inclusion (R-R.5), LLM calibration-threshold justification (R-L.8), strength-scale note (R-F.5).

### Re-coding required
- No (initial release).

### Known ambiguities carried forward (owner decisions pending)
- **KA-1**: Sponsored / platform-self-identified appearances — inclusive vs exclusive headline ARS. Default: classify on substantive text; report both.
- **KA-2**: Hedge language ("may be worth considering") with a condition matching the buyer's profile. Default: C3.
- **KA-11**: Brand alias resolution — whether to publish a canonical brand registry per category. Default: record literal token, use most plausible canonical name, adjudicate if identity changes the code.
