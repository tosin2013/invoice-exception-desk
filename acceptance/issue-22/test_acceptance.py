"""L7 acceptance checks for issue <N>: accepted rows expose `overdue` (003 FR-033).

Self-contained: no conftest, no fixtures, and no helpers from tests/. Each test
matches the acceptance check with the same number in the issue and uses its exact rows.
Run from the repo root:
    pytest acceptance -q --noconftest --import-mode=importlib
"""

import json
from datetime import date
from pathlib import Path

from invoice_desk import import_invoices
from invoice_desk.queue import build_followup_queue

AS_OF = date(2026, 10, 15)
HEADER = "issuer,invoice_id,issue_date,due_date,amount_cents,currency,paid_cents"
_HERE = Path(__file__).resolve()
ROOT = next(
    p for p in (*_HERE.parents, Path.cwd()) if (p / "data" / "invoices.csv").is_file()
)

FR032_ACCEPTED_KEYS = {
    "row", "status", "reason", "issuer", "invoice_id", "issue_date", "due_date",
    "amount_cents", "currency", "paid_cents", "remaining_balance_cents",
    "days_overdue", "aging_bucket",
}
NON_ACCEPTED_KEYS = {
    "row", "status", "reason", "remaining_balance_cents", "days_overdue", "aging_bucket",
}


def frozen():
    text = (ROOT / "data" / "invoices.csv").read_text(encoding="utf-8")
    return import_invoices(text, AS_OF)


def one_row(line):
    rows = import_invoices(HEADER + "\n" + line, AS_OF)["rows"]
    assert len(rows) == 1 and rows[0]["status"] == "accepted"
    return rows[0]


def accepted_by_id(result):
    return {r["invoice_id"]: r for r in result["rows"] if r["status"] == "accepted"}


# Check 1: frozen CSV at 2026-10-15
def test_1_frozen_overdue_flags():
    rows = accepted_by_id(frozen())
    overdue_true = {
        "INV-1003", "INV-1004", "INV-1005", "INV-1006", "INV-1007",
        "INV-1008", "INV-1009", "INV-1010", "INV-1012", "INV-1014",
    }
    overdue_false = {"INV-1001", "INV-1002", "INV-1011", "INV-1013"}
    assert set(rows) == overdue_true | overdue_false
    for invoice_id in overdue_true:
        assert rows[invoice_id]["overdue"] is True, invoice_id
    for invoice_id in overdue_false:
        assert rows[invoice_id]["overdue"] is False, invoice_id


# Check 2: due today is not overdue
def test_2_due_today_not_overdue():
    row = one_row("Acme,INV-T0,2026-09-01,2026-10-15,1000,USD,0")
    assert row["overdue"] is False
    assert row["days_overdue"] == 0
    assert row["aging_bucket"] == "current"


# Check 3: due yesterday is overdue
def test_3_due_yesterday_overdue():
    row = one_row("Acme,INV-T1,2026-09-01,2026-10-14,1000,USD,0")
    assert row["overdue"] is True
    assert row["days_overdue"] == 1
    assert row["aging_bucket"] == "1-30"


# Check 4: fully paid but long past due; a one-cent balance
def test_4_fully_paid_and_one_cent():
    paid = one_row("Acme,INV-P1,2026-06-01,2026-07-01,100,USD,100")
    assert paid["overdue"] is False
    assert paid["days_overdue"] == 0
    assert paid["aging_bucket"] == "paid"

    cent = one_row("Acme,INV-C1,2026-09-01,2026-10-14,100,USD,99")
    assert cent["remaining_balance_cents"] == 1
    assert cent["overdue"] is True
    assert cent["days_overdue"] == 1
    assert cent["aging_bucket"] == "1-30"


# Check 5: exact key sets, None on rejected and duplicate rows
def test_5_exact_key_sets():
    rows = frozen()["rows"]
    assert len(rows) == 30
    for row in rows[:14]:
        assert row["status"] == "accepted"
        assert set(row) == FR032_ACCEPTED_KEYS | {"overdue"}
        assert type(row["overdue"]) is bool
    for row in rows[14:18]:
        assert row["status"].startswith("duplicate_")
        assert set(row) == NON_ACCEPTED_KEYS | {"overdue"}
        assert row["overdue"] is None
    for row in rows[18:30]:
        assert row["status"] == "rejected"
        assert set(row) == NON_ACCEPTED_KEYS | {"overdue"}
        assert row["overdue"] is None


# Check 6: overdue is exactly days_overdue > 0 on accepted rows
def test_6_overdue_matches_days_overdue():
    for row in frozen()["rows"]:
        if row["status"] == "accepted":
            assert row["overdue"] == (row["days_overdue"] > 0), row["invoice_id"]


# Check 7: JSON-serialisable and deterministic
def test_7_json_and_determinism():
    first, second = frozen(), frozen()
    assert first == second
    assert json.dumps(first) == json.dumps(second)
    decoded = json.loads(json.dumps(first))
    assert [r["overdue"] for r in decoded["rows"]] == [r["overdue"] for r in first["rows"]]


# Check 8: totals (with the aging table), queue order and queue item keys unchanged
def test_8_totals_aging_and_queue_unchanged():
    result = frozen()
    assert result["totals"] == {
        "total_rows": 30,
        "accepted": 14,
        "rejected": 12,
        "duplicate_identical": 2,
        "duplicate_inconsistent": 2,
        "outstanding_invoice_count": 13,
        "total_outstanding_cents": 2139435,
        "total_paid_cents": 289999,
        "aging": {
            "current": {"count": 3, "remaining_cents": 597047},
            "1-30": {"count": 3, "remaining_cents": 396862},
            "31-60": {"count": 3, "remaining_cents": 259664},
            "61-90": {"count": 2, "remaining_cents": 863731},
            "91+": {"count": 2, "remaining_cents": 22131},
            "paid": {"count": 1, "remaining_cents": 0},
        },
    }
    queue = build_followup_queue(result)
    assert [item["invoice_id"] for item in queue] == [
        "INV-1009", "INV-1012", "INV-1008", "INV-1007", "INV-1005", "INV-1006",
        "INV-1014", "INV-1004", "INV-1003", "INV-1010", "INV-1001", "INV-1002",
        "INV-1013", "INV-1011",
    ]
    for item in queue:
        assert set(item) == {
            "issuer", "invoice_id", "remaining_balance_cents", "days_overdue",
            "aging_bucket", "owner", "notes", "position",
        }
