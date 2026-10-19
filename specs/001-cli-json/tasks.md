---
description: "Task list for `--json` output for the slugify CLI"
---

# Tasks: `--json` output for the slugify CLI

**Input**: Design documents from `/specs/001-cli-json/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests ARE requested (spec SC-002 requires new tests covering FR-001 to FR-005). Test tasks are included below.

**Organization**: Tasks are grouped by user story. Both user stories are Priority P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `slugify/__main__.py` (the ONLY source file in scope)
- **Tests**: `tests/test_cli_json.py` (the ONLY new test file; do NOT edit existing test files)
- **Out of scope**: README/CHANGELOG edits, any other file, `slugify/_legacy.py`, `tests/test_legacy.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the pre-change baseline before touching code.

- [x] T001 From the repo root, run `python -m pytest -q` and confirm the existing suite is green (including `tests/test_legacy.py`, `tests/test_release.py`, `tests/test_cli_interrupt.py`); record the result as the pre-change baseline.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared CLI surface required by both user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 In `slugify/__main__.py`, add the `--json` argument in `parse_args`: `parser.add_argument('--json', action='store_true', default=argparse.SUPPRESS, help='Print {"input": ..., "slug": ...} as JSON')`. Do NOT add `json` to `slugify_params()` and do NOT add it to the key list iterated there (constitution III: parsed Namespace and `slugify_params()` output keep their current shape unless the user passes `--json`).

**Checkpoint**: Flag declared and suppressed by default; user stories can now proceed.

---

## Phase 3: User Story 1 - Machine-readable output (Priority: P1) 🎯 MVP

**Goal**: A script calling `slugify --json Hello World` gets one line of parseable JSON containing the original text and the slug.

**Independent Test**: Run `slugify --json Hello World` and assert stdout is exactly `{"input": "Hello World", "slug": "hello-world"}\n` with exit code 0; verify options and stdin variants produce correct `slug`/`input`.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.** All tasks below edit the same file, `tests/test_cli_json.py`, so they must be performed sequentially (not [P]).

- [x] T003 [US1] In `tests/test_cli_json.py`, add a test calling `main(['slugify', '--json', 'Hello', 'World'])` with `capsys` asserting stdout is exactly `{"input": "Hello World", "slug": "hello-world"}` followed by a newline (FR-001, FR-002; spec US1 acceptance scenario 1).
- [x] T004 [US1] In `tests/test_cli_json.py`, add a test that `--json` combined with other options (e.g. `--separator _`) makes the `slug` field reflect those options while `input` stays the original text (FR-003; spec US1 acceptance scenario 2).
- [x] T005 [US1] In `tests/test_cli_json.py`, add a test for `--json --stdin` where `input` equals the exact stdin text including any trailing newline and `slug` is its slug (FR-002; spec US1 acceptance scenario 3).
- [x] T006 [US1] In `tests/test_cli_json.py`, add a test that `slugify --json` with empty input prints `{"input": "", "slug": ""}` (spec Edge Cases).
- [x] T007 [US1] In `tests/test_cli_json.py`, add a test that non-ASCII input is escaped with default `json.dumps` (`ensure_ascii=True`), e.g. `Café` yields the `input`/`slug` fields containing `Caf\u00e9` (spec Edge Cases; FR-002 default escaping).

### Implementation for User Story 1

- [x] T008 [US1] In `slugify/__main__.py`, add `import json` at the top and, in `main()` inside the existing `try`, compute `result = slugify(**params)`; if `getattr(args, 'json', False)` print `json.dumps({'input': params['text'], 'slug': result})`, otherwise `print(result)`. Key order MUST be `input` then `slug`; use default `json.dumps` separators/escaping; keep the `KeyboardInterrupt` handling unchanged (FR-002, FR-003).

**Checkpoint**: User Story 1 is fully functional and testable independently — this is the MVP.

---

## Phase 4: User Story 2 - Nothing changes without the flag (Priority: P1)

**Goal**: Any command without `--json` produces output and argument shape identical to before this feature.

**Independent Test**: Run commands without `--json` and confirm stdout matches the pre-feature baseline exactly, and that the parsed Namespace/`slugify_params()` contain no new keys.

