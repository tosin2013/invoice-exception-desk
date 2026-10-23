# Phase 0 Research: Deterministic follow-up queue with owners and notes

**Feature**: `004-deterministic-followup-queue`
**Date**: 2026-10-23
**Inputs**: [spec.md](./spec.md), `.specify/memory/constitution.md`, `ACCEPTANCE.md` AT-05,
existing `invoice_desk.import_invoices`, `data/invoices.csv`

No `NEEDS CLARIFICATION` markers remain in the specification. The clarifications already
resolved ordering precedence, accepted-set membership, storage, error handling, and the
assignment API. This document records the resulting technical decisions.

## 1. Queue input and ordering

- **Decision**: Build the queue only from rows in the `import_invoices` result whose
  `status == "accepted"`, keyed by the exact `(issuer, invoice_id)` pair. Sort by bucket
  priority `91+`, `61-90`, `31-60`, `1-30`, `current`, `paid`; then
  `remaining_balance_cents` descending; then `invoice_id` ascending; then `issuer`
  ascending (last key; corrected by Tosin, Oct 23). Assign 1-based contiguous positions after sorting.
- **Rationale**: This is a total order for accepted invoices. Issuer as the final key, after
  invoice ID, is required because invoice identifiers are only unique within an issuer
  (FR-005/FR-006). It matches the requested bucket-first ordering while preserving AT-05's
  binding requirement that ordering be a repeatable pure function of row data. The computed
  order for the frozen fixture at `as_of = 2026-10-15` is exactly the SC-002 sequence.
