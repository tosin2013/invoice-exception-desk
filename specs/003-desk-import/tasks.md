---

description: "Task list for Invoice Exception Desk import (R1 slice)"
---

# Tasks: Invoice CSV import and aging

**Input**: Design documents from `/specs/003-desk-import/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Included because `plan.md` explicitly scopes `tests/test_invoice_desk.py` and the project constitution requires every public function to have tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. `spec.md` and `plan.md` are inputs only and MUST NOT be modified.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `invoice_desk/` package and `tests/` at repository root, per `plan.md`
- Allowed write scope: `invoice_desk/__init__.py` and `tests/test_invoice_desk.py` only

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package entry point and the test module shared by all stories

- [X] T001 [P] Create `invoice_desk/__init__.py` with the public stub `import_invoices(csv_text: str, as_of: date) -> dict` returning `{"rows": [], "totals": {}}`, importing `date` from `datetime` per the exact interface in `plan.md`
- [X] T002 [P] Create `tests/test_invoice_desk.py` with a shared helper that reads `data/invoices.csv` as text, a constant `AS_OF = date(2026, 10, 15)`, and a helper for the all-zero six-bucket totals shape

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared parsing, normalization, and validation primitives required by every user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Define in `invoice_desk/__init__.py` the seven header field names in order (`issuer`, `invoice_id`, `issue_date`, `due_date`, `amount_cents`, `currency`, `paid_cents`), the four statuses, the six rejection reasons, the two duplicate reason tokens (`identical_duplicate`, `inconsistent_duplicate`), and the six aging bucket names (`current`, `1-30`, `31-60`, `61-90`, `91+`, `paid`) as module constants
- [X] T004 Implement a private CSV parsing helper in `invoice_desk/__init__.py` using `csv.reader(io.StringIO(csv_text))` and **not** `DictReader`, mapping columns from the header row, treating empty or header-only input as zero data rows, preserving blank lines as data rows, padding rows shorter than seven cells with `""`, ignoring cells beyond the seventh, and trimming leading/trailing whitespace on all seven fields (FR-002, FR-030, FR-031)
- [X] T005 Implement a private row validation helper in `invoice_desk/__init__.py` that returns normalized field values or exactly one rejection reason using the precedence `empty_row`, `missing_required_field`, `invalid_date`, `invalid_amount`, `invalid_currency`, `invalid_payment`: `empty_row` when no cells or all cells blank; `missing_required_field` only when `issuer` or `invoice_id` is blank (all other fields use their own reason); `invalid_date` for a blank or non-strict non-real `YYYY-MM-DD` date; `invalid_amount` for a blank or non-`[0-9]+` amount (using `re.fullmatch`, rejecting `+100`, `-500`, `12.50`, `abc`); `invalid_currency` for a blank or non-`USD` currency; `invalid_payment` for a non-`[0-9]+` payment or one exceeding `amount_cents`, with a blank `paid_cents` treated as `0` (FR-005 to FR-011)
  - *Historical note (added 2026-10-24, L4): the amount clause of this task (`invalid_amount` for a blank or non-`[0-9]+` amount) is superseded by FR-008a and T028: `amount_cents` must match `[1-9][0-9]*`, so `0`, `00` and `0100` are `invalid_amount`. The `paid_cents` clause (`[0-9]+`) is unchanged. The text above is kept as it was when the free model implemented it.*

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Import and classify every invoice row (Priority: P1) 🎯 MVP

**Goal**: Classify every data row as accepted, rejected with a reason, identical duplicate, or inconsistent duplicate, with deterministic import counts and no state between calls.

**Independent Test**: Import the frozen `data/invoices.csv` text as of `2026-10-15`, assert `total_rows = 30`, `accepted = 14`, `rejected = 12`, `duplicate_identical = 2`, `duplicate_inconsistent = 2`, verify every row status and rejection reason, then import the same text again and confirm an identical result with no double-counting.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [US1] Write US1 tests in `tests/test_invoice_desk.py` covering AT-01 and AT-02: all 30 row classifications, exact reasons for rows 19-30, rows 15-16 `duplicate_identical`, rows 17-18 `duplicate_inconsistent`, no accepted fields from rejected/duplicate rows, identical second call, empty `csv_text` and header-only input yielding zero rows plus zero totals with all six aging buckets present as `{"count": 0, "remaining_cents": 0}`, header-driven normalization/trimming, whitespace trimming, `+100` rejected as `invalid_amount`, short rows, and ignored extra cells; also assert accepted rows expose normalized `issuer`, `invoice_id`, `amount_cents`, and `paid_cents`

### Implementation for User Story 1

- [X] T007 [US1] Implement duplicate detection in `invoice_desk/__init__.py` keyed by `(issuer, invoice_id)`, accepting the first validated occurrence and classifying later validated matches as `duplicate_identical` when all seven normalized values match or `duplicate_inconsistent` otherwise, without altering the accepted record (FR-012 to FR-015)
- [X] T008 [US1] Populate `rows` in input order in `invoice_desk/__init__.py`, with 1-based data-row `row` numbers, `status`, and `reason` (`None` for accepted rows, the rejection reason for rejected rows, `"identical_duplicate"` / `"inconsistent_duplicate"` for duplicates), including the normalized `issuer`, `invoice_id`, `amount_cents`, and `paid_cents` on accepted rows per the `plan.md` interface, and leaving `remaining_balance_cents`, `days_overdue`, and `aging_bucket` as `None` for non-accepted rows
- [X] T009 [US1] Populate `totals` in `invoice_desk/__init__.py` with `total_rows`, `accepted`, `rejected`, `duplicate_identical`, and `duplicate_inconsistent`; for empty or header-only input return zero counts with `outstanding_invoice_count = 0`, `total_outstanding_cents = 0`, `total_paid_cents = 0`, and all six aging buckets present as `{"count": 0, "remaining_cents": 0}`; keep the import pure per call with no module-level or persisted state (FR-004, FR-021)

**Checkpoint**: User Story 1 is fully functional and independently testable

---

## Phase 4: User Story 2 - See the exact amount still outstanding (Priority: P2)

**Goal**: Report a non-negative integer-cent remaining balance for every accepted invoice plus exact outstanding and paid totals.

**Independent Test**: Import the frozen CSV, verify each accepted invoice balance equals `amount_cents - paid_cents`, then assert `outstanding_invoice_count = 13`, `total_outstanding_cents = 2139435`, `total_paid_cents = 289999`, and that fully paid `INV-1011` contributes zero and is excluded from the outstanding count.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US2] Write US2 tests in `tests/test_invoice_desk.py` covering AT-03: remaining balance equals `amount_cents - paid_cents` for accepted rows, all amounts are integers, outstanding count and cent sum are exactly `13` and `2139435`, total paid is exactly `289999`, `INV-1011` has remaining `0` and is excluded from outstanding totals, and rejected/duplicate rows retain `remaining_balance_cents = None`; locate invoices via the normalized `invoice_id` exposed on accepted rows

### Implementation for User Story 2

- [X] T011 [US2] Compute `remaining_balance_cents` in `invoice_desk/__init__.py` for every accepted row as `amount_cents - paid_cents` using integer arithmetic and set it to `None` for rejected and duplicate rows (FR-015, FR-016, FR-025)
- [X] T012 [US2] Compute `outstanding_invoice_count` and `total_outstanding_cents` in `invoice_desk/__init__.py` from accepted invoices with a positive remaining balance only, and `total_paid_cents` as the sum of accepted `paid_cents`, all in integer cents (FR-022, FR-023, FR-025)

**Checkpoint**: User Stories 1 and 2 both work independently

---

## Phase 5: User Story 3 - Age invoices against an explicit as-of date (Priority: P3)

**Goal**: Report deterministic days overdue and aging buckets as of the caller-supplied `as_of` date, with exact per-bucket totals.

**Independent Test**: Import the frozen CSV with `as_of = 2026-10-15`, verify each accepted invoice's `days_overdue` and bucket, test the 0/1/30/31/60/61/90/91 boundaries plus due-today, future-due, and fully paid cases, then assert the six aging totals exactly.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [US3] Write US3 tests in `tests/test_invoice_desk.py` covering AT-04: per-invoice `days_overdue` and bucket mapping (`INV-1001 current`, `INV-1002 current`, `INV-1003 1-30`, `INV-1004 1-30`, `INV-1005 31-60`, `INV-1006 31-60`, `INV-1007 61-90`, `INV-1008 61-90`, `INV-1009 91+`, `INV-1010 1-30`, `INV-1011 paid`, `INV-1012 91+`, `INV-1013 current`, `INV-1014 31-60`), boundary unit cases at 0/1/30/31/60/61/90/91 days, future and due-today invoices, fully paid overdue invoice, and aging totals `current {3, 597047}`, `1-30 {3, 396862}`, `31-60 {3, 259664}`, `61-90 {2, 863731}`, `91+ {2, 22131}`, `paid {1, 0}`

### Implementation for User Story 3

- [X] T014 [US3] Compute `days_overdue` in `invoice_desk/__init__.py` for every accepted row as `0` when `due_date` is on or after `as_of`, otherwise `(as_of - due_date).days`, and `None` for rejected and duplicate rows (FR-017, FR-018)
  - *Historical note (added after the build): this task text is superseded by review fix R1 (commit `7010d31`). A fully paid invoice (zero remaining balance) is never overdue, so `days_overdue` is `0` for it, per the updated FR-018. The text above is kept as it was when the free model implemented it.*
- [X] T015 [US3] Assign exactly one `aging_bucket` in `invoice_desk/__init__.py` for every accepted row: `paid` for zero remaining balance, otherwise `current` when not overdue, otherwise `1-30` for 1-30 days, `31-60` for 31-60, `61-90` for 61-90, and `91+` for 91 or more, with `None` for non-accepted rows (FR-019, FR-020)
- [X] T016 [US3] Populate `totals["aging"]` in `invoice_desk/__init__.py` with all six buckets always present as `{"count": int, "remaining_cents": int}`, counting accepted invoices per bucket and summing their integer-cent remaining balances, with `paid` remaining always `0` (FR-024)

**Checkpoint**: All three user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and end-to-end validation across all stories

- [X] T017 Add concise docstrings and type hints to `import_invoices` and its private helpers in `invoice_desk/__init__.py`, documenting the pure, offline, integer-cent, and explicit-`as_of` contract
- [X] T018 Verify the change set is limited to `invoice_desk/__init__.py` and `tests/test_invoice_desk.py`; confirm `bill_split`, `tests/test_split_bill.py`, `tests/test_split_weighted.py`, `data/`, `pyproject.toml`, `ROADMAP.md`, `ACCEPTANCE.md`, `NON_GOALS.md`, `spec.md`, and `plan.md` are unchanged
- [X] T019 Run `python -m pytest -q` from the repository root and confirm `tests/test_invoice_desk.py` plus the existing `tests/test_split_bill.py` and `tests/test_split_weighted.py` all pass
- [X] T020 Audit `invoice_desk/__init__.py` for no floating-point money, no system-clock reads, no network calls, no external dependencies, and no credentials or real personal data, then re-confirm AT-01 through AT-04 values against `ACCEPTANCE.md` and the frozen `data/invoices.csv`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (uses its accepted invoices and row structure)
- **User Story 3 (Phase 5)**: Depends on User Story 1 for accepted rows and User Story 2 for remaining balances (needed for the `paid` bucket)
- **Polish (Phase 6)**: Depends on all three user stories being complete

### Task Dependencies

- T001 ∥ T002 (different files, no dependency on each other)
- T001 → T003 → T004 → T005
- T005 → T006 (tests written and failing) → T007 → T008 → T009
- T009 → T010 (tests written and failing) → T011 → T012
- T012 → T013 (tests written and failing) → T014 → T015 → T016
- T016 → T017 → T018 → T019 → T020

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories after Foundational
- **User Story 2 (P2)**: Depends on US1's accepted-invoice set; independently testable through balances and totals
- **User Story 3 (P3)**: Depends on US1's accepted-invoice set and US2's remaining balance; independently testable through aging output

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Duplicate detection and row outcomes before totals
- Remaining balances before outstanding and paid totals
- Days overdue before bucket assignment, and buckets before aging totals
- Story complete before moving to the next priority

### Parallel Opportunities

- T001 and T002 touch different files and can run in parallel
- After Foundational, all remaining tasks modify either `invoice_desk/__init__.py` or `tests/test_invoice_desk.py`; because both files are shared, the user stories should be implemented sequentially rather than in parallel to avoid conflicts

---

## Parallel Example: Setup

```bash
# T001 and T002 touch different files and have no dependency on each other:
Task: "Create invoice_desk/__init__.py with the import_invoices stub"
Task: "Create tests/test_invoice_desk.py with the frozen CSV helper, AS_OF constant, and zero-totals helper"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the US1 tests and confirm exact AT-01/AT-02 classifications, counts, and the empty-input zero-totals shape
5. Continue to US2 and US3 only after US1 is green

