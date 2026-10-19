# Implementation Plan: Split a bill fairly

**Branch**: `001-split-bill` | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

## Summary
One pure function, `split_bill`, using integer division and remainder.

## Technical Context
**Language/Version**: Python 3.11+ | **Primary Dependencies**: none | **Testing**: pytest (`python -m pytest -q`)
**Project Type**: tiny library | **Scope**: create `bill_split/__init__.py`, `tests/test_split_bill.py`, and a minimal `pyproject.toml`. Nothing else.

## Constitution Check
I integer cents PASS · II pure PASS · III stdlib only PASS · IV tests in `tests/` PASS · V one commit PASS

## Design
1. `bill_split/__init__.py`: `def split_bill(total_cents: int, people: int) -> list[int]:`
   - Type checks first: `if type(total_cents) is not int or type(people) is not int: raise TypeError(...)` (this rejects `bool` and `float`).
   - `if people < 1 or total_cents < 0: raise ValueError(...)`
   - `base, extra = divmod(total_cents, people)`; return `[base + 1] * extra + [base] * (people - extra)`.
2. `tests/test_split_bill.py`: one test per acceptance scenario.
3. `pyproject.toml`: project name `bill-split`, version `0.1.0`, `requires-python = ">=3.11"`, pytest `testpaths = ["tests"]`.

## Out of scope
CLI, README changes, extra tooling.
