# Reliability Statistics

This directory implements **PROTOCOL.md D7** — inter-coder reliability evaluation for the ARS coding protocol.

## Files

| File | Description |
|---|---|
| [`reliability.py`](./reliability.py) | Computes Cohen's kappa (2 coders) and Krippendorff's alpha (≥2 coders), with bootstrap CIs, confusion matrix, and D7 threshold enforcement. |

## Usage

### Standard double-coding reliability check

```bash
python reliability/reliability.py --annotations data/annotations.jsonl
```

### With bootstrap confidence intervals (≥1,000 resamples per R-R.2)

```bash
python reliability/reliability.py --annotations data/annotations.jsonl --bootstrap 2000
```

### Gold Standard onboarding check (per R-R.7)

A coder must reach α ≥ 0.80 against the Gold Standard before coding live data:

```bash
python reliability/reliability.py \
    --annotations data/annotations.jsonl \
    --gold-standard data/gold-standard.jsonl
```

This computes each coder's alpha against the Gold Standard and reports PASS/FAIL per coder.

## What it computes

| Statistic | When | Rule |
|---|---|---|
| **Krippendorff's alpha** (nominal, 7-category) | Always (primary) | R-R.2 |
| **Bootstrap 95% CI** for alpha | ≥1,000 resamples, units = events | R-R.2 |
| **Cohen's kappa** (aggregate + per-class one-vs-rest) | Exactly 2 coders | R-R.1 |
| **Pairwise kappa** | >2 coders (secondary) | R-R.1 |
| **Confusion matrix** on `class_code` | 2 coders (step 2 of remediation R-R.4) | R-R.4 |
| **ADJUDICATE share** | Always; triggers if >5% | R-R.2 |
| **Missing-data detection** | Always; if unbalanced, alpha is primary | R-R.1a |

The 7-category value domain is `["C1", "C2", "C3", "C4", "C5", "C6", "ADJUDICATE"]` — ADJUDICATE is a distinct category, never merged with any class (per R-R.1, R-R.2).

## Threshold table (per D7)

| Krippendorff's α | Interpretation | Exit code | Action |
|:---:|---|:---:|---|
| α ≥ 0.800 | Good; measurement-ready | 0 | Publish headline ARS figures |
| 0.667 ≤ α < 0.800 | Tentative; acceptable with caveat | 0 | Publish with documented caveat; flag for improvement |
| α < 0.667 | Unacceptable | 1 | Do NOT publish ARS figures; run the remediation checklist (R-R.4) |

Additional trigger: if ADJUDICATE exceeds 5% of events, the protocol is treated as under-specified and remediation is triggered **regardless of alpha** (R-R.2).

## Gold Standard onboarding (R-R.7)

Before coding live data, each human coder must reach α ≥ 0.80 against the Gold Standard. Use the `--gold-standard` flag to run this check. The Gold Standard is a frozen ≥50-event subset with full multi-coder agreement (post-adjudication), per R-R.5.

## Remediation checklist (R-R.4)

When α < 0.667, the script prints the full remediation checklist:

1. Examine the confusion matrix to identify the dominant class-pair confusion.
2. Refine or add boundary rules for that class pair; cite the new rule IDs.
3. Re-train all coders on the revised rules (onboarding quiz D9 + refreshed calibration set).
4. Re-code a fresh, equivalently-sized sample (not the original) and recompute α.
5. Repeat until α ≥ 0.667 on the full taxonomy.
6. If a single class remains below 0.667 after two remediation cycles, report ARS for the reliable classes only and exclude the unreliable class with explicit documentation.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | α ≥ 0.667 (measurement-ready or tentative-with-caveat) |
| 1 | α < 0.667 (unacceptable) OR ADJUDICATE share > 5% |
| 2 | Usage error or I/O failure |

## Dependencies

- `numpy` — array operations
- `krippendorff` — Krippendorff's alpha computation
- Python 3.10+ (stdlib `json`, `collections`, `argparse`)

Install: `pip install numpy krippendorff`
