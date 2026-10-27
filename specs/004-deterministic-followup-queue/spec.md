# Feature Specification: Deterministic follow-up queue with owners and notes

**Feature Branch**: `004-deterministic-followup-queue`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "AT-05 (full): a deterministic follow-up queue on top of L3's import_invoices. Order the queue by bucket, then balance, then invoice ID. Each queue item can carry an owner and free-text notes. Use ACCEPTANCE.md AT-05 as the source of truth. Do not implement anything."

## Clarifications

### Session 2026-10-24 (L4 ripple)

- Q: Does the L4 change to 003 FR-008 (positive canonical amounts) need recording in 004? → A: Yes (Tosin, 2026-10-24). FR-021 and SC-010 keep their text as scope rules for the 004 build, and each now carries a dated L4 note recording the import-behaviour change made in 003. No 004 behaviour or code changes.

### Session 2026-10-25 (L5 ripple)

- Q: Does the L5 change to 003 FR-007 (due date not before issue date) need recording in 004? → A: Yes (Tosin, 2026-10-25). FR-021 and SC-010 keep their text as scope rules for the 004 build, and each now carries a dated L5 note recording the import-behaviour change made in 003. No 004 behaviour or code changes.

### Session 2026-10-23

*Answers 2–5 approved by Tosin on Oct 23, 2026; answer 1 corrected by Tosin on Oct 23, 2026 (option B: issuer is the last key).*

- Q: AT-05 gives an illustrative ordering (`days_overdue` descending, then balance, then issuer, then invoice ID), while the request says bucket, then balance, then invoice ID. Which is binding? → A: AT-05's binding pass criterion is that ordering is a pure function of row data and is identical on repeated runs. The request's keys are used in that order (bucket, balance descending, invoice ID), with `issuer` added as the last key so the order stays total when two issuers reuse the same invoice identifier. *(Corrected by Tosin, Oct 23.)*
- Q: Does the follow-up queue contain every accepted invoice or only invoices with a positive balance? → A: AT-05 names the accepted set as the input, so the queue contains every accepted invoice; a fully paid invoice remains in the queue in the `paid` bucket at the lowest priority.
- Q: Where should owners and notes be stored, in what format, and how should each annotation be keyed so it survives a restart? → A: In a single versioned UTF-8 JSON file at a caller-supplied path, defaulting to `state/followup_annotations.json` under the project root; each record stores `issuer`, `invoice_id`, `owner`, and `notes`, keyed by the exact `(issuer, invoice_id)` pair, and each successful change is written through immediately with atomic whole-file replacement.
- Q: What should happen when the annotation store is missing, unreadable, corrupt, or has an unsupported version? → A: A missing file means an empty annotation set; an unreadable, malformed, duplicate-identity, or unsupported-version file raises a clear error and is never overwritten or silently reset.
- Q: How should an operator assign or clear an owner and notes? → A: Through explicit local library calls that take the annotation-store path, the current accepted identities, the invoice identity, and the new owner or notes value; no CLI, network, or authenticated interface is required.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See one deterministic priority order (Priority: P1)

An operator imports the invoice CSV and receives a follow-up queue in a predictable priority order. The most severely overdue invoices come first, larger balances come before smaller balances inside the same aging bucket, and two identical imports always produce the same sequence.

**Why this priority**: If the queue order can change between runs, the operator cannot trust the worklist or compare one review with the next. Determinism is the core of AT-05.

**Independent Test**: Build the queue twice from the same accepted set and as-of date, compare the two sequences, and verify the sequence against the documented bucket and tie-break order.

**Acceptance Scenarios**:

1. **Given** the accepted invoices from the frozen CSV at `as_of = 2026-10-15`, **When** the queue is built, **Then** every accepted invoice appears exactly once, rejected and duplicate rows do not appear, and the order is `INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014, INV-1004, INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011`.
2. **Given** the same accepted invoices, **When** the queue is built a second time, **Then** the sequence is byte-for-byte identical in invoice identity and order.
3. **Given** invoices in the `91+`, `61-90`, `31-60`, `1-30`, `current`, and `paid` buckets, **When** the queue is ordered, **Then** the bucket priority is `91+` first, then `61-90`, `31-60`, `1-30`, `current`, and `paid` last.
4. **Given** two invoices in the same bucket, **When** their remaining balances differ, **Then** the larger remaining balance comes first.
5. **Given** two invoices with the same bucket and the same remaining balance, **When** their invoice identifiers or issuers differ, **Then** the invoice identifier in ascending order is the next tie-breaker, and only if that also ties, the issuer name in ascending order.
6. **Given** the fully paid invoice `INV-1011`, **When** the queue is built, **Then** it appears in the `paid` bucket after every other accepted invoice, with a remaining balance of `0`.
7. **Given** an empty accepted set, **When** the queue is built, **Then** the queue is empty rather than an error.

---

### User Story 2 - Record who owns an invoice and what was noted (Priority: P2)

An operator assigns an owner and writes free-text notes on queue items. Those annotations remain attached to the right invoices after the queue is rebuilt, after the import is repeated, and after the application is restarted.

**Why this priority**: A deterministic queue is only actionable when the operator can record ownership and context without losing it. AT-05 explicitly requires owner and note persistence across restart.

**Independent Test**: Assign an owner to one accepted invoice and notes to another, rebuild the queue, restart the application, and verify that each annotation is still attached to the same invoice identity.

**Acceptance Scenarios**:

1. **Given** an accepted invoice in the queue, **When** an owner value is assigned, **Then** that queue item reports the owner and no other item inherits it.
2. **Given** an accepted invoice in the queue, **When** free-text notes are assigned, **Then** that queue item reports the exact note text and no other item inherits it.
3. **Given** an item with an owner and notes, **When** the application is restarted, **Then** the same invoice identity still reports the same owner and the same notes.
4. **Given** items with owner and note assignments, **When** the queue is rebuilt from the same accepted set, **Then** the annotations are still attached and the ordering is unchanged.
5. **Given** an item with an owner and notes, **When** the owner is cleared, **Then** only the owner becomes unassigned and the notes remain unchanged; clearing notes behaves the same way in reverse.
6. **Given** an annotated invoice, **When** the operator changes only its owner or notes, **Then** its balance, days overdue, bucket, and queue position do not change.
7. **Given** an invoice that is not accepted, **When** an owner or notes assignment is attempted, **Then** no queue item is created and the queue is unchanged.
8. **Given** no annotation store file exists, **When** the queue is built, **Then** every item reports no owner and no notes and no error occurs.
9. **Given** an unreadable or malformed annotation store, **When** an owner or notes change is attempted, **Then** the change is refused with a clear error and the existing file is left untouched.
10. **Given** a successful owner or notes change, **When** the process is stopped immediately afterwards, **Then** the same invoice identity still reports the change after restart.

---

### Edge Cases