- **Alternatives considered**:
  - Sort by `days_overdue` descending only (AT-05's illustrative example): rejected because
    the user request and spec FR-005 require bucket first, and it would not guarantee the
    same relative order as bucket boundaries.
  - Sort by row number or insertion order: rejected because it is not a function of row
    data and would change with CSV order.
  - Issuer as the third key (the first draft): replaced by Tosin's decision (Oct 23) to keep the
    requested bucket, balance, invoice ID order, with issuer last to break remaining ties.
  - Invoice ID with no issuer key: rejected because two issuers may reuse `INV-*` IDs,
    leaving ties unresolved.

## 2. Separating ordering from annotations

- **Decision**: `invoice_desk/queue.py` contains only pure ordering helpers and returns
  queue items whose `owner` and `notes` are `None`. `invoice_desk/annotations.py` contains
  all storage and attachment logic. The convenience `followup_queue` composition lives in
  the annotations module, not in `queue.py`.
- **Rationale**: The user requires ordering to be buildable first by a different agent.
  A pure module with no filesystem or annotation imports can be implemented, tested, and
  accepted independently. Stage 2 then fills existing item fields without changing the
  sort keys, item shape, or positions.
- **Alternatives considered**:
  - One module containing both ordering and persistence: rejected because it couples a pure
    computation to local I/O and blocks the independent Stage 1 handoff.
  - Passing annotations into `build_followup_queue`: rejected because ordering must not
    depend on owner/notes (FR-007, FR-013).

## 3. Annotation store shape, keying, and path

- **Decision**: Use one versioned UTF-8 JSON document:
  `{"version": 1, "annotations": [{"issuer", "invoice_id", "owner", "notes"}, ...]}`.
  Key records in memory by the exact tuple `(issuer, invoice_id)` and emit them sorted by
  that tuple. Default path is `state/followup_annotations.json` under the project root,
  computed from the package location; callers may supply any path.
- **Rationale**: JSON is standard-library-only, local, and human-inspectable. Explicit
  `issuer` and `invoice_id` fields avoid the delimiter-collision problem of concatenated
  keys, and a list allows the loader to detect duplicate identities. A sorted list keeps
  writes deterministic without adding timestamps. The default is project-root-relative
  rather than current-working-directory-relative so it does not move when commands are run
  from another directory.
- **Alternatives considered**:
  - A single JSON object keyed by `"issuer|invoice_id"`: rejected because delimiter strings
    can collide and the clarification explicitly excludes concatenated keys.
  - Nested objects keyed by issuer then invoice ID: workable, but a flat record list more
    directly satisfies the requirement that each record carries all four fields and makes
    duplicate detection explicit.
  - SQLite or another store: rejected by the stdlib/offline/small-scope constraints.
  - Writing into the repository root directly: rejected because runtime state is not a
    fixture and should be isolated under `state/` and gitignored.

## 4. Durable atomic writes with the standard library

- **Decision**: Serialize the complete next store in memory, create the parent directory,
  write to a `tempfile.mkstemp` file in the same directory, flush and `os.fsync` it, close
  it, then `os.replace` it onto the target. Attempt to fsync the parent directory on POSIX.
  Remove the temporary file on failure and raise a clear write error. A successful
  assignment returns only after the replacement completes.
- **Rationale**: `os.replace` is atomic on the same filesystem, so a reader sees either the
  previous complete file or the new complete file, never a partial JSON document
  (FR-023, SC-013). Writing the temporary file beside the target keeps the replacement on
  one filesystem. No clock or random content is written; the temporary name is the only
  nondeterministic detail and is never part of the store contract.
- **Alternatives considered**:
  - Rewriting the target in place: rejected because an interrupted write can leave
    unloadable partial JSON.
  - A separate lock/transaction protocol: rejected as unnecessary for a documented
    single-writer local store; concurrent processes are out of scope.
  - `pickle` or a custom format: rejected because JSON is inspectable and safer for local
    state, and the clarification requires JSON.

## 5. Store errors and assignment refusal

- **Decision**: Missing file means an empty annotation set. Unreadable, malformed,
  duplicate-identity, or unsupported-version stores raise distinct errors and are never
  overwritten or silently reset. Assignment first validates that the identity is in the
  current accepted set and raises an error otherwise. All failures leave existing bytes
  unchanged.
- **Rationale**: Directly implements FR-016, FR-024, FR-025, and the spec's edge cases.
  Distinct error types make the failure mode clear to the operator and testable. Validating
  the accepted identity before loading prevents a rejected or duplicate row from ever
  becoming annotatable and makes the refusal independent of store contents.
- **Alternatives considered**:
  - Treat any unreadable/corrupt store as empty: rejected because it would silently lose
    annotations, explicitly forbidden by FR-024.
  - Auto-repair or overwrite a corrupt store: rejected because it destroys evidence and
    violates the "never silently reset" requirement.
  - Allow annotations for any identity present in the CSV: rejected because rejected and
    duplicate rows must never become annotatable.

## 6. Owner/notes semantics

- **Decision**: Owner and notes are independent free-text fields. Empty or whitespace-only
  owner clears the owner; `None` or empty notes clears notes. Non-empty text is preserved
  exactly, including whitespace, punctuation, newlines, and non-ASCII characters. A record
  with both fields empty is omitted. Queue items expose absent values as `None`; the JSON
  store uses empty strings.
- **Rationale**: Satisfies FR-009 to FR-012 and the edge cases for clearing, multi-line
  notes, and non-ASCII text. Keeping the two fields independent prevents clearing one from
  resetting the other. The `None` queue representation follows the existing import style
  for non-applicable values, while empty JSON strings keep every stored record to the
  required four string fields.
- **Alternatives considered**:
  - A unified "annotation blob": rejected because owner and notes must be independently
    assignable and clearable.
  - Trimming stored notes: rejected because notes must be stored exactly as entered.
  - Dropping the record whenever either field is empty: rejected because it would lose the
    other field.

## 7. Test strategy

- **Decision**: Split tests into `tests/test_followup_queue.py` (Stage 1) and
  `tests/test_followup_annotations.py` (Stage 2). Keep `tests/test_invoice_desk.py`
  unchanged. Use pytest, `tmp_path` for stores, and monkeypatching for simulated write
  failure. Run `python -m pytest -q`.
- **Rationale**: Mirrors the implementation split so ordering can be verified before
  storage exists. The existing suite guards FR-021 and AT-01 to AT-04. `tmp_path` keeps
  tests off the real `state/` path, and byte snapshots before/after error cases prove the
  store is untouched.
- **Alternatives considered**:
  - One combined test module: rejected because it would make Stage 1 depend on Stage 2
    files and undermine the handoff.
  - Testing only through the convenience `followup_queue`: rejected because the pure
    ordering contract and the storage contract need independent, focused coverage.

## Resolved unknowns

| Unknown | Resolution |
|---------|------------|
| Ordering keys and total order | Bucket priority, descending balance, ascending invoice ID, ascending issuer |
| Whether paid invoices appear | Yes; every accepted invoice appears, `paid` last |
| Store format and version | Versioned UTF-8 JSON, `version: 1`, record list keyed by `(issuer, invoice_id)` |
| Store path | Caller-supplied, default project-root `state/followup_annotations.json` |
| Missing/corrupt store behavior | Missing = empty; corrupt/unsupported/duplicate = clear error, untouched file |
| Atomicity | Same-directory temp file, fsync, `os.replace`, cleanup on failure |
| Owner/notes API | Explicit `set_owner` / `set_notes` calls with accepted identities and store path |
| How ordering and annotations stay separable | Pure `queue.py`; all storage and attachment in `annotations.py` |
