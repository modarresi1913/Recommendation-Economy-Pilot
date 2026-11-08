# Pre-Registration Draft — AI Recommendation Share (ARS) Measurement Study

> **Status:** DRAFT. This pre-registration must be archived (e.g., on OSF) **before** any collection wave begins. The coding protocol froze only the *coding* rules (PROTOCOL.md D2, D3); the *sampling* plan is frozen by this pre-registration.
>
> **Language note:** This document is exploratory and contains no results. All fields marked `[owner to fill]` are placeholders.

---

## 1. Study title and owner

- **Title:** AI Recommendation Share (ARS): Measuring Brand Visibility in AI-Generated Recommendations
- **Owner / principal investigator:** Seyed Alireza Alhosseini Almodarresieh
- **ORCID:** [owner to fill]
- **Affiliation:** [owner to fill]
- **Repository:** https://github.com/modarresi1913/Recommendation-Economy-Pilot
- **Protocol version:** 1.1.0 (frozen for measurement)
- **Pre-registration version:** 0.1.0 (draft)

## 2. Research questions

1. **RQ1:** Which brands receive qualified recommendations (C4/C5) in AI-generated responses to buyer-intent questions across the CRM, project management, and AI coding assistant categories?
2. **RQ2:** How does ARS (Recommendation Incidence) vary across AI platforms, software categories, and collection waves?
3. **RQ3:** What is the transition rate from qualified recommendation (C4/C5) to Final Choice (the single winning brand), and how does it vary by platform and category?
4. **RQ4 (exploratory):** How stable are per-brand ARS estimates across waves (volatility), and do platform-level differences persist after controlling for question-level heterogeneity?

## 3. Design

### 3.1 Market Question Cells (MQCs)

- **30 active MQCs:** 10 CRM, 10 project management, 10 AI coding assistants.
- Source: `questions/questions-active.yaml` (owner replaces draft questions and sets `status: active` before waves).
- Each MQC has 2–5 explicit `requirements` (stated needs) that are normative for coding (R-C4.1b, R-C4.6, R-C4.7, R-C5.5).

### 3.2 Platforms

- **5 AI platforms** (owner declares the specific platforms based on API availability and ToS compliance).
- Collection via permitted interfaces only (official APIs or authorized web use); no scraping.

### 3.3 Runs per question

- **R = 10 runs per question per platform per wave.**
- Total per wave: 30 questions × 5 platforms × 10 runs = **1,500 responses** (planned).

### 3.4 Waves and cadence

- **Minimum 5 waves.**
- Cadence: [owner to fill — e.g., weekly, biweekly, monthly].
- Wave 1 start date: [owner to fill].
- Wave 5 end date: [owner to fill].
- Rationale for cadence: [owner to fill].

### 3.5 Collection instrument

- `collection/collect.py` with `--api` mode for platforms with usable APIs; `--import-manual` for platforms without.
- `collection_version`: 1.0.0 (owner bumps if the collection instrument changes).
- Temperature: 0.0 (deterministic; per R-L.2 LLM-coder rule, applied here to collection too for reproducibility).

## 4. Classification

### 4.1 Protocol

- Per **PROTOCOL.md v1.1.0** (frozen). No deviations.
- Six-class taxonomy (C1–C6) + ADJUDICATE fallback (R-DP.9).
- Decision procedure: 9-rule cascade (R-DP.1–R-DP.9).
- All rule citations required in every annotation's `rationale`.

### 4.2 Coding depth

- **Double coding:** every brand–response event coded by ≥ 2 independent coders (R-A.1).
- **Triple coding:** Gold Standard subset and any response with sponsored/self-id (R-A.1).
- Coders work blind to each other's codes (R-A.2).

### 4.3 Adjudication

- Disagreements identified per R-A.3 (class_code, subtype, rank_position, or final_choice differ).
- Adjudicator codes blind, with recusal (R-A.5a).
- Resolved codes documented per R-A.9, R-A.10 in `data/adjudications/`.