- Two accepted invoices from different issuers have the same `invoice_id`; they remain separate queue items with independent owners and notes, and the final issuer tie-breaker prevents an ambiguous order.
- Two invoices share a bucket and a remaining balance; invoice identifier then issuer resolve the order completely.
- A pending invoice due today or in the future is in `current`; it appears after all overdue buckets and before `paid`.
- A fully paid invoice remains in the queue in `paid` with a zero balance and the lowest priority.
- A rejected or duplicate row can never receive an owner or notes and never appears in the queue.
- An owner or note containing non-ASCII text, punctuation, or multiple lines is preserved exactly across a restart.
- An empty or whitespace-only owner means unassigned; an empty notes value means no notes.
- The annotation store file does not exist: the queue still builds and every item reports no owner and no notes.
- The annotation store is unreadable, malformed, contains duplicate invoice identities, or declares an unsupported version: the feature raises a clear error, leaves the file unchanged, and does not silently rebuild an empty store.
- An annotation-store write is interrupted: the previous complete store remains readable, and a partially written file is never loaded.
- An annotation record with both owner and notes empty is equivalent to no annotation and need not be retained.
- Concurrent writes from multiple processes are out of scope; the annotation store is local single-writer state.
- Re-importing the same CSV must not duplicate queue items or annotation records.
- An annotated invoice that is absent from the current accepted set is not shown in the queue, but its annotation is retained by invoice identity and reappears if that invoice is accepted again.
- Annotation assignments attach to invoice identity, not to a queue position, so a reordering caused by changed balances or aging cannot move an owner or note to another invoice.
- An empty accepted set produces an empty queue and no errors.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST build a follow-up queue from the accepted invoices produced by the existing `import_invoices` capability, using its explicit `as_of` date. It MUST NOT re-implement import classification or mutate the import result.
- **FR-002**: The queue MUST contain exactly one item per accepted invoice, keyed by the pair `(issuer, invoice_id)`. Rejected rows and both duplicate classifications MUST NOT produce queue items.
- **FR-003**: The queue MUST include every accepted invoice, including an invoice with a remaining balance of `0`, which belongs to the `paid` bucket.
- **FR-004**: Every queue item MUST expose the invoice identity `(issuer, invoice_id)`, `remaining_balance_cents`, `days_overdue`, `aging_bucket`, owner, notes, and its position in the queue.
- **FR-005**: The queue MUST be sorted by a single total order:
  1. aging bucket priority: `91+`, then `61-90`, then `31-60`, then `1-30`, then `current`, then `paid`;
  2. remaining balance in descending order, so the larger balance comes first;
  3. invoice identifier in ascending, case-sensitive, locale-independent text order;
  4. issuer in ascending, case-sensitive, locale-independent text order.
- **FR-006**: The final tie-break sequence MUST be total for accepted invoices. Issuer MUST be the last key, after the invoice identifier, because invoice identifiers are only unique within an issuer; it resolves any remaining tie.
- **FR-007**: Queue ordering MUST be a pure function of invoice row data and the as-of date. It MUST NOT depend on the clock, randomness, insertion order beyond the documented keys, owner, notes, or storage order.
- **FR-008**: Building the queue twice from the same accepted set and as-of date MUST produce the same sequence of invoice identities.
- **FR-009**: Each queue item MUST support an optional owner, recorded as free text and attached to the invoice identity. No owner means unassigned.
- **FR-010**: Each queue item MUST support optional free-text notes, attached to the invoice identity and stored exactly as entered. Notes MAY contain multiple lines and non-ASCII characters.
- **FR-011**: Owner and notes MUST persist across an application restart and remain attached to the same invoice identity with unchanged content.
- **FR-012**: Owner and notes MUST be independent of each other: either MAY be set, changed, or cleared without altering the other.
- **FR-013**: Changing an owner or notes MUST NOT change any invoice's remaining balance, days overdue, aging bucket, or queue position.
- **FR-014**: Re-importing the same accepted set MUST NOT create duplicate queue items or duplicate annotation records, and MUST NOT detach annotations from their invoice identities.
- **FR-015**: Annotations MUST be retained by invoice identity when that invoice is absent from the current accepted set. Such annotations MUST NOT be displayed as queue items until the invoice is accepted again.
- **FR-016**: An owner or notes assignment MUST be refused for an invoice identity that is not in the current accepted set. A rejected or duplicate row identity MUST NOT become annotatable through this feature.
- **FR-017**: An empty accepted set MUST produce an empty queue without error, and MUST preserve any stored annotations for later accepted sets.
- **FR-018**: All monetary values used for ordering and display MUST remain integer cents; no floating-point arithmetic may be introduced.
- **FR-019**: The feature MUST remain local and offline: no network calls, external services, credentials, secrets, or real personal data.
- **FR-020**: The feature MUST NOT provide authentication, roles, multi-tenancy, reminders, outbound messages, payment processing, or collections automation. Owner is an internal label only.
- **FR-021**: The feature MUST leave the existing `import_invoices` behaviour unchanged, including its classifications, balances, aging buckets, and totals.
  - *L4 note (2026-10-24):* This requirement is about what the 004 build itself may change. Separately, the L4 revision of 003 (FR-008 superseded by FR-008a, commit 2526069) changed import behaviour: amount `0` and non-canonical amounts like `0100` are now `invalid_amount`, so zero-amount rows no longer appear in the follow-up queue's input. 004 code is unchanged; see `specs/003-desk-import/drift.md`.
  - *L5 note (2026-10-25):* This requirement is about what the 004 build itself may change. Separately, the L5 revision of 003 (FR-007 superseded by FR-007a) changed import behaviour: a row whose `due_date` is strictly earlier than its `issue_date` is now `invalid_date`, so it no longer appears in the follow-up queue's input. 004 code is unchanged; see `specs/003-desk-import/drift.md`.
