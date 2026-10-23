# Implementation Plan: Deterministic follow-up queue with owners and notes

**Branch**: `004-deterministic-followup-queue` | **Date**: 2026-10-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-deterministic-followup-queue/spec.md`

## Summary

Extend the existing pure `invoice_desk.import_invoices` capability with a follow-up queue
and a small owner/notes persistence layer. The work is deliberately split into two
independently landable stages:

1. **Queue ordering** — a pure, side-effect-free projection of an `import_invoices` result
   into a totally ordered list. It has no annotation imports and no filesystem access, so a
   different agent can build and verify it first.
2. **Annotations** — a versioned UTF-8 JSON store at a caller-supplied path
   (default `state/followup_annotations.json` under the project root) with explicit
   owner/notes assignment calls, atomic whole-file replacement, and a separate function that
   attaches stored annotations to an already ordered queue.

Queue ordering remains a pure function of imported row data. Annotations never influence
ordering, position, balances, days overdue, or aging. Money stays in integer cents, the
implementation uses only the Python standard library, and tests use pytest.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: none; standard library only (`json`, `os`, `tempfile`, `pathlib`,
`datetime` already used by the import layer)

**Storage**: one versioned UTF-8 JSON annotation file at a caller-supplied path; default
`state/followup_annotations.json` under the project root. Local single-writer runtime state,
not an import fixture and not a source of invoice truth.

**Testing**: pytest, run with `python -m pytest -q`; existing import tests must remain green

**Target Platform**: local, offline Python 3.11+ (Linux/macOS/Windows); no network calls

**Project Type**: library (`invoice_desk` package)

**Performance Goals**: queue build is `O(n log n)` over accepted invoices; annotation load and
save are linear in the number of stored records. The frozen fixture has 14 accepted invoices.

**Constraints**: integer cents only; ordering is deterministic and independent of insertion
order, owner, notes, or storage order; no clock, randomness, network, credentials, or real
personal data; import classification, balances, aging, and totals remain unchanged

**Scale/Scope**: one operator, one CSV import at a time, small local annotation store
(tens to thousands of records); concurrent writers are explicitly out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.1.0:

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Money is integer cents | PASS | Queue exposes `remaining_balance_cents` copied from the import result; no float arithmetic is introduced. |
| II. Deterministic and pure | PASS with isolated persistence boundary | Queue ordering is pure and uses only row data. The spec-mandated annotation store is the only I/O boundary; it uses no clock, randomness, or network, and is confined to `invoice_desk/annotations.py`. See Complexity Tracking. |
| III. Standard library only | PASS | JSON persistence and atomic replacement use `json`, `os`, `tempfile`, and `pathlib`. |
| IV. Small and tested | PASS | Two small modules and two focused pytest modules; every public function gets tests. |
| V. Spec and code together | PASS | Implementation lands with this plan/tasks/spec on the feature branch; no behaviour change without its spec change. |
| VI. Synthetic data, offline only | PASS | All fixtures remain synthetic; no network, secrets, or real personal data. |
| VII. Explicit as-of date | PASS | Ordering reuses the already-computed `days_overdue`/`aging_bucket` from the explicit `as_of`; annotations never read the clock. |
| VIII. Sealed answer key per phase | PASS | The plan derives only from the spec, `ACCEPTANCE.md`, and the public repository; it does not assume access to the oracle. |

No unresolved clarifications remain. The one constitution tension (local file I/O required by
AT-05) is justified in Complexity Tracking rather than silently waived.

## Project Structure

### Documentation (this feature)

```text
specs/004-deterministic-followup-queue/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── public-api.md
│   └── annotation-store.schema.json
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
invoice_desk/
├── __init__.py          # Existing import_invoices; add re-exports only, do not refactor it
├── queue.py             # NEW, Stage 1: pure ordering and identity helpers
└── annotations.py       # NEW, Stage 2: JSON store, assignment, queue attachment

tests/
├── test_invoice_desk.py         # Existing; must remain unchanged and green
├── test_followup_queue.py       # NEW, Stage 1: ordering only
└── test_followup_annotations.py # NEW, Stage 2: persistence and attachment

