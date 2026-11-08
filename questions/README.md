# Question Registry

This directory contains the **Market Question Cells (MQCs)** — the standardized buyer-intent questions posed to AI platforms during collection waves.

## ⚠️ PLACEHOLDER NOTICE

**The 30 MQCs in `questions-draft.yaml` are PLACEHOLDERS (`status: draft`). They must be replaced by the owner's actual 30 pilot questions before any collection wave begins.** Do not run waves against draft questions.

## Files

| File | Description |
|---|---|
| [`questions.schema.json`](./questions.schema.json) | JSON Schema (draft 2020-12) for one MQC record. |
| [`questions-draft.yaml`](./questions-draft.yaml) | 30 draft MQCs (10 CRM, 10 PM, 10 AI coding assistants). All `status: draft`. |

## The `requirements` array is normative

Each MQC has a `requirements` array listing the buyer's stated needs. **This array is what "matches the buyer's stated need" means in the coding protocol:**

| Coding rule | How `requirements` is used |
|---|---|
| R-C4.1b | A recommendation must relate to the MQC scenario (the `requirements`). |
| R-C4.6 | A conditional recommendation ("if you need X, then Y") qualifies as C4 only if X matches an entry in `requirements`. |
| R-C4.7 | A conditional recommendation whose condition does NOT match `requirements` → conservative C3. |
| R-C5.5 | A category winner ("best for X") is C5 rank 1 only if X matches an entry in `requirements`. |
| R-C6.5 | A conditional rejection ("if you need X, avoid Y") is C6 only if X matches `requirements`. |

Changing `requirements` changes coding outcomes. That is why an edit to `requirements` is a new version, never a silent overwrite.

## Owner-replacement workflow

1. **Draft your 30 real questions** offline, each with 2–5 explicit `requirements`.
2. **Replace each record** in `questions-draft.yaml` (or create a new `questions-active.yaml`).
3. **Bump each record's `version`** to `1.0.0` and set `status: active`.
4. **Validate** every record against `questions.schema.json`:
   ```bash
   python3 -c "
   import json, yaml, jsonschema
   schema = json.load(open('questions/questions.schema.json'))
   records = yaml.safe_load(open('questions/questions-active.yaml'))
   for r in records:
       jsonschema.validate(r, schema)
   print(f'{len(records)} records valid')
   "
   ```
5. **Commit** the replacement. This is a MINOR version bump of the protocol's data layer (the coding protocol itself is unchanged).

## Versioning and governance

- An edit to a question's `question_text` or `requirements` is a **new version** (never a silent overwrite), mirroring the protocol's freeze rule R-V.3.
- `question_id` is immutable. Once a question is `active`, its `question_id` is locked.
- Retired questions (`status: retired`) are kept for provenance; their `question_id` is never reused.
- The `question_id` in every response and annotation record must match an `active` MQC in this registry.

## How `question_id` maps to response and annotation records

```
questions/questions-active.yaml
  └── question_id: crm-q03
        ├── data/responses.jsonl → response.question_id = "crm-q03"
        └── data/annotations.jsonl → annotation.question_id = "crm-q03"
```

The validator (`validation/validate.py`) does not currently check MQC registry membership (it checks schema and cross-record integrity). A future enhancement may add an E6 check for MQC membership; for now, the wave runner (`collection/collect.py`) refuses to collect against a `question_id` not present in the active registry.
