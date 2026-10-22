---

description: "Task list for weighted bill split"
---

# Tasks: Weighted bill split

**Input**: Design documents from `/specs/002-weighted-split/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), `.specify/memory/constitution.md`

**Tests**: Required. The spec's success criteria SC-003, SC-005, and SC-006 require automated tests for every acceptance scenario and invalid-input category, and constitution principle IV requires tests for every public function. The plan explicitly calls for `tests/test_split_weighted.py`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. All three user stories are priority P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `bill_split/` and `tests/` at repository root.
- Only `bill_split/__init__.py` and `tests/test_split_weighted.py` may be added/modified. Do not change `split_bill`, `tests/test_split_bill.py`, or `pyproject.toml`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a clean baseline before adding the new function.

- [X] T001 Run `python -m pytest -q` from the repository root and confirm the existing `split_bill` tests in `tests/test_split_bill.py` pass before any changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared public entry point that every user story builds on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add the public `split_weighted(total_cents: int, weights: list[int] | tuple[int, ...]) -> list[int]` function stub with its docstring in `bill_split/__init__.py`, leaving the existing `split_bill` function untouched.

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Split in proportion to what each person ordered (Priority: P1) 🎯 MVP

**Goal**: Return one non-negative integer share per weight, proportional to that weight, with all shares summing exactly to `total_cents`.

**Independent Test**: Split a total using two or more different weights and verify each share is proportional to its weight and the shares sum exactly to the total.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**

- [X] T003 [US1] Add acceptance tests for `1000, [2, 1] -> [667, 333]`, `1000, [1, 1] -> [500, 500]`, `100, [3, 1] -> [75, 25]`, and `0, [1, 2] -> [0, 0]` in `tests/test_split_weighted.py`.
- [X] T004 [US1] Add edge-case tests for a zero weight producing a zero-cent share, a single positive weight receiving the entire total, and very large totals/weights returning exact integers in `tests/test_split_weighted.py`.

### Implementation for User Story 1

- [X] T005 [US1] Implement the proportional allocation in `split_weighted` in `bill_split/__init__.py`: compute `wsum = sum(weights)`, then for each index `i` compute `base_i, rem_i = divmod(total_cents * weights[i], wsum)`, assign the leftover cents to the indices with the largest remainders (ties to the lower index) using `sorted(range(n), key=lambda i: (-rem[i], i))[:leftover]`, and return shares in weight order.
- [X] T006 [US1] Verify each returned share is a non-negative integer, the result length equals `len(weights)`, and the shares sum exactly to `total_cents`; run the User Story 1 tests and fix the implementation in `bill_split/__init__.py` until they pass.

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Fair rounding when proportions are not whole cents (Priority: P1)

**Goal**: Round every fractional share while keeping each share within one cent of its exact proportional amount and assigning the full total.

**Independent Test**: Use totals and weights that produce fractional shares, verify each share is within one cent of its exact proportional value, and verify the sum equals the total.

### Tests for User Story 2 ⚠️

- [X] T007 [US2] Add acceptance tests for `1000, [1, 1, 1] -> [334, 333, 333]` and `100, [1, 1, 1] -> [34, 33, 33]`, plus sum-exact and within-one-cent checks over a table of fractional total/weight combinations, in `tests/test_split_weighted.py`.
- [X] T008 [US2] Add tie-breaking tests proving leftover cents go to the largest fractional remainders and that ties favour the earlier weight index in `tests/test_split_weighted.py`.

### Implementation for User Story 2

- [X] T009 [US2] Harden the largest-remainder allocation in `split_weighted` in `bill_split/__init__.py` so it satisfies the within-one-cent guarantee (FR-005) and deterministic tie-break rule (FR-006) using integer arithmetic only, with no `round` and no floats.
- [X] T010 [US2] Add equal-weight parity tests comparing `split_weighted(total, [1] * n)` with `split_bill(total, n)` for several totals in `tests/test_split_weighted.py`, then run the User Story 2 tests and fix `bill_split/__init__.py` until they pass.

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Invalid input is rejected (Priority: P1)

**Goal**: Reject invalid totals and weights with the documented error type before returning any shares.

**Independent Test**: Call the split with each invalid input category and verify the documented error type is raised.

### Tests for User Story 3 ⚠️

- [X] T011 [US3] Add `TypeError` tests for a non-integer total, a float weight, `bool` total and `bool` weights, a generator, a string, `None`, and other non-sequence weight containers in `tests/test_split_weighted.py`.
- [X] T012 [US3] Add `TypeError` precedence tests for inputs that are both wrong type and out of range, such as `total_cents = -1.5`, and add `ValueError` tests for a negative total, empty weights, all-zero weights, and any negative weight in `tests/test_split_weighted.py`.

### Implementation for User Story 3

- [X] T013 [US3] Implement type validation first in `split_weighted` in `bill_split/__init__.py`: raise `TypeError` when `type(total_cents) is not int`, when `not isinstance(weights, (list, tuple))`, or when any `type(w) is not int`; this must reject `bool`, `float`, generators, strings, and `None`.
- [X] T014 [US3] Implement value validation after all type checks in `split_weighted` in `bill_split/__init__.py`: raise `ValueError` when `total_cents < 0`, `len(weights) == 0`, any `w < 0`, or `sum(weights) == 0`.
- [X] T015 [US3] Run the User Story 3 tests and the full suite, and fix `bill_split/__init__.py` until all validation tests pass.

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the completed feature against the spec, plan, and constitution.

- [X] T016 [P] Run `python -m pytest -q` from the repository root and confirm all existing tests in `tests/test_split_bill.py` and new tests in `tests/test_split_weighted.py` pass (SC-006).
- [X] T017 [P] Review `git diff` to confirm `split_bill`, `tests/test_split_bill.py`, and `pyproject.toml` are unchanged and that only `bill_split/__init__.py` and `tests/test_split_weighted.py` changed.
- [X] T018 [P] Audit `bill_split/__init__.py` for integer-only arithmetic, deterministic pure behavior, stdlib-only implementation, and no I/O, randomness, or clock access (FR-011, constitution I-III).
- [X] T019 Review the acceptance scenarios and invalid-input categories in `specs/002-weighted-split/spec.md` against `tests/test_split_weighted.py` and add any missing coverage (SC-003, SC-005).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion.
  - US1 must complete before US2 because US2 verifies and hardens US1's rounding behavior.
  - US3 can begin after Foundational, but its edits to `bill_split/__init__.py` must be merged after US1/US2 to avoid file conflicts.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependencies on other stories.
- **User Story 2 (P1)**: Depends on User Story 1's proportional allocation and leftover distribution.
- **User Story 3 (P1)**: Depends on Foundational for the function entry point; final integration depends on US1/US2 because all edits touch the same file.

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Type validation MUST run before value validation (FR-010).
- Core allocation MUST be complete before the rounding hardening and equal-weight parity checks.
- Story complete before moving to the next priority.

### Parallel Opportunities

- T016, T017, and T018 are read-only verification tasks and can run in parallel.
- US1, US2, and US3 cannot be safely parallelized because nearly every task edits the same two files (`bill_split/__init__.py` and `tests/test_split_weighted.py`).

---

## Parallel Example: Polish Verification

```bash
# Run these independent verification tasks together:
Task: "Run python -m pytest -q and confirm all tests pass"
Task: "Review git diff for unintended changes to split_bill, its tests, and pyproject.toml"
Task: "Audit bill_split/__init__.py for integer-only, pure, stdlib-only implementation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Test User Story 1 independently with the documented acceptance scenarios.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready.
2. Add User Story 1 -> Test independently -> Deploy/demo (MVP).
3. Add User Story 2 -> Test independently -> Deploy/demo.
4. Add User Story 3 -> Test independently -> Deploy/demo.
5. Complete the Polish phase and run the full suite.

### Parallel Team Strategy

Because all implementation touches the same function and test file, prefer one developer working sequentially in priority order. Run only the read-only Polish checks in parallel.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps each task to its user story for traceability.
- Each user story is independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group, keeping the spec and code changes together per constitution principle V.
- Avoid vague tasks, same-file conflicts, and cross-story dependencies that break independence.
