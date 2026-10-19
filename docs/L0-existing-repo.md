---
title: "L0: Start from an existing repo"
---

# L0: Start from an existing repo

[← Home](index.md)

- **You are here if** you have a real codebase with existing code and tests, and no Spec Kit yet.
- **You should already have** Git, Python 3.11+ with [uv](https://github.github.io/spec-kit/install/uv.html), the `specify` CLI (see [L1](L1-setup.md) step 1), an AI coding agent, and a passing (or at least known) test suite.
- **You leave with** Spec Kit installed in place, a constitution written from your real code, a recorded test baseline, and one pilot feature built and checked against an answer key you wrote yourself.
- **Stuck on** install syntax → [L1: Setup](L1-setup.md). An agent hanging or failing → see "What went wrong" below.

Starting from an existing repo is the hardest way to begin with Spec Kit, because the agent has to respect decisions that were made long before it arrived. This page walks through six steps, using a real trial run as the example.

> **About the example.** We ran these steps on [un33k/python-slugify](https://github.com/un33k/python-slugify) (MIT license), a small Python library with a command-line tool and a strict `AGENTS.md`. The work happened in a local clone and nothing was pushed upstream. The agent was **OpenCode 1.19.3 with a free model** (`opencode/deepseek-v4.1-flash-free`), and we used specify-cli 1.1.3. The results come from one run, graded only against our own answer key and the project's tests. **They are not independently certified beyond that.**

## The short version (for seniors)

1. Take inventory before you install anything.
2. Install in place, scoped to what you'll change.
3. Write the constitution from the code; every rule must point to a file that already follows it.
4. Record a test baseline.
5. Adopt forward: only spec new work.
6. Pick a small pilot feature, write an independent answer key **before** the build, and land the spec and the code in the same commit.

In our trial, the pilot passed **8/8** answer-key cases, and the original tests stayed at **133 passed, 5 skipped** before and after. Along the way we hit a hang, two connection resets, a false claim, and a plan bug. Details are below.

## Step by step

### Step 0: Take inventory (change nothing)

Ask the agent to read the repo and write down what's already true: conventions (with file paths), how tests run, no-go areas, and the smallest folder a new feature would touch.

```bash
opencode run -m opencode/deepseek-v4.1-flash-free \
  "Do NOT install or change anything. Write INVENTORY.md: conventions (cite files), how tests run, no-go areas, smallest scope for a new CLI feature." < /dev/null
```

**What happened:** after retries, it produced a solid 41-line inventory. It correctly found the frozen files (`slugify/_legacy.py`, `tests/test_legacy.py`), the "never push to `master`" rule, and the right scope (`slugify/__main__.py` plus a new test file).

### Step 1: Install in place

```bash
specify init --here --integration opencode
```

Add `--force` if the folder isn't empty (it never is in an existing repo), and `--non-interactive` in scripts. In a monorepo, run this inside the service you're about to change, not at the root.

**What happened:** it took 1 second and only added `.opencode/commands/` and `.specify/`. No code changed.

> **Confusion point: dot or hyphen?** With the OpenCode integration, the commands are **`/speckit.constitution`, `/speckit.plan`** and so on, with a dot. Skills-based agents use `/speckit-<command>`. From a script, OpenCode takes `--command speckit.plan`. Check your agent's command folder to see which form it uses.

### Step 2: Write the constitution from the code

The **constitution** is the project's ground rules. In an existing repo, it must describe what *already* exists and what the agent must not touch. Otherwise the agent starts inventing a new architecture next to the old one.

Test for every rule: *can I point to a file that already follows it?*

```bash
opencode run -m opencode/deepseek-v4.1-flash-free --command speckit.constitution \
  "Existing repo. Write the constitution FROM THE CODE. Every principle must cite an existing file that already obeys it. Don't change code." < /dev/null
```

**What happened:** it wrote five principles (legacy output is frozen, modern behaviour is opt-in, keep the public API and CLI compatible, single-source packaging with strict typing, and evidence-based validation). Every cited file existed, and the line numbers we spot-checked were accurate.

### Step 3: Record a test baseline

Run the tests *before* any change and write the numbers down, so you can tell later whether a failure is new.

```bash
python -m pytest -q
```

**Baseline:** 133 passed, 5 skipped, 136 subtests passed.

### Step 4: Adopt forward (don't backfill)

Don't write specs for everything that already exists. Start with the next feature. Only backfill specs for the high-risk areas you're about to change.

### Step 5: Pilot feature, with an independent answer key

Pick something small, real, and easy to check. Ours was a new **`--lines`** option: with `--stdin`, slugify each line separately and print one result per line, skip blank lines, make `--lines` without `--stdin` a usage error, and leave everything unchanged when the flag isn't used.

**Before the agent builds anything**, the reviewer writes an **answer key**: a small set of inputs and expected outputs that the builder never sees. Ours had 8 cases (basic use, blank lines, options applying per line, the usage error, unchanged behaviour, max length, the modern algorithm, and line order). This matters because tests the agent writes for its own code only prove the agent agrees with itself. See the R0 lesson on the [wiki](https://github.com/tosin2013/invoice-exception-desk/wiki/R0-Results-and-Lessons).

Then run the phases:

```bash
opencode run -m opencode/deepseek-v4.1-flash-free --command speckit.specify "Spec ONLY this new feature: ..." < /dev/null
opencode run -m opencode/deepseek-v4.1-flash-free --command speckit.plan "..." < /dev/null
opencode run -m opencode/deepseek-v4.1-flash-free --command speckit.tasks "..." < /dev/null
opencode run -m opencode/deepseek-v4.1-flash-free --command speckit.implement "Make exactly ONE commit with the spec folder and the code." < /dev/null
```

| Phase | Time | Result |
|---|---|---|
| specify | 31s | 3 user stories, 10 requirements |
| plan | 152s | Plan, research, contract and quickstart files |
| tasks | 122s | 16 tasks, and it caught a plan bug |
| implement | 196s | Code, 11 new tests, README note, one commit |

### Step 6: The spec and the behaviour land together

From day one: a behaviour change and its spec change go in the **same commit or PR**. That way the spec can't quietly fall out of date.

**What happened:** pass. One commit contained the `specs/001-cli-lines-option/` folder, the code change, and the new tests.

## Results

| Check | Result |
|---|---|
| Reviewer's answer key (8 cases) | **8/8 pass** (2/8 before the build) |
| Original tests, before | 133 passed, 5 skipped |
| Original tests, after | 133 passed, 5 skipped (unchanged) |
| All tests after (with the 11 new ones) | 144 passed, 5 skipped |
| Frozen legacy files touched? | No |
| Spec and code in one commit? | Yes |

## What went wrong (and what to do about it)

1. **`opencode run` hung for about 11 minutes** with no model call when run from a script. It seemed to be waiting for input. **Fix:** add `< /dev/null`.
2. **"Connection reset by server" twice.** These were provider hiccups, not token limits. A plain retry worked.
3. **A false claim.** The plan's report said it had created a git branch. It hadn't. **Lesson:** check what the agent says against `git`.
4. **A plan bug, caught by the existing tests' rules.** The plan's design would have broken a frozen test. The tasks step noticed and fixed it. **Lesson:** this is why the constitution has to cite real files and tests.
5. **Small scope creep.** Implement also edited the README and installed extra lint and type-check tools that we hadn't asked for. It did report both, but you should still review the full diff.
6. **Partial coverage.** Only one Python version and the default backend were tested, not the project's full tox matrix. The agent said so itself.

Total time was about 26 minutes, with roughly half of that lost to the hang and the retries.

## Checklist

- [ ] Inventory written, nothing changed
- [ ] `specify init --here --integration <key>` run inside the right scope
- [ ] Constitution rules each cite an existing file
- [ ] Baseline test numbers recorded
- [ ] Answer key written by someone other than the builder, before the build
- [ ] Spec and code in the same commit
- [ ] Answer key and baseline rerun after the build

Next: [L1: Setup](L1-setup.md) if you're also new to the CLI, or L2: First feature *(coming soon)*. Back to [Home](index.md).