### Incremental Delivery

1. Complete Setup + Foundational → parsing and validation foundation ready
2. Add User Story 1 → verify AT-01/AT-02 independently → deliverable MVP classification slice
3. Add User Story 2 → verify AT-03 independently → exact outstanding and paid totals delivered
4. Add User Story 3 → verify AT-04 independently → aging buckets and totals delivered
5. Complete Polish → full `python -m pytest -q` green and acceptance values re-confirmed

### Sequential Single-Module Strategy

The production code is one module (`invoice_desk/__init__.py`) and the tests are one file (`tests/test_invoice_desk.py`), so split work by story priority rather than by parallel ownership. Keep each checkpoint green before starting the next story.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to a specific user story for traceability
- Tests are included per `plan.md` and the constitution, not as an optional TDD request
- Do not modify `spec.md` or `plan.md`
- Do not introduce persistence, owners, notes, payment events, promised-pay annotations, migration, CLI, UI, or network access; these are out of scope (FR-029 and `NON_GOALS.md`)
- All money values must remain integer cents; never use floats
- `import_invoices` must accept an explicit `as_of` date and never read the machine clock

---

## Phase 7: L4 revision (2026-10-24) - FR-008a positive canonical amounts

**Goal**: Enforce FR-008a: after trimming (FR-030), `amount_cents` must match the canonical positive ASCII pattern `[1-9][0-9]*`, so `0`, `00`, `0100` and `007` are `invalid_amount` in addition to `+100`, `-500`, `12.50`, `abc` and blank. `paid_cents` keeps the unchanged `[0-9]+` pattern (FR-010), including a blank meaning `0` and leading zeros such as `0100`. Validation precedence (FR-011), trimming (FR-030), padding (FR-031), duplicates (FR-012 to FR-015), balances, aging, totals and the `import_invoices` interface are unchanged. `data/invoices.csv` stays byte-unchanged.

