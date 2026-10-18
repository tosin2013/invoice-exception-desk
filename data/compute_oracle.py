#!/usr/bin/env python3
"""Independently compute the expected import result for every row (R0).

This script re-implements the import policy from scratch; it does NOT import the
generator. It reads data/invoices.csv and writes data/oracle.json so the app
build (R1) and the acceptance tests can be checked against a frozen expectation.

Policy implemented (see SPEC.md):
  * currency is USD; amounts are integer cents; no negative/overpayment
  * identity key = issuer + invoice_id
  * identical duplicate key+content -> no-op; inconsistent duplicate -> flagged
  * as_of = 2026-10-15 (America/New_York)
  * overdue = balance > 0 AND due_date < as_of
  * aging buckets: current, 1-30, 31-60, 61-90, 91+, paid (zero balance)

Usage:
    python3 data/compute_oracle.py [invoices.csv] [oracle.json]
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "invoices.csv")
DEFAULT_OUT = os.path.join(HERE, "oracle.json")

AS_OF = date(2026, 10, 15)
TIMEZONE = "America/New_York"
CURRENCY = "USD"
SEED = 20261015

BUCKETS = ["current", "1-30", "31-60", "61-90", "91+", "paid"]

REJECT_REASONS = [
    "empty_row",
    "missing_required_field",
    "invalid_amount",
    "invalid_date",
    "invalid_currency",
    "invalid_payment",
]


def aging_bucket(remaining_cents, due, as_of=AS_OF):
    if remaining_cents <= 0:
        return "paid"
    if due >= as_of:
        return "current"
    days = (as_of - due).days
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "91+"


def days_overdue(remaining_cents, due, as_of=AS_OF):
    if remaining_cents <= 0 or due >= as_of:
        return 0
    return (as_of - due).days


def _rejected(row_number, reason):
    return {
        "row": row_number,
        "status": "rejected",
        "reason": reason,
        "remaining_balance_cents": None,
        "days_overdue": None,
        "aging_bucket": None,
    }


def classify(header, rows, as_of=AS_OF):
    """Return (row_results, totals) for the given header/rows."""
    idx = {name: i for i, name in enumerate(header)}
    results = []
    seen = {}  # (issuer, invoice_id) -> canonical content tuple

    for n, raw in enumerate(rows, start=1):
        if len(raw) == 0 or all((cell or "").strip() == "" for cell in raw):
            results.append(_rejected(n, "empty_row"))
            continue

        vals = list(raw) + [""] * (len(header) - len(raw))

        issuer = vals[idx["issuer"]].strip()
        invoice_id = vals[idx["invoice_id"]].strip()
        if not issuer or not invoice_id:
            results.append(_rejected(n, "missing_required_field"))
            continue

        amount_raw = vals[idx["amount_cents"]].strip()
        try:
            amount_cents = int(amount_raw)
        except ValueError:
            results.append(_rejected(n, "invalid_amount"))
            continue
        if amount_cents <= 0 or str(amount_cents) != amount_raw:
            results.append(_rejected(n, "invalid_amount"))
            continue

        try:
            issue_date = date.fromisoformat(vals[idx["issue_date"]].strip())
            due_date = date.fromisoformat(vals[idx["due_date"]].strip())
        except ValueError:
            results.append(_rejected(n, "invalid_date"))
            continue

        if vals[idx["currency"]].strip().upper() != CURRENCY:
            results.append(_rejected(n, "invalid_currency"))
            continue

        paid_raw = vals[idx["paid_cents"]].strip() or "0"
        try:
            paid_cents = int(paid_raw)
        except ValueError:
            results.append(_rejected(n, "invalid_payment"))
            continue
        if paid_cents < 0 or paid_cents > amount_cents:
            results.append(_rejected(n, "invalid_payment"))
            continue

        canonical = (
            issuer,
            invoice_id,
            issue_date.isoformat(),
            due_date.isoformat(),
            amount_cents,
            CURRENCY,
            paid_cents,
        )
        key = (issuer, invoice_id)

        if key in seen:
            if seen[key] == canonical:
                status, reason = "duplicate_identical", "identical_duplicate"
            else:
                status, reason = "duplicate_inconsistent", "inconsistent_duplicate"
            results.append(
                {
                    "row": n,
                    "status": status,
                    "reason": reason,
                    "remaining_balance_cents": None,
                    "days_overdue": None,
                    "aging_bucket": None,
                }
            )
            continue

        seen[key] = canonical
        remaining = amount_cents - paid_cents
        results.append(
            {
                "row": n,
                "status": "accepted",
                "reason": None,
                "issuer": issuer,
                "invoice_id": invoice_id,
                "amount_cents": amount_cents,
                "paid_cents": paid_cents,
                "remaining_balance_cents": remaining,
                "days_overdue": days_overdue(remaining, due_date, as_of),
                "aging_bucket": aging_bucket(remaining, due_date, as_of),
            }
        )

    totals = _totals(results)
    return results, totals


def _totals(results):
    accepted = [r for r in results if r["status"] == "accepted"]
    outstanding = [r for r in accepted if r["remaining_balance_cents"] > 0]

    aging = {b: {"count": 0, "remaining_cents": 0} for b in BUCKETS}
    for r in accepted:
        bucket = aging[r["aging_bucket"]]
        bucket["count"] += 1
        bucket["remaining_cents"] += r["remaining_balance_cents"]

    return {
        "total_rows": len(results),
        "accepted": sum(1 for r in results if r["status"] == "accepted"),
        "rejected": sum(1 for r in results if r["status"] == "rejected"),
        "duplicate_identical": sum(1 for r in results if r["status"] == "duplicate_identical"),
        "duplicate_inconsistent": sum(1 for r in results if r["status"] == "duplicate_inconsistent"),
        "outstanding_invoice_count": len(outstanding),
        "total_outstanding_cents": sum(r["remaining_balance_cents"] for r in outstanding),
        "total_paid_cents": sum(r["paid_cents"] for r in accepted),
        "aging": aging,
    }


def build_oracle(csv_path=DEFAULT_CSV):
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = list(reader)
    results, totals = classify(header, rows)
    return {
        "as_of": AS_OF.isoformat(),
        "timezone": TIMEZONE,
        "currency": CURRENCY,
        "seed": SEED,
        "policy": {
            "key": "issuer+invoice_id",
            "overdue": "balance > 0 AND due_date < as_of",
            "identical_duplicate": "no-op",
            "inconsistent_duplicate": "flagged",
            "buckets": BUCKETS,
            "reject_reasons": REJECT_REASONS,
        },
        "row_count": len(results),
        "rows": results,
        "totals": totals,
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    csv_path = argv[0] if len(argv) > 0 else DEFAULT_CSV
    out = argv[1] if len(argv) > 1 else DEFAULT_OUT
    oracle = build_oracle(csv_path)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(oracle, handle, indent=2, sort_keys=False)
        handle.write("\n")
    totals = oracle["totals"]
    print(
        "oracle: rows={total_rows} accepted={accepted} rejected={rejected} "
        "dup_identical={duplicate_identical} dup_inconsistent={duplicate_inconsistent} "
        "outstanding_cents={total_outstanding_cents} -> {out}".format(out=out, **totals)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
