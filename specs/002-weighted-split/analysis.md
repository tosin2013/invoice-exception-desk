## Specification Analysis Report

No `.specify/extensions.yml` found, so no pre/post hooks were checked or executed. Analysis is read-only; no files were modified.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Ambiguity | HIGH | spec.md:L15, L78, L94; plan.md:L17; tasks.md:L104 | "Accept any sequence (list or tuple)" is self-contradictory. The plan/tasks restrict to `list`/`tuple` via `isinstance`, so behavior for other sequences (e.g. `range`, `array.array`) is unspecified, yet the spec says "any sequence". | State explicitly: only `list`/`tuple` (including subclasses) are accepted; all other types raise `TypeError`. Add a `range` test to lock the contract. |
| G1 | Coverage Gap | MEDIUM | spec.md:L90, L111; tasks.md:L85 | SC-004/FR-006 require equal weights to match `split_bill`, but T010 tests only unit weights `[1] * n`, not other equal-weight sets such as `[5, 5, 5]` or `[2, 2]`. | Add parity cases with non-unit equal weights (e.g. `[3,3,3]`, `(7,7)`). |
| I2 | Inconsistency | MEDIUM | tasks.md:L14, L129-138, L193 | Tasks claim user stories are "independently completable and testable", but the dependency section says US2 depends on US1 and US3 integration depends on US1/US2. | Reconcile wording: either mark US2/US3 as not independently implementable or restructure tasks so each story can truly stand alone. |
| I1 | Terminology Drift | LOW | spec.md:L49 vs L89, L109; plan.md:L23; tasks.md:L79, L84 | Acceptance wording says shares differ by "less than one cent", while requirements/plan/tasks say "within one cent". The latter permits exactly one cent. | Standardize on "less than one cent" (the actual largest-remainder guarantee) everywhere. |
| G2 | Coverage Gap | LOW | spec.md:L94; tasks.md:L99 | FR-010's non-integer categories are tested at container level (`None`, string, generator), but not as individual weights (`[None, 1]`, `["1", 1]`) or as `total_cents` (`None`, string). | Add parametrized cases for non-integer values inside `weights` and for non-integer `total_cents` types beyond `float`/`bool`. |
| I3 | Inconsistency | LOW | tasks.md:L129-131, L145 | L131 says US3 "can begin after Foundational" but must be merged after US1/US2, while L129 implies all story phases simply depend on Foundational; L145 says move to "next priority" though all stories are P1. | Remove the conditional/ambiguous wording and document the actual sequential order (US1 → US2 → US3). |
| I4 | Lifecycle Drift | LOW | spec.md:L7; tasks.md (all `[X]`) | Spec status remains `Draft` although plan, tasks, implementation, and tests are complete. | Update spec status to reflect completion (e.g. `Implemented`/`Ready`). |
| A2 | Ambiguity | LOW | plan.md:L6 | "Written by the human/strong role, like L1" references an undefined process/role not present in the artifacts. | Remove the phrase or define the role/process. |
| D1 | Duplication | LOW | spec.md:L39, L90, L119; plan.md:L19-21; tasks.md:L64, L84 | The largest-remainder and tie-break rule is repeated in the user story, FR-006, assumptions, plan, and multiple tasks. | Keep the normative rule in FR-006 and reference it elsewhere. |
| D2 | Duplication | LOW | plan.md:L16-23; tasks.md:L64, L104-105 | Plan design is reproduced almost verbatim in T005/T013/T014, creating a drift risk. | Have tasks reference the plan section instead of restating the algorithm. |
| U1 | Underspecification | LOW | spec.md:L76 | "Very large totals and weights" has no bound or quantified criterion. | State a concrete bound or clarify that "large" is validated by exactness/property tests. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 split_weighted API | Yes | T002, T005, T013 | Signature matches spec |
| FR-002 one share per weight, same order | Yes | T005, T006 | |
| FR-003 non-negative integer shares | Yes | T004, T006 | |
| FR-004 sum equals total | Yes | T003, T004, T005, T007 | |
| FR-005 within one cent | Yes | T006, T007, T009 | Wording differs from US2 (I1) |
| FR-006 largest remainder + tie-break | Yes | T005, T008, T009 | |
| FR-007 zero weight yields zero | Yes | T004, T005 | |
| FR-008 non-negative ints, no bool | Yes | T011, T012, T013 | |
| FR-009 ValueError cases | Yes | T012, T014 | |
| FR-010 TypeError cases + precedence | Yes | T011, T012, T013 | Container-type scope ambiguous (A1) |
| FR-011 pure/deterministic | Yes | T018 | Audit task, not automated test |
| FR-012 split_bill unchanged | Yes | T001, T017 | Verified by diff + suite |
| SC-001 exact sum | Yes | T003, T004, T005, T007 | |
| SC-002 within one cent | Yes | T007, T009 | |
| SC-003 scenarios tested | Yes | T003, T007, T011, T012, T019 | |
| SC-004 equal-weight parity | Yes | T010 | Only unit weights tested (G1) |
| SC-005 invalid inputs tested | Yes | T011, T012, T015, T019 | Minor element-level gaps (G2) |
| SC-006 existing tests pass | Yes | T001, T016 | |

**Constitution Alignment Issues:** None. Plan and tasks comply with I (integer cents), II (pure/deterministic), III (stdlib only, pytest), and IV (tests for public functions). Principle V (spec + code in same commit) is noted in tasks.md:L195 but cannot be verified from artifacts alone.

**Unmapped Tasks:** None. T001–T002 and T016–T019 map to SC-006, FR-001, FR-011, FR-012, SC-003, and SC-005.

**Metrics:**
- Total Requirements: 18 (12 FR + 6 SC)
- Total Tasks: 19
- Coverage: 100% (18/18 with at least one task)
- Ambiguity Count: 3 (A1, A2, U1)
- Duplication Count: 2 (D1, D2)
- Critical Issues: 0
- Total Findings: 11 (1 HIGH, 2 MEDIUM, 8 LOW)

## Next Actions

No CRITICAL issues; implementation may proceed. Before `/speckit.implement`, resolve the HIGH ambiguity A1 by clarifying accepted `weights` container types in `spec.md` and adding a `range` test. Then address MEDIUM findings G1 (non-unit equal-weight parity) and I2 (task independence contradiction). LOW items can be handled opportunistically.

Suggested commands:
- Run `/speckit.specify` with a refinement to clarify accepted weight container types (A1).
- Manually edit `tasks.md` to add non-unit equal-weight parity cases and reconcile story dependency wording.
- Rerun `/speckit.analyze` afterward to confirm findings are cleared.

Would you like me to suggest concrete remediation edits for the top 3 issues (A1, G1, I2)?
