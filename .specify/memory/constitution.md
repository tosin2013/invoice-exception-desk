# python-slugify Constitution

Written from the existing code (brownfield). Every rule names a file that already follows it.

## Core Principles

### I. Legacy output is frozen (NON-NEGOTIABLE)
Do not change `slugify/_legacy.py` or `tests/test_legacy.py`. `algorithm='legacy'` stays the default.
Evidence: `AGENTS.md` ("Compatibility comes first"), `slugify/slugify.py` (dispatches `algorithm == 'legacy'` to `_legacy_slugify`), `tests/test_legacy.py`.

### II. New behaviour is opt-in
New CLI behaviour must be behind a new flag; with no new flag, output is byte-for-byte unchanged.
Evidence: `slugify/__main__.py` (`--algorithm`, `--backend`, `--replacement-stage` use `default=argparse.SUPPRESS` so they are absent unless given).

### III. The CLI argument shape is a contract
New CLI options must not add keys to the parsed Namespace or to `slugify_params()` output unless the user passes them.
Evidence: `tests/test_release.py::test_cli_preserves_legacy_default_shape`.

### IV. New tests go in new files
Add tests in a new file under `tests/`; do not edit existing test files.
Evidence: `AGENTS.md`, the existing split into `tests/test_release.py`, `tests/test_cli_interrupt.py`, `tests/test_modern_word_boundary.py`.

### V. Standard library first, strict typing
No new runtime dependencies for CLI features; keep type hints (the package ships `py.typed`).
Evidence: `pyproject.toml` (dependencies), `slugify/py.typed`, typed signatures in `slugify/__main__.py`.

## Workflow
- Never push; never commit to `master` (`AGENTS.md`).
- Run `python -m pytest -q`; the existing suite must stay green (`pyproject.toml` pytest config).
- Spec and behaviour change land in the same commit.

**Version**: 1.0.0 | **Ratified**: 2026-10-18 | **Last Amended**: 2026-10-18
