# Feature Specification: Invoice CSV import and aging

**Feature Branch**: `003-desk-import`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "Build the first slice of roadmap phase R1 for the Invoice Exception Desk: a pure Python package invoice_desk that imports invoice CSV text, classifies every row as accepted, rejected (with a reason), duplicate_identical or duplicate_inconsistent, and for accepted rows computes the remaining balance in integer cents, days overdue and aging bucket as of an explicit as_of date, plus totals. It must satisfy ACCEPTANCE.md AT-01 to AT-04 on data/invoices.csv and follow the policies in ROADMAP.md and NON_GOALS.md. The follow-up queue, owners and notes (AT-05) are out of scope for this feature. Use the short name desk-import."

## Clarifications

### Session 2026-10-23

- Q: When a later CSV differs from the original but contains invoice rows already accepted in the store, how should those overlapping rows be classified? → A: There is no store; import is a pure per-call function, so duplicate detection is scoped to the rows within that single call.
- Q: Should surrounding whitespace in CSV cells be trimmed before validation, identity matching, and duplicate comparison, or treated as part of the value? → A: Trim leading/trailing whitespace on all seven fields before validation and duplicate comparison; case and internal characters remain significant.
- Q: How should a data row be handled when its cell count does not match the seven header columns (for example, six or eight cells)? → A: Pad missing trailing cells with blanks and ignore cells beyond the seventh, then apply the normal validation precedence.

### Session 2026-10-24 (L4 revision, decided by Tosin Akinosho)

