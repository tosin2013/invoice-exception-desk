---
title: "L3.5: Handing work between coding agents"
description: "Hand Spec Kit work between coding agents: one agent writes the spec, plan and tasks, a second implements part of tasks.md from a cold start, and the first finishes the rest."
---

# L3.5: Handing work between coding agents

[← Home](index.md)

- **You are here if** you finished [L3](L3-invoice-desk.md) and want one agent to write the spec, plan and tasks, a second agent to implement part of `tasks.md` from a cold start, and the first agent to come back and finish the rest.
- **You should already have** the finished L3 project (`l3-solution`), specify-cli 1.1.3, OpenCode 1.19.3, Python 3.11+ with pytest, and access to a second coding agent.
- **You leave with** acceptance item **AT-05** built across one handoff and one return: a deterministic follow-up queue (`invoice_desk/queue.py`) and owners and notes kept in a versioned JSON file (`invoice_desk/annotations.py`). You also get a handoff packet you can reuse, and an honest record of what broke.
- **Phases shown:** specify, clarify, plan, tasks (agent A); a human correction before the handoff; a frozen handoff packet; implement T001 to T007 (agent B); delivery check; implement T008 to T024 (agent A); review and two rounds of review fixes. **Left out:** a sealed answer key for AT-05 (we didn't write one; see section 8), `/speckit.analyze` and `/speckit.converge` on the return, installing a second Spec Kit integration, teams of several developers (a future lesson), extensions, and `/speckit.taskstoissues`.

> **Key idea (this lesson's handoff contract):** the agents don't share memory, so **only what's committed in the repo crosses a handoff**. A decision that isn't in `spec.md`, `plan.md`, `tasks.md` or the handoff packet doesn't exist for the next agent.

> **Start the exercise**
>
> There's no separate start branch for L3.5. Start from the finished L3 code:
>
> ```bash
> git clone https://github.com/tosin2013/invoice-exception-desk.git
> cd invoice-exception-desk
> git switch l3-solution              # finished L3 (base 99d15d6)
> git switch -c my-l3h                # your own working branch
> ```

> **Inspect our solution**
>
> - [`l3h-handoff`](https://github.com/tosin2013/invoice-exception-desk/tree/l3h-handoff) has the whole run, one commit per step, ending with the merge of both agents' work. See them with `git log --oneline l3-solution..l3h-handoff`.
> - The packet agent B received is [`handoff.md` at `413f493`](https://github.com/tosin2013/invoice-exception-desk/blob/413f493b68407e7cd97df307ea67df4e838195e2/specs/004-deterministic-followup-queue/handoff.md).
> - [`run.log`](https://github.com/tosin2013/invoice-exception-desk/blob/l3h-handoff/run.log) has agent A's raw OpenCode output for specify, clarify, plan and tasks, and short session notes from both agents. Local paths are replaced with `<repo>`.
> - Compare everything: [`l3-solution...l3h-handoff`](https://github.com/tosin2013/invoice-exception-desk/compare/l3-solution...l3h-handoff).
>
> ```mermaid
> flowchart LR
>   b0["l3-solution<br/>99d15d6"] --> a1["A: specify"] --> a2["A: clarify"] --> a3["A: plan"] --> a4["A: tasks"]
>   a4 --> h1["handoff.md"] --> h2["human correction<br/>eba9925"] --> h3["packet v4<br/>413f493"]
>   h3 --> b1["B: T001-T007<br/>d4f22c7"] --> a5["A: T008-T024<br/>40ec7ac"] --> f1["review fix<br/>cd2a567"] --> f2["review fix<br/>2966b12"] --> m["merged into<br/>l3h-handoff"]
> ```

## Who did what in our run

| Role | Who | Did |
|---|---|---|
| Agent A | OpenCode 1.19.3 with the free model `opencode/deepseek-v4.1-flash-free` | specify, clarify, plan, tasks; later T008 to T024 and the review fixes |
| Agent B | A fresh OpenAI hosted-agent session, its own clone, no prior context, no Spec Kit commands | T001 to T007 only, from the packet |
| **You** (the human) | Tosin | approved the clarify answers, corrected one, approved the packet, approved installs |
| Reviewer | Grok Bot, with a second review pass by OpenAI | checked agent B's delivery, reviewed the code, re-ran the tests |

Only one Spec Kit integration (`opencode`) was installed. Agent B worked from the packet and the documents, not from `/speckit.implement`. If you want agent B to run Spec Kit commands, install a second integration first (`specify integration install claude` or `codex`). Then make sure `specify integration status` says "Multi-install safe: yes". **We didn't test this step.**

## What actually travels between agents

| State | Travels? | Where it lives |
|---|---|---|
| Constitution | Yes | `.specify/memory/constitution.md` (committed) |
| Spec, plan, tasks, contracts | Yes | `specs/004-deterministic-followup-queue/` (committed) |
| Task progress | Yes, if committed | `[X]` checkboxes in `tasks.md` |
| Code and tests | Yes | the repo |
| Active feature pointer | **No** | `.specify/feature.json` is gitignored and machine-local. Every fresh checkout has to set it again |
| Chat history and reasoning | **No** | the agent's own session |
| Decisions only said in chat | **No** | nowhere, until someone writes them into the spec or plan |

Both agents set the feature with environment variables instead of writing `feature.json`:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/004-deterministic-followup-queue
export SPECIFY_FEATURE_NO_PERSIST=1     # don't write .specify/feature.json
```

## 1. Agent A: specify, clarify, plan, tasks

Same commands as [L3](L3-invoice-desk.md), each run once with `opencode run -m opencode/deepseek-v4.1-flash-free --command speckit.<step>`. The request was "AT-05 (full): a deterministic follow-up queue … order by bucket, then balance, then invoice ID. Each queue item can carry an owner and free-text notes."

**Our real run** (times are from the `run.log` timestamps, so roughly): specify about 2 minutes, clarify about 2.5, plan about 4, tasks about 1.5. Preflight first: `specify version` reported 1.1.3, and `specify integration status` reported `opencode` as the only integration, with "Multi-install safe: yes".

- **Clarify** ran non-interactively and asked five questions. The important one was **where owners and notes are stored**. The answer: one versioned UTF-8 JSON file, default `state/followup_annotations.json`, keyed by the exact `(issuer, invoice_id)` pair, written atomically. A missing file means "no annotations". A corrupt or unsupported file is an error and is never overwritten.
- **Plan** turned that answer into a designed step and split the work into two stages. Stage 1 is pure ordering, with no file access. Stage 2 is annotation storage.
- **Tasks** made 24 tasks with a handoff line after T007. T001 to T007 (ordering) went to agent B and T008 to T024 (storage, owners, notes, polish) stayed with agent A. Check that no task above the line depends on one below it. Ours didn't.

## 2. A human check before the handoff

The request said "bucket, then balance, then invoice ID", but the spec put **issuer before invoice ID**. The model added issuer so the order would always be total. A human read the clarify answers and chose the other order: **bucket, balance (largest first), invoice ID, then issuer as the last key**. Invoice IDs are only unique within an issuer, so issuer has to come last. That correction went into the spec, plan, research, data model, contract, tasks and handoff file in one commit (`eba9925`). The frozen fixture order (SC-002) didn't change, and the suite stayed at 119 passed.

This is the cheapest place to catch a decision: before the handoff, while there's still only one agent to tell.

## 3. The handoff packet

[`handoff.md`](https://github.com/tosin2013/invoice-exception-desk/blob/413f493b68407e7cd97df307ea67df4e838195e2/specs/004-deterministic-followup-queue/handoff.md) is the one file the receiver trusts. If anything disagrees with it, the receiver stops. It holds:

- **Pins:** the git branch (`l3h-handoff`), the base (`l3-solution`, `99d15d6`), the packet commit's parent (`eba9925`), and how to check the pin with `git ls-remote` before doing anything. A file can't contain its own commit SHA, so the pin (`413f493`) was given in the launch message.
- **Checkout commands**, including the two feature environment variables above.
- **Fresh-receiver preflight:** Python 3.11+, a new `.venv`, `python -m pytest -q` must say **119 passed**, or STOP.
- **Owned tasks and paths:** T001 to T007 only, writing to `tests/test_followup_queue.py`, `invoice_desk/queue.py` and the re-exports in `invoice_desk/__init__.py`.
- **Bookkeeping it may touch:** tick T001 to T007 in `tasks.md`, append one line to `handoff.md`, add decisions to `plan.md`, and append to `run.log`.
- **Frozen:** everything else, including the constitution, `spec.md`, contracts and existing tests. A needed change means STOP and report.
- **Review command:** `git diff --stat <pin>..HEAD` must list only the allowed paths.

The packet we sent was **version 4**; it replaced an earlier, shorter `handoff.md` checklist.

## 4. Agent B: implement T001 to T007

Agent B checked the pin, started from a clean worktree, and wrote the tests first (they failed on import, as expected). Then it wrote the code: a 53-line `invoice_desk/queue.py` with `BUCKET_PRIORITY`, `accepted_invoice_identities` and `build_followup_queue`, sorted by `(bucket priority, -balance, invoice_id, issuer)`. It ticked T001 to T007, appended its confirmation line to `handoff.md`, added two decision bullets to `plan.md`, and wrote its session notes to `run.log`.

**Our real run:** about 4 hours 20 minutes elapsed (17:13 to 21:33 EDT), but almost all of that was waiting. It stopped twice, as the packet told it to:

1. **pytest wasn't installed** in its fresh environment. It stopped and didn't install anything until a human said yes. Then it installed only pytest into its `.venv`.
2. **"Branch" meant two things.** The spec and plan headers say `Feature Branch: 004-deterministic-followup-queue`, but the git branch is `l3h-handoff`. The receiver asked which one was meant. The answer: the header names the feature directory, not a git ref. The packet already says this in its pins table, but the headers still look like a git branch name.

Result: **135 passed** (119 baseline plus 16 new). Focused suite (`tests/test_followup_queue.py tests/test_invoice_desk.py`): 68 passed.

## 5. Delivery: check what arrived

Agent B's commit stayed in its own clone. It sent back the complete patch as text, with its size and SHA-256. The reviewer (Grok Bot) rebuilt the patch file and checked, in order:

| Check | Result |
|---|---|
| Size and SHA-256 match what the sender stated | 20,877 bytes, `85d07df2…f191`, both match |
| `git apply --check` on a fresh clone at the pin `413f493` | clean |
| `git diff --stat 413f493..HEAD` | only the 7 allowed paths |
| Full suite | **135 passed** |
| Code against T004 to T006 | sort key, `paid` last, `owner`/`notes` always `None`, no file access: no blocking findings |

It was committed as `d4f22c7` (parent `413f493`). The commit message says the patch is OpenAI-authored and applied by Grok Bot. When an agent can't push, **don't retype or "clean up" its work**. Move the exact bytes and prove they're the same.

## 6. Agent A returns: T008 to T024

Agent A (OpenCode, same free model) ran `/speckit.implement` once on top of `d4f22c7`, with the two feature environment variables set. **Our real run:** about 2 minutes, exit 0, commit `40ec7ac`.

- It wrote `tests/test_followup_annotations.py` first (the import failed, as expected), then `invoice_desk/annotations.py`, the re-exports, and `state/` in `.gitignore`.
- Its first targeted test run had 2 failures (99 passed). Both were mistakes in its own test fixtures, not in the code. It fixed the tests and got **168 passed** on the full suite.
- `queue.py` and agent B's tests were not touched.

We did **not** run `/speckit.analyze` or `/speckit.converge` on the return. Agent A went straight from reading the repo to implement.

## 7. Review, and two rounds of fixes

The review found real problems that the 168 passing tests didn't:

| Finding | Severity | Fix |
|---|---|---|
| The full OpenCode transcript (`agent-a-implement.log`, 674 lines) was committed, outside T024's list of allowed paths | should fix | removed in `cd2a567` |
| `set_notes(..., 5)` wrote `"notes": 5`, so **every later load failed** until someone fixed the file by hand | should fix | `cd2a567`: new `AnnotationValueTypeError` for any owner or notes that isn't a string or `None`, raised before the store is read or written |
| A hand-edited whitespace-only owner (`"   "`) came back as text, but the spec says it means unassigned | minor | `cd2a567`: treated as unassigned when reading and when writing |
| No tests for temp-file cleanup when the write or `fsync` fails | minor | `cd2a567`: tests added (**184 passed**) |
| The new type check ran **before** the accepted-identity check. T015/T016 say to raise `InvoiceNotAcceptedError` first, without touching the store | should fix | `2966b12`: identity first, then value type, then the store (**188 passed**) |

The first fix introduced the last problem: the check order was right in the tasks but wrong in the code. Each round got the same scrutiny as the first: diff stat, full suite, and a probe in a temporary folder.

**Known, non-blocking, still open:**

- If `os.fdopen` fails after the temp file is made, the file handle leaks. The temp file itself is still removed.
- `AnnotationValueTypeError` is not yet listed in the error table in `contracts/public-api.md`.
- `_set_field` repeats the accepted-identity check that `set_owner` and `set_notes` now do first. It's redundant but harmless.

## 8. Reviewer checks

| Field | Value |
|---|---|
| Tested commit | `2966b12`; the merge into `l3h-handoff` has the same tree |
| Command | `python -m pytest -q` |
| Result | **188 passed** (119 from L3, 16 queue, 53 annotations) |
| Ordering unchanged | `queue.py` and `tests/test_followup_queue.py` are identical to `d4f22c7` |
| Import unchanged | `import_invoices`, `tests/test_invoice_desk.py` and `data/` are unchanged since L3 |
| Run by | Grok Bot (Python 3.13.5, pytest 9.1.1, no new installs) |

> **Weaker than our own constitution.** Rule VIII asks for a sealed answer key per phase. **For AT-05 we didn't write one.** The frozen queue order (SC-002) came from the spec, and agent B's tests check that order, so they share the spec's reading. The review was a code review plus the builders' own tests. It caught real bugs, but it isn't the independent check that caught the paid-invoice bug in L3. Writing a sealed key for the queue order and the store's error cases is the obvious next step.

## Failure modes we actually hit

- **Silent decision, caught early.** The spec added a tie-break order nobody asked for. A human caught it before the handoff (section 2).
- **One word, two meanings.** "Feature Branch" in the spec header isn't a git branch. The receiver stopped and asked (section 4).
- **Missing tool on arrival.** pytest wasn't installed. The receiver stopped instead of installing things itself, which is what the packet said to do.
- **Work stuck on the receiver's side.** Agent B couldn't push, so its patch had to be moved by hand and checked byte for byte (section 5).
- **Scope creep in files, not code.** Agent A committed its own transcript log, outside the allowed paths (section 7).
- **Fixes need review too.** The first review fix put two checks in the wrong order (section 7).

Two we guarded against and didn't hit: two agents in one checkout (one writer at a time, separate clones), and an agent working past its handoff point (agent B's diff had only the allowed paths).

## Grading the handoff

| Criterion | Our run |
|---|---|
| Receiver asked zero questions | **No.** It stopped twice: once for install approval, once for the branch-name question |
| Every decision is findable in `plan.md` or the spec's Clarifications | **Yes.** Agent B added its two decisions to `plan.md` |
| Every `[X]` in `tasks.md` matches a fresh test run | **Yes.** 135 passed after T001 to T007, 188 after T024 |
| Receiver's diff touched only its owned paths | **Yes** |

## Retrospective

> **Was the handoff worth it here?**
>
> - **What it cost.** About 10 minutes of agent A time for specify through tasks, and a few minutes of implement time on each side. The real cost was human time: correcting the tie-break, writing and re-writing the packet to version 4, approving an install, answering the branch question, moving the patch, and two review rounds. For 53 lines of ordering code, one agent doing everything would have been faster.
> - **What it bought.** The handoff forced every decision into the repo before anyone wrote code. The receiver started cold and still built the right thing. Its delivery could be checked mechanically: hash, clean apply, allowed paths, tests. Independent review then found a bug that made the store unreadable, which 168 green tests had missed.
> - **Verdict.** Worth it as practice, and for any split where the two halves are cleanly separable. Here they were: pure ordering, then storage. It isn't a speed-up on its own. Budget for the packet and the review, and write the sealed key, which we skipped.

## Checklist

- [ ] Working on your own branch (`git switch -c my-l3h`)
- [ ] Agent A runs specify, clarify, plan and tasks. Storage is decided in clarify and designed in `plan.md`
- [ ] A human reads the clarify answers and corrects them **before** the handoff
- [ ] `tasks.md` has a clear handoff line, and nothing above it depends on anything below
- [ ] The packet names the branch, the base, how to check the pin, exact checkout and venv commands, the expected baseline, owned tasks and paths, allowed bookkeeping, and what's frozen
- [ ] The receiver checks the pin, confirms the baseline, and appends its confirmation line before coding
- [ ] The receiver STOPs instead of installing, guessing, or fixing anything outside its tasks
- [ ] The delivery is checked mechanically: hash, `git apply --check`, `git diff --stat`, full suite
- [ ] Agent A reads the diff and the ticked tasks before implementing the rest
- [ ] Every review fix is reviewed again, and non-blocking items are written down
- [ ] A sealed answer key grades the result (we skipped this; you shouldn't)

Compare the start branch with the finished steps: [`l3-solution...l3h-handoff`](https://github.com/tosin2013/invoice-exception-desk/compare/l3-solution...l3h-handoff). Next: [L4: Changing a spec after code exists](L4-maintenance.md). Back: [L3: Invoice Exception Desk walkthrough](L3-invoice-desk.md). Back to [Home](index.md).
