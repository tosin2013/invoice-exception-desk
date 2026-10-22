# ROADMAP — Invoice Exception Desk

Decision queue for a fictional B2B commercial-cleaning operator. Answers: *Which unpaid
invoices need attention, what is truly outstanding, who does what next?* This is not
invoicing, collections, payments, or a QuickBooks replacement (see `NON_GOALS.md`).

- Product source: Notion child plan **"DRAFT v0.1 — Invoice Exception Desk"** (`<internal-plan-id>`).
- This roadmap starts at **R0**, the only stage marked `[planned]` on the source plan.

Legend — status: `done` | `planned` | `blocked`. Owner is the accountable party; the
reviewer approves stage exit.

| ID | Objective (one line) | Depends on | Owner | Status |
|----|----------------------|------------|-------|--------|
| R0 | Freeze discovery artifacts: data contract, oracle, acceptance suite, guardrails | — | Implementer (review: Founder) | done |
| R1 | Build the read-only exception desk MVP: import, aging, follow-up queue | R0 | Implementer (review: Founder) | planned |
| R2 | Add payment events: partial payments, idempotent event IDs, overpay/negative guards | R1 | Implementer (review: Founder) | planned |
| R3 | Add promised-pay annotations (note-only; never mutates balance) | R2 | Implementer (review: Founder) | planned |
| R4 | Prioritization, owners, notes persistence and queue workflow hardening | R1 | Implementer (review: Founder) | planned |
| R5 | Schema/version migration (v1 → v2a → v2b) with no data loss | R2, R3 | Implementer (review: Founder) | planned |
| R6 | Review, hardening, and hand-off readiness (no deployment) | R4, R5 | Implementer (review: Founder) | planned |

---

## R0 — Discovery & Spec Kit

- **Objective:** Produce the frozen, verifiable discovery kit (data contract, deterministic
  fixture, independently computed oracle, acceptance suite, guardrails) with no application build.
- **In scope:** `SPEC.md`; `data/generate_invoices.py`; `data/invoices.csv`; `data/compute_oracle.py`;
  `data/oracle.json`; `tests/test_oracle.py`; `ACCEPTANCE.md`; `NON_GOALS.md`; this roadmap; `R0_REPORT.md`.
- **Out of scope:** Any application/runtime code, UI, persistence, network calls, deployment (**R1**).
- **Dependencies:** None. Blocking dependency for every later stage.
- **Owner:** Implementer; exit reviewed by Founder.
- **Spec/test links:** `SPEC.md` (T1–T7); `tests/test_oracle.py`; `ACCEPTANCE.md` (AT-01..AT-10).
- **Exit evidence:** Generator is byte-for-byte deterministic; `python3 -m unittest discover -s tests -v`
  is green; `data/oracle.json` recomputes exactly; boundary cases match policy.

## R1 — Exception Desk MVP

- **Objective:** Import a CSV, classify accepted/rejected/duplicate rows with reasons, compute exact
  remaining balance, days overdue and aging bucket as of an explicit as-of date, and present a
  follow-up queue with owner and notes.
- **In scope:** Import (AT-01, AT-02), integer-cent balances and sums (AT-03), aging (AT-04),
  deterministic prioritization + owner/notes persistence (AT-05), no network/secrets (AT-09),
  fresh-checkout reproducibility (AT-10).
- **Out of scope:** Payments/partial payments (**R2**), promised-pay notes (**R3**), schema migration (**R5**),
  deployment, auth/multi-tenancy (**R6 / NON_GOALS**).
- **Dependencies:** R0.
- **Owner:** Implementer; exit reviewed by Founder.
- **Spec/test links:** `ACCEPTANCE.md` AT-01..AT-05, AT-09, AT-10; `data/oracle.json`.
- **Exit evidence:** All R1 acceptance items pass against the frozen oracle on the generated CSV;
  rejected rows never partially import; re-import is idempotent.

## R2 — Payment Events (v2a)

- **Objective:** Record (never overwrite) payment events so partial payments recalculate the
  remaining balance without altering the original invoice amount.
- **In scope:** Event-ID idempotency, no negative payments, no overpayment (AT-06); balance recalc.
- **Out of scope:** Outbound payment collection/processing, bank feeds, promised pay (**R3**).
- **Dependencies:** R1.
- **Owner:** Implementer; exit reviewed by Founder.
- **Spec/test links:** `ACCEPTANCE.md` AT-06; `data/oracle.json` (rows the partial-payment fixtures).
- **Exit evidence:** Replaying the same payment event ID is a no-op; overpay/negative are rejected;
  original `amount_cents` is immutable.

## R3 — Promised-Pay Annotations (v2b)

- **Objective:** Let an operator record a promised-pay date as a note for prioritization.
- **In scope:** Store promised-pay date; it may influence ordering but **never** reduces balance (AT-07).
- **Out of scope:** Automated reminders/messages, calendar sync, contracts.
- **Dependencies:** R2.
- **Owner:** Implementer; exit reviewed by Founder.
- **Spec/test links:** `ACCEPTANCE.md` AT-07; `SPEC.md` user story BR-05.
- **Exit evidence:** Setting/clearing a promised-pay date leaves all balances and aging buckets unchanged.

## R4 — Prioritization, Owners & Notes

- **Objective:** Harden the follow-up queue: deterministic priority ordering, owner assignment,
  note history, and stable persistence across restarts.
- **In scope:** AT-05 deterministic ordering + owner/notes persistence, queue filters.
- **Out of scope:** Notifications, SLAs/automation, analytics beyond the queue.
- **Dependencies:** R1 (R2/R3 fields become available during this stage).
- **Owner:** Implementer; exit reviewed by Founder.
- **Spec/test links:** `ACCEPTANCE.md` AT-05.
- **Exit evidence:** Same input yields the same queue order; owner/notes survive restart; ties broken deterministically.

## R5 — Schema & Version Migration

- **Objective:** Migrate persisted data across v1 → v2a → v2b without data loss or balance drift.
- **In scope:** Migration preserves v1 rows (AT-08); forward/backward compatibility checks.
- **Out of scope:** Cross-tenant or cloud migration, deployment.
- **Dependencies:** R2, R3.
- **Owner:** Implementer; exit reviewed by Founder.
- **Spec/test links:** `ACCEPTANCE.md` AT-08.
- **Exit evidence:** Migrated store reproduces the pre-migration balances and queue exactly.

## R6 — Review & Hand-off Readiness

- **Objective:** Final review/hardening pass and a clean hand-off package; confirm guardrails hold.
- **In scope:** Full acceptance run (AT-01..AT-10), secrecy/network checks (AT-09), reproducibility on a
  fresh checkout (AT-10), documentation sync.
- **Out of scope:** Deployment, hosting, auth/multi-tenancy, production operations.
- **Dependencies:** R4, R5.
- **Owner:** Implementer; approved by Founder.
- **Spec/test links:** `ACCEPTANCE.md` AT-01..AT-10; `NON_GOALS.md`.
- **Exit evidence:** Every acceptance item passes from a clean checkout with no network access.
