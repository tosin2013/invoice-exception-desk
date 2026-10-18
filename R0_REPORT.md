# R0_REPORT — Discovery phase (Invoice Exception Desk)

- **Phase:** R0 (Discovery) — no application build.
- **Date:** 2026-10-18
- **As-of (aging):** 2026-10-15, America/New_York
- **Generator seed:** `20261015`
- **Status:** T1–T7 complete; test suite green.

## What was done

| Task | Deliverable | Summary |
|------|-------------|---------|
| T1 | `ROADMAP.md` | R0–R6 with objective, in/out scope, dependencies, owner, status, spec/test links, exit evidence. |
| T2 | `data/generate_invoices.py`, `data/invoices.csv` | Stdlib-only deterministic generator (fixed seed) writing 30 rows: valid rows at every due-date boundary, identical/inconsistent duplicates, invalid amounts/dates/currency/payments, a missing key, empty rows, and partial-payment rows for v2a. |
| T3 | `data/compute_oracle.py`, `data/oracle.json` | Separate script independently re-derives per-row status/reason, remaining balance (cents), days overdue, aging bucket, and totals. |
| T4 | `ACCEPTANCE.md` | AT-01..AT-10, each with inputs, expected outcomes referencing oracle rows, and a pass criterion. |
| T5 | `tests/test_oracle.py` | 15 stdlib unittest checks: generator determinism, CSV↔generator agreement, oracle recomputation agreement, counts reconcile, boundaries, duplicates, rejection reasons, zero-balance exclusion, idempotency. |
| T6 | `NON_GOALS.md` | Exclusions: no PII, credentials, reminders, payment processing, tax advice, deployment, auth/multi-tenancy, external services, collections. |
| T7 | `R0_REPORT.md` | This report. |

## How to run

```sh
python3 data/generate_invoices.py     # writes data/invoices.csv
python3 data/compute_oracle.py        # writes data/oracle.json
python3 -m unittest discover -s tests -v
```

## Test output

```
test_committed_csv_matches_generator (test_oracle.GeneratorDeterminismTest.test_committed_csv_matches_generator) ... ok
test_records_are_deterministic (test_oracle.GeneratorDeterminismTest.test_records_are_deterministic) ... ok
test_rendered_bytes_are_deterministic (test_oracle.GeneratorDeterminismTest.test_rendered_bytes_are_deterministic) ... ok
test_row_count_is_about_thirty (test_oracle.GeneratorDeterminismTest.test_row_count_is_about_thirty) ... ok
test_recompute_twice_is_stable (test_oracle.IdempotencyTest.test_recompute_twice_is_stable) ... ok
test_all_amounts_are_integer_cents (test_oracle.OracleAgreementTest.test_all_amounts_are_integer_cents) ... ok
test_oracle_counts_reconcile (test_oracle.OracleAgreementTest.test_oracle_counts_reconcile) ... ok
test_oracle_matches_independent_recomputation (test_oracle.OracleAgreementTest.test_oracle_matches_independent_recomputation) ... ok
test_aging_boundaries (test_oracle.PolicyTest.test_aging_boundaries) ... ok
test_csv_has_empty_rows (test_oracle.PolicyTest.test_csv_has_empty_rows) ... ok
test_duplicate_classification (test_oracle.PolicyTest.test_duplicate_classification) ... ok
test_not_due_and_due_today_are_not_overdue (test_oracle.PolicyTest.test_not_due_and_due_today_are_not_overdue) ... ok
test_partial_payment_remaining_is_never_negative (test_oracle.PolicyTest.test_partial_payment_remaining_is_never_negative) ... ok
test_rejection_reasons_by_row (test_oracle.PolicyTest.test_rejection_reasons_by_row) ... ok
test_zero_balance_is_excluded_from_outstanding (test_oracle.PolicyTest.test_zero_balance_is_excluded_from_outstanding) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.002s

OK
```

## Oracle summary (seed 20261015)

- Rows: 30 total → accepted 14, rejected 12, duplicate_identical 2, duplicate_inconsistent 2.
- Outstanding: 13 invoices, `2,139,435` cents (integer); `total_paid_cents = 289,999`.
- Aging (accepted): current 3 / 597,047; 1–30 3 / 396,862; 31–60 3 / 259,664;
  61–90 2 / 863,731; 91+ 2 / 22,131; paid 1 / 0.

Aging boundary fixtures (relative to as_of 2026-10-15): not-due (`INV-1001`) → current;
due-today (`INV-1002`) → current; 1d, 30d → 1–30; 31d, 60d → 31–60; 61d, 90d → 61–90;
91d → 91+. Fully paid row `INV-1011` → paid (excluded from outstanding).

## Open questions for the Founder / reviewer

1. **Aging bucket labels.** Confirmed set is `current`, `1-30`, `31-60`, `61-90`, `91+`, `paid`.
   Should the zero-balance bucket be reported in the aging table at all, or hidden?
2. **Amount strictness.** The oracle rejects non-canonical integer strings (e.g. `00012`, `1_000`)
   as `invalid_amount`. Is plain-digit-only the intended rule, or should leading zeros be tolerated?
3. **Cross-field date rule.** The oracle does not require `issue_date <= due_date`. Should an
   inverted pair be rejected, and with which reason?
4. **Duplicate scope.** Duplicates are keyed per `issuer+invoice_id` and only compared against
   previously *accepted* rows. Should a duplicate of a rejected row be flagged, or remain rejected?
5. **Inconsistent-duplicate handling.** Currently flagged and not imported. Should the first-wins
   record be replaced, or should the row be quarantined for manual review?
6. **Prioritization key (AT-05).** Proposed order: `days_overdue` desc, `remaining_balance_cents`
   desc, `issuer`, `invoice_id`. Confirm or supply the preferred tie-breakers.
7. **Presence of `paid_cents` in v1.** v1 currently accepts a `paid_cents` column before R2 payments
   exist. Keep it in the v1 contract, or defer it to R2 and treat payments as events only?
8. **Scope confirmation.** R1 (build) is intentionally not started; confirm no app work should begin
   until the R0 artifacts are approved.
