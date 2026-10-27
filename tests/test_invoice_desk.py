from datetime import date, timedelta

import pytest

from invoice_desk import import_invoices

CSV_PATH = "data/invoices.csv"
AS_OF = date(2026, 10, 15)
BUCKETS = ("current", "1-30", "31-60", "61-90", "91+", "paid")
HEADER = (
    "issuer",
    "invoice_id",
    "issue_date",
    "due_date",
    "amount_cents",
    "currency",
    "paid_cents",
)


def frozen_csv_text():
    with open(CSV_PATH, encoding="utf-8") as handle:
        return handle.read()


def make_csv(*rows):
    return "\n".join([",".join(HEADER), *rows])


def zero_totals():
    return {
        "total_rows": 0,
        "accepted": 0,
        "rejected": 0,
        "duplicate_identical": 0,
        "duplicate_inconsistent": 0,
        "outstanding_invoice_count": 0,
        "total_outstanding_cents": 0,
        "total_paid_cents": 0,
        "aging": {bucket: {"count": 0, "remaining_cents": 0} for bucket in BUCKETS},
    }


def frozen_result():
    return import_invoices(frozen_csv_text(), AS_OF)


def accepted_by_id(result):
    return {
        row["invoice_id"]: row
        for row in result["rows"]
        if row["status"] == "accepted"
    }