- **FR-022**: Owner and notes MUST be stored in a single versioned UTF-8 JSON annotation store at a caller-supplied path, defaulting to `state/followup_annotations.json` relative to the project root. Each stored record MUST carry `issuer`, `invoice_id`, `owner`, and `notes`, and MUST be keyed by the exact `(issuer, invoice_id)` pair rather than by row number, queue position, or a concatenated delimiter string.
- **FR-023**: Each successful owner or notes change MUST be written through to the annotation store immediately, using atomic whole-file replacement, before the change is reported as applied. A crash during a write MUST NOT leave a partially written store that can be loaded.
- **FR-024**: A missing annotation store MUST be treated as an empty annotation set. An unreadable, malformed, duplicate-identity, or unsupported-version store MUST cause a clear error, MUST leave the existing file untouched, and MUST NOT be silently reset or overwritten.
- **FR-025**: Owner and notes MUST be assignable and clearable only through explicit local library calls that take the annotation-store path, the current accepted identities, the invoice identity, and the new value. No CLI, network service, or authenticated user interface is required, and hand-editing the store is not a supported assignment path.
- **FR-026**: The annotation store MUST remain local runtime state, not an import fixture or source of invoice truth. Its contents MUST never feed back into import classification, balances, aging, or queue ordering.

### Key Entities *(include if feature involves data)*