- Q: Is an `amount_cents` of `0` a valid invoice amount? → A: No. Only positive face amounts are valid; `0` is rejected as `invalid_amount`. Why: a zero-amount "invoice" is not a receivable, and accepting it silently placed a non-debt in the `paid` bucket (and, through 004, in the follow-up queue's `paid` bucket). This supersedes the earlier edge case "a zero amount is valid". Replaces FR-008 with FR-008a.
- Q: Is an amount with a leading zero, such as `0100`, valid? → A: No. Only canonical ASCII decimal amounts are valid (first digit `1`-`9`, no leading zeros); `0100` is rejected as `invalid_amount`. Why: one amount must have one spelling, so the stored value and the source text cannot disagree on review. Replaces FR-008 with FR-008a.
- Q: Should a lower-case currency such as `usd` be accepted? → A: No change. It stays rejected as `invalid_currency` under FR-009 (exactly `USD`). Recorded here so the L4 ruling is complete.
- Unchanged by this session: `paid_cents` parsing and limits (FR-010, including a blank meaning `0`), error precedence (FR-011), trimming (FR-030), short-row padding (FR-031) and duplicate handling (FR-012 to FR-015). A fully paid invoice with a positive amount is still accepted and placed in the `paid` bucket.
- `/speckit.clarify` (OpenCode, free model, no human in the session, told not to answer its own questions) raised five questions on 2026-10-24. Each is answered from the rulings above or from the approved L4 run brief; none introduced new policy:
  - Q: How is `paid_cents` parsed, and are `0100` and `100` identical for duplicate comparison? → A: Unchanged (ruling: `paid_cents` and duplicate handling unchanged). `paid_cents` stays `[0-9]+` after trimming under FR-010 (leading zeros allowed, no sign, blank means `0`), and duplicates compare normalized parsed values (FR-014), so `0100` and `100` in `paid_cents` compare equal. FR-008a does not apply to `paid_cents`.
  - Q: Does "a blank required field is `missing_required_field`" cover all seven fields? → A: Unchanged (ruling: precedence unchanged). Only `issuer` and `invoice_id` are required (FR-005); a blank amount is `invalid_amount`, a blank date `invalid_date`, a blank currency `invalid_currency`, and a blank `paid_cents` means `0`.
  - Q: Which whitespace characters are trimmed? → A: Unchanged (ruling: trimming unchanged). FR-030 and the shipped behaviour stay as they are: surrounding whitespace as removed by Python's `str.strip()`. FR-008a is checked on the trimmed value.
  - Q: Does 004's "import behaviour unchanged" guarantee (004 FR-021, SC-010) need an amendment? → A: No amendment to 004's requirements. 004 FR-021/SC-010 constrain what 004 itself may change; this revision is owned by 003 (constitution V). The ripple (a zero-amount invoice is now rejected at import, so it can no longer reach 004's queue or its `paid` bucket) is recorded in 003 `plan.md` (L4 revision), in 004 `plan.md` (Constitution v2.0.0 re-check and L4 ripple) and in 003 `drift.md`, and checked by `/speckit.analyze` on 004.
  - Q: How is the revised amount policy validated, given the frozen fixture has none of the new invalid values? → A: Synthetic unit tests in `tests/test_invoice_desk.py` (written first), with `data/invoices.csv` byte-unchanged. Grading against an independently sealed L4 key, held outside the builder workspace, follows constitution VIII.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import and classify every invoice row (Priority: P1)

An operator feeds the invoice CSV text into the desk and gets one clear outcome for every row: accepted, rejected with a reason, identical duplicate, or inconsistent duplicate. Invalid rows never leak into the desk, and importing the same file again does not double-count anything.

**Why this priority**: Classification is the foundation of the desk. Without trustworthy import and duplicate handling, every balance and aging figure downstream is suspect.

**Independent Test**: Import the frozen `data/invoices.csv` text as of `2026-10-15`, inspect every row outcome and the import counts, then call the import again with the same text and confirm the returned result is identical.

**Acceptance Scenarios**:

1. **Given** `data/invoices.csv` and `as_of = 2026-10-15`, **When** the file is imported, **Then** the result contains `total_rows = 30`, `accepted = 14`, `rejected = 12`, `duplicate_identical = 2`, and `duplicate_inconsistent = 2`.
2. **Given** the same CSV text is imported again as a separate call, **When** the call completes, **Then** all import counts, row classifications, and balances are identical and no invoice is counted twice.
3. **Given** rows 15-18, **When** they are classified against the earlier accepted rows in the same call, **Then** rows 15-16 are `duplicate_identical`, rows 17-18 are `duplicate_inconsistent`, and neither duplicate type creates or alters an accepted invoice.
4. **Given** rejected rows 19-30, **When** they are classified, **Then** their reasons are exactly: `19 invalid_amount`, `20 invalid_amount`, `21 invalid_amount`, `22 invalid_date`, `23 invalid_date`, `24 invalid_date`, `25 missing_required_field`, `26 invalid_currency`, `27 invalid_payment`, `28 invalid_payment`, `29 empty_row`, `30 empty_row`.
5. **Given** any rejected or duplicate row, **When** the import finishes, **Then** no field from that row contributes to the accepted invoices.

---

### User Story 2 - See the exact amount still outstanding (Priority: P2)

An operator needs to know what is truly still owed. Accepted invoices report a remaining balance in whole cents, and the desk reports the total outstanding and total already paid without floating-point drift.

**Why this priority**: Exact money is the reason the desk exists. A one-cent error or a paid invoice counted as outstanding destroys trust in the queue.

**Independent Test**: Import the frozen CSV, inspect accepted balances, and verify the outstanding count and sums against the acceptance values, including the fully paid invoice.

**Acceptance Scenarios**:

1. **Given** an accepted invoice with amount `A` cents and recorded payment `P` cents, **When** its balance is calculated, **Then** the remaining balance is `A - P` integer cents and is never negative.
2. **Given** the accepted rows from `data/invoices.csv`, **When** outstanding totals are calculated, **Then** `outstanding_invoice_count = 13` and `total_outstanding_cents = 2139435`.
3. **Given** the accepted rows, **When** paid totals are calculated, **Then** `total_paid_cents = 289999`.
4. **Given** `INV-1011` (row 11) with remaining balance `0`, **When** outstanding totals and the paid bucket are calculated, **Then** it contributes `0` to the outstanding sum, is excluded from the outstanding count, and the `paid` bucket reports `{count: 1, remaining_cents: 0}`.
5. **Given** any reported amount, **When** it is inspected, **Then** it is an integer number of cents, never a floating-point value.

---

### User Story 3 - Age invoices against an explicit as-of date (Priority: P3)

An operator reviews the desk for a specific reporting date and sees how overdue each unpaid invoice is, grouped into stable aging buckets. The result never depends on the machine clock.

**Why this priority**: Aging turns raw balances into a work queue, but it is only useful if every operator and every rerun sees the same buckets for the same reporting date.

**Independent Test**: Import the frozen CSV with `as_of = 2026-10-15`, then verify each accepted invoice's days overdue and bucket at the 0/1/30/31/60/61/90/91 boundaries plus the future and fully paid cases.

**Acceptance Scenarios**:

1. **Given** an accepted invoice with a positive remaining balance and `due_date < as_of`, **When** aging is calculated, **Then** it is marked overdue with days overdue equal to the calendar days from `due_date` to `as_of`.
2. **Given** an accepted invoice due on `as_of` or later, **When** aging is calculated, **Then** days overdue is `0`, it is not overdue, and its bucket is `current`.
3. **Given** the frozen accepted rows at `as_of = 2026-10-15`, **When** buckets are assigned, **Then** `INV-1001 current`, `INV-1002 current`, `INV-1003 1-30`, `INV-1004 1-30`, `INV-1005 31-60`, `INV-1006 31-60`, `INV-1007 61-90`, `INV-1008 61-90`, `INV-1009 91+`, `INV-1010 1-30`, `INV-1011 paid`, `INV-1012 91+`, `INV-1013 current`, and `INV-1014 31-60`.
4. **Given** the frozen accepted rows, **When** aging totals are calculated, **Then** `current = {3, 597047}`, `1-30 = {3, 396862}`, `31-60 = {3, 259664}`, `61-90 = {2, 863731}`, `91+ = {2, 22131}`, and `paid = {1, 0}`.

---

### Edge Cases

- A row with no cells, or with every cell blank after trimming surrounding whitespace, is `empty_row`; it is never reported as a different missing-field or validation error.
- Surrounding whitespace is trimmed from all seven fields before validation and comparison, so ` USD ` is valid and matches `USD`, while `"Acme Cleaning Co "` and `"Acme Cleaning Co"` are the same value; case and internal spacing remain significant.
- A row with fewer than seven cells is padded with blank values for the missing trailing fields, and cells beyond the seventh are ignored; the padded row then follows the normal precedence (so a missing required trailing field is `missing_required_field`, and an otherwise-all-blank row is `empty_row`).
- A row with a blank required field is `missing_required_field`, even if another field would also fail validation.
- Both `issue_date` and `due_date` must be real calendar dates in strict `YYYY-MM-DD` form; `2026-13-40`, `not-a-date`, and `10/15/2026` are invalid dates.
- An amount of `abc`, `12.50`, or `-500` is invalid. An amount of `0` is invalid (`invalid_amount`), and so is an amount with a leading zero such as `0100` or `00` (FR-008a). *(Revised 2026-10-24. Superseded text, non-normative: "a zero amount is valid as an integer number of cents.")*
- A canonical positive amount such as `1`, `100` or `1000000` is valid; surrounding whitespace is trimmed first (FR-030), so ` 100 ` is valid, but a leading zero is still invalid after trimming (` 0100 ` is `invalid_amount`).
- A fully paid invoice with a positive amount (for example `amount_cents = 100`, `paid_cents = 100`) is still accepted, with zero remaining, in the `paid` bucket.
- A currency other than `USD`, including a case or spelling variant, is invalid.
- A negative payment, an overpayment, or a non-integer payment is invalid; a payment exactly equal to the amount is valid and leaves zero remaining.
- The same invoice identifier from a different issuer is not a duplicate; the duplicate key is issuer plus invoice identifier.
- An inconsistent duplicate is flagged and never replaces or merges with the first accepted record.
- A later row identical to an accepted record is `duplicate_identical` and is a no-op.
- Processing the same CSV text again in a separate call produces an identical result; there is no stored state in which rows could accumulate.
- An invoice due today is `current` with zero days overdue; an invoice due tomorrow is also `current` with zero days overdue.
- An invoice with a positive balance of one cent is outstanding; only a zero balance is excluded from the outstanding count and sum.
- A fully paid invoice whose due date is long past is placed in `paid`, never in an overdue bucket.
- An empty CSV data set, or a file with only a header, yields zero rows and zero totals rather than an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The capability MUST accept invoice CSV text and an explicit `as_of` calendar date; it MUST NOT read the system clock.
- **FR-002**: The CSV MUST be interpreted through its header row, which provides `issuer`, `invoice_id`, `issue_date`, `due_date`, `amount_cents`, `currency`, and `paid_cents`. Data rows MUST be evaluated in input order.
- **FR-003**: Every data row MUST receive exactly one classification: `accepted`, `rejected` with exactly one reason, `duplicate_identical`, or `duplicate_inconsistent`. The four import counts MUST sum to the total number of data rows.
- **FR-004**: Import MUST be a pure per-call function: no state persists between calls, duplicate detection is scoped to the rows of that single call, and the same CSV text and `as_of` date MUST return an identical result with no accumulated or double-counted records.
- **FR-005**: The required fields are `issuer` and `invoice_id` (the identity). A row where either is missing or blank MUST be rejected as `missing_required_field`. A blank date, amount or currency is rejected with that field's own reason (`invalid_date`, `invalid_amount`, `invalid_currency`). A blank `paid_cents` means `0`. *(Analyze fix A1.)*
- **FR-006**: A row with no cells or only blank cells MUST be rejected as `empty_row`. This reason takes precedence over every other validation reason.
- **FR-007**: `issue_date` and `due_date` MUST each be a real Gregorian calendar date in strict `YYYY-MM-DD` form. Any other form or impossible date MUST be rejected as `invalid_date`.
- **FR-008** *(SUPERSEDED 2026-10-24 by FR-008a; non-normative, kept for history)*: ~~`amount_cents` MUST be one or more ASCII digits `[0-9]+` (no sign, no decimal point, no spaces inside). Anything else, including `+100`, `-500`, `12.50` and `abc`, MUST be rejected as `invalid_amount`.~~ *(Analyze fix A3.)*
- **FR-008a** *(added 2026-10-24, Clarification session 2026-10-24, decided by Tosin Akinosho; replaces FR-008)*: After trimming (FR-030), `amount_cents` MUST be a positive, canonical ASCII decimal integer: it MUST match `[1-9][0-9]*` (no sign, no decimal point, no spaces inside, no leading zeros). Anything else, including `0`, `00`, `0100`, `+100`, `-500`, `12.50`, `abc` and a blank amount, MUST be rejected as `invalid_amount`. This requirement applies to `amount_cents` only; `paid_cents` stays governed by FR-010.
- **FR-009**: `currency` MUST be exactly `USD`. Any other value MUST be rejected as `invalid_currency`.
- **FR-010**: `paid_cents` MUST be a non-negative base-10 integer number of cents and MUST NOT exceed `amount_cents`. A negative payment, an overpayment, a non-integer payment, or a payment that cannot be parsed MUST be rejected as `invalid_payment`.
- **FR-011**: When a row fails more than one validation, the reported reason MUST be deterministic, using this precedence: `empty_row`, `missing_required_field`, `invalid_date`, `invalid_amount`, `invalid_currency`, `invalid_payment`.
- **FR-012**: Only rows that pass validation participate in duplicate detection. Duplicate identity MUST use the pair `(issuer, invoice_id)`.
- **FR-013**: The first validated occurrence of an invoice identity within the call MUST be accepted and included as an accepted invoice.
- **FR-014**: A subsequent validated row in the same call with the same identity MUST be `duplicate_identical` when all seven normalized field values match the first accepted record, and `duplicate_inconsistent` when any field value differs. Neither duplicate classification may alter, replace, merge with, or add to the accepted record.
- **FR-015**: A rejected or duplicate row MUST NOT contribute any field to the accepted invoices, either wholly or partially.
- **FR-016**: For every accepted invoice, `remaining_balance_cents` MUST equal `amount_cents - paid_cents` as an integer number of cents, and MUST be zero or positive.
- **FR-017**: An invoice MUST be considered overdue only when its remaining balance is positive and its `due_date` is earlier than `as_of`.
- **FR-018**: For an accepted invoice, `days_overdue` MUST be `0` when the invoice is not overdue under FR-017 (a zero remaining balance, or `due_date` on or after `as_of`), and otherwise the number of calendar days from `due_date` to `as_of`. *(Review fix R1: the earlier wording ignored the zero-balance case and contradicted FR-017.)*
- **FR-019**: Every accepted invoice MUST receive exactly one aging bucket: `paid` when the remaining balance is `0`; otherwise `current` when it is not overdue; otherwise `1-30` for 1 through 30 days overdue, `31-60` for 31 through 60, `61-90` for 61 through 90, and `91+` for 91 or more.
- **FR-020**: Aging bucket boundaries MUST be based on days overdue, not on calendar month names, and MUST place 0 days in `current`, 1 and 30 days in `1-30`, 31 and 60 days in `31-60`, 61 and 90 days in `61-90`, and 91 days in `91+`.
- **FR-021**: Import totals MUST include `total_rows`, `accepted`, `rejected`, `duplicate_identical`, and `duplicate_inconsistent`, and MUST be identical whenever the same CSV text and `as_of` date are supplied again.
- **FR-022**: Outstanding totals MUST include the count and cent sum of accepted invoices whose remaining balance is positive. Zero-balance invoices MUST be excluded from that count and sum.
- **FR-023**: Paid totals MUST include the sum of recorded `paid_cents` for accepted invoices, expressed in integer cents.
- **FR-024**: Aging totals MUST report, for every bucket, the number of accepted invoices in that bucket and the sum of its remaining balances in integer cents. The `paid` bucket MUST report its count and a remaining sum of `0`.
- **FR-025**: Every monetary calculation and total MUST use integer cents. Floating-point arithmetic MUST NOT be used for money.
- **FR-026**: The same CSV text and `as_of` date MUST always produce the same classifications, balances, buckets, and totals.
- **FR-027**: The capability MUST be delivered as a pure, offline Python package named `invoice_desk`, using only the standard library, with no UI or command-line workflow required for this slice.
- **FR-028**: The capability MUST make no network calls, use no external services, and contain no credentials, secrets, or real personal data.
- **FR-029**: The follow-up queue, prioritization order, owner assignment, note persistence, payment events, promised-pay annotations, and schema migration are out of scope for this feature.
- **FR-030**: Before any validation, empty-row detection, identity matching, or duplicate comparison, leading and trailing whitespace MUST be trimmed from all seven field values. Case and internal characters MUST remain significant, so trimming MUST NOT change case or collapse internal spacing.
- **FR-031**: A data row with fewer than seven cells MUST be treated as having blank values for each missing trailing field, and cells beyond the seventh MUST be ignored. The padded row MUST then be evaluated using the same validation precedence and rejection reasons as a full-width row.

### Key Entities *(include if feature involves data)*

- **Source row**: One data row from the CSV, in input order, with its seven invoice fields and its outcome.
- **Import outcome**: The classification of one source row: accepted, rejected with a reason, duplicate identical, or duplicate inconsistent.
- **Accepted invoice**: A validated first occurrence of an invoice identity, with issuer, invoice identifier, dates, amount, currency, recorded payment, remaining balance, days overdue, and aging bucket.
- **Import result**: The value returned by one pure import call, containing the classification of every source row plus the accepted invoices and totals. No store or state persists between calls.
- **Import totals**: The counts of every classification plus outstanding, paid, and aging summary figures.
- **Aging bucket**: One of `current`, `1-30`, `31-60`, `61-90`, `91+`, or `paid`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Importing the frozen `data/invoices.csv` at `as_of = 2026-10-15` yields exactly `total_rows = 30`, `accepted = 14`, `rejected = 12`, `duplicate_identical = 2`, and `duplicate_inconsistent = 2` in 100% of runs.
- **SC-002**: Every row classification and every rejection reason matches the acceptance expectations for rows 1-30, with zero unknown or missing outcomes.
- **SC-003**: Processing the same CSV text again in a separate call returns identical counts, balances, and classifications and adds no duplicate invoice records.
- **SC-004**: Outstanding totals are exactly `13` invoices and `2139435` cents, and total paid is exactly `289999` cents.
- **SC-005**: A zero-balance invoice contributes exactly `0` to outstanding totals, is excluded from the outstanding count, and appears in the `paid` bucket with a remaining sum of `0`.
- **SC-006**: The 0/1/30/31/60/61/90/91-day boundaries map to the required buckets in 100% of cases, including due-today and future-due invoices.
- **SC-007**: Aging totals equal `current {3, 597047}`, `1-30 {3, 396862}`, `31-60 {3, 259664}`, `61-90 {2, 863731}`, `91+ {2, 22131}`, and `paid {1, 0}`.
- **SC-008**: Rejected and duplicate rows contribute zero accepted-invoice fields, so no partially imported record can be observed.
- **SC-009**: Repeated runs with identical inputs produce identical results, and results are independent of the machine clock.
- **SC-010**: The feature operates with networking blocked and uses no credentials, secrets, or real personal data.

## Assumptions

- The frozen fixture `data/invoices.csv` (30 rows, seed `20261015`) and the acceptance values in `ACCEPTANCE.md` are the source of truth for this slice; the reporting date is `2026-10-15` in `America/New_York`.
- The CSV is synthetic, contains a header row, and uses the seven documented columns in the documented order; additional caveats about malformed headers are outside this slice.
- Import is a pure per-call function with no store or persistence; re-running the same input reproduces the same result. Persistence across process restarts, owners, notes, and the follow-up queue belong to AT-05 and are out of scope.
- "Duplicate identity" means the same `issuer` plus `invoice_id`. The field comparison for identical duplicates uses normalized accepted values rather than raw text formatting; normalization trims surrounding whitespace but preserves case and internal characters.
- Dates are civil dates in `America/New_York`; no time-of-day arithmetic is needed, and an explicit `as_of` value is always supplied by the caller.
- Amounts in the CSV are already integer cents. There is no currency conversion, tax computation, invoicing, payment processing, reminders, or collections workflow.
- Payment events, partial-payment event identifiers, promised-pay annotations, and schema migrations belong to later roadmap phases R2, R3, and R5 and MUST NOT be introduced by this feature.
- The package is delivered as a pure library for programmatic use in this slice; a graphical or command-line front end, hosting, authentication, and multi-tenancy are out of scope.
- The acceptance document supplies the business policies for this slice; where it is silent, the deterministic defaults in this specification apply.