def due_before(days):
    return (AS_OF - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# User Story 1 -- import and classify every invoice row (AT-01, AT-02)
# ---------------------------------------------------------------------------


def test_frozen_import_counts():
    result = frozen_result()

    assert len(result["rows"]) == 30
    assert result["totals"]["total_rows"] == 30
    assert result["totals"]["accepted"] == 14
    assert result["totals"]["rejected"] == 12
    assert result["totals"]["duplicate_identical"] == 2
    assert result["totals"]["duplicate_inconsistent"] == 2
    assert (
        result["totals"]["accepted"]
        + result["totals"]["rejected"]
        + result["totals"]["duplicate_identical"]
        + result["totals"]["duplicate_inconsistent"]
        == 30
    )


def test_frozen_row_statuses_and_numbers():
    result = frozen_result()

    assert [row["row"] for row in result["rows"]] == list(range(1, 31))
    expected = (
        ["accepted"] * 14
        + ["duplicate_identical"] * 2
        + ["duplicate_inconsistent"] * 2
        + ["rejected"] * 12
    )
    assert [row["status"] for row in result["rows"]] == expected


def test_frozen_rejection_reasons():
    result = frozen_result()
    expected = {
        19: "invalid_amount",
        20: "invalid_amount",
        21: "invalid_amount",
        22: "invalid_date",
        23: "invalid_date",
        24: "invalid_date",
        25: "missing_required_field",
        26: "invalid_currency",
        27: "invalid_payment",
        28: "invalid_payment",
        29: "empty_row",
        30: "empty_row",
    }
    for row_number, reason in expected.items():
        row = result["rows"][row_number - 1]
        assert row["row"] == row_number
        assert row["status"] == "rejected"
        assert row["reason"] == reason


def test_frozen_duplicate_reasons():
    rows = frozen_result()["rows"]

    assert rows[14]["status"] == "duplicate_identical"
    assert rows[14]["reason"] == "identical_duplicate"
    assert rows[15]["status"] == "duplicate_identical"
    assert rows[15]["reason"] == "identical_duplicate"
    assert rows[16]["status"] == "duplicate_inconsistent"
    assert rows[16]["reason"] == "inconsistent_duplicate"
    assert rows[17]["status"] == "duplicate_inconsistent"
    assert rows[17]["reason"] == "inconsistent_duplicate"


def test_duplicates_never_alter_the_first_accepted_record():
    result = frozen_result()
    invoices = accepted_by_id(result)

    assert len(invoices) == 14
    assert invoices["INV-1003"]["amount_cents"] == 105038
    assert invoices["INV-1005"]["amount_cents"] == 253172
    assert invoices["INV-1005"]["remaining_balance_cents"] == 253172


def test_rejected_and_duplicate_rows_expose_no_accepted_fields():
    result = frozen_result()

    for row in result["rows"]:
        if row["status"] == "accepted":
            continue
        assert "issuer" not in row
        assert "invoice_id" not in row
        assert "amount_cents" not in row
        assert "paid_cents" not in row
        assert row["remaining_balance_cents"] is None
        assert row["days_overdue"] is None
        assert row["aging_bucket"] is None


def test_accepted_rows_expose_normalized_fields():
    result = frozen_result()

    for row in result["rows"]:
        if row["status"] != "accepted":
            continue
        assert isinstance(row["issuer"], str) and row["issuer"]
        assert isinstance(row["invoice_id"], str) and row["invoice_id"]
        assert type(row["amount_cents"]) is int
        assert type(row["paid_cents"]) is int
        assert 0 <= row["paid_cents"] <= row["amount_cents"]


def test_second_import_is_identical_and_has_no_state():
    first = frozen_result()
    second = frozen_result()

    assert first == second


def test_empty_input_returns_zero_rows_and_zero_totals():
    result = import_invoices("", AS_OF)

    assert result == {"rows": [], "totals": zero_totals()}


def test_header_only_input_returns_zero_rows_and_zero_totals():
    result = import_invoices(",".join(HEADER), AS_OF)

    assert result == {"rows": [], "totals": zero_totals()}


def test_header_mapping_trims_whitespace_and_follows_names():
    text = "\n".join(
        [
            "paid_cents, currency ,amount_cents,due_date,issue_date,invoice_id,issuer",
            " 0 , USD , 1000 , 2026-10-01 , 2026-09-01 , INV-H1 , Acme ",
        ]
    )

    result = import_invoices(text, AS_OF)
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["issuer"] == "Acme"
    assert row["invoice_id"] == "INV-H1"
    assert row["amount_cents"] == 1000
    assert row["paid_cents"] == 0
    assert row["remaining_balance_cents"] == 1000
    assert row["days_overdue"] == 14
    assert row["aging_bucket"] == "1-30"


def test_whitespace_is_trimmed_before_duplicate_comparison():
    text = make_csv(
        " Acme , INV-W1 , 2026-09-01 , 2026-10-01 , 1000 , USD , 0 ",
        "Acme,INV-W1,2026-09-01,2026-10-01,1000,USD,0",
    )

    rows = import_invoices(text, AS_OF)["rows"]

    assert rows[0]["status"] == "accepted"
    assert rows[1]["status"] == "duplicate_identical"


def test_blank_lines_are_preserved_as_empty_rows():
    text = "\n".join(
        [
            ",".join(HEADER),
            "Acme,INV-E1,2026-09-01,2026-10-01,1000,USD,0",
            "",
            "   ,   ,   ,   ,   ,   ,   ",
            "Acme,INV-E2,2026-09-01,2026-10-01,1000,USD,0",
        ]
    )

    result = import_invoices(text, AS_OF)

    assert result["totals"]["total_rows"] == 4
    assert [row["status"] for row in result["rows"]] == [
        "accepted",
        "rejected",
        "rejected",
        "accepted",
    ]
    assert result["rows"][1]["reason"] == "empty_row"
    assert result["rows"][2]["reason"] == "empty_row"


def test_short_rows_are_padded_with_blanks():
    result = import_invoices(
        make_csv(
            "Acme,INV-S1,2026-09-01,2026-10-01,1000,USD",
            "Acme,INV-S2,2026-09-01,2026-10-01,1000",
            "Acme,INV-S3,2026-09-01,2026-10-01",
            "Acme",
        ),
        AS_OF,
    )
    rows = result["rows"]

    assert rows[0]["status"] == "accepted"
    assert rows[0]["paid_cents"] == 0
    assert rows[1]["reason"] == "invalid_currency"
    assert rows[2]["reason"] == "invalid_amount"
    assert rows[3]["reason"] == "missing_required_field"


def test_cells_beyond_the_seventh_are_ignored():
    result = import_invoices(
        make_csv("Acme,INV-X1,2026-09-01,2026-10-01,1000,USD,0,ignored,more"),
        AS_OF,
    )
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["amount_cents"] == 1000
    assert row["paid_cents"] == 0


def test_same_invoice_id_from_a_different_issuer_is_not_a_duplicate():
    result = import_invoices(
        make_csv(
            "Acme,INV-C1,2026-09-01,2026-10-01,1000,USD,0",
            "Other,INV-C1,2026-09-01,2026-10-01,1000,USD,0",
        ),
        AS_OF,
    )

    assert result["totals"]["accepted"] == 2
    assert result["totals"]["duplicate_identical"] == 0
    assert result["totals"]["duplicate_inconsistent"] == 0


def test_zero_amount_is_rejected_as_invalid_amount():
    result = import_invoices(
        make_csv("Acme,INV-Z1,2026-09-01,2026-09-01,0,USD,"),
        AS_OF,
    )
    row = result["rows"][0]

    assert row["status"] == "rejected"
    assert row["reason"] == "invalid_amount"
    assert "issuer" not in row
    assert "invoice_id" not in row
    assert "amount_cents" not in row
    assert "paid_cents" not in row
    assert row["remaining_balance_cents"] is None
    assert row["days_overdue"] is None
    assert row["aging_bucket"] is None
    assert result["totals"]["accepted"] == 0
    assert result["totals"]["rejected"] == 1
    assert result["totals"]["aging"]["paid"] == {"count": 0, "remaining_cents": 0}


@pytest.mark.parametrize(
    "amount",
    ["1", "100", " 100 "],
)
def test_canonical_positive_amounts_are_accepted(amount):
    text = make_csv(f"Acme,INV-A-{amount.strip()},2026-09-01,2026-10-01,{amount},USD,0")

    result = import_invoices(text, AS_OF)
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["amount_cents"] == int(amount.strip())
    assert row["remaining_balance_cents"] == int(amount.strip())


def test_fully_paid_positive_invoice_stays_accepted_and_paid():
    result = import_invoices(
        make_csv("Acme,INV-FP1,2026-09-01,2026-10-01,100,USD,100"),
        AS_OF,
    )
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["amount_cents"] == 100
    assert row["paid_cents"] == 100
    assert row["remaining_balance_cents"] == 0
    assert row["aging_bucket"] == "paid"


def test_paid_cents_with_leading_zero_is_unchanged():
    result = import_invoices(
        make_csv("Acme,INV-PZ1,2026-09-01,2026-10-01,1000,USD,0100"),
        AS_OF,
    )
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["paid_cents"] == 100
    assert row["remaining_balance_cents"] == 900


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ("Acme,INV-PR1,2026-13-40,2026-10-01,0,USD,0", "invalid_date"),
        ("Acme,INV-PR2,not-a-date,2026-10-01,0,USD,0", "invalid_date"),
        ("Acme,INV-PR3,2026-09-01,2026-10-01,0,EUR,0", "invalid_amount"),
        ("Acme,INV-PR4,2026-09-01,2026-10-01,0,usd,0", "invalid_amount"),
        ("Acme,INV-PR5,2026-09-01,2026-10-01,1000,usd,0", "invalid_currency"),
    ],
)
def test_zero_amount_precedence_and_currency(row, reason):
    result = import_invoices(make_csv(row), AS_OF)

    assert result["rows"][0]["status"] == "rejected"
    assert result["rows"][0]["reason"] == reason
    assert result["totals"]["rejected"] == 1


