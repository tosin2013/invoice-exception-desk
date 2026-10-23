# Implementation Plan: Invoice Exception Desk import (R1 slice)

**Branch**: `003-desk-import` | **Date**: 2026-10-23 | **Spec**: [spec.md](./spec.md)

## Summary
One pure function, `import_invoices`, that reads CSV text, classifies each data row, and computes balances, aging and totals as of an explicit date. Written by the human/strong role, from the spec and the public `ACCEPTANCE.md` only.

## Technical Context
**Language/Version**: Python 3.11+ | **Primary Dependencies**: none (stdlib `csv`, `io`, `re`, `datetime`) | **Testing**: pytest (`python -m pytest -q`)
**Project Type**: library | **Scope**: create `invoice_desk/__init__.py` and `tests/test_invoice_desk.py`. Do not change `bill_split`, its tests, `data/`, `pyproject.toml`, `ROADMAP.md`, `ACCEPTANCE.md` or `NON_GOALS.md`. Nothing else.

## Constitution Check (v1.1.0)
I integer cents PASS · II pure PASS · III stdlib only PASS · IV tests PASS · V spec/plan/tasks/code land together on the branch (squash on merge) · VI synthetic, offline PASS · VII explicit `as_of` PASS · VIII sealed answer key held by the reviewer PASS

## Interface (exact)
```python
from datetime import date
def import_invoices(csv_text: str, as_of: date) -> dict: ...
```
Returns `{"rows": [...], "totals": {...}}`.

- `rows`: one dict per data row, in input order. Keys: `row` (1-based data-row number; the header is not counted), `status` (`accepted`, `rejected`, `duplicate_identical`, `duplicate_inconsistent`), `reason` (the rejection reason for rejected rows, `None` for accepted, `"identical_duplicate"` / `"inconsistent_duplicate"` for duplicates), `remaining_balance_cents`, `days_overdue`, `aging_bucket` (integers/strings for accepted rows, `None` otherwise). Accepted rows also carry the normalized `issuer`, `invoice_id`, `amount_cents` and `paid_cents` *(analyze fix C1)*.
- Empty `csv_text` (no header) returns zero rows and zero totals, with all six aging buckets present as `{"count": 0, "remaining_cents": 0}` *(analyze fix A2)*.
- `totals`: `total_rows`, `accepted`, `rejected`, `duplicate_identical`, `duplicate_inconsistent`, `outstanding_invoice_count`, `total_outstanding_cents`, `total_paid_cents`, and `aging`: a dict with all six buckets `current`, `1-30`, `31-60`, `61-90`, `91+`, `paid`, each `{"count": int, "remaining_cents": int}`.

## Design
1. Parse with `csv.reader(io.StringIO(csv_text))`. **Not** `DictReader`: it silently skips blank lines, and blank lines are data rows that must be reported as `empty_row` (ACCEPTANCE rows 29 and 30).
2. The first row is the header; map columns by name. Pad short rows with `""`; ignore extra cells (clarification 3). Strip whitespace on every field (clarification 2).
3. Validate in the spec's precedence order (FR-011). Integers: the stripped text must match the ASCII pattern `[0-9]+` (use `re.fullmatch`, not `str.isdigit()`, which accepts characters like `²`), so `12.50`, `-500`, `+100` and `abc` fail. A blank `paid_cents` is `0`. Dates: `date.fromisoformat` on a string matching `YYYY-MM-DD` exactly.
4. Duplicates: keep a dict of the first accepted row per `(issuer, invoice_id)` and its seven normalized values; compare later valid rows against it (FR-012 to FR-014).
5. Balance and aging per FR-016 to FR-020, using `(as_of - due_date).days`.
6. Totals per FR-021 to FR-024. All six aging buckets are always present.
7. `tests/test_invoice_desk.py`: read `data/invoices.csv` and check every AT-01 to AT-04 number in `ACCEPTANCE.md`, plus unit tests for each rejection reason, the bucket boundaries, whitespace, short rows, and calling the function twice.

## Out of scope
Follow-up queue, owners, notes (AT-05), payments (R2), promised pay (R3), migration (R5), CLI, persistence.
