# L5 ruling request v1: reject an invoice due before it is issued (003 FR-007a)

- **Document:** `request-v1.md`, the frozen ruling for the L5 worked example (asked for in Relay MSG-1256)
- **Version:** v1
- **Date:** 2026-10-25
- **Status:** draft for Tosin review — not yet approved
- **Source:** L5 outline revision 3.3 (`L5-outline.md`, Oct 24, 2026), Tosin's decisions L5-D1 to L5-D8 and L5-Q2 (Oct 24, 2026), Tosin's key-holder decision (Oct 25, 2026), and the repo `tosin2013/invoice-exception-desk` read at the SHAs below.
- **Owning feature:** `specs/003-desk-import/` (feature 003). Feature 004 gets a dated note only.

This ruling does not authorize a run on its own. It takes effect only when the "Final approval" line in section 9 is filled in by Tosin, after which the ruling text is hashed and the key holder seals against it.

## 1. The rule

**FR-007a (new, in `specs/003-desk-import/spec.md`; supersedes FR-007, which is kept struck through for history and not deleted):**

> After trimming (FR-030), `issue_date` and `due_date` MUST each be a real Gregorian calendar date in strict `YYYY-MM-DD` form, and `due_date` MUST NOT be strictly earlier than `issue_date`. A row with an invalid date form, an impossible date, or a `due_date` strictly earlier than its `issue_date` MUST be rejected as `invalid_date`. A row whose `due_date` equals its `issue_date` is valid.

Current FR-007 text being superseded (spec.md line 118 at the baseline):

> **FR-007**: `issue_date` and `due_date` MUST each be a real Gregorian calendar date in strict `YYYY-MM-DD` form. Any other form or impossible date MUST be rejected as `invalid_date`.

Points fixed by this ruling:

- **Strictly before only.** Only `due_date < issue_date` is rejected (L5-D6). **Equal dates are valid** (L5-D7).
- **Reason reused.** The rejection reason is the existing `invalid_date` (L5-D8). No new reason is added.
- **Unchanged:** the FR-011 precedence order (`empty_row`, `missing_required_field`, `invalid_date`, `invalid_amount`, `invalid_currency`, `invalid_payment`), the reason set, and the `ACCEPTANCE.md` acceptance table (AT-01 to AT-04 values, including the AT-02 row 19–30 reasons). On a row that fails both the date order and another field, the reason is whatever FR-011 gives `invalid_date` against that field.
- **Duplicates (FR-012 to FR-014) unchanged in wording.** A consequence the key must pin: because only validated rows take part in duplicate detection, a first occurrence that is now rejected under FR-007a lets a later valid row with the same `(issuer, invoice_id)` be accepted.
- **004:** FR-021 and SC-010 in `specs/004-deterministic-followup-queue/spec.md` keep their text; each gets a dated L5 note that the accepted set can shrink for new inputs because of 003 FR-007a, in the same way L4 did in commit `f6a9b5a`. No 004 code, contracts, data model or tests change.

### Known impact (verified against `l3h-handoff` at `a130646`; see "Verification" below)

- **A public test breaks:** `test_aging_bucket_boundaries` in `tests/test_invoice_desk.py` (lines 542–565). Its rows are issued `2026-01-01` with due dates counted back from `AS_OF = 2026-10-15`. Row **`INV-B365`** has issue `2026-01-01`, due `2025-10-15`, and the test expects it accepted in `91+`. Under FR-007a it is rejected as `invalid_date`. The other eight offsets (0, 1, 30, 31, 60, 61, 90, 91 days) are due on or after the issue date and are unaffected.
  - **Required change:** move that test's issue date earlier (for example `2025-01-01`) so every row is valid and the 365-day aging case is kept, not dropped. The dated Clarification names this edited test (rule V).
  - **New tests (must fail first on the baseline code):** a due-before-issue row rejected with `invalid_date`; an equal-dates row accepted.