state/                   # Runtime default location, created on first write; gitignored
```

**Structure Decision**: Keep the existing import implementation in `invoice_desk/__init__.py`
untouched to honour FR-021. Add a pure `queue.py` first and a stateful `annotations.py`
second. `__init__.py` only re-exports public names. Splitting the test modules along the same
stage boundary lets ordering be implemented and accepted before annotation storage exists.

## Public Interface

```python
from datetime import date
from os import PathLike
from pathlib import Path
from typing import Iterable

# Existing, unchanged
def import_invoices(csv_text: str, as_of: date) -> dict: ...

# Stage 1: pure ordering, no filesystem or annotation dependency
BUCKET_PRIORITY: dict[str, int]

def accepted_invoice_identities(import_result: dict) -> set[tuple[str, str]]: ...
def build_followup_queue(import_result: dict) -> list[dict]: ...

# Stage 2: persistence and attachment
DEFAULT_ANNOTATION_STORE_PATH: Path
ANNOTATION_STORE_VERSION: int

def load_annotations(
    store_path: str | PathLike[str] | None = None,
) -> dict[tuple[str, str], dict[str, str]]: ...

def set_owner(
    accepted_identities: Iterable[tuple[str, str]],
    issuer: str,
    invoice_id: str,
    owner: str | None,
    *,
    store_path: str | PathLike[str] | None = None,
) -> None: ...

def set_notes(
    accepted_identities: Iterable[tuple[str, str]],
    issuer: str,
    invoice_id: str,
    notes: str | None,
    *,
    store_path: str | PathLike[str] | None = None,
) -> None: ...

def attach_annotations(
    queue: list[dict],
    store_path: str | PathLike[str] | None = None,
) -> list[dict]: ...

