"""Pure CSV invoice import and aging for the Invoice Exception Desk.

The public entry point, :func:`import_invoices`, reads invoice CSV text and
classifies every data row as accepted, rejected with a reason, an identical
duplicate, or an inconsistent duplicate. Accepted invoices report an integer-cent
remaining balance, days overdue, and an aging bucket as of an explicit date.

The function is pure and offline: it uses only the standard library, never reads
the system clock, never touches the network, and keeps no state between calls.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import date

from .annotations import (
    ANNOTATION_STORE_VERSION,
    DEFAULT_ANNOTATION_STORE_PATH,
    AnnotationError,
    AnnotationStoreDuplicateIdentityError,
    AnnotationStoreMalformedError,
    AnnotationStoreUnreadableError,
    AnnotationStoreVersionError,
    AnnotationStoreWriteError,
    AnnotationValueTypeError,
    InvoiceNotAcceptedError,
    attach_annotations,
    followup_queue,
    load_annotations,
    set_notes,
    set_owner,
)
from .queue import BUCKET_PRIORITY, accepted_invoice_identities, build_followup_queue

HEADER_FIELDS = (
    "issuer",
    "invoice_id",
    "issue_date",
    "due_date",
    "amount_cents",
    "currency",
    "paid_cents",
)

STATUSES = (
    "accepted",
    "rejected",
    "duplicate_identical",
    "duplicate_inconsistent",
)

REJECTION_REASONS = (
    "empty_row",
    "missing_required_field",
    "invalid_date",
    "invalid_amount",
    "invalid_currency",
    "invalid_payment",
)

DUPLICATE_IDENTICAL_REASON = "identical_duplicate"
DUPLICATE_INCONSISTENT_REASON = "inconsistent_duplicate"

AGING_BUCKETS = ("current", "1-30", "31-60", "61-90", "91+", "paid")

_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_INTEGER_PATTERN = re.compile(r"[0-9]+\Z")


def _zero_aging() -> dict[str, dict[str, int]]:
    """Return a fresh all-zero aging-bucket mapping."""
    return {bucket: {"count": 0, "remaining_cents": 0} for bucket in AGING_BUCKETS}


def _parse_date(value: str) -> date | None:
    """Parse a strict ``YYYY-MM-DD`` civil date, or return ``None``."""
    if _DATE_PATTERN.fullmatch(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_csv(csv_text: str) -> list[list[str]]:
    """Parse CSV text into seven trimmed field values per data row.

    The first row is the header and columns are mapped by name. Blank lines are
    preserved as data rows, short rows are padded with blanks, extra cells are
    ignored, and every field is stripped of surrounding whitespace.
    """
    reader = csv.reader(io.StringIO(csv_text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    positions: dict[str, int] = {}
    for position, raw_name in enumerate(header):
        name = raw_name.strip().lstrip("\ufeff")
        if name in HEADER_FIELDS and name not in positions:
            positions[name] = position

    data_rows: list[list[str]] = []
    for raw_cells in reader:
        values = []
        for name in HEADER_FIELDS:
            position = positions.get(name)
            if position is None or position >= len(raw_cells):
                values.append("")
            else:
                values.append(raw_cells[position].strip())
        data_rows.append(values)
    return data_rows


def _validate_row(
    values: list[str],
) -> tuple[dict[str, object] | None, str | None]:
    """Validate one parsed row in precedence order.

    Returns the normalized seven fields and ``None`` on success, or ``None`` and
    exactly one rejection reason on failure.
    """
    if not values or all(value == "" for value in values):
        return None, "empty_row"

    (
        issuer,
        invoice_id,
        issue_text,
        due_text,
        amount_text,
        currency,
        paid_text,
    ) = values

    if issuer == "" or invoice_id == "":
        return None, "missing_required_field"

    issue_date = _parse_date(issue_text)
    due_date = _parse_date(due_text)
    if issue_date is None or due_date is None:
        return None, "invalid_date"

    if _INTEGER_PATTERN.fullmatch(amount_text) is None:
        return None, "invalid_amount"
    amount_cents = int(amount_text)

    if currency != "USD":
        return None, "invalid_currency"

    if paid_text == "":
        paid_cents = 0
    elif _INTEGER_PATTERN.fullmatch(paid_text) is None:
        return None, "invalid_payment"
    else:
        paid_cents = int(paid_text)

    if paid_cents > amount_cents:
        return None, "invalid_payment"

    return (
        {
            "issuer": issuer,
            "invoice_id": invoice_id,
            "issue_date": issue_date,
            "due_date": due_date,
            "amount_cents": amount_cents,
            "currency": currency,
            "paid_cents": paid_cents,
        },
        None,
    )


def import_invoices(csv_text: str, as_of: date) -> dict:
    """Import invoice CSV text and compute balances, aging, and totals.

    ``as_of`` is supplied explicitly; the function never reads the clock. Money is
    handled strictly as integer cents. Duplicate detection is scoped to this call
    and keyed by ``(issuer, invoice_id)``. The same text and date always produce
    the same result.
    """
    rows: list[dict[str, object]] = []
    totals: dict[str, object] = {
        "total_rows": 0,
        "accepted": 0,
        "rejected": 0,
        "duplicate_identical": 0,
        "duplicate_inconsistent": 0,
        "outstanding_invoice_count": 0,
        "total_outstanding_cents": 0,
        "total_paid_cents": 0,
        "aging": _zero_aging(),
    }
    aging: dict[str, dict[str, int]] = totals["aging"]  # type: ignore[assignment]
    first_accepted: dict[tuple[str, str], dict[str, object]] = {}

    for row_number, values in enumerate(_parse_csv(csv_text), start=1):
        totals["total_rows"] += 1  # type: ignore[operator]
        normalized, reason = _validate_row(values)

        if reason is not None:
            totals["rejected"] += 1  # type: ignore[operator]
            rows.append(
                {
                    "row": row_number,
                    "status": "rejected",
                    "reason": reason,
                    "remaining_balance_cents": None,
                    "days_overdue": None,
                    "aging_bucket": None,
                }
            )
            continue

        assert normalized is not None
        identity = (
            normalized["issuer"],
            normalized["invoice_id"],
        )
        original = first_accepted.get(identity)

        if original is not None:
            is_identical = all(
                normalized[field] == original[field] for field in HEADER_FIELDS
            )
            status = (
                "duplicate_identical"
                if is_identical
                else "duplicate_inconsistent"
            )
            totals[status] += 1  # type: ignore[operator]
            rows.append(
                {
                    "row": row_number,
                    "status": status,
                    "reason": (
                        DUPLICATE_IDENTICAL_REASON
                        if is_identical
                        else DUPLICATE_INCONSISTENT_REASON
                    ),
                    "remaining_balance_cents": None,
                    "days_overdue": None,
                    "aging_bucket": None,
                }
            )
            continue

        first_accepted[identity] = normalized
        amount_cents = int(normalized["amount_cents"])
        paid_cents = int(normalized["paid_cents"])
        remaining_cents = amount_cents - paid_cents
        # FR-017/FR-018: a fully paid invoice is never overdue.
        days_overdue = (
            max(0, (as_of - normalized["due_date"]).days)  # type: ignore[operator]
            if remaining_cents > 0
            else 0
        )

        if remaining_cents == 0:
            bucket = "paid"
        elif days_overdue == 0:
            bucket = "current"
        elif days_overdue <= 30:
            bucket = "1-30"
        elif days_overdue <= 60:
            bucket = "31-60"
        elif days_overdue <= 90:
            bucket = "61-90"
        else:
            bucket = "91+"

        rows.append(
            {
                "row": row_number,
                "status": "accepted",
                "reason": None,
                "issuer": normalized["issuer"],
                "invoice_id": normalized["invoice_id"],
                "amount_cents": amount_cents,
                "paid_cents": paid_cents,
                "remaining_balance_cents": remaining_cents,
                "days_overdue": days_overdue,
                "aging_bucket": bucket,
            }
        )

        totals["accepted"] += 1  # type: ignore[operator]
        totals["total_paid_cents"] += paid_cents  # type: ignore[operator]
        if remaining_cents > 0:
            totals["outstanding_invoice_count"] += 1  # type: ignore[operator]
            totals["total_outstanding_cents"] += remaining_cents  # type: ignore[operator]

        bucket_totals = aging[bucket]
        bucket_totals["count"] += 1
        bucket_totals["remaining_cents"] += remaining_cents

    return {"rows": rows, "totals": totals}
