#!/usr/bin/env python3
"""Runnable stdlib unittest checks for the R0 data artifacts.

Run from the repository root:
    python3 -m unittest discover -s tests -v
or directly:
    python3 tests/test_oracle.py
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CSV_PATH = os.path.join(DATA, "invoices.csv")
ORACLE_PATH = os.path.join(DATA, "oracle.json")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = _load_module("generate_invoices", os.path.join(DATA, "generate_invoices.py"))
oracle = _load_module("compute_oracle", os.path.join(DATA, "compute_oracle.py"))


class GeneratorDeterminismTest(unittest.TestCase):
    def test_records_are_deterministic(self):
        self.assertEqual(generate.build_records(), generate.build_records())

    def test_rendered_bytes_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = os.path.join(tmp, "first.csv")
            second = os.path.join(tmp, "second.csv")
            generate.render_csv(first)
            generate.render_csv(second)
            with open(first, "rb") as fh:
                a = fh.read()
            with open(second, "rb") as fh:
                b = fh.read()
            self.assertEqual(a, b)

    def test_committed_csv_matches_generator(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh = os.path.join(tmp, "invoices.csv")
            generate.render_csv(fresh)
            with open(fresh, "rb") as fh:
                fresh_bytes = fh.read()
        with open(CSV_PATH, "rb") as fh:
            committed_bytes = fh.read()
        self.assertEqual(fresh_bytes, committed_bytes, "data/invoices.csv is stale; regenerate it")

    def test_row_count_is_about_thirty(self):
        self.assertEqual(len(generate.build_records()), 30)


class OracleAgreementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ORACLE_PATH, encoding="utf-8") as fh:
            cls.oracle = json.load(fh)

    def test_oracle_matches_independent_recomputation(self):
        recomputed = oracle.build_oracle(CSV_PATH)
        self.assertEqual(recomputed, self.oracle)

    def test_oracle_counts_reconcile(self):
        totals = self.oracle["totals"]
        self.assertEqual(
            totals["total_rows"],
            totals["accepted"]
            + totals["rejected"]
            + totals["duplicate_identical"]
            + totals["duplicate_inconsistent"],
        )
        aging = totals["aging"]
        self.assertEqual(sum(b["count"] for b in aging.values()), totals["accepted"])
        self.assertEqual(len(self.oracle["rows"]), totals["total_rows"])

    def test_all_amounts_are_integer_cents(self):
        for row in self.oracle["rows"]:
            if row["status"] == "accepted":
                for field in ("amount_cents", "paid_cents", "remaining_balance_cents", "days_overdue"):
                    self.assertIsInstance(row[field], int, f"{row.get('invoice_id')} {field}")
        self.assertIsInstance(self.oracle["totals"]["total_outstanding_cents"], int)


class PolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ORACLE_PATH, encoding="utf-8") as fh:
            cls.oracle = json.load(fh)
        cls.by_row = {r["row"]: r for r in cls.oracle["rows"]}
        cls.by_key = {r.get("invoice_id"): r for r in cls.oracle["rows"] if r.get("invoice_id")}

        with open(CSV_PATH, newline="", encoding="utf-8") as fh:
            cls.csv_rows = list(csv.reader(fh))

    def test_aging_boundaries(self):
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
            "INV-1012": (91, "91+"),
            "INV-1014": (31, "31-60"),
        }
        for invoice_id, (days, bucket) in expected.items():
            row = self.by_key[invoice_id]
            self.assertEqual(row["status"], "accepted", invoice_id)
            self.assertEqual(row["days_overdue"], days, invoice_id)
            self.assertEqual(row["aging_bucket"], bucket, invoice_id)

    def test_not_due_and_due_today_are_not_overdue(self):
        for invoice_id in ("INV-1001", "INV-1002", "INV-1013"):
            row = self.by_key[invoice_id]
            self.assertEqual(row["days_overdue"], 0, invoice_id)
            self.assertEqual(row["aging_bucket"], "current", invoice_id)

    def test_duplicate_classification(self):
        self.assertEqual(self.by_row[15]["status"], "duplicate_identical")
        self.assertEqual(self.by_row[15]["reason"], "identical_duplicate")
        self.assertEqual(self.by_row[16]["status"], "duplicate_identical")
        self.assertEqual(self.by_row[17]["status"], "duplicate_inconsistent")
        self.assertEqual(self.by_row[17]["reason"], "inconsistent_duplicate")
        self.assertEqual(self.by_row[18]["status"], "duplicate_inconsistent")

    def test_rejection_reasons_by_row(self):
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
            row = self.by_row[row_number]
            self.assertEqual(row["status"], "rejected", row_number)
            self.assertEqual(row["reason"], reason, row_number)

    def test_zero_balance_is_excluded_from_outstanding(self):
        paid = self.by_key["INV-1011"]
        self.assertEqual(paid["remaining_balance_cents"], 0)
        self.assertEqual(paid["aging_bucket"], "paid")

        totals = self.oracle["totals"]
        expected_outstanding = sum(
            r["remaining_balance_cents"]
            for r in self.oracle["rows"]
            if r["status"] == "accepted" and r["remaining_balance_cents"] > 0
        )
        self.assertEqual(totals["total_outstanding_cents"], expected_outstanding)
        self.assertEqual(totals["aging"]["paid"]["remaining_cents"], 0)
        outstanding_count = sum(
            1
            for r in self.oracle["rows"]
            if r["status"] == "accepted" and r["remaining_balance_cents"] > 0
        )
        self.assertEqual(totals["outstanding_invoice_count"], outstanding_count)

    def test_partial_payment_remaining_is_never_negative(self):
        for row in self.oracle["rows"]:
            if row["status"] == "accepted":
                self.assertGreaterEqual(row["remaining_balance_cents"], 0)
                self.assertEqual(
                    row["remaining_balance_cents"], row["amount_cents"] - row["paid_cents"]
                )

    def test_csv_has_empty_rows(self):
        empty = [r for r in self.csv_rows[1:] if len(r) == 0]
        self.assertEqual(len(empty), 2)


class IdempotencyTest(unittest.TestCase):
    def test_recompute_twice_is_stable(self):
        first = oracle.build_oracle(CSV_PATH)
        second = oracle.build_oracle(CSV_PATH)
        self.assertEqual(first, second)
        self.assertEqual(first["totals"], second["totals"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
