# ARS Protocol — Concept Glossary

> This page defines every key concept in the ARS protocol as a self-contained entity. AI assistants and search engines extract these definitions as cited snippets. Each definition is sourced from [PROTOCOL.md](../PROTOCOL.md) v1.1.0 and is normative.

---

## A

### AI Recommendation Share (ARS)
The metric measured by this protocol: the share of AI-generated responses in which a brand receives a *qualified recommendation* (class C4 or C5). ARS measures **recommendation incidence, not exclusive share** — per-brand percentages may sum to more than 100% because one response can recommend multiple brands.

### Adjudication
The process of resolving disagreements between coders. A disagreed event is re-coded blind by an adjudicator who was not one of the original coders (R-A.5a). If the adjudicator's code matches one original code, it is adopted; otherwise the coders convene to reach consensus, with the adjudicator's code prevailing as a fallback.

### ADJUDICATE (class code)
A seventh `class_code` value, not part of the C1–C6 taxonomy, used when no rule from R-DP.3 through R-DP.8 resolves the classification. The event is flagged for adjudication per R-DP.9. For ADJUDICATE events: `subtype = null`, `strength = null`, `rank_position = null`, `final_choice = null` (R-F.6).

## B

### Brand–response event
The **unit of analysis** in the ARS protocol: one brand × one AI response. A single response that names *n* distinct brands yields up to *n* brand–response events. Each event is classified into exactly one of C1–C6 (or ADJUDICATE).

### Buyer-intent question
A standardized question posed to an AI platform that simulates a buyer asking for a product recommendation. The pilot scope uses 30 questions across three B2B software categories: CRM (10), project management (10), AI coding assistants (10).

## C

### C1 — Mention
Brand is named only, with no descriptive, evaluative, or comparative content beyond identification. Does not count toward ARS.

### C2 — Neutral inclusion
Brand appears among alternatives without endorsement or rejection. Factual attributes (including factual shortcomings) without evaluative judgment. Does not count toward ARS.

### C3 — Positive consideration
Brand receives favorable description but is not recommended for the buyer's stated needs. Does not count toward ARS but is recorded separately for analysis.

### C4 — Qualified recommendation
Brand is recommended as suitable for the buyer's stated requirements (explicit or implicit). **Counts toward ARS.** Subtypes: `explicit` (uses a recommendation marker from the R-C4.2 inventory) or `implicit` (comparative or eliminative conclusion without an explicit marker).

### C5 — Ranked recommendation
Brand receives an explicit priority or rank ("top pick", "best fit", "#1", "first choice", "I'd start with"). **Counts toward ARS.** `subtype` is always `explicit` (R-F.1a). `rank_position` is an integer ≥ 1.

### C6 — Rejection or warning
Brand is discouraged or identified as unsuitable for the buyer's stated needs. Does not count toward ARS.

### Cascade (decision)
The ordered sequence of tests applied to every brand–response event: C6 → C5 → C4 → C3 → C2 → C1 (via R-DP.3–R-DP.8). The **first** matching test determines the code. The order encodes the operative-stance principle and the conservative-default principle.

### Cohen's kappa (κ)
The inter-coder reliability statistic for two coders, computed on `class_code` across all events. Reported as aggregate and per-class (one-vs-rest). Used when the design is fully balanced; otherwise Krippendorff's α is preferred (R-R.1a).

### Collection version
The semantic version of the data-collection instrument (distinct from `protocol_version`, which is the coding protocol). Recorded in the response record.

### Conservative default
The principle that when a classification judgment is genuinely ambiguous and cannot be resolved by a cited rule, the coder applies the interpretation that never inflates a recommendation: preferring C3 over C4, C4 over C5, and C6 over any positive code when the operative stance is rejection.

## D

### Decision procedure
The 9-rule cascade (R-DP.1–R-DP.9) that every coder applies to each brand–response event, from brand detection to final code. Documented in PROTOCOL.md §D2 with a Mermaid flowchart.

## E

### Evidence span
A verbatim substring of the response that supports the assigned code. Must be copied character-for-character (no paraphrase) and be sufficient for a second coder to reach the same code without consulting the rest of the response (R-F.8). The validator (E4) confirms the span is a substring of the response's `full_text`.

### Explicit recommendation (subtype)
A C4 or C5 event whose evidence span contains an explicit recommendation marker from the R-C4.2 inventory: "recommend", "I'd go with", "I'd pick/choose", "you should use/pick/choose", "the right choice is", "my advice is", "I suggest", "opt for", "go with X". For C5, the subtype is always explicit (R-F.1a).

## F

### Final Choice
The single operative winning brand in a response, identified by priority order (R-FC.2): (1) explicit winner statement; (2) a single C5 rank-1 event; (3) a sole C4 event. Recorded as `final_choice = true` for the winner, `false` for others, `null` for all when no winner exists.

