# Quickstart Validation Guide

**Feature**: `004-deterministic-followup-queue`
**Purpose**: prove the queue ordering and annotation persistence work end to end

This guide describes validation only. Implementation details live in [plan.md](./plan.md),
[data-model.md](./data-model.md), and the [public API contract](./contracts/public-api.md).

## Prerequisites

- Python 3.11 or newer.
- The repository's virtual environment (if used) activated.
- No third-party runtime packages and no network access.
- The existing fixture `data/invoices.csv` and synthetic `as_of = 2026-10-15`.

## 1. Run the test suite

```bash
python -m pytest -q
```

Expected: all existing import tests and the new queue/annotation tests pass. The existing
`tests/test_invoice_desk.py` must remain unchanged. `python -m pytest` alone is also valid
because `pyproject.toml` sets `testpaths = ["tests"]`.

## 2. Verify the frozen queue order

Run a short caller-side check against the public API:

```bash
python - <<'PY'
from datetime import date
from pathlib import Path
from invoice_desk import build_followup_queue, import_invoices

csv_text = Path("data/invoices.csv").read_text(encoding="utf-8")
result = import_invoices(csv_text, date(2026, 10, 15))
queue = build_followup_queue(result)
print([item["invoice_id"] for item in queue])
PY
```

Expected order:

```text
['INV-1009', 'INV-1012', 'INV-1008', 'INV-1007', 'INV-1005', 'INV-1006',
 'INV-1014', 'INV-1004', 'INV-1003', 'INV-1010', 'INV-1001', 'INV-1002',
 'INV-1013', 'INV-1011']
```

Also confirm:

- Every accepted invoice appears exactly once; rejected and duplicate rows do not appear.
- `INV-1011` is last in `paid` with `remaining_balance_cents == 0`.
- Every item has contiguous 1-based `position` values.
- `owner` and `notes` are `None` at this stage.

## 3. Verify determinism

```bash
python - <<'PY'
from datetime import date
from pathlib import Path
from invoice_desk import build_followup_queue, import_invoices

csv_text = Path("data/invoices.csv").read_text(encoding="utf-8")
result = import_invoices(csv_text, date(2026, 10, 15))
first = build_followup_queue(result)
second = build_followup_queue(result)
print(first == second)
PY
```

Expected: `True`. Rebuilding from the same import result or re-importing the same CSV and
rebuilding must produce the same identity sequence.

## 4. Verify owner and notes persistence

Use a temporary store so the repository's `state/` directory is untouched:

```bash
python - <<'PY'
import tempfile
from datetime import date
from pathlib import Path
from invoice_desk import (
    accepted_invoice_identities,
    followup_queue,
    import_invoices,
    set_notes,
    set_owner,
)

csv_text = Path("data/invoices.csv").read_text(encoding="utf-8")
result = import_invoices(csv_text, date(2026, 10, 15))
identities = accepted_invoice_identities(result)

with tempfile.TemporaryDirectory() as tmp:
    store = Path(tmp) / "followup_annotations.json"
    set_owner(identities, "Acme Cleaning Co", "INV-1001", "Dana", store_path=store)
    set_notes(
        identities,
        "Acme Cleaning Co",
        "INV-1002",
        "Call Tuesday.\nAsk for AP.",
        store_path=store,
    )

    first = followup_queue(result, store)
    second = followup_queue(result, store)

    by_id = {item["invoice_id"]: item for item in first}
    assert by_id["INV-1001"]["owner"] == "Dana"
    assert by_id["INV-1001"]["notes"] is None
    assert by_id["INV-1002"]["owner"] is None
    assert by_id["INV-1002"]["notes"] == "Call Tuesday.\nAsk for AP."
    assert [item["invoice_id"] for item in first] == [
        item["invoice_id"] for item in second
    ]
    assert store.exists()
    print("annotations persisted; order unchanged")
PY
```

Expected: `annotations persisted; order unchanged`. Simulate a restart by running
`followup_queue(result, store)` again in a separate process with the same store path; the
same identity still reports the same owner/notes. Clearing the owner must leave notes
unchanged, and clearing notes must leave the owner unchanged.

## 5. Verify missing and invalid stores

- **Missing store**: call `followup_queue(result, path_that_does_not_exist)`. The queue must
  build with every `owner` and `notes` equal to `None`, and the missing path must not be
  created.
- **Malformed store**: write `{not json` to a temporary file, record its bytes, attempt
  `set_owner`, and expect `AnnotationStoreMalformedError`. The file bytes must be identical
  afterwards, and the queue must not silently treat the store as empty.
- **Unsupported version**: write a valid document with `"version": 2` and expect
  `AnnotationStoreVersionError`; the file must remain unchanged.
- **Duplicate identity**: write two records with the same `(issuer, invoice_id)` and expect
  `AnnotationStoreDuplicateIdentityError`; the file must remain unchanged.
- **Not accepted**: attempt an assignment for a rejected or duplicate row identity and expect
  `InvoiceNotAcceptedError`; the store must remain unchanged.

The exact error names and store shape are defined in
[contracts/public-api.md](./contracts/public-api.md) and
[contracts/annotation-store.schema.json](./contracts/annotation-store.schema.json).

## 6. Verify annotation changes do not reorder the queue

Assign an owner and notes to an existing invoice, rebuild the queue, and compare the
`invoice_id` sequence and all `position` values with the pre-annotation queue. Expected:
identical sequence and positions; only `owner`/`notes` differ on the annotated item.

## 7. Verify retained annotations for absent invoices

1. In a temporary store, annotate an accepted identity.
2. Build a queue from a different accepted set that does not contain that identity.
3. Confirm the identity is absent from the queue but still present in `load_annotations`.
4. Import an accepted set containing that identity again and confirm the annotation
   reappears on the same queue item.

## Expected end state

- Queue ordering is pure, total, and repeatable.
- All accepted invoices appear once; `paid` is last; empty input yields an empty queue.
- Owner and notes are independent, survive reloads, and preserve text exactly.
- Missing stores mean no annotations; invalid stores fail clearly without being overwritten.
- No changes to import classifications, balances, aging buckets, totals, or `bill_split`.
