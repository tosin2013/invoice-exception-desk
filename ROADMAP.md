# ROADMAP — Invoice Exception Desk

Decision queue for a fictional B2B commercial-cleaning operator. Answers: *Which unpaid
invoices need attention, what is truly outstanding, who does what next?* This is not
invoicing, collections, payments, or a QuickBooks replacement (see `NON_GOALS.md`).

- Product source: Notion child plan **"DRAFT v0.1 — Invoice Exception Desk"** (`<internal-plan-id>`).
- This roadmap starts at **R0**, the only stage marked `[planned]` on the source plan.

Owner of this file: the PM / Founder (plans and replans). This file is the **one roadmap of record**:
GitHub issues and PRs are linked from it, not a second status source; boards are views, not records.
IDs never change. `Order` is the PM's priority (lowest first). Owner per stage is the accountable party
(see each section); that stage's reviewer accepts its exit.

Status legend (one per row):

- `planned` — on the roadmap, no reviewed spec yet. A candidate for `/speckit.specify`, not a build job.
- `specified` — the row has a usable, reviewed spec (spec.md, and plan/tasks once written); no
  implementation yet.
- `building` — implementation is underway on one or more of the row's specs; the row's exit criteria
  are not all met. A PR that finishes one of several specs adds its link and the row stays `building`.
- `blocked — <reason>; reopen when <condition>` — can't proceed for a reason outside the row's own work.
  Spec dirs and links stay. Never eligible to run.
- `done` — the row's **full** exit criteria (its section below) are met and the stage reviewer has
  accepted it. Only the change that meets them sets `done`. A PR or commit link is evidence that a change
  exists, not that it was accepted.
- `dropped — <reason>` — removed on purpose. A dropped dependency is **not** satisfied: rows that
  depend on it must be re-planned.

Rows may list several spec dirs and several issue/PR/commit links. A `done` row needs at least one PR or
commit link; a row finished before Spec Kit was used (R0) may have Spec dir `— (pre-Spec Kit)` if it has a
commit link.