**Dependency note**: This phase depends on Phases 1-6 (T001 to T020) being complete and green. Within the phase, the test changes (T021 to T027) MUST be written and FAIL before the implementation change (T028); T028 depends on T021 to T027; T029 depends on T028; T030 depends on T029. No task in this phase may modify `spec.md`, `plan.md`, `data/`, `ACCEPTANCE.md`, `bill_split`, or any other file.

### Tests for Phase 7 (write first, ensure they FAIL) ⚠️

- [X] T021 Change, not delete, `test_zero_amount_is_valid_and_lands_in_paid` in `tests/test_invoice_desk.py`: rename it to state the new rule (for example `test_zero_amount_is_rejected_as_invalid_amount`), and assert that the row `Acme,INV-Z1,2026-09-01,2026-09-01,0,USD,` is `rejected` with reason `invalid_amount`, exposes no accepted fields (`issuer`, `invoice_id`, `amount_cents`, `paid_cents`, `remaining_balance_cents`, `days_overdue`, `aging_bucket`), and that totals show `accepted = 0`, `rejected = 1`, and the `paid` bucket as `{"count": 0, "remaining_cents": 0}`
- [X] T022 Extend the parametrized `invalid_amount` cases in `test_validation_reasons_and_precedence` in `tests/test_invoice_desk.py` with `0`, `00`, `0100`, and the trimmed ` 0100 `, each expected to be `invalid_amount` (keeping the existing `+100`, `abc`, `12.50`, `-500` and blank cases)
- [X] T023 Add a test in `tests/test_invoice_desk.py` that canonical positive amounts `1`, `100` and ` 100 ` are accepted (assert `status == "accepted"`, the parsed integer `amount_cents`, and `remaining_balance_cents`)
- [X] T024 Add a test in `tests/test_invoice_desk.py` that a fully paid positive invoice (`amount_cents = 100`, `paid_cents = 100`) is still accepted, has `remaining_balance_cents == 0`, and lands in the `paid` bucket
- [X] T025 Add a test in `tests/test_invoice_desk.py` that `paid_cents` with a leading zero (`0100` on amount `1000`) is still accepted unchanged under FR-010, with `paid_cents == 100` and `remaining_balance_cents == 900`
- [X] T026 Add precedence tests in `tests/test_invoice_desk.py`: a zero amount with a bad date is `invalid_date`; a zero amount with `EUR` or `usd` is `invalid_amount`; a positive amount with `usd` is `invalid_currency`
- [X] T027 Add a duplicate-detection test in `tests/test_invoice_desk.py` where a zero-amount row shares the same `(issuer, invoice_id)` as a later valid row: the zero row is `rejected` / `invalid_amount` and does not take part in duplicate detection, so the later valid row is `accepted` and totals show `accepted = 1`, `rejected = 1`, `duplicate_identical = 0`, `duplicate_inconsistent = 0`

