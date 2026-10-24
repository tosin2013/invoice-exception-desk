# Drift log: 003-desk-import (L4, 2026-10-24)

Every mismatch found between spec, plan, tasks, docs, tests and code during the L4 revision
(FR-008 → FR-008a, positive canonical amounts). Each entry: what, where, how found, and the fix
or "accepted, why". Commit `2526069` is the behaviour change (spec, tests, code in one commit).

## Baseline (before `l4-start`)

| ID | What | Where | How found | Disposition |
|----|------|-------|-----------|-------------|
| B1 | `set_owner` / `set_notes` consumed `accepted_identities` twice, so a one-shot iterator raised `InvoiceNotAcceptedError`. | `invoice_desk/annotations.py` (004) | Manual probe during L4 pre-run review (2026-10-23) | **Fixed before L4** by PR #7 (merge `3ba09fd`, fix `751d28c`), with a one-shot-iterator test. `l4-start` was cut from `3ba09fd`. |

## Found by `/speckit.analyze` on 003 (OpenCode, free model, read-only)

| ID | Sev | What | Where | Disposition |
|----|-----|------|-------|-------------|
| 003-I1 | HIGH | T005 still states the old amount clause (`[0-9]+`) without a superseded marker. | `tasks.md` T005 | **Fixed** (follow-up commit): dated historical note under T005 pointing to FR-008a/T028; T005 text kept byte-identical. |
| 003-I2 | MEDIUM | Pre-L4 `analysis.md` (A3, C2) reads as current: `[0-9]+` grammar, "zero amount is valid". | `analysis.md` | **Fixed**: dated "pre-L4 snapshot, non-normative" note at the top; rows kept. |
| 003-I3 | LOW | Spec and plan cite `drift.md`, which did not exist yet. | `spec.md` Clarifications, `plan.md` L4 revision | **Fixed**: this file. |
| 003-U1 | LOW | Accepted rows expose `issuer`, `invoice_id`, `amount_cents`, `paid_cents` but not dates/currency, while the Key Entity lists them. | `plan.md` Interface, `spec.md` Key Entities | **Accepted, pre-existing** (L3 interface, unchanged by L4, no behaviour drift from FR-008a). Candidate for a later editorial clarification. |
| 003-C1 | LOW | Top-level Constitution Check still cites v1.1.0. | `plan.md` | **Fixed**: marked historical, pointing to the v2.0.0 check in the L4 revision section. |

## Found by `/speckit.analyze` on 004 (OpenCode, free model, read-only)

| ID | Sev | What | Where | Disposition |
|----|-----|------|-------|-------------|
| 004-C1 | HIGH | 004 plan's Constitution Check cites v1.1.0 and treats the annotation store as an exception; v2.0.0 rule II now authorizes it explicitly. | 004 `plan.md` | **Fixed**: v1.1.0 check marked historical; dated "Constitution v2.0.0 re-check and L4 ripple" section with a no-behaviour-impact note (rule V). |
| 004-I1 | HIGH | The L4 ripple was not recorded on the 004 side, and 004 plan says `tests/test_invoice_desk.py` "must remain unchanged", which L4 changed. | 004 `plan.md`; 003 `spec.md` Clarification wording | **Fixed**: ripple recorded in the same 004 section; the "unchanged" lines explained as 004 build scope, superseded by the owning 003 revision; 003 Clarification now names both plans. 004 FR-021/SC-010 not amended (they constrain 004 itself). |
| 004-I3 | HIGH | Same as 003-I1 (T005). | 003 `tasks.md` | **Fixed** with 003-I1. |
| 004-I2 | MEDIUM | `drift.md` missing. | 003 | **Fixed**: this file. |
| 004-U1 | MEDIUM | `AnnotationValueTypeError` (non-string owner/notes) exists in code and tests but not in 004 spec, contract, plan or tasks. | `invoice_desk/annotations.py`, 004 docs | **Accepted, pre-existing, out of L4 scope.** Added in L3.5 review fixes (approved by Tosin, see `run.log`), before `l4-start`; unrelated to FR-008a. Needs its own 004 spec clarification in a later change. |
| 004-G1 | MEDIUM | No 004-side regression test that a zero-amount row is absent from the queue and its `paid` bucket. | `tests/test_followup_queue.py` | **Accepted.** 003 tests cover the rejection (`test_zero_amount_is_rejected_as_invalid_amount`), and 004 already tests that rejected rows are excluded from the queue. A 004 test would add coverage, not behaviour; left for the sealed L4 key / reviewer. |
| 004-I4 | LOW | Same as 003-I2 (`analysis.md`). | 003 | **Fixed** with 003-I2. |