**R0 provenance is unchanged.** R0's record is the freeze commit
[`8de94f6`](https://github.com/tosin2013/invoice-exception-desk/commit/8de94f69b1b6307f0fa2617dda3ad1d078b61cf8)
and its [`MANIFEST.sha256`](https://github.com/tosin2013/invoice-exception-desk/blob/8de94f69b1b6307f0fa2617dda3ad1d078b61cf8/MANIFEST.sha256)
(ROADMAP.md `84e5cb4a…dbf3565`). Restructuring this file later changed only its current hash (see
`PACKET.md`); no R0 rerun or revalidation is implied.

**Where the specs live:** this roadmap is on `main`, but the code and `specs/` live on the
[`l5-setup`](https://github.com/tosin2013/invoice-exception-desk/tree/l5-setup) branch. So `Spec dir` names the branch as well as the path
(`l5-setup:specs/NNN-name/`), with a link. The drift check (`.github/workflows/roadmap-drift.yml`) reads those
paths from that branch with `git ls-tree`.

| ID | Feature | One-line scope (in / out) | Outcome | Depends on | Order | Milestone | Status | Spec dir | Issue / PR |
|----|---------|---------------------------|---------|------------|-------|-----------|--------|----------|------------|
| R0 | Discovery & Spec Kit | In: data contract, fixture, oracle, acceptance suite, guardrails / Out: any app code (R1) | Discovery kit frozen; `tests/test_oracle.py` green; oracle recomputes exactly | — | 1 | — | done — R0 freeze record (see note) | — (pre-Spec Kit) | [commit `8de94f6`](https://github.com/tosin2013/invoice-exception-desk/commit/8de94f69b1b6307f0fa2617dda3ad1d078b61cf8) (frozen before PRs were used) |
| R1 | Exception Desk MVP | In: import, aging, follow-up queue with owner/notes, AT-01..05, AT-09, AT-10 / Out: payments (R2), promised pay (R3), migration (R5) | All R1 acceptance items pass against the frozen oracle | R0 | 2 | — | building | [`l5-setup:specs/003-desk-import/`](https://github.com/tosin2013/invoice-exception-desk/tree/l5-setup/specs/003-desk-import) (AT-01..04); [`l5-setup:specs/004-deterministic-followup-queue/`](https://github.com/tosin2013/invoice-exception-desk/tree/l5-setup/specs/004-deterministic-followup-queue) (AT-05) | [issue #16](https://github.com/tosin2013/invoice-exception-desk/issues/16), [issue #22](https://github.com/tosin2013/invoice-exception-desk/issues/22) / [PR #5](https://github.com/tosin2013/invoice-exception-desk/pull/5), [PR #7](https://github.com/tosin2013/invoice-exception-desk/pull/7), [PR #8](https://github.com/tosin2013/invoice-exception-desk/pull/8), [PR #14](https://github.com/tosin2013/invoice-exception-desk/pull/14), [PR #17](https://github.com/tosin2013/invoice-exception-desk/pull/17), [PR #23](https://github.com/tosin2013/invoice-exception-desk/pull/23) |
| R2 | Payment events (v2a) | In: event-ID idempotency, no negative or overpay, balance recalc / Out: collection, bank feeds, promised pay (R3) | AT-06 passes; original `amount_cents` never changes | R1 | 3 | — | planned | — | — |
| R3 | Promised-pay annotations (v2b) | In: promised-pay date as a note that may affect ordering / Out: reminders, calendar sync | AT-07 passes; balances and buckets unchanged | R2 | 4 | — | planned | — | — |
| R4 | Prioritization, owners & notes hardening | In: deterministic order, owner, note history, persistence across restarts, queue filters / Out: notifications, SLAs, analytics | Same input gives the same queue; owner/notes survive restart (AT-05) | R1 | 5 | — | planned | — | — |
| R5 | Schema & version migration | In: v1 → v2a → v2b with no data loss / Out: cross-tenant or cloud migration | AT-08 passes; balances and queue identical after migration | R2, R3 | 6 | — | planned | — | — |
| R6 | Review & hand-off readiness | In: full AT-01..AT-10 run, secrecy/network checks, fresh-checkout run, docs sync / Out: deployment, hosting, auth | Every acceptance item passes from a clean checkout with no network | R4, R5 | 7 | — | planned | — | — |

**Why R1 is `building`, not `done`:** both R1 slices are specified and implemented on `l5-setup`
(`003-desk-import`: AT-01..AT-04, L3, then PRs #8, #14, #17, #23; `004-deterministic-followup-queue`: AT-05,
PRs #5 and #7, merged via `l3h-handoff`, which `l5-setup` contains). Every task in both `tasks.md` files is
ticked and the suite on `l5-setup` passes. But R1's scope also names AT-09 (no network/secrets) and AT-10
(fresh-checkout reproducibility), which no spec covers yet, and the R1 exit has not been reviewed by the
Founder. Set `done` when that review happens, with the PR that records it.

**Spec back-links:** `l5-setup:specs/004-deterministic-followup-queue/spec.md` opens with
`Input: Parent roadmap -> R1` (added in PR #40, `ca86ed4`); 003's Input names R1 in prose.

**R0 acceptance, honestly:** R0's `done` predates this legend. It was written by the R0 run itself
and frozen in commit `8de94f6`; its evidence is that freeze record (`R0_REPORT.md`, `MANIFEST.sha256`,
`PACKET.md`). `PACKET.md` says the oracle and tests were written by the builder and are self-grading, not
independent correctness evidence. No separate reviewer acceptance record is linked in this repo. R0 stays
`done` as the frozen discovery baseline that R1 was built on, not as an independently verified result.
This self-graded `done` is a labeled historical exception, not a precedent: new rows reach `done` only
through the whole-row rule above.

**Why this order** (from this file's own content):

- **R1 before everything else (after R0):** every later stage depends on it, and R1's out-of-scope list
  hands payments to R2, promised pay to R3 and migration to R5.
- **R2 follows R1:** R2 depends on R1. R1 computes the exact remaining balance; R2 records payment events
  so partial payments *recalculate* that balance without changing the original amount. R2 extends R1's
  balance, so it can't come first.
- **R3 after R2, R5 after R2 and R3:** R3 is "v2b" and R2 is "v2a"; R5 migrates v1 → v2a → v2b, so both
  schemas must exist before there is anything to migrate.
- **R4 at Order 5:** R4 depends only on R1, so it could run before R2. This file doesn't say why it comes
  after R3. Its section says "R2/R3 fields become available during this stage", which suggests it waits for
  them, but that is not stated as the reason. The order is kept from the original file; the PM decides.
- **Riskiest assumption and value:** not recorded in this file, so they don't explain the order here.

### Specs outside this roadmap

These dirs on `l5-setup` are the L1/L2 tutorial exercises (`bill_split`), not Invoice Exception Desk
features, so they have no row. The drift check counts a dir listed here as accounted for.

- `l5-setup:specs/001-split-bill/` (L1)
- `l5-setup:specs/002-weighted-split/` (L2)

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
- **Spec dirs (on `l5-setup`):** `specs/003-desk-import/` (AT-01..AT-04) and
  `specs/004-deterministic-followup-queue/` (AT-05). AT-09 and AT-10 have no spec yet.
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
