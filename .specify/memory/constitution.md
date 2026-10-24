# bill-split + Invoice Exception Desk Constitution

## Core Principles

### I. Money is integer cents
All amounts are integers in cents. No floats anywhere.

### II. Deterministic and pure
Computation is pure: importing, validating, balances, aging and queue ordering do no I/O, read no clock and use no randomness. Same input, same output.

File I/O is allowed only where the approved owning feature specification and plan explicitly authorize it as a designed persistence step, at a caller-supplied or documented path.
- Persistence may read or write only the domain fields and storage metadata that the approved contract authorizes. The contract states its path and its failure and preservation guarantees. Example: today's 004 annotation store in `invoice_desk/annotations.py`, whose mutable domain fields are owner and notes.
- Data read back from a designed persistence step is an explicit input: same persisted state, same output.
- Persistence never feeds back into invoice classification, balances, aging or queue ordering. Principles VI and VII still apply.
- The exception doesn't extend automatically: each new persistence contract needs its own approved scope review.

### III. Standard library only
Python 3.11+, no runtime dependencies. Tests use pytest.

### IV. Small and tested
Every public function has tests in `tests/`. Run with `python -m pytest -q`.

### V. Specs are living, and land with the code
A behaviour change lands in one commit with its spec change and the tests that show it.

A behaviour revision within an existing capability updates its owning feature spec:
- add a dated entry under Clarifications saying what changed, who decided, and why;
- mark the old requirement text as superseded and non-normative, keeping its requirement ID, with the date and the one requirement that replaces it, instead of deleting it.

A new capability, or a separately versioned API or storage contract, gets a new feature folder with explicit links to the specs it changes and an impact review of them.

After a normative requirement, scope or contract change, regenerate the affected plan and tasks and reconcile their statuses against recorded execution evidence. Editorial-only changes need a recorded no-behaviour-impact note instead of regeneration. Regenerated files rely on git for their history.

### VI. Synthetic data, offline only
No real personal data, credentials, or network calls. Fixtures are synthetic (see `NON_GOALS.md`).

### VII. Explicit as-of date
Anything time-based takes an explicit `as_of` date argument. Never read the clock. Dates are ISO `YYYY-MM-DD` in America/New_York.

### VIII. Sealed answer key per phase and per behaviour change
Each roadmap phase (R1 to R6), and every later change to shipped behaviour, is graded against an answer key the builder never sees. Refactors, documentation and formatting with no behaviour change are out of scope.
- An independent reviewer writes or validates the key, or a versioned amendment for the change. The reviewer seals it against the approved contract revision **before implementation starts**, recording its baseline, version and hashes.
- Keys stay outside the builder-accessible repository and workspace.
- Merge requires passing the unchanged regression coverage and the approved changed-policy coverage. Unexpected failures block merge.
- Only explicitly approved differences from an earlier key's policy are reported separately, each citing the dated Clarification (rule V) that approved it. They are never counted as passes or fixes.
- Earlier keys stay byte-unchanged. A policy change after sealing needs a newly approved, independently versioned seal.
- Builder-written tests alone never mean "done".

**Version**: 2.0.0 | **Ratified**: 2026-10-18 | **Last Amended**: 2026-10-24