def followup_queue(
    import_result: dict,
    store_path: str | PathLike[str] | None = None,
) -> list[dict]: ...
```

`followup_queue` is the convenience composition `attach_annotations(build_followup_queue(...))`.
It lives in `annotations.py`, never in `queue.py`, so Stage 1 has no dependency on storage.

### Queue item contract

`build_followup_queue` returns one new dict per accepted import row, in priority order:

```text
issuer                  str
invoice_id              str
remaining_balance_cents int
days_overdue            int
aging_bucket            str
owner                   None        # Stage 1 value; Stage 2 may fill a str
notes                   None        # Stage 1 value; Stage 2 may fill a str
position                int         # 1-based, contiguous after sorting
```

Rejected and duplicate rows are excluded. Non-accepted rows never become queue items.
`build_followup_queue` does not mutate `import_result` or any row inside it.

## Design

### Queue ordering (separable; build first)

**Stage 1 files**: `invoice_desk/queue.py`, `tests/test_followup_queue.py`, and a re-export in
`invoice_desk/__init__.py`.

1. Derive the accepted set with `status == "accepted"` and key each item by the exact tuple
   `(issuer, invoice_id)`.
2. Sort with the total-order key:
   1. `BUCKET_PRIORITY[aging_bucket]` — `91+`=0, `61-90`=1, `31-60`=2, `1-30`=3,
      `current`=4, `paid`=5;
   2. `-remaining_balance_cents` — descending integer cents;
   3. `invoice_id` — ascending, case-sensitive, locale-independent Unicode text order;
   4. `issuer` — ascending, case-sensitive, locale-independent Unicode text order (last key; corrected by Tosin, Oct 23).
3. Assign `position` only after sorting, starting at `1`.
4. Return a fresh list of fresh dicts with the queue item fields above. Do not read files,
   import `annotations`, accept an annotation argument, or consult the clock.
5. For the frozen accepted set at `as_of = 2026-10-15`, the result must be exactly:
   `INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014, INV-1004,`
   `INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011`.
6. An empty accepted set returns `[]`. `paid` remains in the queue at the lowest priority.

**Handoff guarantee**: Stage 1 can land, be reviewed, and pass all ordering tests with no
`annotations.py`, no `state/` directory, and no persistence behaviour. Stage 2 must not change
the queue item shape, sort keys, or positions.

### Annotation storage (decision from Clarifications)

**Stage 2 files**: `invoice_desk/annotations.py`, `tests/test_followup_annotations.py`, and
re-exports in `invoice_desk/__init__.py`.

**Store format (version 1)** — a single UTF-8 JSON document with this shape:

```json
{
  "version": 1,
  "annotations": [
    {
      "issuer": "Acme Cleaning Co",
      "invoice_id": "INV-1001",
      "owner": "Dana",
      "notes": "Call Tuesday.\nAsk for AP."
    }
  ]
}
```

- `version` MUST be the integer `1`.
- `annotations` MUST be a list; each record carries exactly the four keys `issuer`,
  `invoice_id`, `owner`, and `notes`, all strings.
- Records are keyed in memory by the exact `(issuer, invoice_id)` tuple, never by row number,
  queue position, or a concatenated/delimiter string. In JSON, the pair is represented by the
  two explicit fields on each record; duplicate pairs are rejected on load.
- Records are serialized in ascending `(issuer, invoice_id)` order, UTF-8, with non-ASCII
  characters preserved (`ensure_ascii=False`) and a trailing newline. No timestamp is stored,
  so output never depends on the clock.
- A record whose `owner` and `notes` are both empty is equivalent to no annotation and is
  omitted on the next successful write. An empty/whitespace-only owner means unassigned; an
  empty notes value means no notes. Non-empty text, including multi-line and non-ASCII notes,
  is preserved exactly as supplied.

**Path** — every public annotation function takes `store_path`; a caller-supplied value is
used as given. When it is `None`, use `DEFAULT_ANNOTATION_STORE_PATH`, computed from the
package location as `<project root>/state/followup_annotations.json`. The store is local
single-writer runtime state; `state/` is added to `.gitignore` and is not committed. A read
never creates the file or its directory; the first successful write creates the parent
directory.

**Read and validation behaviour**:
- A missing file is an empty annotation mapping; no error and no file creation.
- Open/read/UTF-8 decoding failures raise `AnnotationStoreUnreadableError`.
- Invalid JSON, a non-object document, a missing/non-integer `version`, a non-list
  `annotations` value, a record that is not an object, a missing/extra/non-string field, or
  an otherwise invalid shape raises `AnnotationStoreMalformedError`.
- A document whose `version` is not `1` raises `AnnotationStoreVersionError`.
- Two records with the same `(issuer, invoice_id)` raise
  `AnnotationStoreDuplicateIdentityError`.
- On any of these errors the file is left untouched and is never silently reset, truncated, or
  rebuilt as empty.

**Assignment behaviour**:
- `set_owner` / `set_notes` first check that `(issuer, invoice_id)` is in the supplied current
  accepted identities; otherwise raise `InvoiceNotAcceptedError` without touching the store.
  This is the only path by which a rejected or duplicate row can be considered, and it is
  refused.
- The existing store is then loaded (missing means empty) and the one field is changed; the
  other field is untouched. `owner=None` or a whitespace-only owner clears the owner;
  `notes=None` or `notes == ""` clears the notes.
- A record with both fields empty is dropped. Annotations for identities not in the current
  accepted set are retained unchanged; they are simply not shown in the queue.
- A successful change is durable before the call returns. The function does not return until
  the atomic replacement has completed.

**Atomic whole-file write**:
1. Serialize the complete next document in memory.
2. Create the parent directory if needed.
3. Write to a uniquely named temporary file in the same directory, using
   `tempfile.mkstemp`/`os.fdopen(..., "w", encoding="utf-8", newline="\n")`.
4. Flush and `os.fsync` the temporary file, close it, then `os.replace` it onto the target
   path so readers see either the previous complete file or the new complete file.
5. Best-effort `os.fsync` the parent directory on POSIX for rename durability.
6. On any write/replace failure, remove the temporary file, leave the previous store intact,
   and raise `AnnotationStoreWriteError`.

A crash can therefore leave at most a stray temporary file, never a partially written store
that can be loaded. Concurrent writes from multiple processes are out of scope; no lock file
or cross-process transaction is introduced.

**Error hierarchy**:

```text
AnnotationError
├── AnnotationStoreUnreadableError
├── AnnotationStoreMalformedError
├── AnnotationStoreVersionError
├── AnnotationStoreDuplicateIdentityError
├── AnnotationStoreWriteError
└── InvoiceNotAcceptedError
```

All errors are explicit and fixable by the operator; none is silently swallowed.

### Attaching annotations to an ordered queue

1. Read the store once with the same validation rules; a missing store yields an empty map.
2. Copy each queue item, preserve its order and `position`, and fill `owner`/`notes` from the
   record with the exact `(issuer, invoice_id)` identity.
3. Empty stored strings are exposed as `None` (unassigned / no notes); non-empty text is
   exposed exactly.
4. Leave items without a record at `owner=None`, `notes=None`.
5. Ignore stored records whose identities are absent from the queue; retain them in the store
   for a future accepted import.
6. Do not write during attachment. A malformed/unreadable/unsupported store raises the same
   clear error as an assignment; it is not treated as empty.

## Test Plan (pytest, stdlib only)

**Stage 1 — `tests/test_followup_queue.py`**
- Exact SC-002/acceptance sequence for the frozen CSV at `2026-10-15`.
- Two calls produce equal sequences; repeated runs are byte-identical in identity order.
- Each bucket priority, descending balance within a bucket, ascending invoice ID, then ascending
  issuer as the last key; no unresolved ties.
- Same invoice ID from two issuers remains two items with the final issuer tie-break.
- Zero-balance `INV-1011` is present exactly once in `paid` with balance `0`.
- Empty accepted set returns `[]`; rejected and duplicate rows are excluded.
- Item fields, integer types, contiguous 1-based positions, and non-mutation of the import
  result.
- No filesystem/annotation dependency: the module imports and runs without `annotations.py`
  or `state/`.

**Stage 2 — `tests/test_followup_annotations.py`**
- Missing store: queue builds with all `owner=None`, `notes=None`; no file is created.
- Assign owner and notes independently; only the targeted identity changes; queue order and
  positions remain unchanged.
- Restart simulation: reload from the same path in a fresh call/process and observe identical
  values; multi-line and non-ASCII notes round-trip exactly.
- Clear owner without touching notes and vice versa; clearing both drops the record.
- Non-accepted identity is refused and the store is unchanged.
- Malformed JSON, unsupported version, duplicate identity, non-string/missing fields, and an
  unreadable path each raise the documented error and leave the original bytes untouched.
- Successful writes replace atomically; a simulated `os.replace` failure leaves the previous
  store readable and leaves no temporary file behind.
- An annotation for an identity absent from the current accepted set is retained but not
  displayed; it reappears when that identity is accepted again.

**Regression**: `tests/test_invoice_desk.py` remains unchanged and green; no changes to
`bill_split`, `data/`, `pyproject.toml`, `ROADMAP.md`, `ACCEPTANCE.md`, or `NON_GOALS.md`.

## Out of Scope

Payments/partial payments (R2), promised-pay annotations (R3), schema migration (R5), queue
filters and other R4 hardening beyond AT-05, CLI, network service, authentication, roles,
multi-tenancy, concurrent writers, reminders, outbound messages, payment processing, and
deployment. No import behaviour is re-implemented or changed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Local file I/O in `annotations.py`, which is not a pure function under Principle II | FR-022 to FR-025 and AT-05 require owner/notes to survive restart; durable local state cannot be achieved with pure functions alone. | Keeping annotations in memory fails persistence. A database or external service fails stdlib-only/offline and is far larger. I/O is isolated behind explicit store calls; ordering stays pure, deterministic, and clock-free. |
| A second persistence module beyond the existing import module | Keeps the stateful store separate so queue ordering can be built and reviewed first by a different agent. | Putting storage in `queue.py` would couple pure ordering to filesystem state and prevent the requested independent Stage 1 handoff. |

## Post-Design Constitution Re-check

- I, III, IV, V, VI, VII, VIII: still PASS; the design adds no floats, dependencies,
  network, clock use, or changes to import output.
- II: PASS for all domain/ordering functions; the single stateful boundary is the explicitly
  required annotation store, justified above and confined to `annotations.py`.

## Decisions (receiver log)

Agent B appends one bullet per decision made while implementing T001–T007 (date, task ID, decision, reason). Empty at handoff.