## 5. Reliability gates

Per PROTOCOL.md D7:

| Krippendorff's α | Action |
|---|---|
| α ≥ 0.800 | Measurement-ready; publish headline figures |
| 0.667 ≤ α < 0.800 | Tentative; publish with documented caveat |
| α < 0.667 | Unacceptable; do NOT publish; run remediation (R-R.4) |

- **Gold Standard:** ≥ 50 events, full agreement post-adjudication (R-R.5). Each coder must reach α ≥ 0.80 against the Gold Standard before live coding (R-R.7).
- **ADJUDICATE share:** if > 5% of events, remediation triggered regardless of α (R-R.2).
- **LLM coders** (if used): must reach α ≥ 0.85 against the Gold Standard (R-L.8), temperature 0, ≥ 20% human verification (R-L.5).

## 6. Analysis plan

### 6.1 Descriptive statistics

- **Recommendation Incidence** per brand × platform × wave and pooled (R-F.4).
- **Final Choice Incidence** per brand × platform × wave and pooled (R-FC.1–R-FC.5).
- **Mention rate (C1)** and **Consideration rate (C3)** for context.

### 6.2 Uncertainty

- **Wilson score 95% intervals** for every proportion (never Wald).
- **Bootstrap 95% CIs** for Krippendorff's α (≥1,000 resamples, units = events; R-R.2).

### 6.3 Headline duality (R-F.16)

- Every ARS figure reported **twice**: inclusive and exclusive of `sponsored`/`platform_self_id` events.

### 6.4 Mixed-effects model

- `recommended ~ platform + category + (1 | question_id)` per brand (logistic GLMM).
- Random intercept on question absorbs within-question correlation.
- **Descriptive association only; not causal.**

### 6.5 Volatility

- Per brand × platform: SD of ARS across waves.

## 7. Exclusions and failure semantics

- **Failed collections** (API errors, timeouts) are logged to `collection/failures-{wave}.jsonl` and **excluded from denominators**. A failed request is not a negative recommendation (Layer 2: unknown is not zero).
- **ADJUDICATE events** are reported separately and excluded from ARS numerators unless resolved. If unresolved, they remain excluded.
- **Missing responses** (planned but not collected) do not enter any denominator.
- **Outliers:** no a priori exclusion of outlier brands or platforms; all observed brands reported.

## 8. Deviations policy

Any deviation from this pre-registration — including changes to the question set, platform list, run count, cadence, or analysis plan — will be documented in the results write-up with:
- The nature of the deviation.
- The reason for the deviation.
- The point in the study timeline when the deviation occurred.
- An assessment of the deviation's impact on the conclusions.

Deviations are also recorded in `CHANGELOG.md` as PATCH or MINOR version bumps of the study layer (the coding protocol itself remains frozen).

## 9. Data availability

- **Repository:** https://github.com/modarresi1913/Recommendation-Economy-Pilot
- **Zenodo DOI:** [to be filled after first archival — see `data/README.md` for the procedure]
- **Data files:** `data/responses.jsonl`, `data/annotations.jsonl`, `data/gold-standard.jsonl`, `data/adjudications/`
- **License:** Data and protocol text under CC-BY-4.0; code under MIT.

## 10. Conflicts of interest

The author is the developer of the ARS framework and coding protocol. This creates a potential conflict of interest analogous to the protocol's own observatory/marketplace separation (Layer 2): the author has an interest in the framework's adoption, which could bias instrument design or reporting. Mitigations:
- The coding protocol is frozen (v1.1.0) and publicly version-controlled; post-freeze changes are governed by R-V.3.
- This pre-registration freezes the sampling plan before data collection.
- All data, code, and adjudication records are published openly.
- Reliability is measured by independent coders against a Gold Standard.
- Any future commercial application of the framework will be disclosed in the results write-up.

---

*End of pre-registration draft. Archive on OSF (or equivalent) before Wave 1.*