def test_zero_amount_does_not_take_part_in_duplicate_detection():
    result = import_invoices(
        make_csv(
            "Acme,INV-ZD1,2026-09-01,2026-10-01,0,USD,0",
            "Acme,INV-ZD1,2026-09-01,2026-10-01,1000,USD,0",
        ),
        AS_OF,
    )

    assert result["rows"][0]["status"] == "rejected"
    assert result["rows"][0]["reason"] == "invalid_amount"
    assert result["rows"][1]["status"] == "accepted"
    assert result["rows"][1]["amount_cents"] == 1000
    assert result["totals"]["accepted"] == 1
    assert result["totals"]["rejected"] == 1
    assert result["totals"]["duplicate_identical"] == 0
    assert result["totals"]["duplicate_inconsistent"] == 0


def test_inconsistent_duplicate_does_not_replace_first_record():
    result = import_invoices(
        make_csv(
            "Acme,INV-D1,2026-09-01,2026-10-01,1000,USD,0",
            "Acme,INV-D1,2026-09-02,2026-10-01,2000,USD,0",
        ),
        AS_OF,
    )

    assert result["rows"][0]["status"] == "accepted"
    assert result["rows"][0]["amount_cents"] == 1000
    assert result["rows"][1]["status"] == "duplicate_inconsistent"
    assert "amount_cents" not in result["rows"][1]
    assert result["totals"]["accepted"] == 1
    assert result["totals"]["duplicate_inconsistent"] == 1


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ("Acme,INV-V1,2026-09-01,2026-10-01,+100,USD,0", "invalid_amount"),
        ("Acme,INV-V2,2026-09-01,2026-10-01,abc,USD,0", "invalid_amount"),
        ("Acme,INV-V3,2026-09-01,2026-10-01,12.50,USD,0", "invalid_amount"),
        ("Acme,INV-V4,2026-09-01,2026-10-01,-500,USD,0", "invalid_amount"),
        ("Acme,INV-V5,2026-09-01,2026-10-01,,USD,0", "invalid_amount"),
        ("Acme,INV-V22,2026-09-01,2026-10-01,0,USD,0", "invalid_amount"),
        ("Acme,INV-V23,2026-09-01,2026-10-01,00,USD,0", "invalid_amount"),
        ("Acme,INV-V24,2026-09-01,2026-10-01,0100,USD,0", "invalid_amount"),
        ("Acme,INV-V25,2026-09-01,2026-10-01, 0100 ,USD,0", "invalid_amount"),
        ("Acme,INV-V6,2026-13-40,2026-10-01,1000,USD,0", "invalid_date"),
        ("Acme,INV-V7,not-a-date,2026-10-01,1000,USD,0", "invalid_date"),
        ("Acme,INV-V8,10/15/2026,2026-10-01,1000,USD,0", "invalid_date"),
        ("Acme,INV-V9,2026-09-01,,1000,USD,0", "invalid_date"),
        ("Acme,,2026-09-01,2026-10-01,1000,USD,0", "missing_required_field"),
        (",INV-V11,2026-09-01,2026-10-01,1000,USD,0", "missing_required_field"),
        (",INV-V12,2026-09-01,2026-10-01,abc,USD,0", "missing_required_field"),
        ("Acme,INV-V13,,2026-10-01,abc,USD,0", "invalid_date"),
        ("Acme,INV-V14,2026-09-01,2026-10-01,abc,EUR,0", "invalid_amount"),
        ("Acme,INV-V15,2026-09-01,2026-10-01,1000,EUR,15000", "invalid_currency"),
        ("Acme,INV-V16,2026-09-01,2026-10-01,1000,usd,0", "invalid_currency"),
        ("Acme,INV-V17,2026-09-01,2026-10-01,1000, EUR ,0", "invalid_currency"),
        ("Acme,INV-V18,2026-09-01,2026-10-01,1000,USD,-1", "invalid_payment"),
        ("Acme,INV-V19,2026-09-01,2026-10-01,1000,USD,1.5", "invalid_payment"),
        ("Acme,INV-V20,2026-09-01,2026-10-01,1000,USD,abc", "invalid_payment"),
        ("Acme,INV-V21,2026-09-01,2026-10-01,1000,USD,2000", "invalid_payment"),
    ],
)
def test_validation_reasons_and_precedence(row, reason):
    result = import_invoices(make_csv(row), AS_OF)

    assert result["rows"][0]["status"] == "rejected"
    assert result["rows"][0]["reason"] == reason
    assert result["totals"]["rejected"] == 1