- **Equal-date rows stay valid:** fixture `data/invoices.csv` rows `INV-1010` (2026-09-15 / 2026-09-15), `INV-1011` (2026-08-15 / 2026-08-15), `INV-1012` (2026-07-16 / 2026-07-16) and `INV-1014` (2026-09-14 / 2026-09-14) have equal issue and due dates and are accepted today; they stay accepted. `INV-Z1` in `test_zero_amount_is_rejected_as_invalid_amount` also has equal dates (2026-09-01) and stays `invalid_amount`.
- **Malformed-date rows (already `invalid_date`, unchanged):** fixture data rows 22–24: `INV-9004` (`2026-13-40`), `INV-9005` (`not-a-date`), `INV-9006` (`10/15/2026`).
- **Frozen fixture:** no row of `data/invoices.csv` (30 data rows) with two valid dates has `due_date` before `issue_date`, so SC-001 to SC-007, the AT tables and 004's queue order do not move. `data/` is not edited.

**Verification (2026-10-25, on the box):** the fixture was read row by row; every CSV passed to `import_invoices` during the full public test run (205 tests, header-aware) was scanned for valid-date rows with `due_date < issue_date`. The only such row found was `INV-B365` (2026-01-01 / 2025-10-15). No mismatch with the outline's impact account.

## 2. Baselines and what the seal binds to

| Item | Value |
|---|---|
| Application baseline (`origin/l3h-handoff` head; Spec Kit 1.2.3, constitution v2.0.0) | `a130646d0b5406c60625022e1998c2262a7e8284` |
| Operator setup commit (Ralph v1.5.0 install, parent = application baseline), local branch `l5-setup` | `d6c7d7be4fa61084cf48c400a73c44798e1a063a` |
| **Seal binds to** (the exact tree the builder starts from) | `d6c7d7be4fa61084cf48c400a73c44798e1a063a` (setup SHA) |
| Sealed base for the grading bundle | `d6c7d7be4fa61084cf48c400a73c44798e1a063a`; the bundle covers `d6c7d7be4fa61084cf48c400a73c44798e1a063a..<final SHA>` |
| Scope and size comparison base | `d6c7d7be4fa61084cf48c400a73c44798e1a063a` |
| Public test baseline at both SHAs | 205 passed (`uv run --with pytest python -m pytest -q`) |

- **Bundle prerequisite:** `git bundle verify` needs the sealed base in the verifier's repository. The setup commit is local (not pushed), so the key holder and the run machine must first receive it, for example from the setup bundle `l5-setup.bundle` (range `a130646..d6c7d7b`, head `refs/heads/l5-setup` = `d6c7d7be4fa61084cf48c400a73c44798e1a063a`, SHA-256 `9a3dbac39bc28be7ac929714572deb08eeee11e7eb77396cf0dd734301ab3569`). Whether it is moved by that bundle or by publishing `l5-setup` is Tosin's call; the SHA must match either way.
- **Branch:** the builder works on a local branch `l5/003-due-before-issue` (proposed slug) created from the setup SHA.

## 3. Allowed paths for the builder

Compared against the setup SHA. Any change outside this list stops the run.

- `specs/003-desk-import/spec.md`: dated Clarification (session 2026-10-25, citing this ruling and naming the edited test), FR-007 superseded (struck, kept), FR-007a added, edge case added.
- `specs/003-desk-import/plan.md` and `specs/003-desk-import/tasks.md`: regenerated after the normative change (rule V). `tasks.md` is also the file Ralph reads and checks off.
- `specs/003-desk-import/drift.md`: L5 entry.
- `specs/003-desk-import/progress.md` and `specs/003-desk-import/ralph-memory.md`: Ralph's notes files (created by `ralph-loop.sh` in the spec directory); allowed and kept in Ralph's commits, not squashed out.
- `specs/004-deterministic-followup-queue/spec.md`: a dated Clarification and dated notes under FR-021 and SC-010 only.
- `ACCEPTANCE.md`: a note under AT-02 only; the oracle values do not change.
- `tests/test_invoice_desk.py`: the `test_aging_bucket_boundaries` issue-date change and the new FR-007a tests.
- `invoice_desk/__init__.py`: date validation (near `_DATE_PATTERN`, line 69, and the `invalid_date` return, line 148, at the baseline).
- `run.log` (repo root): sanitized receipt copy only.
- Outside the repository, run directory `/workspace/l5-run/` (mounted into the container): `receipt.md`, the bundle, the pre-seal `questions.md`, and wrapper logs.

