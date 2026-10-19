# Repository Inventory (Spec Kit Step 0)

Read-only survey of `python-slugify`. No files changed. Evidence cited by path.

## (a) Project conventions (evidenced)

- Packaging is PEP 621 in `pyproject.toml`; `setup.py` is a thin shim ("metadata and build configuration live in pyproject.toml"). `requires-python = ">=3.10"`, MIT license, single package `slugify` (`pyproject.toml`).
- Version is a single source of truth: `slugify/__version__.py` (`__version__ = '9.1.3'`), read dynamically via `[tool.setuptools.dynamic]` in `pyproject.toml`.
- Typing: package ships `slugify/py.typed`; mypy `strict = true` over `packages = "slugify"` (`pyproject.toml`). `from __future__ import annotations` used in `slugify/__main__.py`, `slugify/special.py`.
- Style: `pycodestyle` with `--ignore=E128,E261,E225,E501,W605` and `flake8` with `--ignore=E501,F403,F401,E241,E225,E128` (`tox.ini`, `format.sh`, `.github/workflows/ci.yml`).
- CLI is registered as console script `slugify = "slugify.__main__:main"` and also runs via `python -m slugify` (`pyproject.toml`, README).
- Public API re-exported through `slugify/__init__.py` (`from .special import *`, `from .slugify import *`).
- Contributions are issues-first: "Open an issue before writing code" and do not edit frozen files (`CONTRIBUTING.md`).

## (b) Tests: how run and layout

- Config: `[tool.pytest.ini_options] testpaths = ["tests"]`, warnings escalated to errors (`filterwarnings = ["error"]`) (`pyproject.toml`).
- Canonical matrix is `tox` (`tox.ini`): CPython 3.10–3.14 and PyPy 3.11 across `unidecode`, `text_unidecode`, `anyascii` backends, plus `coverage-report` (fail_under=97), `mypy`, `pycodestyle`, `flake8`, and `packaging` (`tools/check_dist.py`).
- Maintainer commands from `CONTRIBUTING.md`: `python -m pytest`, `python -m mypy`, `python tools/check_dist.py`. Dev install in README: `python -m pip install -e '.[unidecode,anyascii]'`.
- Layout (`tests/`): `test_legacy.py` (frozen original suite, uses `unittest`), `test_release.py` (modern/CLI regression), `test_cli_interrupt.py`, `test_modern_word_boundary.py`, `test_add_uppercase_error.py`, `test_legacy_backend_errors.py`. Both `unittest` and `pytest` styles coexist.
- Coverage source is `slugify` (`tox.ini`, `pyproject.toml`).

## (c) No-go areas (must not touch)

- `slugify/_legacy.py` and `tests/test_legacy.py` are frozen; changes that alter legacy output are rejected on principle (`AGENTS.md:12,14,15;17`; `CONTRIBUTING.md:32`).
- `algorithm='legacy'` must remain the permanent default; no silent default switch (`AGENTS.md:13`, `docs/release-9/migration.md`).
- Preserve the public `smart_truncate` contract (`AGENTS.md:15`).
- Do not change transliteration defaults or add a GPL-only default dependency; base dep stays `text-unidecode` (`AGENTS.md:21,25,26,27`).
- Never commit/push to `master`; all changes via PR. Publishing, pushing, PRs, merges, tags need explicit authorization (`AGENTS.md:7,8,31`).
- Unsolicited external PRs are closed; issues-first policy (`AGENTS.md:41`).
- CLI regex-forwarding correction is the one documented intentional exception to old CLI behavior (`AGENTS.md:17`).
- Historical evidence/notes must not be rewritten: `docs/release-9/*` (`AGENTS.md:37,46`).

## (d) Smallest directory scope for a new CLI feature

`slugify/` + `tests/`, and only specific files within:

- `slugify/__main__.py` — argparse setup (`parse_args`), param mapping (`slugify_params`), `main` (`slugify/__main__.py:10,67,98`).
- `slugify/slugify.py` — only if the feature needs a new core option.
- `tests/` — add a NEW modern/CLI test file (e.g. follow `tests/test_cli_interrupt.py` or `tests/test_release.py`); never edit `tests/test_legacy.py`.
- `README.md` — document the option if user-facing (install/usage sections). `CHANGELOG.md` only if asked (`CONTRIBUTING.md`).
- Avoid: `slugify/_legacy.py`, `tests/test_legacy.py`, `slugify/special.py`, `docs/release-9/`.