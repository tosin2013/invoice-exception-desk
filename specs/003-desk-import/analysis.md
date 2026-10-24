## Specification Analysis Report

> *Pre-L4 snapshot (historical, non-normative, noted 2026-10-24): findings A3 and C2 refer to the superseded FR-008 (`[0-9]+`, zero allowed). The current rule is FR-008a; see spec.md and drift.md.*

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Ambiguity | HIGH | `spec.md:101,107,79` | FR-005/FR-011 require “required fields” but never enumerate them. A blank `amount_cents`, `currency`, `paid_cents`, or date is ambiguous between `missing_required_field` and the field-specific rejection reason. | State that all seven fields are required (or list exceptions), and align T005 with that precedence. |
| C1 | Underspecification | HIGH | `spec.md:131-135`, `plan.md:22`, `tasks.md:67,84,105` | The plan’s `rows` interface exposes only `row`, `status`, `reason`, `remaining_balance_cents`, `days_overdue`, and `aging_bucket`. Spec’s **Source row** and **Accepted invoice** entities require the seven input fields, and T010/T013 assert per-invoice behavior by `INV-####`. | Add the normalized seven fields to accepted/source-row output (or add a separate `invoices` list), and update T008/T010/T013 accordingly. |
| A2 | Ambiguity | MEDIUM | `spec.md:91`, `plan.md:26-28`, `tasks.md:62` | Empty-string/no-header input is not defined; T006 expects zero rows for “empty input,” while the plan says the first row is the header. The shape of “zero totals” (all six aging buckets?) is also unspecified. | Define no-header/empty-input behavior and the exact zero-totals shape; align T006. |
| A3 | Ambiguity / Inconsistency | MEDIUM | `spec.md:104,106`, `plan.md:28` | The plan rejects `+100`, while FR-008 only rejects signs implying a negative value. Also, `str.isdigit()` accepts non-ASCII digits such as `²`, which are not base-10 and may fail `int()`. | Specify an ASCII `[0-9]+` grammar and explicit plus-sign handling; align FR-008/FR-010 and plan design 3. |
| A4 | Ambiguity | LOW | `spec.md:98,156`, `plan.md:27` | The header contract is incomplete: the plan maps columns by name, while the spec assumes the documented order. Behavior for missing, duplicate, or unknown header columns is not defined. | State exact header requirements (fixed order or name-based) and behavior for malformed headers. |
| C2 | Coverage Gap | LOW | `spec.md:81,84`, `tasks.md:62,84,105` | Spec edge cases “zero amount is valid” and “same invoice id from a different issuer is not a duplicate” have no explicit test task and no fixture row. | Add unit cases to T006 or a dedicated test task. |
| F1 | Inconsistency | LOW | `spec.md:99,110`, `plan.md:22`, `tasks.md:67-68` | Duplicate `reason` tokens `"identical_duplicate"` / `"inconsistent_duplicate"` invert the spec/status terms `duplicate_identical` / `duplicate_inconsistent`; T003 defines neither reason value. | Use the spec tokens or omit duplicate reasons; add constants if retained. |
| F2 | Inconsistency | LOW | `tasks.md:33-34,141,164` | T001/T002 are described as parallel in prose, but only T002 carries `[P]`; T001 → T002 is also listed as a dependency. | Mark both `[P]` or remove the dependency arrow and clarify. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T001, T004, T014, T020 | Explicit `as_of`, no clock |
| FR-002 | Yes | T004 | Header mapping |
| FR-003 | Yes | T007-T009 | Four-way classification |
| FR-004 | Yes | T006, T009, T020 | Pure per-call |
| FR-005 | Yes | T005 | Required-field set ambiguous (A1) |
| FR-006 | Yes | T005 | |
| FR-007 | Yes | T005 | |
| FR-008 | Yes | T005 | Numeric grammar ambiguous (A3) |
| FR-009 | Yes | T005 | |
| FR-010 | Yes | T005 | Blank `paid_cents` ambiguity (A1) |
| FR-011 | Yes | T005 | |
| FR-012 | Yes | T007 | |
| FR-013 | Yes | T007 | |
| FR-014 | Yes | T007 | |
| FR-015 | Yes | T007, T008, T011 | T006 assertion weak until C1 is fixed |
| FR-016 | Yes | T011 | |
| FR-017 | Yes | T014 | |
| FR-018 | Yes | T014 | |
| FR-019 | Yes | T015 | |
| FR-020 | Yes | T015 | |
| FR-021 | Yes | T009 | |
| FR-022 | Yes | T012 | |
| FR-023 | Yes | T012 | |
| FR-024 | Yes | T016 | |
| FR-025 | Yes | T011, T012, T016, T020 | |
| FR-026 | Yes | T006, T009, T020 | |
| FR-027 | Yes | T001, T003, T018 | |
| FR-028 | Yes | T020 | |
| FR-029 | Yes | T018, T020 | Scope guard |
| FR-030 | Yes | T004 | |
| FR-031 | Yes | T004 | |
| SC-001 | Yes | T006, T009 | |
| SC-002 | Yes | T006 | |
| SC-003 | Yes | T006, T009 | |
| SC-004 | Yes | T010, T012 | |
| SC-005 | Yes | T010, T011 | |
| SC-006 | Yes | T013, T015 | |
| SC-007 | Yes | T013, T016 | |
| SC-008 | Yes | T006, T011 | Weak until C1 is fixed |
| SC-009 | Yes | T006, T009, T020 | |
| SC-010 | Yes | T020 | |

**Constitution Alignment Issues:** None. The plan’s Constitution Check cites v1.1.0 and matches the current constitution; no MUST principle is violated by the spec/plan/tasks set.

**Unmapped Tasks:** None. T017-T020 are cross-cutting polish/verification tasks mapped to FR-025/FR-026/FR-027/FR-028/FR-029 and SC-009/SC-010.

**Metrics:**

- Total Requirements: 41 (31 FR + 10 SC)
- Total Tasks: 20
- Coverage: 100% (41/41 have at least one mapped task)
- Ambiguity Count: 4
- Duplication Count: 0
- Critical Issues Count: 0
- Severity Mix: 2 HIGH, 2 MEDIUM, 4 LOW

**Cross-document note (informational, outside the three-file scope):** `ACCEPTANCE.md:117` expects `python3 -m unittest discover -s tests -v` to report 15 tests, while `plan.md:9`, `tasks.md:123`, and the constitution use pytest; the current suite has 67 pytest tests. This does not change the spec/plan/tasks internals but should be reconciled before acceptance. Also, `ROADMAP.md` lists AT-05 under R1 while this feature intentionally excludes it, making this a deliberate partial-R1 slice.

## Next Actions

No CRITICAL issues were found. Resolve the two HIGH findings before `/speckit.implement`:

1. **C1** — Extend the plan interface and T008/T010/T013 so accepted invoices expose identity and source fields (`issuer`, `invoice_id`, `issue_date`, `due_date`, `amount_cents`, `currency`, `paid_cents`).
2. **A1** — Enumerate the required fields in `spec.md` and confirm the validation precedence for blank values.
3. Address A2/A3 and the LOW wording/parallel-marker issues via `/speckit.specify`, `/speckit.plan`, and `/speckit.tasks` refinement, or manual edits.
4. Then run `/speckit.implement`.

Would you like me to suggest concrete remediation edits for the top 3 issues — C1, A1, and A3? I will not apply them automatically.
