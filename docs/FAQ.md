<!--
  Schema.org FAQPage structured data (JSON-LD) for answer-engine optimization.
  Search engines and AI assistants parse this block to extract Q&A pairs.
  Source of truth: PROTOCOL.md v1.1.0. Do not edit answers without updating PROTOCOL.md.
-->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the AI Recommendation Share (ARS) protocol?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The AI Recommendation Share (ARS) protocol is an open, deterministic coding protocol for measuring how frequently brands receive qualified recommendations in AI-generated responses to buyer-intent questions. It classifies every brand appearance into one of six classes (C1–C6) and reports both Recommendation Incidence and Final Choice Incidence. The protocol is designed for computational social science and market research and is usable by human coders and LLM-assisted coders. It is published at https://github.com/modarresi1913/Recommendation-Economy-Pilot under CC-BY-4.0."
      }
    },
    {
      "@type": "Question",
      "name": "What is a qualified recommendation in the ARS protocol?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A qualified recommendation is a brand appearance classified as C4 (Qualified recommendation) or C5 (Ranked recommendation). It must satisfy three conditions: (1) the response communicates that the brand is a suitable option, not merely names or describes it; (2) the recommendation relates to the buyer requirements stated in the question (the Market Question Cell); (3) the response contains enough context to support the classification. Only C4 and C5 events count toward the ARS metric."
      }
    },
    {
      "@type": "Question",
      "name": "What are the six classes in the ARS taxonomy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The six classes are: C1 Mention (brand named only), C2 Neutral inclusion (listed among alternatives, no endorsement or rejection), C3 Positive consideration (favorably described but not recommended for the buyer's stated needs), C4 Qualified recommendation (recommended as suitable for the buyer's stated requirements), C5 Ranked recommendation (assigned an explicit priority or rank), and C6 Rejection or warning (discouraged or identified as unsuitable). Only C4 and C5 count toward ARS."
      }
    },
    {
      "@type": "Question",
      "name": "How does the ARS protocol ensure reliability between coders?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The protocol ensures reliability through five mechanisms: (1) a 9-rule decision cascade applied identically by every coder; (2) double or triple coding of every brand-response event; (3) a blind adjudication workflow for disagreements; (4) Krippendorff's alpha targets of 0.800 (good) and 0.667 (minimum acceptable); and (5) a frozen Gold Standard of at least 50 events used for coder onboarding and calibration. LLM coders must reach alpha 0.85 against the Gold Standard before use."
      }
    },
    {
      "@type": "Question",
      "name": "What is the difference between Recommendation Incidence and Final Choice Incidence?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Recommendation Incidence counts all qualifying recommendations (classes C4 and C5) in a response, so multiple brands can each count and per-brand percentages may sum to more than 100%. Final Choice Incidence counts only the single winning recommendation per response, where one exists. The two metrics are recorded separately and never merged."
      }
    },
    {
      "@type": "Question",
      "name": "Can the ARS protocol be used with LLM coders?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The protocol defines rules for LLM-assisted coding: the LLM is invoked with a fixed system prompt at temperature 0; it must achieve alpha 0.85 against the Gold Standard before use; at least 20% of LLM-coded events must be independently verified by a human coder; and the system prompt and calibration are re-run on every model change. LLM-coded events carry coder_type 'llm' and a coder_id identifying the model and prompt version."
      }
    },
    {
      "@type": "Question",
      "name": "What is the conservative default principle in the ARS protocol?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "When a classification judgment is genuinely ambiguous and cannot be resolved by a cited rule, the coder applies the conservative default: the interpretation that never inflates a recommendation. In practice this means preferring C3 over C4, C4 over C5, and C6 over any positive code when the operative stance is rejection. Every conservative default is recorded in the Known Ambiguities appendix for owner review."
      }
    },
    {
      "@type": "Question",
      "name": "How is the ARS protocol versioned and governed?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The protocol follows semantic versioning (MAJOR.MINOR.PATCH). Classification rules are frozen before measurement begins; during a measurement cycle only PATCH changes are permitted. MAJOR changes (which alter classification outcomes) require re-coding; MINOR changes are additive and do not alter outcomes; PATCH changes are non-normative. The protocol owner is the sole approver of MAJOR and MINOR changes. The current version is 1.1.0."
      }
    },
    {
      "@type": "Question",
      "name": "Where can I find the ARS protocol schemas and validator?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The annotation record schema is at schema/ars-record.schema.json (JSON Schema draft 2020-12, with if/then conditional constraints on class_code). The response record schema is at schema/response-record.schema.json. The dataset validator is at validation/validate.py (Python 3.10+, stdlib plus jsonschema). It enforces schema compliance, response-level final_choice consistency (R-FC.5), referential integrity, evidence-span verbatimness, and duplicate detection. All are in the repository at https://github.com/modarresi1913/Recommendation-Economy-Pilot."
      }
    }
  ]
}
</script>

# Frequently Asked Questions

