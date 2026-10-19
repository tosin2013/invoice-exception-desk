---

description: "Task list for Split a bill fairly"
---

# Tasks: Split a bill fairly

**Input**: Design documents from `/specs/001-split-bill/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), `.specify/memory/constitution.md`

**Tests**: Included — the spec's SC-001 requires tests covering every acceptance scenario and plan.md explicitly specifies `tests/test_split_bill.py` with one test per scenario.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project (tiny library)**: `bill_split/`, `tests/`, `pyproject.toml` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and minimal structure

- [X] T001 [P] Create `pyproject.toml` with project name `bill-split`, version `0.1.0`, `requires-python = ">=3.11"`, and pytest config `testpaths = ["tests"]`
- [X] T002 [P] Create the `bill_split/` package directory with an empty `bill_split/__init__.py` and the `tests/` directory per plan.md scope

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared scaffolding that MUST exist before either user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Define the public signature `def split_bill(total_cents: int, people: int) -> list[int]:` as a stub (docstring + `raise NotImplementedError`) in `bill_split/__init__.py`, then confirm `python -c "import bill_split"` succeeds

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Even split with remainder (Priority: P1) 🎯 MVP

**Goal**: `split_bill` returns a list of length `people` whose shares sum exactly to `total_cents`, with the remainder cents given to the first shares.

**Independent Test**: Call `split_bill(1000, 3)` → `[334, 333, 333]`, `split_bill(900, 3)` → `[300, 300, 300]`, `split_bill(0, 2)` → `[0, 0]`.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T004 [US1] Write tests for the three even-split acceptance scenarios (`1000/3 → [334, 333, 333]`, `900/3 → [300, 300, 300]`, `0/2 → [0, 0]`) in `tests/test_split_bill.py`, run `python -m pytest -q`, and confirm they FAIL
- [X] T005 [US1] Implement the even-split logic in `bill_split/__init__.py` using `base, extra = divmod(total_cents, people)` and returning `[base + 1] * extra + [base] * (people - extra)`
- [X] T006 [US1] Run `python -m pytest -q` and confirm all User Story 1 tests PASS

**Checkpoint**: User Story 1 is fully functional and testable independently

---

## Phase 4: User Story 2 - Bad input is rejected (Priority: P1)

**Goal**: `split_bill` raises `ValueError` for `people < 1` or `total_cents < 0`, and `TypeError` for non-`int` arguments (including `bool` and `float`).

**Independent Test**: `split_bill(100, 0)` and `split_bill(-1, 2)` raise `ValueError`; `split_bill(100.0, 2)`, `split_bill(100, True)`, and `split_bill("100", 2)` raise `TypeError`.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [US2] Write tests for the invalid-input acceptance scenarios (people `0`/negative and negative total → `ValueError`; non-integer total or people including `bool` and `float` → `TypeError`) in `tests/test_split_bill.py`, run `python -m pytest -q`, and confirm they FAIL
- [X] T008 [US2] Implement validation in `bill_split/__init__.py`: first `if type(total_cents) is not int or type(people) is not int: raise TypeError(...)`, then `if people < 1 or total_cents < 0: raise ValueError(...)`, before the split logic
- [X] T009 [US2] Run `python -m pytest -q` and confirm all User Story 1 and User Story 2 tests PASS

**Checkpoint**: Both user stories work independently and together

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification affecting the whole feature

- [X] T010 [P] Run the full `python -m pytest -q` suite and confirm SC-001 coverage: every acceptance scenario in spec.md has at least one test
- [X] T011 Review `bill_split/__init__.py` and `pyproject.toml` for constitution compliance (integer cents only, pure/no I/O, standard-library only, no extra files beyond plan.md scope)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Both depend on Foundational completion
- **Polish (Phase 5)**: Depends on User Story 2 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependency on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - shares `bill_split/__init__.py` with US1, so run after US1 when working sequentially

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation before the final run-tests verification task

### Parallel Opportunities

- T001 and T002 (different files) can run in parallel
- After Foundational completes, US1 and US2 test tasks touch the same `tests/test_split_bill.py`, so serialise the file edits; the two stories can still be reasoned about independently

---

## Parallel Example: Setup

```bash
# Launch both setup tasks together:
Task: "Create pyproject.toml with project metadata in pyproject.toml"
Task: "Create bill_split/__init__.py and tests/ directory"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `python -m pytest -q` — User Story 1 works independently
5. Deliver the minimal even-split function

### Incremental Delivery

1. Setup + Foundational → structure ready
2. Add User Story 1 → test → MVP (correct even split)
3. Add User Story 2 → test → robust input rejection
4. Polish → full suite and constitution review

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps each task to a specific user story for traceability
- Every task names an exact file path so it is immediately executable
- Tests use the standard-library-only constitution: pytest tests live in `tests/`
- Do NOT modify `spec.md` or `plan.md` while executing these tasks
