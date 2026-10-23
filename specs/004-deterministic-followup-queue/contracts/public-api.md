# Public API Contract: invoice_desk follow-up queue and annotations

**Feature**: `004-deterministic-followup-queue`
**Contract version**: 1
**Audience**: callers of the `invoice_desk` Python package (local library use only)

This contract adds names to the existing `invoice_desk` package without changing
`import_invoices`. All money values are integer cents. No network, authentication, CLI, or
external service is part of this contract.

## Stage 1 — pure queue ordering

### `BUCKET_PRIORITY`

A mapping from aging bucket to its sort rank:

```text
91+ = 0, 61-90 = 1, 31-60 = 2, 1-30 = 3, current = 4, paid = 5
```

### `accepted_invoice_identities(import_result) -> set[tuple[str, str]]`

Returns the exact `(issuer, invoice_id)` pairs of rows whose `status == "accepted"`.
Rejected and duplicate rows are excluded. The input is not modified.

### `build_followup_queue(import_result) -> list[dict]`

Returns a new list with one new dict per accepted import row, sorted by:

1. `BUCKET_PRIORITY[aging_bucket]` ascending;
2. `remaining_balance_cents` descending;
3. `invoice_id` ascending (case-sensitive, locale-independent);
4. `issuer` ascending (case-sensitive, locale-independent), the last key.

Each queue item has exactly these keys:

```text
issuer                  str
invoice_id              str
remaining_balance_cents int
days_overdue            int
aging_bucket            str
owner                   None
notes                   None
position                int    # 1-based, contiguous
```

Guarantees:

- Empty accepted set returns `[]`.
- Every accepted invoice appears exactly once, including a zero-balance `paid` invoice.
- Rejected and duplicate rows never appear.
- Repeated calls with the same import result return equal sequences.
- The function performs no file I/O, reads no clock, uses no randomness, imports no
  annotation module, and mutates neither the input nor its rows.

Frozen-fixture example at `as_of = 2026-10-15`:

```text
INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014,
INV-1004, INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011
```

## Stage 2 — annotation persistence

### Store location

`DEFAULT_ANNOTATION_STORE_PATH` resolves to
`<project root>/state/followup_annotations.json`. Every function accepts an optional
`store_path`; when supplied, it is used as given. Reads never create the path. The first
successful write creates the parent directory if needed.

### `load_annotations(store_path=None) -> dict[tuple[str, str], dict[str, str]]`

Reads and validates the whole store, returning a mapping keyed by the exact
`(issuer, invoice_id)` tuple. Each value has string keys `issuer`, `invoice_id`, `owner`,
and `notes`.

- Missing file returns `{}`.
- A valid empty store (`{"version": 1, "annotations": []}`) returns `{}`.
- Empty owner/notes strings are returned as stored; callers that build queue items map them
  to `None` when attaching.
- Any invalid store raises one of the documented errors and never writes.

### `set_owner(accepted_identities, issuer, invoice_id, owner, *, store_path=None) -> None`

Assigns or clears the owner for one identity.

- `(issuer, invoice_id)` must be in `accepted_identities`; otherwise
  `InvoiceNotAcceptedError` is raised before any store write.
- `owner=None` or a whitespace-only string clears the owner.
- A non-empty owner is stored exactly; notes are untouched.
- The change is persisted atomically before the call returns.
- A store with both fields empty after the change is omitted.

### `set_notes(accepted_identities, issuer, invoice_id, notes, *, store_path=None) -> None`

Assigns or clears notes for one identity.

- `(issuer, invoice_id)` must be in `accepted_identities`; otherwise
  `InvoiceNotAcceptedError` is raised before any store write.
- `notes=None` or `notes == ""` clears the notes.
- Non-empty notes are stored exactly, including newlines, punctuation, and non-ASCII text;
  the owner is untouched.
- The change is persisted atomically before the call returns.
- A store with both fields empty after the change is omitted.

### `attach_annotations(queue, store_path=None) -> list[dict]`

Returns a new queue list with the same order and `position` values, filling `owner` and
`notes` on each item from the exact identity match.

- Missing store: every item keeps `owner=None`, `notes=None`.
- Stored empty strings are exposed as `None`.
- Annotations for identities not present in `queue` are retained in the store but ignored
  by this call.
- The input queue is not mutated.
- An invalid store raises the same clear error as `load_annotations`; it is not treated as
  empty.

### `followup_queue(import_result, store_path=None) -> list[dict]`

Convenience composition of `attach_annotations(build_followup_queue(import_result), ...)`.
It does not re-implement ordering and does not change queue fields other than
`owner`/`notes`.

## Store document contract

The file is UTF-8 JSON and MUST match
[`annotation-store.schema.json`](./annotation-store.schema.json):

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

- `version` is the integer `1`. No other version is supported.
- `annotations` is a list. Each record has exactly `issuer`, `invoice_id`, `owner`, and
  `notes`, all strings.
- Records are keyed by the exact pair; duplicate pairs are invalid.
- Records are serialized sorted by ascending `(issuer, invoice_id)`.
- A record with both `owner` and `notes` empty is equivalent to no annotation and is omitted
  on the next write.
- The store contains no clock-derived or random content.

## Error contract

All errors derive from `AnnotationError`:

| Error | Meaning |
|-------|---------|
| `AnnotationStoreUnreadableError` | The store exists but cannot be opened, read, or decoded as UTF-8 |
| `AnnotationStoreMalformedError` | Invalid JSON or wrong document/record shape, including missing/non-string fields |
| `AnnotationStoreVersionError` | The store declares a version other than integer `1` |
| `AnnotationStoreDuplicateIdentityError` | Two records share the same `(issuer, invoice_id)` |
| `AnnotationStoreWriteError` | Serialization, temporary-file creation, write, fsync, or replacement failed |
| `InvoiceNotAcceptedError` | An assignment targets an identity not in the supplied accepted set |

On any load/validation error, the existing file is left untouched and is never silently
reset or overwritten. On a write error, the previous complete store remains readable and any
temporary file is removed. Concurrent writers are out of scope.

## Durability and atomicity

Each successful assignment writes a complete new document to a temporary file in the same
directory, flushes and fsyncs it, then atomically replaces the target with `os.replace`.
The call returns only after replacement. Readers therefore see either the previous complete
store or the new complete store, never a partial document.
