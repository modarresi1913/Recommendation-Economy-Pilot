# Changelog

All notable changes to the AI Recommendation Share (ARS) Public Coding Protocol are documented here.
Versioning follows [Semantic Versioning](https://semver.org/). See `PROTOCOL.md` §D11 for the full versioning policy and change-log template.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] — 2026-11-08

### Added
- **R-F.6 (ADJUDICATE event field values):** for `class_code = "ADJUDICATE"`, `subtype`, `strength`, `rank_position`, and `final_choice` must be `null`; `evidence_span` must quote the ambiguous passage; `rationale` must cite R-DP.9 and name candidate codes (DF-2).
- **R-F.7 (Category-winner strength):** C5 category winners under R-C5.5 (matching a stated need, not overall winner) record `rank_position = 1` and `strength = 3`; strength 4–5 reserved for overall ordered preferences (DF-2, DF-7).
- **KA-13:** Known Ambiguity entry for category-winner vs overall-winner strength conflation (DF-7).
- `schema/response-record.schema.json`: new JSON Schema (draft 2020-12) for `data/responses.jsonl`, with fields `response_id`, `question_id`, `platform`, `model_version`, `language`, `timestamp_collected`, `full_text`, `citations`, `sponsored_block_present`, `self_disclosure`, `collection_channel`, `collection_version` (DF-6).
- `validation/validate.py`: standalone dataset validator enforcing E1–E5 (errors) and W1–W3 (warnings) with `--strict` flag (DF-4).
- `validation/README.md`: validator documentation with error/warning code reference and exit codes (DF-4).
- D10 §10.5: Response record schema subsection defining each field with recording rules (DF-6).
- D10 §10.3a: Conditional constraints table documenting the `if`/`then` rules enforced by the annotation schema (DF-3).
- `CITATION.cff`: CFF 1.2 citation file (S1).
- `LICENSE-CODE`: MIT license for code artifacts (schemas, validator) (S2).
- README "Data availability" section and dual-license notice (S3).

### Changed
- `schema/ars-record.schema.json`: `$id` updated from `https://example.org/...` to canonical GitHub raw URL `https://raw.githubusercontent.com/modarresi1913/Recommendation-Economy-Pilot/main/schema/ars-record.schema.json` (DF-1).
- `schema/ars-record.schema.json`: added `allOf` with `if`/`then` blocks per `class_code` enforcing subtype/strength/rank_position constraints (DF-3).
- R-F.4 mapping table: strength-3 row updated to "≥ 3 **or category winner (R-F.7)**"; ADJUDICATE added to the null row (DF-7).
- R-F.14 amended: per-event `platform_self_id` flag applies only when a classified brand IS the platform; response-level disclosures naming no classified brand go in the response record's `self_disclosure` object (DF-5).
- Q10 answer text amended to record the OpenAI disclosure at the response level (`self_disclosure` object) rather than as a per-event flag; classification codes unchanged (DF-5).
- E22 strength annotation corrected: Pipedrive (category winner) strength 5 → 3 per R-F.7; class and rank unchanged (DF-2).
- README validation snippet replaced with full `validate.py` usage and exit codes; all version mentions updated to 1.1.0 (S3).
- `.gitignore`: added `data/_scratch/` for local data scratch (S5).
- D1 front matter and D10 §10.3 inline schema: version updated to 1.1.0; `$id` added to inline JSON.

### Rationale
- External audit defect fixes DF-1–DF-7 prior to measurement freeze.

### Re-coding required
- No.

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