def test_blank_paid_cents_means_zero():
    result = import_invoices(
        make_csv("Acme,INV-P1,2026-09-01,2026-10-01,1000,USD,"),
        AS_OF,
    )
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["paid_cents"] == 0
    assert row["remaining_balance_cents"] == 1000


# ---------------------------------------------------------------------------
# User Story 2 -- exact outstanding amount (AT-03)
# ---------------------------------------------------------------------------


def test_remaining_balance_is_amount_minus_paid_for_every_accepted_row():
    for row in frozen_result()["rows"]:
        if row["status"] != "accepted":
            continue
        assert row["remaining_balance_cents"] == (
            row["amount_cents"] - row["paid_cents"]
        )
        assert type(row["remaining_balance_cents"]) is int
        assert row["remaining_balance_cents"] >= 0


def test_frozen_outstanding_and_paid_totals():
    totals = frozen_result()["totals"]

    assert totals["outstanding_invoice_count"] == 13
    assert totals["total_outstanding_cents"] == 2139435
    assert totals["total_paid_cents"] == 289999


def test_fully_paid_invoice_is_excluded_from_outstanding():
    result = frozen_result()
    invoice = accepted_by_id(result)["INV-1011"]

    assert invoice["amount_cents"] == 50000
    assert invoice["paid_cents"] == 50000
    assert invoice["remaining_balance_cents"] == 0
    assert result["totals"]["aging"]["paid"] == {"count": 1, "remaining_cents": 0}


