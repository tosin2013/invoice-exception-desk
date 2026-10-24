---

description: "Task list for deterministic follow-up queue with owners and notes"
---

# Tasks: Deterministic follow-up queue with owners and notes

**Input**: Design documents from `/specs/004-deterministic-followup-queue/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/public-api.md, contracts/annotation-store.schema.json, quickstart.md

**Tests**: Included because `plan.md` defines a two-stage pytest test plan, `quickstart.md` requires `python -m pytest -q`, and constitution IV requires every public function to have tests.

**Organization**: The ordering stage is deliberately placed first as a self-contained block so it can be implemented and accepted by Agent B with no annotation storage, no `state/` directory, and no owners/notes work. The marked handoff line separates that block from the owners/notes, annotation storage, and polish tasks kept by Agent A.

**Hard dependency rule**: Every task above the handoff line MUST be completable using only the existing `invoice_desk.import_invoices` result and MUST NOT depend on any task below the handoff line. Tasks below the handoff line may depend on the completed ordering block.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `invoice_desk/` package, `tests/` at repository root, optional runtime `state/` directory
- Stage 1 write scope: `invoice_desk/queue.py`, `invoice_desk/__init__.py`, `tests/test_followup_queue.py`
- Stage 2 write scope: `invoice_desk/annotations.py`, `invoice_desk/__init__.py`, `tests/test_followup_annotations.py`, `.gitignore`
- Do not modify `invoice_desk.import_invoices`, `tests/test_invoice_desk.py`, `bill_split/`, `data/`, `pyproject.toml`, `ROADMAP.md`, `ACCEPTANCE.md`, or `NON_GOALS.md`

---

## Phase 1: Queue Ordering (Stage 1 - Agent B) 🎯 MVP

**Goal**: Build a pure, side-effect-free follow-up queue over the accepted invoices from `invoice_desk.import_invoices`, sorted by bucket priority, descending remaining balance, ascending invoice ID, then ascending issuer, with 1-based positions.

**Independent Test**: Import the frozen `data/invoices.csv` at `as_of = 2026-10-15`, build the queue twice, and verify the exact SC-002 sequence `INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014, INV-1004, INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011`, plus determinism, item shape, positions, exclusions, and non-mutation, without creating or importing `invoice_desk/annotations.py` or `state/`.

### Tests for Queue Ordering (write first, ensure they FAIL before implementation)

- [X] T001 [US1] Create `tests/test_followup_queue.py` with a shared helper that reads `data/invoices.csv` as UTF-8 text, a constant `AS_OF = date(2026, 10, 15)`, and a test asserting the exact SC-002 identity sequence for `build_followup_queue(import_invoices(csv_text, AS_OF))`: `INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014, INV-1004, INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011`
- [X] T002 [US1] Extend `tests/test_followup_queue.py` with determinism and sort-key tests: two calls return equal sequences and identical identity order; `BUCKET_PRIORITY` maps `91+`=0, `61-90`=1, `31-60`=2, `1-30`=3, `current`=4, `paid`=5; each bucket precedes the next; within a bucket `remaining_balance_cents` is descending; ties then use `invoice_id` ascending (case-sensitive, locale-independent), then `issuer` ascending (case-sensitive, locale-independent) as the last key; no unresolved ties
- [X] T003 [US1] Extend `tests/test_followup_queue.py` with edge-case and contract tests: two issuers reusing the same `invoice_id` remain two separate items, ordered by the final issuer tie-break; zero-balance `INV-1011` appears exactly once in `paid` with `remaining_balance_cents == 0`; an empty accepted set returns `[]`; rejected and both duplicate statuses are excluded; each item has exactly `issuer`, `invoice_id`, `remaining_balance_cents`, `days_overdue`, `aging_bucket`, `owner=None`, `notes=None`, `position`; money and day fields are `int` with `remaining_balance_cents >= 0` and `days_overdue >= 0`; `aging_bucket` is one of `91+`, `61-90`, `31-60`, `1-30`, `current`, `paid`; positions are contiguous 1-based values; `import_result` and its rows are not mutated; the module runs with no `invoice_desk/annotations.py` file and no `state/` directory present

### Implementation for Queue Ordering

- [X] T004 [US1] Create `invoice_desk/queue.py` with module constant `BUCKET_PRIORITY` exactly `{"91+": 0, "61-90": 1, "31-60": 2, "1-30": 3, "current": 4, "paid": 5}` and implement `accepted_invoice_identities(import_result) -> set[tuple[str, str]]` returning the exact `(issuer, invoice_id)` pairs of rows whose `status == "accepted"` without modifying the input
- [X] T005 [US1] Implement `build_followup_queue(import_result) -> list[dict]` in `invoice_desk/queue.py`: select only `status == "accepted"` rows, exclude every rejected and duplicate row, include every accepted invoice including zero-balance `paid`, sort by `(BUCKET_PRIORITY[aging_bucket], -remaining_balance_cents, invoice_id, issuer)`, assign contiguous 1-based `position` after sorting, and return a new list of new dicts with exactly the contract fields and Stage 1 `owner=None`, `notes=None`; perform no file I/O, read no clock, use no randomness, and import no annotation module
- [X] T006 [US1] Re-export `BUCKET_PRIORITY`, `accepted_invoice_identities`, and `build_followup_queue` from `invoice_desk/__init__.py` without changing `import_invoices` or any import classification, balance, aging bucket, or total behaviour
- [X] T007 [US1] Run `python -m pytest -q tests/test_followup_queue.py tests/test_invoice_desk.py`, confirm the ordering tests pass and the existing import tests remain green, and confirm no `invoice_desk/annotations.py` or `state/` path is required

**Checkpoint**: Stage 1 is complete and independently accepted. The queue order is pure, total, repeatable, and has no owners/notes dependency.

---

## Handoff Boundary

--- HANDOFF: Agent B (OpenAI hosted) owns the tasks above; Agent A (OpenCode) keeps the tasks below (owners/notes, annotation storage, polish) ---

---

## Phase 2: Setup (Annotation Runtime - Agent A)

**Purpose**: Prepare the runtime-state location for the versioned annotation store without creating annotation data.

- [ ] T008 [P] Add `state/` to `.gitignore` so the default annotation store at `<project root>/state/followup_annotations.json` remains local runtime state and is not committed; do not create `state/` or any annotation file in this task

---

## Phase 3: User Story 2 - Persist owners and notes (Priority: P2)

**Goal**: Let an operator assign and clear an owner and free-text notes on accepted invoice identities through explicit local library calls, persist them immediately in a versioned UTF-8 JSON store using atomic whole-file replacement, and attach them to an already ordered queue without changing order, positions, balances, days overdue, or aging buckets.

**Independent Test**: Using a temporary store path, assign an owner to one accepted identity and notes to another, rebuild the queue, reload from the same path in a fresh call, and verify each annotation is still on the same identity with unchanged content, all other items have no owner/notes, and the queue order and positions are unchanged.

### Tests for User Story 2 (write first, ensure they FAIL before implementation)

- [ ] T009 [US2] Create `tests/test_followup_annotations.py` with shared helpers using `tmp_path` and tests for the basic contract: a missing store means an empty annotation mapping and an all-`None` owner/notes queue with no file creation; `load_annotations` returns `{}` for a missing file and for a valid empty store `{"version": 1, "annotations": []}`; `set_owner` and `set_notes` change only the targeted identity; `attach_annotations` preserves queue order and positions and maps stored empty strings to `None`
- [ ] T010 [US2] Extend `tests/test_followup_annotations.py` with persistence and independence tests: annotate two different identities and confirm no cross-contamination; reload from the same path and observe identical values; multi-line and non-ASCII notes round-trip exactly; clearing the owner leaves notes intact and clearing notes leaves the owner intact; clearing both drops the record; a non-accepted identity raises `InvoiceNotAcceptedError` and leaves store bytes unchanged; an annotation for an identity absent from the current accepted set is retained in `load_annotations` but absent from the queue, then reappears when that identity is accepted again; changing annotations never changes queue sequence, positions, balances, days overdue, or aging buckets
- [ ] T011 [US2] Extend `tests/test_followup_annotations.py` with validation and atomicity tests: malformed JSON, non-object documents, missing/non-integer `version`, non-list `annotations`, non-object records, missing/extra/non-string fields, unsupported version, duplicate `(issuer, invoice_id)` pairs, and unreadable paths each raise the documented error and leave the original bytes untouched; a simulated `os.replace` failure raises `AnnotationStoreWriteError`, leaves the previous store readable, and leaves no temporary file behind; a successful write uses UTF-8 with `ensure_ascii=False`, records sorted by ascending `(issuer, invoice_id)`, and a trailing newline

### Implementation for User Story 2

- [ ] T012 [P] [US2] Create `invoice_desk/annotations.py` with `DEFAULT_ANNOTATION_STORE_PATH` computed from the package location as `<project root>/state/followup_annotations.json`, `ANNOTATION_STORE_VERSION = 1`, and the error hierarchy `AnnotationError` with `AnnotationStoreUnreadableError`, `AnnotationStoreMalformedError`, `AnnotationStoreVersionError`, `AnnotationStoreDuplicateIdentityError`, `AnnotationStoreWriteError`, and `InvoiceNotAcceptedError`; use standard library only
- [ ] T013 [US2] Implement `load_annotations(store_path=None) -> dict[tuple[str, str], dict[str, str]]` in `invoice_desk/annotations.py`: a missing file returns `{}` without creating anything; read UTF-8 JSON and validate that `version` is the integer `1`, `annotations` is a list, each record is an object with exactly the four string fields `issuer`, `invoice_id`, `owner`, `notes`, with `issuer` and `invoice_id` non-empty, and no duplicate `(issuer, invoice_id)` pairs; raise `AnnotationStoreUnreadableError`, `AnnotationStoreMalformedError`, `AnnotationStoreVersionError`, or `AnnotationStoreDuplicateIdentityError` as specified and never write during a read
- [ ] T014 [US2] Implement the private atomic store writer in `invoice_desk/annotations.py`: serialize the complete next document in memory as UTF-8 JSON with non-ASCII preserved, records sorted by ascending `(issuer, invoice_id)`, and a trailing newline; omit records whose `owner` and `notes` are both empty; create the parent directory if needed; write to a uniquely named temporary file in the same directory using `tempfile.mkstemp` and `os.fdopen(..., "w", encoding="utf-8", newline="\n")`; flush, `os.fsync`, close, then `os.replace` onto the target; best-effort `os.fsync` the parent directory on POSIX; on failure remove the temporary file, leave the previous store intact, and raise `AnnotationStoreWriteError`
- [ ] T015 [US2] Implement `set_owner(accepted_identities, issuer, invoice_id, owner, *, store_path=None) -> None` in `invoice_desk/annotations.py`: first raise `InvoiceNotAcceptedError` if `(issuer, invoice_id)` is not in `accepted_identities` without touching the store; otherwise load the existing store, set only `owner` (`None` or whitespace-only clears it), preserve `notes`, drop the record only when both fields are empty, persist atomically, and return only after `os.replace` completes
- [ ] T016 [US2] Implement `set_notes(accepted_identities, issuer, invoice_id, notes, *, store_path=None) -> None` in `invoice_desk/annotations.py`: first raise `InvoiceNotAcceptedError` if `(issuer, invoice_id)` is not in `accepted_identities` without touching the store; otherwise load the existing store, set only `notes` (`None` or `""` clears it), preserve non-empty notes exactly including newlines, punctuation, and non-ASCII text, preserve `owner`, drop the record only when both fields are empty, persist atomically, and return only after `os.replace` completes
- [ ] T017 [US2] Implement `attach_annotations(queue, store_path=None) -> list[dict]` in `invoice_desk/annotations.py`: load and validate the store once, return a new queue list with the same order and `position` values, fill `owner`/`notes` only on exact `(issuer, invoice_id)` matches, expose stored empty strings as `None`, leave unmatched items at `owner=None`/`notes=None`, ignore stored records absent from the queue without deleting them, do not mutate the input queue, and do not write during attachment
- [ ] T018 [US2] Implement `followup_queue(import_result, store_path=None) -> list[dict]` in `invoice_desk/annotations.py` as `attach_annotations(build_followup_queue(import_result), store_path)`, importing `build_followup_queue` from `invoice_desk/queue.py`; do not re-implement ordering or change any queue field other than `owner`/`notes`
- [ ] T019 [US2] Re-export `DEFAULT_ANNOTATION_STORE_PATH`, `ANNOTATION_STORE_VERSION`, `load_annotations`, `set_owner`, `set_notes`, `attach_annotations`, `followup_queue`, and all `AnnotationError` subclasses from `invoice_desk/__init__.py` without changing `import_invoices` or the Stage 1 exports
- [ ] T020 [US2] Run `python -m pytest -q tests/test_followup_annotations.py tests/test_followup_queue.py tests/test_invoice_desk.py`, confirm all annotation persistence, validation, atomicity, ordering, and existing import tests pass, and confirm `state/` is never created by reads or by the temporary-path tests

**Checkpoint**: User Stories 1 and 2 are both independently functional: ordering is pure and repeatable, and owners/notes persist atomically without affecting ordering.

---

## Phase 4: Polish & Cross-Cutting Concerns (Agent A)

**Purpose**: Verify the completed feature against the quickstart, constitution, and repository boundaries.

- [ ] T021 [P] Run the full suite with `python -m pytest -q`, confirm every test passes, and confirm `tests/test_invoice_desk.py` remains unchanged and green
- [ ] T022 [P] Run the `quickstart.md` validation checks in sections 2 through 7, including the frozen queue order, determinism, annotation persistence, missing/invalid stores, order preservation after annotation changes, and retained annotations for absent invoices, using temporary store paths only
- [ ] T023 [P] Review `invoice_desk/queue.py` and `invoice_desk/annotations.py` for integer-cents-only money handling, standard-library-only imports, no clock/randomness/network access, no annotation influence on ordering, and no changes to import classifications, balances, aging buckets, or totals
- [ ] T024 [P] Inspect `git status` and the diff to confirm only `invoice_desk/queue.py`, `invoice_desk/annotations.py`, `invoice_desk/__init__.py`, `tests/test_followup_queue.py`, `tests/test_followup_annotations.py`, and `.gitignore` changed, and that no `state/` file is committed or tracked

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 - Queue Ordering (T001-T007)**: No dependency on any unfinished work; it uses only the existing `invoice_desk.import_invoices`. It MUST complete before the handoff checkpoint.
- **Handoff line**: A boundary, not an executable task. Agent B owns Phase 1; Agent A owns Phase 2 onward.
- **Phase 2 - Annotation Setup (T008)**: Independent of Phase 1 and may run at any time; it does not affect ordering.
- **Phase 3 - User Story 2 (T009-T020)**: Depends on T008 for the gitignored runtime location and on the annotation module tasks. T018 additionally depends on the completed T005 (`build_followup_queue`). It MUST NOT be a dependency of any Phase 1 task.
- **Phase 4 - Polish (T021-T024)**: Depends on all Phase 3 implementation tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Can start immediately after reading the existing import result; no dependency on User Story 2, annotations, or `state/`.
- **User Story 2 (P2)**: Storage, assignment, and attachment are independently testable after its own module exists; only the convenience `followup_queue` composition uses the finished User Story 1 queue builder.
- Ordering MUST NOT depend on owner/notes persistence, annotation storage, or any polish task.

### Within Each User Story

- Tests are written first and MUST fail before implementation.
- For User Story 1: tests, then `BUCKET_PRIORITY`/identity helper, then `build_followup_queue`, then re-exports, then verification.
- For User Story 2: tests, then module constants/errors, then load validation, then atomic writer, then `set_owner`/`set_notes`, then `attach_annotations`, then `followup_queue`, then re-exports, then verification.
- Models and pure helpers precede stateful operations; loading precedes writing; writing precedes attachment and composition.

### Parallel Opportunities

- T008 (`.gitignore`) can run in parallel with annotation test authoring because they touch different files.
- T012 (`invoice_desk/annotations.py` skeleton) can run in parallel with T009-T011 test authoring because they touch different files.
- T021-T024 (full-suite run, quickstart validation, code review, and repository-boundary inspection) can run in parallel after implementation because they are read-only verification tasks.
- Phase 1 is intentionally sequential within one module and one test file so the ordering block stays self-contained and reviewable as a unit.

---

## Parallel Example: User Story 2

```bash
# After T008, test authoring and the annotation module skeleton touch different files:
Task: "T009-T011 author tests in tests/test_followup_annotations.py"
Task: "T012 create constants and error hierarchy in invoice_desk/annotations.py"
```

```bash
# After T020, read-only polish checks can run together:
Task: "T021 run python -m pytest -q"
Task: "T022 run quickstart.md sections 2-7 with temporary stores"
Task: "T023 review for integer cents, stdlib-only, no clock/random/network"
Task: "T024 inspect git status and diff boundaries"
```

---

## Implementation Strategy

### MVP First (Stage 1 / User Story 1 Only)

1. Complete T001-T003: write the ordering tests and confirm they fail.
2. Complete T004-T006: implement and re-export the pure ordering API.
3. Complete T007: verify ordering and existing import tests.
4. **STOP at the handoff line and validate**: Agent B delivers only pure ordering, with no annotation module, no `state/`, and no owners/notes dependency.

### Incremental Delivery

1. Stage 1 ordering lands and is accepted independently (Agent B).
2. Agent A adds the gitignored runtime location (T008).
3. Agent A adds annotation tests, then storage, assignment, attachment, and composition (T009-T020).
4. Agent A runs quickstart and polish verification (T021-T024).
5. Each stage adds value without changing the import behaviour or the Stage 1 queue order.

---

## Notes

- [P] tasks touch different files and have no dependency on incomplete tasks.
- [US1] marks the ordering block above the handoff; [US2] marks owners/notes and annotation storage below it.
- Every task above the handoff MUST remain implementable with `invoice_desk/annotations.py` absent and `state/` absent.
- Verify tests fail before implementing; commit after each logical group only when explicitly requested.
- Do not implement anything as part of task generation; this document is the plan only.
