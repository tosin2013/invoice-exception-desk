# Implementation Plan: `--json` output for the slugify CLI

**Branch**: `001-cli-json` | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

## Summary
Add a `--json` flag in `slugify/__main__.py`. In `main()`, after computing the slug, print `json.dumps({"input": params["text"], "slug": slug})` when the flag is set; otherwise print the slug as today.

## Technical Context
**Language/Version**: Python 3.10+ (per `pyproject.toml`) | **Primary Dependencies**: standard library only (`json`, `argparse`)
**Testing**: pytest, `python -m pytest -q` | **Project Type**: library + CLI | **Scope**: `slugify/__main__.py` and ONE new file `tests/test_cli_json.py`. Nothing else.

## Constitution Check
- I Legacy frozen: no change to `_legacy.py` / `test_legacy.py`. PASS
- II Opt-in: new flag only. PASS
- III Argument shape: declare with `action='store_true', default=argparse.SUPPRESS`; read with `getattr(args, 'json', False)`. Do NOT add it to `slugify_params()`. PASS
- IV New tests in a new file. PASS
- V Standard library only. PASS

## Design
1. In `parse_args`, add: `parser.add_argument('--json', action='store_true', default=argparse.SUPPRESS, help='Print {"input": ..., "slug": ...} as JSON')`.
2. Add `import json` at the top of `slugify/__main__.py`.
3. In `main()`, inside the existing `try`: compute `result = slugify(**params)`; if `getattr(args, 'json', False)` print `json.dumps({'input': params['text'], 'slug': result})`, else `print(result)`. Keep the `KeyboardInterrupt` handling unchanged.
4. New tests in `tests/test_cli_json.py` using `main([...])` with `capsys`, covering: basic output, options applied, stdin input, empty input, non-ASCII escaping, unchanged output without the flag, unchanged argument shape without the flag.

## Out of scope
README/CHANGELOG edits, dev-tool installs, any other file.
