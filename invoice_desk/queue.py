"""Pure follow-up ordering over an existing invoice import result.

Balances and aging are copied from accepted rows, never recalculated. Annotation
storage is deliberately separate; Stage 1 always returns unassigned fields.
"""

BUCKET_PRIORITY = {
    "91+": 0,
    "61-90": 1,
    "31-60": 2,
    "1-30": 3,
    "current": 4,
    "paid": 5,
}


def accepted_invoice_identities(import_result: dict) -> set[tuple[str, str]]:
    """Return exact accepted identity pairs without modifying the import result."""
    return {
        (row["issuer"], row["invoice_id"])
        for row in import_result["rows"]
        if row["status"] == "accepted"
    }


def build_followup_queue(import_result: dict) -> list[dict]:
    """Return fresh items in bucket, balance, invoice ID, then issuer order.

    Includes paid invoices and assigns contiguous 1-based positions. This only
    reads the supplied import result: no I/O, clock, or annotation dependency.
    """
    accepted = sorted(
        (row for row in import_result["rows"] if row["status"] == "accepted"),
        key=lambda row: (
            BUCKET_PRIORITY[row["aging_bucket"]],
            -row["remaining_balance_cents"],
            row["invoice_id"],
            row["issuer"],
        ),
    )
    return [
        {
            "issuer": row["issuer"],
            "invoice_id": row["invoice_id"],
            "remaining_balance_cents": row["remaining_balance_cents"],
            "days_overdue": row["days_overdue"],
            "aging_bucket": row["aging_bucket"],
            "owner": None,
            "notes": None,
            "position": position,
        }
        for position, row in enumerate(accepted, start=1)
    ]
