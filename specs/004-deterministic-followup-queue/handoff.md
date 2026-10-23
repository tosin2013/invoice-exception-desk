# Handoff: Agent A (OpenCode) → Agent B (OpenAI native hosted agent)

Written by Agent A's operator on Oct 23, 2026. Decisions live in `spec.md` (Clarifications) and `plan.md`; this file is only the checklist.

- [x] **Branch:** `l3h-handoff` (repo https://github.com/tosin2013/invoice-exception-desk)
- [x] **Base SHA:** `99d15d693a28b4b554ea4e4d53a033a74fee34ce` (`l3-solution`)
- [x] **Head SHA:** the commit that adds this file. the tip of `l3h-handoff` after the tie-break correction commit (which also edits this file, so it can't name its own SHA). Check that `git rev-parse HEAD` matches `git ls-remote origin l3h-handoff`, and that `git log -1 --format=%s` starts with "L3.5 correction: AT-05 tie-break".
- [x] **Clean worktree:** `git status --short` must be empty. Use your own worktree; one writer at a time.
- [x] **Versions:** specify-cli 1.1.3 (`uvx --from git+https://github.com/github/spec-kit.git@v1.1.3 specify version`); Agent A ran OpenCode 1.19.3 with `opencode/deepseek-v4.1-flash-free`.
- [x] **Integrations:** `specify integration status` → `Multi-install safe: yes` (opencode only). STOP if not; `--force` isn't a fix.
- [x] **Feature pointer:** `export SPECIFY_FEATURE_DIRECTORY=specs/004-deterministic-followup-queue` and `export SPECIFY_FEATURE_NO_PERSIST=1` (`.specify/feature.json` is gitignored).
- [x] **Environment and tests:** `python3 -m venv .venv && . .venv/bin/activate && pip install pytest` (done by the operator; Agent B installs nothing), then `python -m pytest -q` → **119 passed** at this handoff (no feature code yet).
- [x] **STOP if the tests aren't green on arrival.** Don't fix anything; report back.
- [x] **Frozen (read-only):** `.specify/memory/constitution.md`, `spec.md`, `ACCEPTANCE.md`, `NON_GOALS.md`, `ROADMAP.md`, `data/invoices.csv`. Spec changes only through Agent A via Clarifications; any decision Agent B makes goes into `plan.md`.
- [x] **Owned task IDs (Agent B):** T001–T007 (US1 queue ordering: `tests/test_followup_queue.py`, `invoice_desk/queue.py`, re-exports in `invoice_desk/__init__.py`). Mark them `[X]` in `tasks.md`; nothing below the HANDOFF line.
- [x] **Dependencies:** T001–T007 depend only on the existing `import_invoices` (L3). They depend on no task T008–T024 (rule stated in `tasks.md`). Within the block: tests T001–T003 first, then T004 → T005 → T006, then T007 verifies.
- [x] **Queue order (corrected by Tosin, Oct 23):** bucket priority, then `remaining_balance_cents` descending, then `invoice_id` ascending, then `issuer` ascending as the last key. See `spec.md` FR-005/FR-006 and Clarifications; the SC-002 sequence for the fixture is unchanged.
- [x] **Agent A keeps:** T008–T024 (annotation storage per `plan.md` → "Annotation storage (decision from Clarifications)", owners/notes, polish), then analyze, implement and converge.
- [x] **Expected after T001–T007:** `python -m pytest -q` all green: 119 existing tests plus the new `tests/test_followup_queue.py`.
- [x] **Answer key:** `data/oracle.json` / `compute_oracle.py` are not on this branch and stay with the reviewer.

## Receiver confirmation (Agent B appends one line below before coding)