> This page is structured as a `FAQPage` (schema.org). The JSON-LD block above is machine-readable; the questions below are the human-readable mirror. All answers are sourced from [PROTOCOL.md](../PROTOCOL.md) v1.1.0.

---

**Q1. What is the AI Recommendation Share (ARS) protocol?**

The AI Recommendation Share (ARS) protocol is an open, deterministic coding protocol for measuring how frequently brands receive qualified recommendations in AI-generated responses to buyer-intent questions. It classifies every brand appearance into one of six classes (C1–C6) and reports both Recommendation Incidence and Final Choice Incidence. The protocol is designed for computational social science and market research and is usable by human coders and LLM-assisted coders. It is published at [github.com/modarresi1913/Recommendation-Economy-Pilot](https://github.com/modarresi1913/Recommendation-Economy-Pilot) under CC-BY-4.0.

**Q2. What is a qualified recommendation in the ARS protocol?**

A qualified recommendation is a brand appearance classified as C4 (Qualified recommendation) or C5 (Ranked recommendation). It must satisfy three conditions: (1) the response communicates that the brand is a suitable option, not merely names or describes it; (2) the recommendation relates to the buyer requirements stated in the question (the Market Question Cell); (3) the response contains enough context to support the classification. Only C4 and C5 events count toward the ARS metric.

**Q3. What are the six classes in the ARS taxonomy?**

The six classes are:
- **C1 — Mention:** brand named only.
- **C2 — Neutral inclusion:** listed among alternatives, no endorsement or rejection.
- **C3 — Positive consideration:** favorably described but not recommended for the buyer's stated needs.
- **C4 — Qualified recommendation:** recommended as suitable for the buyer's stated requirements.
- **C5 — Ranked recommendation:** assigned an explicit priority or rank.
- **C6 — Rejection or warning:** discouraged or identified as unsuitable.

Only C4 and C5 count toward ARS.

**Q4. How does the ARS protocol ensure reliability between coders?**

The protocol ensures reliability through five mechanisms:
1. A 9-rule decision cascade (R-DP.1–R-DP.9) applied identically by every coder.
2. Double or triple coding of every brand–response event.
3. A blind adjudication workflow for disagreements (R-A.5a recusal enforced).
4. Krippendorff's α targets: 0.800 (good, measurement-ready), 0.667 (minimum acceptable).
5. A frozen Gold Standard of ≥ 50 events used for coder onboarding and calibration.

LLM coders must reach α ≥ 0.85 against the Gold Standard before use.

**Q5. What is the difference between Recommendation Incidence and Final Choice Incidence?**

**Recommendation Incidence** counts all qualifying recommendations (classes C4 + C5) in a response — multiple brands can each count, so per-brand percentages may sum to more than 100%. **Final Choice Incidence** counts only the single winning recommendation per response, where one exists. The two metrics are recorded separately and never merged.

**Q6. Can the ARS protocol be used with LLM coders?**

Yes. The protocol defines rules for LLM-assisted coding (D8):
- The LLM is invoked with a fixed system prompt at temperature 0.
- It must achieve α ≥ 0.85 against the Gold Standard before use (R-L.8).
- At least 20% of LLM-coded events must be independently verified by a human coder (R-L.5).
- The system prompt and calibration are re-run on every model change and at least quarterly.
- LLM-coded events carry `coder_type = "llm"` and a `coder_id` identifying the model and prompt version.

**Q7. What is the conservative default principle in the ARS protocol?**

When a classification judgment is genuinely ambiguous and cannot be resolved by a cited rule, the coder applies the **conservative default**: the interpretation that never inflates a recommendation. In practice this means preferring C3 over C4, C4 over C5, and C6 over any positive code when the operative stance is rejection. Every conservative default is recorded in the [Known Ambiguities appendix](../PROTOCOL.md#appendix-b--known-ambiguities) for owner review.

**Q8. How is the ARS protocol versioned and governed?**

The protocol follows semantic versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR:** alters classification outcomes for already-coded data; requires re-coding.
- **MINOR:** additive changes that do not alter outcomes for previously-agreed cases.
- **PATCH:** non-normative changes (typos, formatting).

Classification rules are frozen before measurement begins (R-V.3); during a measurement cycle only PATCH changes are permitted. The protocol owner is the sole approver of MAJOR and MINOR changes. Current version: **1.1.0**.

**Q9. Where can I find the ARS protocol schemas and validator?**

- Annotation record schema: [`schema/ars-record.schema.json`](../schema/ars-record.schema.json) (JSON Schema draft 2020-12, with `if`/`then` conditional constraints on `class_code`).
- Response record schema: [`schema/response-record.schema.json`](../schema/response-record.schema.json).
- Dataset validator: [`validation/validate.py`](../validation/validate.py) (Python 3.10+, stdlib + `jsonschema`). It enforces schema compliance, response-level `final_choice` consistency (R-FC.5), referential integrity, evidence-span verbatimness, and duplicate detection.

Repository: [github.com/modarresi1913/Recommendation-Economy-Pilot](https://github.com/modarresi1913/Recommendation-Economy-Pilot).
