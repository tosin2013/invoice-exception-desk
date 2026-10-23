# Frozen task packet v4: Agent A (OpenCode) → Agent B (fresh receiver)

**This file is the ONE authoritative packet for Agent B.** It merges the earlier `handoff.md` checklist and the local `task-packet.md`. If anything elsewhere disagrees with this file, this file wins; report the disagreement and STOP. No chat context crosses this handoff.

Prepared Oct 23, 2026 (America/New_York). Approved by Tosin. Decisions live in `spec.md` (Clarifications) and `plan.md`; this file only routes to them.

## 1. Pins: branch vs feature directory

| Thing | Value |
|---|---|
| Repo | https://github.com/tosin2013/invoice-exception-desk |
| **Git branch** | `l3h-handoff` (a git ref; Spec Kit did not create its own feature branch) |
| **Spec Kit feature directory** | `specs/004-deterministic-followup-queue/` (a folder on that branch, not a branch) |
| Base (`l3-solution`) | `99d15d693a28b4b554ea4e4d53a033a74fee34ce` |
| Packet parent (last sender commit before this packet) | `eba9925e83470b3b605b1d9cf6e3bf6a3a2c8af7` |
| **Packet pin** | the commit whose subject is exactly `L3.5 frozen task packet v4 for Agent B (handoff.md, parent eba9925)` and whose parent is `eba9925e83470b3b605b1d9cf6e3bf6a3a2c8af7`. A file can't contain its own commit SHA; the operator gives the full 40-character value in the launch message, and you verify it as below |

Verify the pin before anything else:

```bash
git ls-remote https://github.com/tosin2013/invoice-exception-desk.git refs/heads/l3h-handoff
# → <PACKET_SHA>  refs/heads/l3h-handoff   (must equal the SHA in your launch message)
git log -1 --format='%H%n%P%n%s' <PACKET_SHA>
# line 1 = <PACKET_SHA>; line 2 = eba9925e83470b3b605b1d9cf6e3bf6a3a2c8af7;
# line 3 = L3.5 frozen task packet v4 for Agent B (handoff.md, parent eba9925)
```

If the branch tip has moved past the packet pin, or any line differs: STOP and report.

## 2. Checkout and feature selection (exact commands)

```bash
git clone https://github.com/tosin2013/invoice-exception-desk.git ied-agent-b
cd ied-agent-b
export PACKET_SHA=<full 40-char SHA from your launch message>
git checkout -b agent-b-work "$PACKET_SHA"   # local branch at the pin; no push unless the operator says so
test "$(git rev-parse HEAD)" = "$PACKET_SHA" || { echo "STOP: wrong SHA"; exit 1; }
test -z "$(git status --porcelain)" || { echo "STOP: dirty worktree"; exit 1; }
export SPECIFY_FEATURE_DIRECTORY=specs/004-deterministic-followup-queue
export SPECIFY_FEATURE_NO_PERSIST=1          # don't write .specify/feature.json (it's gitignored and machine-local)
```

One writer at a time: Agent A is stopped while you work. Use only this clone.

## 3. Fresh-receiver preflight (no existing .venv assumed)

```bash
python3 --version                            # need >= 3.11 (pyproject: requires-python >= 3.11)
python3 -m venv .venv || { echo "STOP: venv unavailable"; exit 1; }
. .venv/bin/activate
python -m pytest --version || echo "STOP: pytest missing"
python -m pytest -q                          # expected: 119 passed
# optional, if uvx is already present (don't install it):
uvx --from git+https://github.com/github/spec-kit.git@v1.1.3 specify version              # CLI Version 1.1.3
uvx --from git+https://github.com/github/spec-kit.git@v1.1.3 specify integration status   # Multi-install safe: yes
```