def test_non_accepted_rows_have_no_remaining_balance():
    for row in frozen_result()["rows"]:
        if row["status"] != "accepted":
            assert row["remaining_balance_cents"] is None


def test_all_reported_money_values_are_integers():
    result = frozen_result()
    totals = result["totals"]

    for key in (
        "total_outstanding_cents",
        "total_paid_cents",
    ):
        assert type(totals[key]) is int
    for bucket in BUCKETS:
        assert type(totals["aging"][bucket]["remaining_cents"]) is int
    for row in result["rows"]:
        if row["status"] == "accepted":
            assert type(row["remaining_balance_cents"]) is int


# ---------------------------------------------------------------------------
# User Story 3 -- aging against an explicit as-of date (AT-04)
# ---------------------------------------------------------------------------


def test_frozen_days_overdue_and_buckets():
    invoices = accepted_by_id(frozen_result())
    expected = {
        "INV-1001": (0, "current"),
        "INV-1002": (0, "current"),
        "INV-1003": (1, "1-30"),
        "INV-1004": (30, "1-30"),
        "INV-1005": (31, "31-60"),
        "INV-1006": (60, "31-60"),
        "INV-1007": (61, "61-90"),
        "INV-1008": (90, "61-90"),
        "INV-1009": (91, "91+"),
        "INV-1010": (30, "1-30"),
        "INV-1011": (0, "paid"),  # review fix R1: zero balance is never overdue
        "INV-1012": (91, "91+"),
        "INV-1013": (0, "current"),
        "INV-1014": (31, "31-60"),
    }

    for invoice_id, (days, bucket) in expected.items():
        assert invoices[invoice_id]["days_overdue"] == days
        assert invoices[invoice_id]["aging_bucket"] == bucket


def test_aging_bucket_boundaries():
    offsets = (
        (0, "current"),
        (1, "1-30"),
        (30, "1-30"),
        (31, "31-60"),
        (60, "31-60"),
        (61, "61-90"),
        (90, "61-90"),
        (91, "91+"),
        (365, "91+"),
    )
    rows = [
        f"Acme,INV-B{offset},2025-01-01,{due_before(offset)},1000,USD,0"
        for offset, _bucket in offsets
    ]

    result = import_invoices(make_csv(*rows), AS_OF)
    invoices = accepted_by_id(result)

    for offset, bucket in offsets:
        invoice = invoices[f"INV-B{offset}"]
        assert invoice["days_overdue"] == offset
        assert invoice["aging_bucket"] == bucket


