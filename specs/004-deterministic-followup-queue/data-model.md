# Data Model: Deterministic follow-up queue with owners and notes

**Feature**: `004-deterministic-followup-queue`
**Date**: 2026-10-23
**Source**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### Import result (existing input)

Produced by `invoice_desk.import_invoices(csv_text, as_of)`; this feature only reads it.

| Field | Type | Notes |
|-------|------|-------|
| `rows` | `list[dict]` | One entry per CSV data row, in input order |
| `rows[].status` | `str` | `accepted`, `rejected`, `duplicate_identical`, or `duplicate_inconsistent` |
| `rows[].issuer` | `str` | Present only on accepted rows |
| `rows[].invoice_id` | `str` | Present only on accepted rows |
| `rows[].remaining_balance_cents` | `int` | Present only on accepted rows; non-negative integer cents |
| `rows[].days_overdue` | `int` | Present only on accepted rows; `0` for zero-balance invoices |
| `rows[].aging_bucket` | `str` | Present only on accepted rows; one of the six buckets |
| `totals` | `dict` | Existing totals; never modified by this feature |

The import result remains the sole source of invoice truth. Annotation data never feeds back
into it (FR-001, FR-026).

### Invoice identity

| Field | Type | Validation |
|-------|------|------------|
| `issuer` | `str` | Exact normalized value from the accepted import row; case-sensitive |
| `invoice_id` | `str` | Exact normalized value from the accepted import row; case-sensitive |

Represented as the tuple `(issuer, invoice_id)`. It is the only key for queue membership and
annotation lookup. It is never a row number, queue position, or concatenated string.

### Queue item

| Field | Type | Validation / derivation |
|-------|------|-------------------------|
| `issuer` | `str` | Copied from an accepted import row |
| `invoice_id` | `str` | Copied from an accepted import row |
| `remaining_balance_cents` | `int` | Copied unchanged; integer cents, `>= 0` |
| `days_overdue` | `int` | Copied unchanged; `>= 0` |
| `aging_bucket` | `str` | Copied unchanged; one of `91+`, `61-90`, `31-60`, `1-30`, `current`, `paid` |
| `owner` | `None` or `str` | `None` when unassigned; otherwise the stored owner text |
| `notes` | `None` or `str` | `None` when no notes; otherwise the stored notes text exactly |
| `position` | `int` | 1-based, contiguous, assigned after sorting |

Rules:

- Exactly one queue item per accepted `(issuer, invoice_id)`; rejected and duplicate rows
  produce none (FR-002, FR-003).
- Every accepted invoice is included, including a zero-balance invoice in `paid`.
- Additional fields from the import result are not copied into the queue item.
- Ordering is independent of `owner`, `notes`, storage order, or insertion order
  (FR-007).
- `position` is not part of the sort key; it is derived from the final order.
- Changing annotations never changes any field other than `owner`/`notes` (FR-013).

### Aging bucket priority

| Bucket | Rank |
|--------|------|
| `91+` | 0 |
| `61-90` | 1 |
| `31-60` | 2 |
| `1-30` | 3 |
| `current` | 4 |
| `paid` | 5 |

Sort key, in order: `(rank, -remaining_balance_cents, invoice_id, issuer)`.
`invoice_id` and `issuer` use ascending, case-sensitive, locale-independent text order.

### Annotation record

One stored annotation for one invoice identity.

| Field | Type | Validation |
|-------|------|------------|
| `issuer` | `str` | Non-empty in a valid store; forms the first half of the key |
| `invoice_id` | `str` | Non-empty in a valid store; forms the second half of the key |
| `owner` | `str` | `""` means unassigned; otherwise preserved exactly |
| `notes` | `str` | `""` means no notes; otherwise preserved exactly, including newlines and non-ASCII |

Rules:

- `owner` and `notes` are independent (FR-012).
- An empty or whitespace-only owner means unassigned; a non-empty owner is stored with its
  exact text.
- `notes == ""` means no notes; a non-empty notes value is stored verbatim.
- A record with both fields empty is equivalent to no annotation and is omitted on the next
  write.
- An annotation may exist for an identity that is not in the current accepted set. It is
  retained but not displayed until that identity is accepted again (FR-015).

### Annotation store (version 1)

Top-level JSON document:

| Field | Type | Validation |
|-------|------|------------|
| `version` | `int` | Must equal `1` |
| `annotations` | `list[Annotation record]` | Each record has exactly `issuer`, `invoice_id`, `owner`, `notes` as strings |

Serialization rules:

- UTF-8, non-ASCII preserved, trailing newline.
- Records sorted by ascending `(issuer, invoice_id)`.
- No timestamp, clock-derived value, or random content inside the document.
- The file is whole-file replaced; a partially written document is never valid.
- Missing file = empty annotation mapping; the file is not created by reads.

## Validation and error rules

| Condition | Result |
|-----------|--------|
| Missing store file | Empty annotation set; queue items have no owner/notes |
| Store cannot be opened/read/decoded as UTF-8 | `AnnotationStoreUnreadableError`; existing file untouched |
| Invalid JSON or wrong document/record shape | `AnnotationStoreMalformedError`; existing file untouched |
| `version` is not the integer `1` | `AnnotationStoreVersionError`; existing file untouched |
| Two records share `(issuer, invoice_id)` | `AnnotationStoreDuplicateIdentityError`; existing file untouched |
| Assignment target not in current accepted identities | `InvoiceNotAcceptedError`; store untouched |
| Write or replacement fails | `AnnotationStoreWriteError`; previous store intact, temporary file removed |

## State transitions

Annotation state is per invoice identity, not per queue position.

```text
no record
   | set owner or notes (identity must be accepted)
   v
record(owner?, notes?)
   | change owner / change notes (independent)
   v
record(owner?, notes?)
   | clear the remaining non-empty field
   v
no record (both fields empty, dropped on write)

record for an identity absent from the accepted set
   | queue rebuild without that identity
   v
record retained in store, not shown in queue
   | identity accepted again
   v
record shown on the queue item again
```

- Assigning an owner does not alter notes, and vice versa.
- Clearing one field leaves the other intact.
- Re-importing the same accepted set neither duplicates queue items nor duplicates or
  detaches annotation records.
- Ordering is recomputed from import row data only; annotation transitions never affect it.

## Relationships

```text
Import row (accepted) 1 ─── 0..1 Queue item        by (issuer, invoice_id)
Invoice identity      1 ─── 0..1 Annotation record  by exact tuple
Annotation record     1 ─── 0..1 Queue item         when the identity is accepted
```

An annotation record can outlive its queue item (identity not currently accepted). A queue
item can appear without an annotation record. The import result never references annotation
storage.
