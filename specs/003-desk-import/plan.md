# Implementation Plan: Invoice Exception Desk import (R1 slice)

**Branch**: `003-desk-import` | **Date**: 2026-10-23 | **Spec**: [spec.md](./spec.md)

## Summary
One pure function, `import_invoices`, that reads CSV text, classifies each data row, and computes balances, aging and totals as of an explicit date. Written by the human/strong role, from the spec and the public `ACCEPTANCE.md` only.

## Technical Context
**Language/Version**: Python 3.11+ | **Primary Dependencies**: none (stdlib `csv`, `io`, `re`, `datetime`) | **Testing**: pytest (`python -m pytest -q`)
**Project Type**: library | **Scope**: create `invoice_desk/__init__.py` and `tests/test_invoice_desk.py`. Do not change `bill_split`, its tests, `data/`, `pyproject.toml`, `ROADMAP.md`, `ACCEPTANCE.md` or `NON_GOALS.md`. Nothing else.

## Constitution Check (v1.1.0)
*(Historical, pre-L4. Current check: "L4 revision (2026-10-24)" below, against v2.0.0.)*
I integer cents PASS · II pure PASS · III stdlib only PASS · IV tests PASS · V spec/plan/tasks/code land together on the branch (squash on merge) · VI synthetic, offline PASS · VII explicit `as_of` PASS · VIII sealed answer key held by the reviewer PASS

## Interface (exact)
```python
from datetime import date
def import_invoices(csv_text: str, as_of: date) -> dict: ...
```
Returns `{"rows": [...], "totals": {...}}`.

- `rows`: one dict per data row, in input order. Keys: `row` (1-based data-row number; the header is not counted), `status` (`accepted`, `rejected`, `duplicate_identical`, `duplicate_inconsistent`), `reason` (the rejection reason for rejected rows, `None` for accepted, `"identical_duplicate"` / `"inconsistent_duplicate"` for duplicates), `remaining_balance_cents`, `days_overdue`, `aging_bucket` (integers/strings for accepted rows, `None` otherwise). Accepted rows also carry the normalized `issuer`, `invoice_id`, `issue_date`, `due_date` (ISO `YYYY-MM-DD` strings), `amount_cents`, `currency` (trimmed string) and `paid_cents` *(analyze fix C1; dates and currency added by FR-032, L6)*.
- Empty `csv_text` (no header) returns zero rows and zero totals, with all six aging buckets present as `{"count": 0, "remaining_cents": 0}` *(analyze fix A2)*.
- `totals`: `total_rows`, `accepted`, `rejected`, `duplicate_identical`, `duplicate_inconsistent`, `outstanding_invoice_count`, `total_outstanding_cents`, `total_paid_cents`, and `aging`: a dict with all six buckets `current`, `1-30`, `31-60`, `61-90`, `91+`, `paid`, each `{"count": int, "remaining_cents": int}`.

## Design
1. Parse with `csv.reader(io.StringIO(csv_text))`. **Not** `DictReader`: it silently skips blank lines, and blank lines are data rows that must be reported as `empty_row` (ACCEPTANCE rows 29 and 30).
2. The first row is the header; map columns by name. Pad short rows with `""`; ignore extra cells (clarification 3). Strip whitespace on every field (clarification 2).
3. Validate in the spec's precedence order (FR-011). Integers: the stripped text must match the ASCII pattern `[0-9]+` (use `re.fullmatch`, not `str.isdigit()`, which accepts characters like `²`), so `12.50`, `-500`, `+100` and `abc` fail. A blank `paid_cents` is `0`. *(Amount part superseded 2026-10-24: `amount_cents` now uses `[1-9][0-9]*` per FR-008a; see "L4 revision" below. `paid_cents` keeps `[0-9]+`.)* Dates: `date.fromisoformat` on a string matching `YYYY-MM-DD` exactly.
4. Duplicates: keep a dict of the first accepted row per `(issuer, invoice_id)` and its seven normalized values; compare later valid rows against it (FR-012 to FR-014).
5. Balance and aging per FR-016 to FR-020, using `(as_of - due_date).days`.
6. Totals per FR-021 to FR-024. All six aging buckets are always present.
7. `tests/test_invoice_desk.py`: read `data/invoices.csv` and check every AT-01 to AT-04 number in `ACCEPTANCE.md`, plus unit tests for each rejection reason, the bucket boundaries, whitespace, short rows, and calling the function twice.

## Out of scope
Follow-up queue, owners, notes (AT-05), payments (R2), promised pay (R3), migration (R5), CLI, persistence.

## L4 revision (2026-10-24)
**Trigger**: Clarification session 2026-10-24 in `spec.md`, decided by Tosin Akinosho. FR-008 is superseded by **FR-008a**: `amount_cents` must be a positive, canonical ASCII decimal integer. Constitution v2.0.0, rule V (spec, tests and code in one commit; superseded text kept, not deleted).