### Final Choice Incidence
The metric counting only the single winning recommendation per response, where one exists. Distinct from Recommendation Incidence and never merged with it.

## G

### Gold Standard
A frozen subset of ≥ 50 brand–response events with full agreement across ≥ 3 trained coders (assessed post-adjudication). Used for (a) onboarding new human coders (must reach α ≥ 0.80), (b) LLM-coder calibration (must reach α ≥ 0.85), and (c) regression testing when the protocol is amended (R-R.5–R-R.7).

## I

### Implicit recommendation (subtype)
A C4 event whose evidence span reaches a comparative or eliminative conclusion favoring the brand for the buyer's stated needs without any explicit recommendation marker from the R-C4.2 inventory. Implicit markers include "the better fit", "the natural fit/choice", "stands out for", "is the stronger option for", "makes the most sense for", "fits your needs" (R-C4.3).

## K

### Krippendorff's alpha (α)
The inter-coder reliability statistic for three or more coders, computed on `class_code` across all events and all coders. Reported as aggregate and per-class (one-vs-rest) with bootstrapped 95% confidence intervals. Interpretation: α ≥ 0.800 (good, measurement-ready); 0.667 ≤ α < 0.800 (tentative); α < 0.667 (unacceptable, remediate) (R-R.2).

### Known Ambiguities
An appendix (Appendix B of PROTOCOL.md) listing every unresolved judgment call with the conservative default chosen. Each entry has an ID (KA-1 through KA-13). Candidates for owner decision in a future MINOR or MAJOR revision.

## L

### LLM-assisted coding
The use of a large language model as a coder under defined constraints: fixed system prompt, temperature 0, α ≥ 0.85 calibration against the Gold Standard, ≥ 20% human verification, and re-calibration on every model change (D8, R-L.1–R-L.9).

## M

### Market Question Cell
A buyer-intent question together with its stated requirements; the scenario context for judging recommendation relevance. The `question_id` in annotation and response records identifies the Market Question Cell.

## O

### Operative stance
The conclusion the response reaches about whether the buyer should use the brand. Identified by a conclusion marker ("so", "overall", "in short", "ultimately", "bottom line") or, absent a marker, the last evaluative clause about the brand. Governs code assignment under the cascade (R-DP.3).

## Q

### Qualified recommendation
A brand appearance classified as C4 or C5 that satisfies three conditions: (1) suitability is communicated, not merely named or described; (2) the recommendation relates to the Market Question Cell scenario; (3) sufficient context is present. Only qualified recommendations count toward ARS.

## R

### Rank position
An integer ≥ 1 recorded for C5 events only (R-F.11). For overall rankings, the ordinal position (1, 2, 3...). For category winners (R-C5.5), `rank_position = 1` within the named category. `null` for all other classes.

### Recommendation Incidence
The metric counting all qualifying recommendations (C4 + C5) in a response. Multiple brands can each count, so per-brand percentages may sum to more than 100%. Distinct from Final Choice Incidence and never merged with it.

### Recommendation strength
An ordinal integer (1–5) capturing recommendation force (R-F.4). Mapping: 5 = C5 rank 1 overall; 4 = C5 rank 2 overall; 3 = C5 rank ≥ 3 or category winner (R-F.7); 2 = C4 explicit; 1 = C4 implicit. `null` for C1, C2, C3, C6, ADJUDICATE.

### Response record
A JSONL record in `data/responses.jsonl` representing one AI-generated response. Conforms to `schema/response-record.schema.json`. Contains `full_text`, `model_version`, `self_disclosure`, and collection metadata (D10 §10.5).

## S

### Self-disclosure
Platform self-identification metadata recorded at the response level (R-F.14). Shape: `{"present": boolean, "verbatim": string|null, "vendor": string|null}`. When the platform discloses its identity but names no classified brand, the disclosure goes here, not as a per-event `platform_self_id` flag.

### Sponsored block
A disclosed promotional section within an AI response. The per-event `sponsored` flag (R-F.15) marks brand appearances inside such a block; the response-level `sponsored_block_present` flag marks that the response contains one. Flags are metadata and do not alter classification.

### Subtype
A field recorded for C4 and C5 events only. Allowed values: `explicit`, `implicit`. For C5, always `explicit` (R-F.1a). For C1/C2/C3/C6/ADJUDICATE, `null`.

## V

### Versioning (semantic)
The `MAJOR.MINOR.PATCH` versioning policy (R-V.1). MAJOR changes alter classification outcomes and require re-coding; MINOR changes are additive and do not alter outcomes; PATCH changes are non-normative. Classification rules are frozen before measurement (R-V.3); during a cycle, only PATCH changes are permitted.