## Found by hand (grep of specs, docs, ACCEPTANCE, README, ROADMAP, NON_GOALS, code, tests)

Searched for: `zero amount`, `zero-amount`, `[0-9]+`, `any digits`, `leading zero`, `0100`, `one or more ASCII digits`.

| ID | What | Where | Disposition |
|----|------|-------|-------------|
| M1 | Old rule in T005 | 003 `tasks.md` | Same as 003-I1 (analyze found it too). **Fixed.** |
| M2 | Old rule in pre-L4 analysis rows A3, C2 | 003 `analysis.md` | Same as 003-I2. **Fixed.** |
| M3 | `_INTEGER_PATTERN = [0-9]+` still in code | `invoice_desk/__init__.py` | **Accepted, intended**: used only for `paid_cents` (FR-010 unchanged); amounts use `_AMOUNT_PATTERN = [1-9][0-9]*`. |
| M4 | ACCEPTANCE.md refers to `data/oracle.json`, which is not in the repository. | `ACCEPTANCE.md` (AT-01 to AT-03 "Oracle refs") | **Accepted, pre-existing**, unrelated to FR-008a. The oracle is held outside the builder workspace with the sealed keys; the public values are the ones written in ACCEPTANCE.md. |
| M5 | 004 test helper `invoice(..., balance=0, ...)` could look like a zero-amount invoice. | `tests/test_followup_queue.py:61` | **No drift**: the call passes `paid=900`, so amount is `900`. No 004 test builds a zero-amount invoice. |
| — | README.md, ROADMAP.md, NON_GOALS.md, 004 spec | — | No statement of the old rule found. |

## Found by the re-check `/speckit.analyze` on 003 (after the fixes above)

All four earlier HIGH findings (003-I1, 004-C1, 004-I1, 004-I3) reported **RESOLVED**; 0 CRITICAL, 0 HIGH.

| ID | Sev | What | Where | Disposition |
|----|-----|------|-------|-------------|
| R-I01 | MEDIUM | T030 (and old T018) say to confirm `spec.md`, `plan.md` and `ACCEPTANCE.md` are unchanged, but the owning L4 revision changed them in the same commit. | `tasks.md` T018, T030 | **Accepted, why:** both are scope checks for what the *implementing agent* may touch. T030 was executed that way (OpenCode's own changes were limited to `tests/test_invoice_desk.py`, `invoice_desk/__init__.py` and the Phase 7 checkboxes; verified by diffing against operator copies). The spec/plan/tasks/ACCEPTANCE edits are the operator's L4 Steps 1–3, in the same commit per rule V. |
| R-I03 | LOW | "T001–T020 unchanged / byte-identical" no longer literal after the T005 historical note. | `plan.md` L4 revision, this file | **Fixed here:** task *text* of T001–T020 is unchanged; one dated historical sub-bullet was added under T005 (drift fix 003-I1), same style as the earlier T014 note. |
| R-I02 | LOW | Duplicate `reason` tokens (`identical_duplicate`) invert the status tokens (`duplicate_identical`). | `plan.md` Interface, T003, T008 | **Accepted, pre-existing** L3 interface, tested and unrelated to FR-008a. |
| R-A01 | LOW | Spec assumes fixed column order; plan maps by header name. | `spec.md` Assumptions, `plan.md` Design 2 | **Accepted, pre-existing**; malformed headers are declared out of scope. |
| R-D01 | LOW | FR-019 and FR-020 both state the bucket boundaries. | `spec.md` | **Accepted, pre-existing**, consistent duplication. |

## Merge conflicts
None. `tasks.md` was appended by `/speckit.tasks` (Phase 7) with the task text of T001–T020 unchanged; no conflict occurred.