**Constitution Check (v2.0.0)**: I integer cents PASS · II pure computation, no I/O added PASS · III stdlib only PASS · IV tests changed and added in `tests/test_invoice_desk.py` PASS · V spec Clarification + superseded FR-008 + FR-008a + plan + tasks + ACCEPTANCE.md + tests + code in one commit · VI synthetic PASS · VII explicit `as_of` PASS · VIII graded against an independently sealed L4 key held outside the builder workspace (not visible to this plan).

**What changes**
- `invoice_desk/__init__.py`, `_validate_row` only: `amount_cents` must `re.fullmatch` the ASCII pattern `[1-9][0-9]*` on the trimmed text, otherwise `invalid_amount`. So `0`, `00`, `0100` and `007` are rejected, in addition to `+100`, `-500`, `12.50`, `abc` and blank.
- Use a new, separate amount pattern. `paid_cents` keeps the existing `[0-9]+` pattern (FR-010 unchanged), so a blank or `0` payment and a leading-zero payment such as `0100` behave exactly as before.
- Unchanged: validation precedence (FR-011: a bad date still wins over a bad amount, a bad amount still wins over a bad currency), trimming (FR-030), padding (FR-031), duplicates (FR-012 to FR-015), balances, aging and totals, and the `import_invoices` interface. `usd` stays `invalid_currency` (FR-009).
- Frozen fixture `data/invoices.csv` is untouched. It contains no zero or leading-zero amount, so AT-01 to AT-04 values are unchanged.

**Tests that flip (changed, not deleted)**
- `test_zero_amount_is_valid_and_lands_in_paid` → renamed to state the new rule; the row `Acme,INV-Z1,...,0,USD,` is now `rejected` / `invalid_amount`, contributes no accepted fields, and totals show `accepted = 0` and an empty `paid` bucket.
- The `[0-9]+` amount cases in the parametrized rejection table gain `0`, `00`, `0100` (and the trimmed ` 0100 `) as `invalid_amount`.

**Tests added**
- Canonical positive amounts `1`, `100`, ` 100 ` are accepted.
- A fully paid positive invoice (`100` paid `100`) is still accepted in `paid` with zero remaining.
- `paid_cents` with a leading zero (`0100` on amount `1000`) is still accepted (unchanged FR-010).
- Precedence: a zero amount plus a bad date is `invalid_date`; a zero amount plus `EUR` or `usd` is `invalid_amount`; a positive amount with `usd` is `invalid_currency`.
- A zero-amount row with the same identity as a later valid row: the zero row is rejected and does not take part in duplicate detection, so the later row is `accepted`.

**004 ripple**
- 004's queue is built from accepted rows only. A zero-amount invoice is now rejected at import, so it can no longer reach 004's queue or its `paid` bucket. The `paid` bucket now holds only fully paid invoices with a positive amount (for example `INV-1011`).
- No 004 code change. 004's tests and spec do not build a zero-amount invoice (its test helper `invoice(..., balance=0, paid=900)` writes amount `900`). 004 FR-021/SC-010 constrain 004 itself, not this owning-spec revision. Checked by `/speckit.analyze` on 004; findings go to `drift.md`.

**Tasks**: append an "L4" phase to `tasks.md` (existing T001 to T020 unchanged).


## L5 revision (2026-10-25)
**Trigger**: Clarification session 2026-10-25 in `spec.md`, decided by Tosin Akinosho, from the approved ruling `specs/003-desk-import/request-v1.md` at commit `a54734c`. FR-007 is superseded by **FR-007a**: a `due_date` strictly earlier than `issue_date` is `invalid_date`; equal dates are valid. Constitution v2.0.0, rule V (spec, tests and code land together; superseded text kept, not deleted).

**Constitution Check (v2.0.0)**: I integer cents PASS · II pure computation, no I/O added PASS · III stdlib only PASS · IV tests changed and added in `tests/test_invoice_desk.py` PASS · V spec Clarification + superseded FR-007 + FR-007a + plan + tasks + ACCEPTANCE.md + tests + code land together · VI synthetic PASS · VII explicit `as_of` PASS · VIII graded against an independently sealed L5 key held outside the builder workspace (not visible to this plan).

**What changes**
- `invoice_desk/__init__.py`, `_validate_row` only: right after the existing `invalid_date` check, return `None, "invalid_date"` when `due_date < issue_date`. Change nothing else.
- Unchanged: the date form check, the FR-011 precedence order, the reason set, trimming (FR-030), padding (FR-031), duplicates (FR-012 to FR-015), balances, aging, totals, the `import_invoices` interface and the `ACCEPTANCE.md` values.
- Frozen fixture `data/invoices.csv` is untouched; it has no valid-date row with `due_date < issue_date`.

**Test that changes**
- `test_aging_bucket_boundaries` in `tests/test_invoice_desk.py`: move every row's issue date from `2026-01-01` to `2025-01-01`, keeping all nine offsets. Row `INV-B365` would otherwise be `invalid_date`; the 365-day case is kept.