def test_due_before_issue_is_invalid_date():
    result = import_invoices(
        make_csv("Acme,INV-D1,2026-09-15,2026-09-14,1000,USD,0"), AS_OF
    )
    row = result["rows"][0]

    assert row["status"] == "rejected"
    assert row["reason"] == "invalid_date"
    assert result["totals"]["accepted"] == 0
    assert result["totals"]["rejected"] == 1


def test_due_before_issue_takes_precedence_over_invalid_amount():
    result = import_invoices(
        make_csv("Acme,INV-D2,2026-09-15,2026-09-14,abc,USD,0"), AS_OF
    )

    assert result["rows"][0]["status"] == "rejected"
    assert result["rows"][0]["reason"] == "invalid_date"


def test_rejected_due_before_issue_does_not_participate_in_duplicates():
    result = import_invoices(
        make_csv(
            "Acme,INV-D3,2026-09-15,2026-09-14,1000,USD,0",
            "Acme,INV-D3,2026-09-15,2026-09-20,1000,USD,0",
        ),
        AS_OF,
    )
    first, second = result["rows"]

    assert first["status"] == "rejected"
    assert first["reason"] == "invalid_date"
    assert second["status"] == "accepted"
    assert result["totals"]["accepted"] == 1
    assert result["totals"]["rejected"] == 1
    assert result["totals"]["duplicate_identical"] == 0
    assert result["totals"]["duplicate_inconsistent"] == 0


def test_equal_issue_and_due_dates_are_accepted():
    result = import_invoices(
        make_csv("Acme,INV-D4,2026-09-15,2026-09-15,1000,USD,0"), AS_OF
    )
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["remaining_balance_cents"] == 1000


def test_due_today_and_future_are_current_with_zero_days():
    rows = [
        f"Acme,INV-TODAY,2026-01-01,{due_before(0)},1000,USD,0",
        f"Acme,INV-FUTURE,2026-01-01,{due_before(-10)},1000,USD,0",
    ]

    invoices = accepted_by_id(import_invoices(make_csv(*rows), AS_OF))

    assert invoices["INV-TODAY"]["days_overdue"] == 0
    assert invoices["INV-TODAY"]["aging_bucket"] == "current"
    assert invoices["INV-FUTURE"]["days_overdue"] == 0
    assert invoices["INV-FUTURE"]["aging_bucket"] == "current"


def test_fully_paid_overdue_invoice_is_paid_not_overdue():
    result = import_invoices(
        make_csv(f"Acme,INV-PAID,2026-01-01,{due_before(61)},1000,USD,1000"),
        AS_OF,
    )
    row = result["rows"][0]

    assert row["status"] == "accepted"
    assert row["remaining_balance_cents"] == 0
    assert row["days_overdue"] == 0  # review fix R1
    assert row["aging_bucket"] == "paid"
    assert result["totals"]["outstanding_invoice_count"] == 0
    assert result["totals"]["total_outstanding_cents"] == 0


def test_frozen_aging_totals():
    aging = frozen_result()["totals"]["aging"]

    assert aging["current"] == {"count": 3, "remaining_cents": 597047}
    assert aging["1-30"] == {"count": 3, "remaining_cents": 396862}
    assert aging["31-60"] == {"count": 3, "remaining_cents": 259664}
    assert aging["61-90"] == {"count": 2, "remaining_cents": 863731}
    assert aging["91+"] == {"count": 2, "remaining_cents": 22131}
    assert aging["paid"] == {"count": 1, "remaining_cents": 0}


def test_all_buckets_are_always_present():
    aging = import_invoices("", AS_OF)["totals"]["aging"]

    assert tuple(aging) == BUCKETS
    for bucket in BUCKETS:
        assert aging[bucket] == {"count": 0, "remaining_cents": 0}


def test_non_accepted_rows_have_no_aging_values():
    for row in frozen_result()["rows"]:
        if row["status"] != "accepted":
            assert row["days_overdue"] is None
            assert row["aging_bucket"] is None