**Never touched by the builder:** `.specify/**` (including the Ralph install and `ralph-config.yml`), `.opencode/**`, the constitution, `data/**`, `invoice_desk/queue.py`, `invoice_desk/annotations.py`, any 004 file other than `spec.md`, `pyproject.toml` (no new dependencies), `main`, `l3h-handoff`. No push, force-push or merge.

Note: the installed `ralph-config.yml` defaults to `agent_cli: "copilot"` and `model: "claude-sonnet-4.6"`. The run must override both from outside the tree (`--model opencode/deepseek-v4.1-flash-free` and the wrapper `opencode` executable path via `SPECKIT_RALPH_AGENT_CLI`); the file itself is not edited. The install also registers an optional `after_tasks` hook (`speckit.ralph.run`) in `.specify/extensions.yml`; the operator decides when Ralph starts.

## 4. Exceptions

- **Setup exception.** The Ralph install commit `d6c7d7be4fa61084cf48c400a73c44798e1a063a` was made by the operator before the seal, in one dedicated commit; it is not builder work and is not graded as builder scope. It is the only allowed change to `.specify/` and `.opencode/`. Its contents: `.specify/extensions.yml`, `.specify/extensions/.registry`, `.specify/extensions/ralph/**` (LICENSE, README.md, commands/iterate.md, commands/run.md, extension.yml, ralph-config.yml, scripts/.gitattributes, scripts/bash/ralph-loop.sh, scripts/powershell/ralph-loop.ps1, templates/.gitattributes, templates/ralph-memory.md), `.opencode/commands/speckit.ralph.iterate.md`, `.opencode/commands/speckit.ralph.run.md` (15 files added, nothing modified or deleted). Tests: 205 passed before and after.
- **Lesson-only multi-commit exception to rule V (L5-Q2).** For this lesson only, and not as a constitution change, the worked example may produce several commits (Ralph makes one per task), all on `l5/003-due-before-issue`:
  - the dated Clarification and the spec change land no later than the first code commit;
  - the bundle covers the sealed base `d6c7d7be4fa61084cf48c400a73c44798e1a063a` to the final SHA;
  - the receipt lists every commit SHA in that range;
  - grading runs on the final SHA.

## 5. Limits (L5-D3, L5-D4)

- Up to **3** fix tries.
- **15 min** per agent call; **90 min** per run, plus a hard wall-clock `timeout` on the whole run.
- **5** empty-output retries (10 min apart; they count against time, not fix tries).
- **300-line** diff cap: added plus deleted lines from `git diff --numstat` against the setup SHA, tests included; `run.log`, `specs/003-desk-import/progress.md` and `specs/003-desk-import/ralph-memory.md` excluded.
- **Spend: $0.** Free model only: `opencode/deepseek-v4.1-flash-free`.
- **Pinned versions:** OpenCode 1.19.3 (npm `opencode-ai@1.19.3`), Ralph Loop v1.5.0 (`https://github.com/Rubiss-Projects/spec-kit-ralph/archive/refs/tags/v1.5.0.zip`), Spec Kit CLI 1.2.3 (`uvx --from git+https://github.com/github/spec-kit.git@v1.2.3 specify`).
- Check command for the agent and the wrapper: `uv run --with pytest python -m pytest -q` (plain `pytest` fails collection).
- Ralph's own breakers (3 failed calls in a row, 3 no-progress iterations, `max_iterations`) apply; the wrapper adds the per-call timeout, empty-output retries, size and scope checks after each iteration, the old-rule grep, and a stop on a contract question.

## 6. Isolation