### Tests for User Story 2 (REQUIRED) ⚠️

> All tasks below edit the same file, `tests/test_cli_json.py`, so they must be performed sequentially (not [P]).

- [x] T009 [US2] In `tests/test_cli_json.py`, add a test that without `--json` output is unchanged (e.g. `main(['slugify', 'Hello', 'World'])` prints `hello-world\n`) (FR-004; spec US2 acceptance scenario 1).
- [x] T010 [US2] In `tests/test_cli_json.py`, add a test that `parse_args(['slugify'])` / `parse_args(['slugify', 'Hello'])` produce no `json` key in the Namespace `vars()` and `slugify_params()` matches the legacy default shape exactly (FR-005; constitution III).

### Implementation for User Story 2

- [x] T011 [US2] Verify no further source change is required for US2: the `default=argparse.SUPPRESS` declaration from T002 ensures the flag is absent unless passed, and the non-`--json` branch of T008 preserves the existing `print(result)` behaviour. If T009/T010 fail, fix only `slugify/__main__.py` without altering legacy output.

**Checkpoint**: User Stories 1 AND 2 both work; output is byte-for-byte unchanged without the flag.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validate the whole change against the constitution and the full suite.

- [x] T012 [P] Run the full suite `python -m pytest -q` and confirm all existing tests pass unchanged plus the new `tests/test_cli_json.py` tests pass (SC-001, SC-002).
- [x] T013 [P] Run typing/style checks `mypy` and `flake8 --ignore=E501,F403,F401,E241,E225,E128 --exclude=legacy_reference.py slugify setup.py tests tools` (and `pycodestyle` per tox.ini) against the changed files; resolve any issues in `slugify/__main__.py` or `tests/test_cli_json.py`.
- [x] T014 [P] Run `git diff --name-only` and confirm `slugify/_legacy.py` and `tests/test_legacy.py` are untouched and no file outside `slugify/__main__.py` and `tests/test_cli_json.py` was modified (constitution I; FR-006).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS both user stories.
- **User Stories (Phase 3 & 4)**: Both depend on Foundational (Phase 2). US2's argument-shape test (T010) also depends on T002.
- **Polish (Phase 5)**: Depends on both user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No dependency on US2.
- **User Story 2 (P1)**: Can start after Foundational (Phase 2). Depends on the T008 implementation to prove the non-flag branch is unchanged in the real `main()`.

### Within Each User Story

- Tests MUST be written and FAIL before implementation.
- T008 (implementation) follows the failing US1 tests T003–T007.
- T011 (US2 verification) follows T009–T010.

### Parallel Opportunities

- T012, T013, T014 are `[P]` (independent commands over the same tree; no shared file writes).
- T001 baseline can run while T002 is prepared, but T002 should not be validated until baseline is recorded.
- Within Phases 3 and 4, test tasks share `tests/test_cli_json.py` and therefore cannot run in parallel. T003–T007 could in principle be authored alongside T002's flag declaration (different files: tests vs source), but they must fail until T008 lands.

---

## Parallel Example: Polish

```bash
# Launch independent validation commands together:
Task: "Run full suite: python -m pytest -q"
Task: "Run mypy and flake8/pycodestyle on slugify and tests"
Task: "Run git diff --name-only to confirm only the two in-scope files changed"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (record baseline).
2. Complete Phase 2: Foundational (declare suppressed `--json` flag).
3. Complete Phase 3: User Story 1 (tests then implementation).
4. **STOP and VALIDATE**: `slugify --json Hello World` prints exactly `{"input": "Hello World", "slug": "hello-world"}`.
5. This increment is the MVP.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → validate JSON output independently → deliver MVP.
3. US2 → validate no-flag output and argument shape unchanged → deliver.
4. Polish → full-suite, typing/style, and legacy-frozen checks.

---

## Notes

- [P] tasks = different files or independent read-only validation; no dependencies.
- Do NOT edit `spec.md`, `plan.md`, `slugify/_legacy.py`, or `tests/test_legacy.py`.
- Keep legacy and modern test coverage separate; new tests go only in `tests/test_cli_json.py`.
- `pytest` runs with `filterwarnings = error`, so new tests must not emit warnings.
- Verify tests fail before implementing T008.