- **Queue item**: One accepted invoice in the follow-up queue, carrying its identity, balance, days overdue, aging bucket, owner, notes, and priority position.
- **Invoice identity**: The pair `(issuer, invoice_id)`, which uniquely identifies an invoice for ordering and annotation purposes.
- **Aging bucket priority**: The deterministic severity order `91+`, `61-90`, `31-60`, `1-30`, `current`, `paid`; it is an ordering concept, not a replacement for the existing bucket labels.
- **Owner**: An optional free-text label on one invoice identity, expressing who is responsible for the next action. It is not an authenticated user.
- **Notes**: Optional free-text context on one invoice identity, preserved verbatim across rebuilds and restarts.
- **Annotation record**: The stored `owner` and `notes` for one `(issuer, invoice_id)` identity, independent of queue position and import order. A record with both values empty is equivalent to no annotation.
- **Annotation store**: The single versioned UTF-8 JSON file that holds annotation records, defaulting to `state/followup_annotations.json` under the project root, keyed by invoice identity and replaced atomically on each successful change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Building the queue repeatedly from the same accepted set and as-of date yields an identical sequence of invoice identities in 100% of runs.
- **SC-002**: For the frozen accepted set at `as_of = 2026-10-15`, the queue order is exactly `INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014, INV-1004, INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011`.
- **SC-003**: For every accepted invoice, the queue position is fully explained by bucket priority, then descending remaining balance, then ascending invoice identifier, then ascending issuer, with zero unresolved ties.
- **SC-004**: Owner and notes assigned to queue items are still present, on the same invoice identities and with unchanged content, after a restart in 100% of tested assignments.
- **SC-005**: Changing owner or notes leaves the queue order, balances, days overdue, and aging buckets unchanged in 100% of tested cases.
- **SC-006**: Rebuilding the queue from the same input produces no duplicated queue items and no duplicated or detached annotation records.
- **SC-007**: No rejected or duplicate row appears in the queue, and no annotation can be attached to one.
- **SC-008**: The queue handles an empty accepted set without error and produces zero items.
- **SC-009**: The feature operates with networking blocked and introduces no credentials, secrets, or real personal data.
- **SC-010**: The existing import classifications, balances, aging buckets, and totals remain unchanged.
  - *L4 note (2026-10-24):* This criterion is about what the 004 build itself may change. Separately, the L4 revision of 003 (FR-008 superseded by FR-008a, commit 2526069) changed import behaviour: amount `0` and non-canonical amounts like `0100` are now `invalid_amount`, so zero-amount rows no longer appear in the follow-up queue's input. 004 code is unchanged; see `specs/003-desk-import/drift.md`.
  - *L5 note (2026-10-25):* This criterion is about what the 004 build itself may change. Separately, the L5 revision of 003 (FR-007 superseded by FR-007a) changed import behaviour: a row whose `due_date` is strictly earlier than its `issue_date` is now `invalid_date`, so it no longer appears in the follow-up queue's input. 004 code is unchanged; see `specs/003-desk-import/drift.md`.
- **SC-011**: With no annotation store present, the queue builds successfully and all items report no owner and no notes in 100% of runs.
- **SC-012**: An unreadable, malformed, duplicate-identity, or unsupported-version annotation store produces a clear error and is never silently overwritten in 100% of tested cases.
- **SC-013**: Every successful owner or notes change is durable before it is reported, and survives an immediate process stop in 100% of tested cases.

## Assumptions

- `ACCEPTANCE.md` AT-05 is the source of truth. Its ordering example uses "e.g.", so the binding requirement is a repeatable, pure ordering; this specification makes the requested keys explicit and adds issuer as the last key, needed for a total order.
- The follow-up queue is built over the full accepted set, including the zero-balance `paid` item, because AT-05 explicitly names the accepted set as the input. Paid invoices are always last.
- Bucket priority is severity-descending (`91+` before `61-90` before `31-60` before `1-30` before `current` before `paid`), matching the intent of AT-05's `days_overdue` descending example while honoring the requested bucket-first ordering.
- "Balance" means `remaining_balance_cents` from the import result, ordered descending; "invoice ID" means the invoice identifier, ordered ascending after balance; issuer, ascending, is the final key.
- Text comparisons are case-sensitive and locale-independent so the order cannot vary by machine configuration.
- Each invoice identity carries one owner value and one free-text notes value. Notes may be a multi-line block; a separate append-only note history is not required by AT-05 and is out of scope.
- Annotations are durable local state for a single operator and are held in one versioned JSON annotation store at a caller-supplied path, defaulting to `state/followup_annotations.json`; "restart" means the same local installation starts again with the same store path and its state intact.
- JSON is chosen because the project is standard-library-only and the store must remain local and human-inspectable; no database, external service, or new dependency is introduced.
- The annotation store is single-writer local runtime state. Concurrent writes from multiple processes are out of scope, and the default store path is expected to be excluded from version control rather than treated as a frozen fixture.
- Annotations are keyed by `(issuer, invoice_id)` rather than by row number or queue position, so sorting and re-importing cannot move an annotation to a different invoice.
- The queue is rebuilt from a fresh import result whenever the accepted set or as-of date is supplied; no import row state is stored or mutated by this feature.
- Roadmap R2 payment events, R3 promised-pay annotations, R5 schema migration, R4 filter/queue-hardening extras beyond AT-05, reminders, and deployment remain out of scope.
