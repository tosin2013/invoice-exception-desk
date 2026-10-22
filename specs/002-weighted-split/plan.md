# Implementation Plan: Weighted bill split

**Branch**: `002-weighted-split` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)

## Summary
One pure function, `split_weighted`, using integer arithmetic and the largest-remainder method. Written by the human/strong role, like L1.

## Technical Context
**Language/Version**: Python 3.11+ | **Primary Dependencies**: none | **Testing**: pytest (`python -m pytest -q`)
**Project Type**: tiny library | **Scope**: edit `bill_split/__init__.py` (add one function) and create `tests/test_split_weighted.py`. Do not change `split_bill`, its tests, or `pyproject.toml`.

## Constitution Check
I integer cents PASS (no floats, no `round`) · II pure PASS · III stdlib only PASS · IV tests in `tests/` PASS · V spec folder and code in one commit PASS

## Design
1. `bill_split/__init__.py`: `def split_weighted(total_cents: int, weights: list[int] | tuple[int, ...]) -> list[int]:`
   - **Types first** (clarification 2): `type(total_cents) is not int` → `TypeError`; `not isinstance(weights, (list, tuple))` → `TypeError`; any `type(w) is not int` → `TypeError` (rejects `bool`, `float`).
   - **Then values**: `total_cents < 0`, `len(weights) == 0`, any `w < 0`, or `sum(weights) == 0` → `ValueError`.
   - `wsum = sum(weights)`; for each index `i`: `base_i, rem_i = divmod(total_cents * weights[i], wsum)`.
   - `leftover = total_cents - sum(bases)` (always `0 <= leftover < len(weights)`).
   - Give one extra cent to the `leftover` indices with the largest `rem_i`; ties go to the lower index. Use `sorted(range(n), key=lambda i: (-rem[i], i))[:leftover]`.
   - Return the list of shares in weight order.
2. `tests/test_split_weighted.py`: one test per acceptance scenario and edge case in the spec, plus a check that equal weights match `split_bill` for a few totals.

## Out of scope
CLI, README changes, changes to `split_bill`, extra tooling.
