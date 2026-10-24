# ACCEPTANCE — Invoice Exception Desk (AT-01 .. AT-10)

Acceptance suite specification. The executable R0 checks live in `tests/test_oracle.py`; the
application acceptance for AT-01..AT-05, AT-09, AT-10 is executed in **R1**, and AT-06/AT-07/AT-08
in **R2/R3/R5** respectively.

**Frozen fixture.** `data/invoices.csv` (30 rows, seed `20261015`, as_of `2026-10-15`).
**Source of truth.** `data/oracle.json`, produced by `data/compute_oracle.py`. Expected values below
quote the oracle; if the seed changes, the oracle — not this table — wins.

Import totals (oracle): `total_rows=30`, `accepted=14`, `rejected=12`,
`duplicate_identical=2`, `duplicate_inconsistent=2`, `outstanding_invoice_count=13`,
`total_outstanding_cents=2139435`, `total_paid_cents=289999`.

Aging totals (accepted rows): `current={3, 597047}`, `1-30={3, 396862}`, `31-60={3, 259664}`,
`61-90={2, 863731}`, `91+={2, 22131}`, `paid={1, 0}`.

---

## AT-01 — Import counts & idempotency

- **Inputs:** `data/invoices.csv`; import twice in the same store.
- **Expected outcomes:** First import yields accepted 14, rejected 12, duplicate_identical 2,
  duplicate_inconsistent 2 (rows 15–18 are the duplicates; row 11 `INV-1011` fully pays down).
  Second import changes no counts and no balances (identical duplicates remain no-ops; nothing
  is re-imported as new).
- **Oracle refs:** `rows[].status`; `totals.*` in `data/oracle.json`.
- **Pass criterion:** After both runs, store counts equal the oracle totals and row-level statuses
  match `oracle.rows` exactly.

## AT-02 — Rejection reasons, no partial import

- **Inputs:** rows 19–30 of `data/invoices.csv`.
- **Expected outcomes:** each rejected row carries exactly its oracle reason, and **no** field from a
  rejected row is written to the store:
  `19 invalid_amount`, `20 invalid_amount`, `21 invalid_amount`, `22 invalid_date`, `23 invalid_date`,
  `24 invalid_date`, `25 missing_required_field`, `26 invalid_currency`, `27 invalid_payment`,
  `28 invalid_payment`, `29 empty_row`, `30 empty_row`.
- **Oracle refs:** rows 19–30 (all `status=rejected`).
- **Pass criterion:** reason per row matches; store contains zero records derived from rejected rows.
- **Amount policy (revised 2026-10-24, decided by Tosin Akinosho; see `specs/003-desk-import/spec.md` FR-008a):**
  `amount_cents` must be a positive, canonical ASCII decimal integer (`[1-9][0-9]*` after trimming).
  `0` and leading-zero amounts such as `0100` are rejected as `invalid_amount`; lower-case `usd` stays
  `invalid_currency`. The frozen fixture contains none of these values, so rows 19–30 and every
  oracle value above are unchanged. Superseded (non-normative): any `[0-9]+` amount, including `0`,
  was accepted.

## AT-03 — Integer-cent sums, zero balance excluded

- **Inputs:** accepted rows; store the fully paid row `INV-1011` (row 11, remaining `0`).
- **Expected outcomes:** all balances are integer cents; `total_outstanding_cents=2139435`
  over `outstanding_invoice_count=13`; `INV-1011` is excluded from the outstanding sum and bucket
  `paid` holds `remaining_cents=0`.
- **Oracle refs:** `totals.total_outstanding_cents`, `totals.outstanding_invoice_count`,
  `totals.aging.paid`, row 11.
- **Pass criterion:** reported outstanding equals the oracle sum and count; no float rounding;
  the zero-balance invoice contributes `0` and is not counted as outstanding.

## AT-04 — Aging boundaries

