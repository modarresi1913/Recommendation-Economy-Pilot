# Analysis Pipeline

This directory implements the **uncertainty-aware analysis** of ARS data.

## Files

| File | Description |
|---|---|
| [`ars.py`](./ars.py) | Computes Recommendation Incidence, Final Choice Incidence, mention/consideration rates, volatility, with Wilson score CIs and R-F.16 headline duality. |
| [`glmm.R`](./glmm.R) | Mixed-effects logistic regression `recommended ~ platform + category + (1|question_id)` per brand. |

## Pipeline order

```
1. validate          → validation/validate.py        (E1–E5, W1–W3)
2. reliability gate  → reliability/reliability.py    (α ≥ 0.667 to proceed)
3. ARS               → analysis/ars.py               (Wilson CIs, duality)
4. GLMM              → analysis/glmm.R               (mixed-effects model)
```

### ⚠️ Reliability gate precedes publication

**ARS figures are not published unless the reliability gate passed for the classes they depend on.** ARS depends on C4 and C5; Final Choice Incidence depends on C4/C5 with `final_choice = true`. If the reliability script (`reliability/reliability.py`) returns exit code 1 (α < 0.667 or ADJUDICATE > 5%), do not publish ARS figures. Run the remediation checklist (R-R.4) first.

## ars.py — usage

```bash
# Basic analysis (uses all annotations)
python analysis/ars.py \
    --responses data/responses.jsonl \
    --annotations data/annotations.jsonl

# Use adjudicated/final labels only (recommended for headline figures)
python analysis/ars.py \
    --responses data/responses.jsonl \
    --annotations data/annotations.jsonl \
    --final-labels adjudicator-1 \
    --json results.json
```

### What it computes

| Metric | Definition | Rule |
|---|---|---|
| **Recommendation Incidence** | Share of responses with a C4/C5 event for the brand | D5, R-F.4 |
| **Final Choice Incidence** | Share of responses where the brand is the winner | R-FC.1–R-FC.5 |
| **Mention rate** | Share of responses with a C1 event | Context |
| **Consideration rate** | Share of responses with a C3 event | Context |
| **Headline duality** | Every ARS figure reported inclusive AND exclusive of sponsored/self-id events | R-F.16 |
| **Volatility** | SD of ARS across waves (per brand × platform) | Descriptive |

### Confidence intervals

All proportions use **Wilson score 95% intervals** (never Wald). Wilson intervals have reliable coverage for small samples and extreme proportions; Wald intervals do not.

### Denominator discipline (unknown is not zero)

- Denominators count **only collected responses** (linked via `response_id`).
- Failed collections (logged in `collection/failures-{wave}.jsonl`) are excluded from denominators — a failed request is not a negative recommendation (Layer 2).
- ADJUDICATE events are excluded from numerators (they are not recommendations and not rejections).
- The coverage table (printed before any result) shows collected response counts per platform × wave.

### `--final-labels` convention

When double coding with adjudication, the dataset contains multiple coders' labels. For headline figures, use `--final-labels` to specify the adjudicator's `coder_id` (e.g., `adjudicator-1`). This ensures the denominator is the set of adjudicated events, not the union of all coders' labels.

If `--final-labels` is omitted, all annotations are used (treat each coder's labels as separate observations — useful for sensitivity analysis, not for headline figures).

## glmm.R — usage

```bash
Rscript analysis/glmm.R \
    --responses data/responses.jsonl \
    --annotations data/annotations.jsonl \
    --brand "HubSpot"
```

### Model

```
recommended ~ platform + category + (1 | question_id)
```

- **Outcome:** `recommended` = 1 if `class_code` ∈ {C4, C5}, else 0. ADJUDICATE excluded.
- **Fixed effects:** `platform`, `category` (crm/pm/code).
- **Random intercept:** `(1 | question_id)` — absorbs within-question correlation. Responses to the same MQC are not independent (the question's stated requirements shape recommendations).

### Interpretation caveat

Coefficients are **descriptive associations, not causal effects**. The protocol measures what AI platforms recommend; it does not claim platforms cause brand outcomes. See the comment block in `glmm.R` for the cluster-robust alternative and the Python/statsmodels equivalent.

## Dependencies

- `ars.py`: Python 3.10+ stdlib only (no external packages).
- `glmm.R`: R with `lme4` and `jsonlite` packages.
