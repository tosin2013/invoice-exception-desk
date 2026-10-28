# Ralph Memory

Feature: 003-desk-import
Started: 2026-10-27T16:34:22Z

## Codebase Patterns

- Production code is the single module `invoice_desk/__init__.py`; tests are `tests/test_invoice_desk.py`.
- `import_invoices(csv_text, as_of)` is pure: stdlib only, integer cents, explicit `as_of`, no clock, no I/O state between calls.
- Row validation lives in `_validate_row` and follows the FR-011 precedence: `empty_row`, `missing_required_field`, `invalid_date`, `invalid_amount`, `invalid_currency`, `invalid_payment`.
- Parsing uses `csv.reader`, not `DictReader`, because blank lines must be preserved as `empty_row` data rows.
- L6: accepted rows also expose `issue_date`, `due_date` (ISO `str`) and `currency`; convert the normalized `date` objects with `.isoformat()` at accepted-row construction only.
- L7: accepted rows expose `overdue: bool` as `days_overdue > 0`; rejected and duplicate rows expose `overdue: None`. This is the only L7 row-shape change; totals, aging, queue order and queue keys are untouched.

## Decisions

- L4 (FR-008a): `amount_cents` matches `[1-9][0-9]*`; `paid_cents` keeps `[0-9]+`.
- L5 (FR-007a): after the date-form check, `due_date < issue_date` returns `invalid_date`; equal dates are valid.
- Rejected rows never enter duplicate detection, so a later valid row with the same `(issuer, invoice_id)` is accepted.
- L6 (FR-032): rejected and duplicate rows keep exactly `{row, status, reason, remaining_balance_cents, days_overdue, aging_bucket}`; accepted rows add `issue_date`, `due_date`, `currency` to their previous key set. Queue totals/order/keys are unchanged.
- L7 (FR-033): `overdue` is present on every row (`bool` accepted, `None` non-accepted). The existing key-set test's two sets are the only allowed edit to an existing test; all other L7 tests are additions.

## Gotchas

- `pytest` is not installed in the base Python; run the suite with `uv run --with pytest python -m pytest -q` (no repo install needed).
- Fully paid invoices have `days_overdue = 0` and bucket `paid` (review fix R1), even if their due date is past.
- A due-before-issue test using issue date `2026-01-01` with a 365-day offset is itself invalid after FR-007a; the boundary test uses `2025-01-01`.

## Reusable Commands

- `uv run --with pytest python -m pytest -q`
- `git diff --numstat d6c7d7be4fa61084cf48c400a73c44798e1a063a` (L5 run scope check)

## Do Not Repeat

- Do not modify `data/invoices.csv`, `spec.md` values, `plan.md` values, or `ACCEPTANCE.md` values for L5; only dated notes were added.
- Do not use `str.isdigit()` for numeric validation; use `re.fullmatch` on ASCII patterns.

## Current Handoff

- Feature complete; no handoff required.