### Implementation for Phase 7

- [X] T028 Change ONLY the amount check in `invoice_desk/__init__.py` `_validate_row`: add a separate amount pattern matching `[1-9][0-9]*` and use it for `amount_cents` (rejecting `0`, `00`, `0100`, `007`, `+100`, `-500`, `12.50`, `abc` and blank as `invalid_amount`), while `paid_cents` keeps the existing `[0-9]+` pattern and validation; leave validation precedence, trimming, padding, duplicates, balances, aging, totals and the `import_invoices` interface unchanged
- [X] T029 Run `python -m pytest -q` from the repository root and confirm all tests pass, including the changed and new L4 tests and the existing `tests/test_split_bill.py` and `tests/test_split_weighted.py`
- [X] T030 Verify implementation scope with `git status` and `git diff`: only `tests/test_invoice_desk.py` and `invoice_desk/__init__.py` changed in implementation; confirm `spec.md`, `plan.md`, `data/invoices.csv`, `ACCEPTANCE.md`, `bill_split`, `tests/test_split_bill.py` and `tests/test_split_weighted.py` are unchanged

## Phase 8: L5 revision (2026-10-25) - FR-007a due date not before issue date

**Goal**: Enforce FR-007a: after trimming (FR-030), `issue_date` and `due_date` must each be real Gregorian dates in strict `YYYY-MM-DD` form, and a `due_date` strictly earlier than `issue_date` is `invalid_date`. Equal dates are valid. `invalid_date` is reused; FR-011, the reason set and the `ACCEPTANCE.md` values are unchanged. A rejected row takes no part in duplicate detection. `data/invoices.csv` stays byte-unchanged.

