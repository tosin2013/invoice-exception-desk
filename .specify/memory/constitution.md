# bill-split + Invoice Exception Desk Constitution

## Core Principles

### I. Money is integer cents
All amounts are integers in cents. No floats anywhere.

### II. Deterministic and pure
Functions have no I/O, randomness, or clock access. Same input, same output.

### III. Standard library only
Python 3.11+, no runtime dependencies. Tests use pytest.

### IV. Small and tested
Every public function has tests in `tests/`. Run with `python -m pytest -q`.

### V. Spec and code together
A behaviour change and its spec change land in the same commit.

### VI. Synthetic data, offline only
No real personal data, credentials, or network calls. Fixtures are synthetic (see `NON_GOALS.md`).

### VII. Explicit as-of date
Anything time-based takes an explicit `as_of` date argument. Never read the clock. Dates are ISO `YYYY-MM-DD` in America/New_York.

### VIII. Sealed answer key per phase
Each roadmap phase (R1 to R6) is graded against an answer key the builder never sees. The oracle is kept outside the repo during the build. Builder-written tests alone never mean "done".

**Version**: 1.1.0 | **Ratified**: 2026-10-18 | **Last Amended**: 2026-10-22