- The run happens in a **Docker container** on a machine with **no key material present**. Only the throwaway checkout and `/workspace/l5-run/` are mounted; no Docker socket, no `--privileged`, no added capabilities; scrubbed environment (allowlist only, no tokens, SSH agent, credential helper or `gh` login; no push remote configured).
- **Key holder:** the same isolated Codex custodian used for L4. Tosin's decision, 2026-10-25 07:36 EDT: "Use the same isolated Codex custodian from L4 as the L5 key holder". The custodian runs the pre-seal impact check, seals, and grades; the builder never does.
- **Canary validation (per MSG-1256):** the operator validates the boundary with non-sensitive canary files placed in an equivalent protected test setup, using the exact container configuration of the run. Canaries are never placed over real key paths, and real keys are never probed. The receipt records an attestation only (canary labels, pass or fail for each, mount list, env var names, image or config hash).
- The builder is given **neither the keys nor their paths**.
- **Stop:** if the boundary cannot be shown (any canary readable, or the mount boundary not enforceable), the run does not start. Writing the gap down is not a pass.

## 7. Grade handover (L5-D5)

- At the end of the run the loop writes one `git bundle` of `d6c7d7be4fa61084cf48c400a73c44798e1a063a..l5/003-due-before-issue` to `/workspace/l5-run/`. Nothing is pushed from the sandbox.
- The receipt records the bundle's SHA-256 and the loop's final SHA.
- Before grading, the key holder checks: the bundle's SHA-256 matches the receipt; `git bundle verify` passes against the sealed base; the bundle head equals the final SHA; the only `.specify/` and `.opencode/` changes are in the setup commit; `progress.md` and `ralph-memory.md` are present in `specs/003-desk-import/`. **If any check fails, the result is "not graded".**
- The key result (PASS, FAIL or not graded; L3 86 + L4 38 regression buckets, the FR-007a policy, any approved divergence) and the execution mode (unassisted, clarified-restarted, assisted) are reported separately. A contract question after the seal marks the seal superseded.
- After the grade, a human publishes the branch and opens the PR, outside the sandbox.

## 8. Not covered by this ruling

- Any other date rule (for example a maximum term or a future issue date).
- Any change to `data/invoices.csv`, the FR-011 order, the reason set or the acceptance values.
- Any 004 behaviour change.

## 9. Approval provenance

Decisions by Tosin Akinosho:

- **2026-10-24 (17:23 EDT) L5-D1:** loop driver is the community Ralph Loop extension for Spec Kit.
- **2026-10-24 (17:23 EDT) L5-D2:** Docker container sandbox; now implemented with safe canaries in an equivalent protected test setup, never over real key paths, per MSG-1256.
- **2026-10-24 (17:23 EDT) L5-D3:** limits as proposed: 3 fix tries, 15 min per call, 90 min per run, 5 empty-output retries, 300-line cap.
- **2026-10-24 (17:23 EDT) L5-D4:** $0; free OpenCode model `opencode/deepseek-v4.1-flash-free` only.
- **2026-10-24 (17:23 EDT) L5-D5:** grade handover by `git bundle` ("if git bundle is better lets do that").
- **2026-10-24 (17:23 EDT) L5-D6:** worked example is the due-before-issue rule (FR-007a in 003).
- **2026-10-24 (17:23 EDT) L5-D7:** equal issue and due dates are valid.
- **2026-10-24 (17:23 EDT) L5-D8:** reuse `invalid_date`; FR-011 order, reason set and acceptance table unchanged.
- **2026-10-24 (17:51 EDT):** Ralph's `progress.md` and `ralph-memory.md` are in scope and kept in the commits; the Ralph install goes in one operator setup commit.
- **2026-10-24 (17:54 EDT) L5-Q2:** multiple commits allowed for the L5 worked example, as a lesson-scoped exception to rule V.
- **2026-10-25 (07:36 EDT):** key holder is the same isolated Codex custodian used for L4.

Final approval: ____ (Tosin, date)