**Dependency note**: This phase depends on Phases 1-7 (T001 to T030) being complete and green. T031 to T033 are one work unit, committed once, with the suite green. Within the unit, the test changes (T031, T032) MUST be written and FAIL before the implementation change (T033); T033 depends on T031 and T032. T034 depends on T033; T035 depends on T034. No task in this phase may modify `spec.md`, `plan.md`, `data/`, or any file outside the allowed list.

**Run rules**
- Allowed files only: `specs/003-desk-import/{spec,plan,tasks,drift,progress,ralph-memory}.md`, `specs/004-deterministic-followup-queue/spec.md`, `ACCEPTANCE.md`, `tests/test_invoice_desk.py`, `invoice_desk/__init__.py`. Anything else stops the run.
- 300-line diff cap for the whole run. Up to 3 fix tries per failing task, then stop and record the failure in `ralph-memory.md`.
- Never edit `.specify/`, `.opencode/`, the constitution, `data/`, `queue.py`, `annotations.py`, `pyproject.toml`, `run.log`. Install nothing. No push, no merge, no new branches, no git config changes.

### Tests for Phase 8 (write first, ensure they FAIL) ⚠️

- [X] T031 In `test_aging_bucket_boundaries`, change the issue date of every row from `2026-01-01` to `2025-01-01`; keep all nine offsets. Suite still passes.
- [X] T032 Add tests (write first; they must FAIL on the current code): a due-before-issue row (for example `Acme,INV-D1,2026-09-15,2026-09-14,1000,USD,0`) is rejected with `invalid_date`; due-before-issue plus amount `abc` is `invalid_date` (FR-011); a due-before-issue row then a valid row with the same issuer and invoice_id: the first is `invalid_date`, the second is `accepted`, with no duplicates. Also add an equal-dates row that is `accepted` (a guard; it passes already). Run the suite and confirm that only the new due-before-issue tests fail.

### Implementation for Phase 8