**Allowed:** creating `.venv/` in the clone (it's gitignored). **Only if your launch message explicitly allows it:** `pip install pytest` inside that `.venv` and nothing else. **Not allowed:** any other install (system packages, other pip packages, uv/uvx, spec-kit, agents), API keys, logins, or paid fallbacks. A missing dependency is a STOP-and-report, not permission to install.

**Expected baseline at the packet pin: `119 passed`.** STOP if it's anything else. Don't fix anything.

## 4. What you own: T001–T007 (US1 queue ordering)

From `tasks.md` (Stage 1 write scope):

| Task | Path |
|---|---|
| T001–T003 (tests first) | `tests/test_followup_queue.py` (new) |
| T004–T005 | `invoice_desk/queue.py` (new) |
| T006 | `invoice_desk/__init__.py` (re-exports only; don't change `import_invoices`) |
| T007 | run `python -m pytest -q tests/test_followup_queue.py tests/test_invoice_desk.py`, then the full suite |

Order: T001 → T002 → T003, then T004 → T005 → T006, then T007. T001–T007 depend only on the existing `invoice_desk.import_invoices` (L3). None depends on T008–T024, which Agent A keeps (annotation storage, owners/notes, polish).

**Bookkeeping exceptions (the only other writes allowed):**
1. `specs/004-deterministic-followup-queue/tasks.md`: change `- [ ]` to `- [X]` for T001–T007 only.
2. This file: append one line under "Receiver confirmation" (section 9).
3. `specs/004-deterministic-followup-queue/plan.md`: append bullets under `## Decisions (receiver log)` only.
4. `run.log`: append your session log at the end (secrets scrubbed); don't edit earlier content.

**Everything else is frozen**, including the constitution (`.specify/`), `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `checklists/`, `ACCEPTANCE.md`, `NON_GOALS.md`, `ROADMAP.md`, `data/`, `bill_split/`, `pyproject.toml`, `.gitignore`, and all existing tests. If a frozen file needs a change, STOP and report. Spec changes go only through Agent A, via Clarifications.

## 5. Approved decisions (don't re-decide)

- **Queue order (Tosin, Oct 23, option B):** bucket priority (`91+`, `61-90`, `31-60`, `1-30`, `current`, `paid`), then `remaining_balance_cents` descending, then `invoice_id` ascending, then `issuer` ascending as the last key. Sort tuple: `(BUCKET_PRIORITY[aging_bucket], -remaining_balance_cents, invoice_id, issuer)`.
- **Membership:** every accepted invoice is in the queue, including zero-balance `paid` items, which come last. Rejected and duplicate rows never appear.
- **Fixture order (SC-002, `data/invoices.csv`, as_of 2026-10-15):** `INV-1009, INV-1012, INV-1008, INV-1007, INV-1005, INV-1006, INV-1014, INV-1004, INV-1003, INV-1010, INV-1001, INV-1002, INV-1013, INV-1011`.
- **Storage (Agent A's work, for context):** one versioned UTF-8 JSON file, default `state/followup_annotations.json`, keyed by `(issuer, invoice_id)`, atomic whole-file writes. A missing file means empty; a corrupt or unsupported file is an error and is never overwritten.
- **Interface:** library API only; no CLI, network or auth.
- Clarify answers 2–5 approved by Tosin; answer 1 corrected by Tosin (see `spec.md`).

## 6. Diff baselines

| Range | Who | Meaning |
|---|---|---|
| `99d15d693a28b4b554ea4e4d53a033a74fee34ce..<PACKET_SHA>` | Sender (Agent A + operator) | Preparation: spec, plan, tasks, corrections, this packet. No feature code |
| `<PACKET_SHA>..<receiver head>` | Receiver (Agent B) | Implementation: only the paths in section 4 |

Review command: `git diff --stat <PACKET_SHA>..HEAD` must list only the allowed paths.

## 7. Evidence to return

- The confirmation line in section 9.
- `git log --oneline <PACKET_SHA>..HEAD` and `git diff <PACKET_SHA>..HEAD` (or the pushed branch name, if the operator allows a push).
- Fresh `python -m pytest -q` output after your last commit: all green (119 plus the new `tests/test_followup_queue.py` tests).
- Session log, with secrets, tokens and personal paths scrubbed.
- Start/end time (America/New_York) and usage or cost, if the harness reports it.
- Any decisions you added to `plan.md`.

**Sealed key:** `data/oracle.json` and `data/compute_oracle.py` aren't on this branch and stay with the reviewer. Don't look for them or ask for them.

## 8. Stop conditions (stop, report, don't work around)

1. The pin check in section 1 fails, or HEAD isn't `<PACKET_SHA>`, or the worktree isn't clean.
2. `python3` < 3.11, venv creation fails, or pytest isn't available (and your launch message didn't allow installing it in `.venv`).
3. The baseline isn't exactly `119 passed`.
4. `specify version` isn't 1.1.3, or integration status doesn't say "Multi-install safe: yes" (only if you ran them). `--force` is an acknowledgment of risk, not a fix.
5. The work needs a write outside section 4, a change to a frozen file, or a decision that contradicts section 5.
6. Anything would need an install beyond section 3, a key, a login, or money.
7. Another writer is active.
8. T001–T007 are done: stop there. Don't start T008 or later.

## 9. Receiver confirmation (Agent B appends one line below before coding)

Format: `YYYY-MM-DD HH:MM ET | started at <PACKET_SHA> | baseline 119 passed | owns T001–T007 | python <version>`