**Tests added**
- A due-before-issue row is `invalid_date`; due-before-issue plus amount `abc` is `invalid_date` (FR-011).
- A due-before-issue row followed by a valid row with the same `(issuer, invoice_id)`: the first is `invalid_date`, the second is `accepted`, with no duplicates.
- An equal-dates row is `accepted` (guard; passes already).

**004 ripple**
- 004's queue is built from accepted rows only. A row rejected under FR-007a can no longer reach 004's queue, so the accepted set can shrink for new inputs. No 004 code, contracts, data model or tests change; 004 FR-021 and SC-010 get dated notes only.

**Run rules**
- Allowed files only: `specs/003-desk-import/{spec,plan,tasks,drift,progress,ralph-memory}.md`, `specs/004-deterministic-followup-queue/spec.md`, `ACCEPTANCE.md`, `tests/test_invoice_desk.py`, `invoice_desk/__init__.py`. Anything else stops the run.
- 300-line diff cap for the whole run. Up to 3 fix tries per failing task, then stop and record the failure in `ralph-memory.md`.
- Never edit `.specify/`, `.opencode/`, the constitution, `data/`, `queue.py`, `annotations.py`, `pyproject.toml`, `run.log`. Install nothing. No push, no merge, no new branches, no git config changes.

**Tasks**: append an "L5" phase to `tasks.md` (existing T001 to T030 unchanged).

## L6 revision (2026-10-27)
**Trigger**: Issue #16, decided by Tosin Akinosho. **FR-032**: every accepted row must also expose `issue_date` and `due_date` as ISO `YYYY-MM-DD` strings and `currency` as the trimmed string, taken from the first accepted occurrence; rejected and duplicate rows must not carry these keys (FR-015, SC-008). Closes drift 003-U1. Constitution v2.0.0, rule V (spec, tests and code land together).

**Constitution Check (v2.0.0)**: I integer cents PASS · II pure computation, no I/O added PASS · III stdlib only PASS · IV tests added in `tests/test_invoice_desk.py` PASS · V spec Clarification + FR-032 + plan + tasks + tests + code land together · VI synthetic PASS · VII explicit `as_of`, dates are `str` PASS · VIII graded by the L6 lesson rule in issue #16 (all acceptance checks, unchanged 209-test regression, Grok Bot approval) instead of a hidden key.

**What changes**
- `invoice_desk/__init__.py`, accepted-row construction only: add `issue_date`, `due_date` (ISO strings from the normalized values) and `currency` (trimmed) to accepted rows. Nothing else changes.
- Unchanged: classification, rejection reasons, validation precedence, trimming, padding, duplicates, balances, aging, totals, the `import_invoices` interface, and rejected/duplicate row keys.
- No totals, aging, queue order or queue item keys change. `queue.py`, `annotations.py`, `contracts/public-api.md` and `ACCEPTANCE.md` are untouched.
- Frozen fixture `data/invoices.csv` is untouched; no AT-01 to AT-04 value changes.

**Tests added** (in `tests/test_invoice_desk.py`, written first; they must fail where the feature is missing)
- Acceptance check 1: accepted `INV-1001`, `INV-1013`, `INV-1011` expose the exact `issue_date`, `due_date`, `currency` as `str`.
- Acceptance check 2: a single trimmed row is accepted with trimmed `issue_date`, `due_date`, `currency`.
- Acceptance check 3: every accepted row has exactly the full key set; every rejected and duplicate row keeps exactly its existing key set.
- Acceptance check 4: first occurrence accepted with `due_date`; inconsistent duplicate has no `due_date` key (FR-014).
- Acceptance check 5: `json.dumps(result)` succeeds and two calls give equal results (FR-004, FR-026).
- Acceptance check 6: through `build_followup_queue`, AT-01 to AT-04 totals, queue order `INV-1009 … INV-1011` and queue item keys are unchanged.

**004 ripple**
- 004's queue is built from accepted rows only and ignores the new keys. No 004 code, contracts, data model or tests change; 004 FR-021 and SC-010 get dated L6 notes only.

**Run rules**
- Allowed files: `specs/003-desk-import/{spec,plan,tasks,drift,progress,ralph-memory}.md`, `specs/004-deterministic-followup-queue/spec.md`, `tests/test_invoice_desk.py`, `invoice_desk/__init__.py`.
- Never edit `queue.py`, `annotations.py`, `contracts/public-api.md`, `ACCEPTANCE.md`, other test files, `data/`, `.specify/`, `.opencode/`, `pyproject.toml`. Never edit or delete an existing test.
- Under 300 changed lines in total. Up to 3 fix tries per failing task, then stop and record it in `ralph-memory.md`. Install nothing. No push, no merge, no new branches, no git config changes.

**Tasks**: append an "L6" phase to `tasks.md` (existing T001 to T035 unchanged).