- **Inputs:** accepted rows 1–14; as_of `2026-10-15` (America/New_York).
- **Expected outcomes:** `overdue = balance > 0 AND due_date < as_of`; buckets:
  `INV-1001` not due → `current`; `INV-1002` due today → `current`; `INV-1003` 1d → `1-30`;
  `INV-1004` 30d → `1-30`; `INV-1005` 31d → `31-60`; `INV-1006` 60d → `31-60`;
  `INV-1007` 61d → `61-90`; `INV-1008` 90d → `61-90`; `INV-1009` 91d → `91+`;
  `INV-1012` 91d → `91+`; `INV-1014` 31d → `31-60`; `INV-1013` future → `current`.
- **Oracle refs:** `rows[].days_overdue`, `rows[].aging_bucket`.
- **Pass criterion:** every row's `days_overdue` and `aging_bucket` equal the oracle; boundaries at
  0/1/30/31/60/61/90/91 land in the specified bucket.

## AT-05 — Deterministic prioritization + owner/notes persistence

- **Inputs:** the accepted set; two owner/note assignments; a restart.
- **Expected outcomes:** the follow-up queue order is a pure function of row data (e.g. sort by
  `days_overdue` desc, then `remaining_balance_cents` desc, then `issuer`, then `invoice_id`), so two
  runs produce identical order; owners and notes persist across restart.
- **Oracle refs:** `rows[].days_overdue`, `rows[].remaining_balance_cents`, `rows[].issuer`,
  `rows[].invoice_id`.
- **Pass criterion:** identical ordering on repeated runs; owner/notes survive a restart unchanged.

## AT-06 — Payment events: idempotency, overpay, negative (R2)

- **Inputs:** a payment event against an accepted row; the same event ID replayed; an overpay
  (`paid > amount`); a negative payment. The oracle already rejects raw overpay/negative rows
  (rows 27, 28 → `invalid_payment`).
- **Expected outcomes:** replaying an event ID is a no-op (balance unchanged); an overpayment is
  rejected; a negative payment is rejected; the original `amount_cents` is never overwritten;
  remaining balance = `amount_cents - sum(valid payments)`.
- **Oracle refs:** rows 27, 28; partial-payment rows 10 (`INV-1010`, remaining `60000`),
  11 (`INV-1011`, remaining `0`), 12 (`INV-1012`, remaining `1`).
- **Pass criterion:** replay is idempotent; invalid payments are rejected; original amounts immutable.

## AT-07 — Promised-pay date never reduces balance (R3)

- **Inputs:** set, then clear, a promised-pay date on an overdue accepted row.
- **Expected outcomes:** balance, `days_overdue` and `aging_bucket` are unchanged; the promised-pay
  date is stored as a note only.
- **Oracle refs:** any accepted overdue row, e.g. row 7 `INV-1007` (61d, `61-90`).
- **Pass criterion:** before/after balances and buckets are identical; only the annotation changes.

## AT-08 — Migration preserves v1 (R5)

- **Inputs:** a v1 data store; migrate to v2a (payments) and v2b (promised-pay).
- **Expected outcomes:** migrated data reproduces pre-migration accepted rows, balances, buckets and
  queue order exactly (equivalent to the oracle for the same CSV).
- **Oracle refs:** full `rows[]` and `totals` from `data/oracle.json`.
- **Pass criterion:** post-migration snapshot equals pre-migration snapshot; no row lost or altered.

## AT-09 — No network / no secrets

- **Inputs:** the repository and the running app during acceptance.
- **Expected outcomes:** no outbound network calls, no external services, no credentials/tokens in
  code, fixtures, or logs (see `NON_GOALS.md`).
- **Oracle refs:** n/a (guardrail).
- **Pass criterion:** acceptance passes with networking blocked; secret/PII scan is clean.

## AT-10 — Fresh-checkout reproducibility

- **Inputs:** a clean checkout with only the Python standard library.
- **Expected outcomes:** `python3 data/generate_invoices.py` reproduces `data/invoices.csv`
  byte-for-byte; `python3 data/compute_oracle.py` reproduces `data/oracle.json`; the test suite is green.
- **Oracle refs:** `data/invoices.csv`, `data/oracle.json`.
- **Pass criterion:** `python3 -m unittest discover -s tests -v` reports **OK** with 15 tests on a
  fresh checkout, and regenerated artifacts are byte-identical to the committed ones.
