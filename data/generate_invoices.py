#!/usr/bin/env python3
"""Deterministic synthetic invoice generator for the Invoice Exception Desk (R0).

Python standard library only. A fixed seed makes the generated CSV byte-for-byte
reproducible on any fresh checkout.

The generated data deliberately exercises the import policy:

* valid rows covering every due-date boundary relative to as_of=2026-10-15
* identical duplicates (must be a no-op)
* inconsistent duplicates (must be flagged, never imported)
* invalid amounts, invalid dates, invalid currency, invalid payments
* missing required fields
* empty rows
* a few partial-payment rows for the later v2a payment story

Usage:
    python3 data/generate_invoices.py [output.csv]
"""

from __future__ import annotations

import csv
import os
import random

SEED = 20261015
AS_OF = "2026-10-15"  # America/New_York reporting date for aging
CURRENCY = "USD"

HEADER = [
    "issuer",
    "invoice_id",
    "issue_date",
    "due_date",
    "amount_cents",
    "currency",
    "paid_cents",
]

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices.csv")

ISSUER_A = "Acme Cleaning Co"
ISSUER_B = "Bright Path Facilities"

# (issuer, invoice_id, issue_date, due_date, paid_cents, boundary_label)
# due_date offsets are measured from AS_OF = 2026-10-15.
_BOUNDARY_ROWS = [
    (ISSUER_A, "INV-1001", "2026-09-01", "2026-10-25", 0, "not_due"),
    (ISSUER_A, "INV-1002", "2026-09-15", "2026-10-15", 0, "due_today"),
    (ISSUER_A, "INV-1003", "2026-09-14", "2026-10-14", 0, "overdue_1"),
    (ISSUER_A, "INV-1004", "2026-08-16", "2026-09-15", 0, "overdue_30"),
    (ISSUER_A, "INV-1005", "2026-08-15", "2026-09-14", 0, "overdue_31"),
    (ISSUER_A, "INV-1006", "2026-07-17", "2026-08-16", 0, "overdue_60"),
    (ISSUER_A, "INV-1007", "2026-07-16", "2026-08-15", 0, "overdue_61"),
    (ISSUER_A, "INV-1008", "2026-06-17", "2026-07-17", 0, "overdue_90"),
    (ISSUER_A, "INV-1009", "2026-06-16", "2026-07-16", 0, "overdue_91"),
]


def build_records():
    """Return the full list of CSV rows (each row a list of strings, or [])."""
    rng = random.Random(SEED)
    records = []
    amounts = {}

    # 1..9: valid rows covering every aging boundary; amounts are seeded.
    for issuer, invoice_id, issue, due, paid, _label in _BOUNDARY_ROWS:
        amount = rng.randint(1000, 500000)
        amounts[invoice_id] = str(amount)
        records.append([issuer, invoice_id, issue, due, str(amount), CURRENCY, str(paid)])

    # 10..11: partial-payment rows for the v2a payment story.
    # INV-1010: outstanding remainder, 30 days overdue.
    records.append([ISSUER_A, "INV-1010", "2026-09-15", "2026-09-15", "100000", CURRENCY, "40000"])
    # INV-1011: fully paid, zero balance (must be excluded from outstanding sums).
    records.append([ISSUER_A, "INV-1011", "2026-08-15", "2026-08-15", "50000", CURRENCY, "50000"])

    # 12..14: cross-issuer rows, tiny remainders, future due date.
    records.append([ISSUER_B, "INV-1012", "2026-07-16", "2026-07-16", "200000", CURRENCY, "199999"])
    future_amount = rng.randint(1000, 99999)
    records.append([ISSUER_B, "INV-1013", "2026-09-20", "2026-11-01", str(future_amount), CURRENCY, "0"])
    records.append([ISSUER_B, "INV-1014", "2026-09-14", "2026-09-14", "1", CURRENCY, "0"])

    # 15..16: identical duplicates (exact same key and content) -> no-op.
    records.append([ISSUER_A, "INV-1004", "2026-08-16", "2026-09-15", amounts["INV-1004"], CURRENCY, "0"])
    records.append([ISSUER_A, "INV-1002", "2026-09-15", "2026-10-15", amounts["INV-1002"], CURRENCY, "0"])

    # 17..18: inconsistent duplicates (same key, different content) -> flagged.
    records.append(
        [ISSUER_A, "INV-1003", "2026-09-14", "2026-10-14", str(int(amounts["INV-1003"]) + 1), CURRENCY, "0"]
    )
    records.append([ISSUER_A, "INV-1005", "2026-08-15", "2026-09-13", amounts["INV-1005"], CURRENCY, "0"])

    # 19..28: rejected rows.
    records.append([ISSUER_A, "INV-9001", "2026-09-01", "2026-10-01", "abc", CURRENCY, "0"])
    records.append([ISSUER_A, "INV-9002", "2026-09-01", "2026-10-01", "-500", CURRENCY, "0"])
    records.append([ISSUER_A, "INV-9003", "2026-09-01", "2026-10-01", "12.50", CURRENCY, "0"])
    records.append([ISSUER_A, "INV-9004", "2026-13-40", "2026-10-01", "10000", CURRENCY, "0"])
    records.append([ISSUER_A, "INV-9005", "not-a-date", "2026-10-01", "10000", CURRENCY, "0"])
    records.append([ISSUER_A, "INV-9006", "10/15/2026", "2026-10-01", "10000", CURRENCY, "0"])
    records.append([ISSUER_A, "", "2026-09-01", "2026-10-01", "10000", CURRENCY, "0"])
    records.append([ISSUER_A, "INV-9007", "2026-09-01", "2026-10-01", "10000", "EUR", "0"])
    records.append([ISSUER_A, "INV-9008", "2026-09-01", "2026-10-01", "10000", CURRENCY, "15000"])
    records.append([ISSUER_A, "INV-9009", "2026-09-01", "2026-10-01", "10000", CURRENCY, "-100"])

    # 29..30: empty rows.
    records.append([])
    records.append([])

    return records


def render_csv(path=DEFAULT_OUT, records=None):
    """Write records to `path` with a stable line terminator. Returns the path."""
    if records is None:
        records = build_records()
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        for row in records:
            writer.writerow(row)
    return path


def main(argv=None):
    import sys

    argv = sys.argv[1:] if argv is None else argv
    out = argv[0] if argv else DEFAULT_OUT
    records = build_records()
    render_csv(out, records)
    print(f"wrote {len(records)} rows (seed={SEED}, as_of={AS_OF}) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