- [X] T033 In `invoice_desk/__init__.py` `_validate_row`, right after the existing `invalid_date` check, return `None, "invalid_date"` when `due_date < issue_date`. Change nothing else. The full suite passes.
- [X] T034 Add dated L5 notes, docs only: an entry in `specs/003-desk-import/drift.md`; in `specs/004-deterministic-followup-queue/spec.md`, a `Session 2026-10-25 (L5 ripple)` Clarification plus one dated L5 note under FR-021 and one under SC-010 (same style as the L4 notes); a note under AT-02 in `ACCEPTANCE.md`. No values change.
- [X] T035 Final check: the full suite passes; `git diff --numstat d6c7d7be4fa61084cf48c400a73c44798e1a063a` shows only allowed paths, with under 300 lines in total; `grep -n 'INV-B{offset},2026-01-01' tests/test_invoice_desk.py` prints nothing; spec.md has no unstruck FR-007 line.

## Phase 9: L6 revision (2026-10-27) - FR-032 accepted rows expose dates and currency

**Goal**: Enforce FR-032: every accepted row also exposes `issue_date` and `due_date` as ISO `YYYY-MM-DD` strings and `currency` as the trimmed string, taken from the first accepted occurrence. Rejected and duplicate rows gain no keys (FR-015, SC-008). Classification, reasons, precedence, trimming, padding, duplicates, balances, aging and totals are unchanged; no queue key or order changes. `data/invoices.csv` stays byte-unchanged.

**Dependency note**: This phase depends on Phases 1-8 (T001 to T035) being complete and green. The tests (T036) and the code change (T037) are one work unit, committed once, with the suite green: write T036 first and confirm it fails where the feature is missing, then implement T037. T038 depends on T037; T039 depends on T038. No task in this phase may modify any file outside the allowed list.

**Run rules**
- Allowed files: `specs/003-desk-import/{spec,plan,tasks,drift,progress,ralph-memory}.md`, `specs/004-deterministic-followup-queue/spec.md`, `tests/test_invoice_desk.py`, `invoice_desk/__init__.py`.
- Never edit `queue.py`, `annotations.py`, `contracts/public-api.md`, `ACCEPTANCE.md`, other test files, `data/`, `.specify/`, `.opencode/`, `pyproject.toml`. Never edit or delete an existing test.
- Under 300 changed lines in total. Up to 3 fix tries per failing task, then stop and record it in `ralph-memory.md`. Install nothing. No push, no merge, no new branches, no git config changes.

### Tests for Phase 9 (write first, ensure they FAIL where the feature is missing) ⚠️

- [X] T036 Add new tests (add only; never edit or delete an existing test) in `tests/test_invoice_desk.py` for acceptance checks 1-6: (1) `INV-1001`, `INV-1013`, `INV-1011` expose the exact `issue_date`, `due_date`, `currency` as `str`; (2) a single trimmed row is accepted with trimmed dates and currency; (3) every accepted row has exactly `{row, status, reason, issuer, invoice_id, issue_date, due_date, amount_cents, currency, paid_cents, remaining_balance_cents, days_overdue, aging_bucket}`, and every rejected (rows 19-30) and duplicate (rows 15-18) row has exactly `{row, status, reason, remaining_balance_cents, days_overdue, aging_bucket}`; (4) an inconsistent duplicate has no `due_date` key (FR-014); (5) `json.dumps(result)` succeeds and two calls give equal results (FR-004, FR-026); (6) through `build_followup_queue`, AT-01 to AT-04 totals, queue order `INV-1009 … INV-1011` and queue item keys are unchanged

### Implementation for Phase 9

- [X] T037 In `invoice_desk/__init__.py`, add `issue_date`, `due_date` (ISO strings) and `currency` (trimmed) to accepted rows only, from the normalized first accepted occurrence. Change nothing else; rejected and duplicate rows keep their existing keys. The full suite passes.
- [X] T038 Docs only: close drift 003-U1 in `specs/003-desk-import/drift.md`; in `specs/004-deterministic-followup-queue/spec.md`, add dated L6 notes under FR-021 and SC-010 (same style as the L4/L5 notes). No 004 code change.
- [X] T039 Final check: full suite passes with the 209 existing tests unchanged (no existing test edited or deleted); diff is under 300 lines; `git status` shows only allowed files touched.
