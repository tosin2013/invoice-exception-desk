"""Stage 1 queue contract; independent of annotation persistence."""

from copy import deepcopy
from datetime import date, timedelta
from itertools import permutations
from pathlib import Path

import pytest

from invoice_desk import (
    BUCKET_PRIORITY,
    accepted_invoice_identities,
    build_followup_queue,
    import_invoices,
)

AS_OF = date(2026, 10, 15)
ROOT = Path(__file__).resolve().parents[1]
HEADER = "issuer,invoice_id,issue_date,due_date,amount_cents,currency,paid_cents"


def frozen_result():
    return import_invoices((ROOT / "data/invoices.csv").read_text(encoding="utf-8"), AS_OF)


def imported(*rows):
    return import_invoices("\n".join([HEADER, *rows]), AS_OF)


def invoice(issuer, invoice_id, balance=100, overdue=1, paid=0):
    due = AS_OF - timedelta(days=overdue)
    return f"{issuer},{invoice_id},2026-01-01,{due},{balance + paid},USD,{paid}"


def identities(queue):
    return [(item["issuer"], item["invoice_id"]) for item in queue]


def test_frozen_sc002_order():
    assert [item["invoice_id"] for item in build_followup_queue(frozen_result())] == [
        "INV-1009", "INV-1012", "INV-1008", "INV-1007", "INV-1005",
        "INV-1006", "INV-1014", "INV-1004", "INV-1003", "INV-1010",
        "INV-1001", "INV-1002", "INV-1013", "INV-1011",
    ]


def test_repeated_calls_and_reversed_input_are_identical():
    result = frozen_result()
    first = build_followup_queue(result)
    assert first == build_followup_queue(result)
    assert identities(first) == identities(build_followup_queue(result))
    result["rows"].reverse()
    assert build_followup_queue(result) == first


def test_bucket_priority_and_precedence():
    assert BUCKET_PRIORITY == {
        "91+": 0, "61-90": 1, "31-60": 2, "1-30": 3, "current": 4, "paid": 5,
    }
    result = imported(
        invoice("A", "paid", 0, 120, 900),
        invoice("A", "current", 900, 0),
        invoice("A", "recent", 800, 1),
        invoice("A", "middle", 700, 31),
        invoice("A", "old", 600, 61),
        invoice("A", "oldest", 500, 91),
    )
    assert [item["aging_bucket"] for item in build_followup_queue(result)] == [
        "91+", "61-90", "31-60", "1-30", "current", "paid",
    ]


@pytest.mark.parametrize("overdue", [0, 1, 31, 61, 91])
def test_balance_descends_before_identifier_or_days(overdue):
    result = imported(
        invoice("A", "A", 1, overdue),
        invoice("A", "Z", 10**20 + 1, overdue),
        invoice("A", "Y", 10**20, overdue),
    )
    assert [item["invoice_id"] for item in build_followup_queue(result)] == ["Z", "Y", "A"]


def test_invoice_id_precedes_issuer_and_days_within_bucket():
    rows = [invoice("A", "z", overdue=30), invoice("Z", "A", overdue=1),
            invoice("B", "a", overdue=20)]
    for ordering in permutations(rows):
        assert identities(build_followup_queue(imported(*ordering))) == [
            ("Z", "A"), ("B", "a"), ("A", "z"),
        ]


def test_shared_identifier_uses_case_sensitive_unicode_issuer_last():
    rows = [invoice(name, "same") for name in ["é", "a", "Z", "A"]]
    for ordering in permutations(rows):
        queue = build_followup_queue(imported(*ordering))
        assert identities(queue) == [(name, "same") for name in ["A", "Z", "a", "é"]]
        assert len(set(identities(queue))) == 4


def test_paid_invoice_is_present_exactly_once_and_last():
    queue = build_followup_queue(frozen_result())
    paid = [item for item in queue if item["invoice_id"] == "INV-1011"]
    assert len(paid) == 1
    assert paid[0] == queue[-1]
    assert paid[0]["remaining_balance_cents"] == 0
    assert paid[0]["aging_bucket"] == "paid"


@pytest.mark.parametrize("result", [
    {"rows": [], "totals": {}},
    {"rows": [{"status": status} for status in [
        "rejected", "duplicate_identical", "duplicate_inconsistent",
    ]], "totals": {}},
])
def test_empty_accepted_set(result):
    assert build_followup_queue(result) == []
    assert accepted_invoice_identities(result) == set()


def test_exact_membership_shape_types_positions_and_identity_helper():
    result = frozen_result()
    accepted = [row for row in result["rows"] if row["status"] == "accepted"]
    expected = {(row["issuer"], row["invoice_id"]) for row in accepted}
    queue = build_followup_queue(result)
    assert accepted_invoice_identities(result) == expected
    assert set(identities(queue)) == expected
    assert len(queue) == len(accepted) == 14
    assert [item["position"] for item in queue] == list(range(1, 15))
    by_identity = {(row["issuer"], row["invoice_id"]): row for row in accepted}
    for item in queue:
        assert set(item) == {"issuer", "invoice_id", "remaining_balance_cents",
                             "days_overdue", "aging_bucket", "owner", "notes", "position"}
        assert item["owner"] is None and item["notes"] is None
        assert type(item["position"]) is int
        for field in ["remaining_balance_cents", "days_overdue"]:
            assert type(item[field]) is int and item[field] >= 0
        assert item["aging_bucket"] in BUCKET_PRIORITY
        original = by_identity[(item["issuer"], item["invoice_id"])]
        for field in ["remaining_balance_cents", "days_overdue", "aging_bucket"]:
            assert item[field] == original[field]


def test_no_input_mutation_and_fresh_output_objects():
    result = frozen_result()
    before = deepcopy(result)
    queue = build_followup_queue(result)
    accepted_invoice_identities(result)
    assert result == before
    another = build_followup_queue(result)
    assert queue is not another
    for left, right in zip(queue, another):
        assert left is not right
        assert all(left is not row for row in result["rows"])
    queue[0]["issuer"] = "changed"
    assert result == before
    assert another == build_followup_queue(result)


def test_ordering_has_no_filesystem_or_annotation_dependency(monkeypatch):
    import builtins
    import invoice_desk.queue as queue_module

    result = frozen_result()
    expected = build_followup_queue(result)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        assert "annotations" not in name
        return original_import(name, *args, **kwargs)

    def forbidden_io(*args, **kwargs):
        raise AssertionError("queue must not perform file I/O")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(builtins, "open", forbidden_io)
    monkeypatch.setattr(Path, "open", forbidden_io)
    assert queue_module.build_followup_queue(result) == expected
    assert queue_module.accepted_invoice_identities(result) == set(identities(expected))
