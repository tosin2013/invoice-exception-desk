---
title: "L4.5: Upgrading Spec Kit itself"
---

# L4.5: Upgrading Spec Kit itself

[← Home](index.md)

- **You are here if** your project was set up with one Spec Kit version and a newer one is out. You want to move to it without losing your constitution or specs, and without breaking the lessons or branches that were recorded on the old version.
- **You should already have** a Spec Kit project with an integration installed (ours is `l3h-handoff`, OpenCode integration), `uv`/`uvx`, Python 3.11+ with pytest, and your agent CLI (we used OpenCode 1.19.3).
- **You leave with** a **repeatable routine** for any upgrade (`X.Y.Z` → next), and one worked example from a real run: **1.1.3 → 1.2.3**. In that run 6 Spec Kit-managed files changed, the constitution and `specs/` stayed byte-identical, the tests stayed at 205 passed, and one smoke command ran clean.
- **Phases shown:** read the release notes, diff the tags, dry-run in a throwaway clone, verify, upgrade on its own branch, update the doc pins, checklist and rollback. **Left out:** re-running a whole lesson on the new version (not needed this time; step 2 says when it is), `specify init --here --force`, extensions, presets, and upgrading OpenCode itself.

> **Key idea:** a Spec Kit upgrade is a **dependency bump**, not a feature. It gets its own branch, its own PR and its own receipt. It must never change your constitution or your specs. The question you're answering is: "did the files Spec Kit owns change, and did anything I own change with them?"

> **Start the exercise**
>
> ```bash
> git clone https://github.com/tosin2013/invoice-exception-desk.git /tmp/speckit-dry-run
> cd /tmp/speckit-dry-run
> git switch l3h-handoff              # the branch we upgraded (8c302ee)
> git switch -c scratch-upgrade       # throwaway: never pushed
> ```

> **Inspect our solution**
>
> - The upgrade itself is [PR #12](https://github.com/tosin2013/invoice-exception-desk/pull/12), branch [`speckit-1.2.3-upgrade`](https://github.com/tosin2013/invoice-exception-desk/tree/speckit-1.2.3-upgrade) off `l3h-handoff`. It has two commits: `ae15359` (the `specify integration upgrade` output) and `aad75d8` (README pin and a sanitized `run.log` receipt). A human reviews and merges it; until then, `l3h-handoff` is still on 1.1.3.
> - A broken link the upgrade exposed was fixed separately in [PR #11](https://github.com/tosin2013/invoice-exception-desk/pull/11). Spec Kit moved its integrations reference page.
> - Compare: [`l3h-handoff...speckit-1.2.3-upgrade`](https://github.com/tosin2013/invoice-exception-desk/compare/l3h-handoff...speckit-1.2.3-upgrade).
>
> ```mermaid
> flowchart LR
>   n1["1. release notes<br/>+ compare view"] --> n2["2. diff templates<br/>+ prompts"]
>   n2 --> n3["3. throwaway clone<br/>integration upgrade"]
>   n3 --> n4["4. verify: constitution,<br/>specs, status, tests, smoke"]
>   n4 --> n5["5. own branch + PR<br/>human merges"]
>   n5 --> n6["6. doc pins"]
>   n6 --> n7["7. checklist<br/>+ rollback"]
> ```

## Who did what in our run

| Role | Who | Did |
|---|---|---|
| **You** (the human) | Tosin | approved the upgrade plan and its recommendations; reviews and merges the PRs |
| Operator | Grok Bot | read the release notes, diffed the tags, ran the dry run and the real upgrade, wrote the receipt and this page |
| Free model | OpenCode 1.19.3 with `opencode/deepseek-v4.1-flash-free` | one read-only `/speckit.analyze` smoke run |

No answer key was needed. This change has no behaviour to grade, and the test suite plus the hash checks are the evidence.

## Before you start: two install traps

- **Pin every call.** Use `uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify`, not whatever `specify` is on your `PATH`. Our machine's default was a development build (1.2.2.dev0) that matched neither version.
- **`uv tool install` doesn't upgrade.** If you installed with `uv tool install specify-cli …`, running the same command again with a newer tag leaves the old version in place. Spec Kit's own [upgrade guide](https://github.github.io/spec-kit/upgrade.html) says so too. Add `--force`, or use `specify self upgrade` (1.2.x also has `--dry-run`), or skip installing altogether and use the `uvx` pin.

```bash
OLD=1.1.3; NEW=1.2.3                       # set these for your upgrade
alias specify-old="uvx --from git+https://github.com/github/spec-kit.git@v$OLD specify"
alias specify-new="uvx --from git+https://github.com/github/spec-kit.git@v$NEW specify"
specify-new version                        # expect CLI Version $NEW
```

## 1. Read the release notes and the compare view

```bash
gh release list -R github/spec-kit --limit 10          # is $NEW real, and is it the latest?
gh release view v$NEW -R github/spec-kit
# and in a browser: https://github.com/github/spec-kit/compare/v$OLD...v$NEW
```

Look for the words *breaking*, *migration*, *removed*, *renamed*, and anything that names your integration, `specify init`, `integration upgrade`, templates, scripts, or the feature env vars (`SPECIFY_FEATURE_DIRECTORY`, `SPECIFY_FEATURE_NO_PERSIST`).

**Our real run:** v1.2.3 is real. Tag `5ea8b1cf`, [published](https://github.com/github/spec-kit/releases/tag/v1.2.3) Oct 22, 2026 at 9:33 AM EDT, and the latest tag at the time. It came after 1.2.0 (Oct 13), 1.2.1 (Oct 16) and 1.2.2 (Oct 19). The [compare view](https://github.com/github/spec-kit/compare/v1.1.3...v1.2.3) shows **81 commits, 279 files, +22,402 / −4,091**. None of the four release notes has a breaking-change or migration notice. Most of the volume is workflows, bundles, presets, extensions and docs. It also says "behind by 1": the 1.1.3 release commit lives on a release branch, and that's harmless.

## 2. Diff the templates and command prompts between tags

This is the step that tells you how risky the upgrade is. Your lessons and specs were produced by the **templates** (`spec`, `plan`, `tasks`, …) and the **command prompts** (`clarify`, `analyze`, `implement`, …). If those didn't change, the free model sees the same instructions as before.

```bash
git clone https://github.com/github/spec-kit.git /tmp/spec-kit && cd /tmp/spec-kit
git diff --stat v$OLD..v$NEW -- templates/                 # spec/plan/tasks templates + templates/commands/
git diff --stat v$OLD..v$NEW -- scripts/bash/              # the helper scripts your agent runs (use scripts/powershell or scripts/python if that's your --script)
git diff --stat v$OLD..v$NEW -- src/specify_cli/integrations/opencode/   # your integration
```

| Result | Risk | What to do |
|---|---|---|
| `templates/` identical | low | dry run + one smoke command is enough |
| templates or command prompts changed | medium | read the diff, then **re-run one lesson** (or one small feature) end to end on a scratch branch before you trust it |
| your integration's package changed | medium | check where command files go and how the agent is invoked |

**Our real run:**
- `templates/`: **0 files changed**. All five templates and all ten command prompts are byte-identical.
- OpenCode integration package: **0 files changed**.
- `scripts/bash/`: **2 files changed**. `setup-plan.sh` now stops with an error when the plan template is missing or empty, instead of quietly writing an empty `plan.md`. `check-prerequisites.sh` now fails when `plan.md` is empty.
- `common.sh`, which resolves `SPECIFY_FEATURE_DIRECTORY` and `SPECIFY_FEATURE_NO_PERSIST`, didn't change.

So the risk was low and we didn't re-run a lesson.

Two more things we found by reading `src/` and `docs/`:
- `specify init` gained `--allow-symlinks` (default deny), and every command now refuses a symlinked `.specify/`.
- Spec Kit's docs split `reference/integrations.html` into `integrations/cli.html` plus a page per agent, so our [L1 link went 404](https://github.com/tosin2013/invoice-exception-desk/pull/11).

## 3. Dry run in a throwaway clone

Never try an upgrade for the first time on a branch you care about.

```bash
cd /tmp/speckit-dry-run                    # the scratch clone from "Start the exercise"
specify-old integration status             # baseline
specify-new integration status             # the new CLI reads the old project
specify-new integration upgrade opencode   # your integration key; NO --force
git status --short && git diff --stat
```

`specify integration upgrade` is the manifest-aware path. It compares each managed file with the hash recorded at install time. Files you never edited get refreshed, and files you did edit block the upgrade. Don't use `specify init --here --force` for an upgrade, because it overwrites shared templates.

**Our real run** (about 1 second):

```text
⚠  12 shared infrastructure path(s) already exist and were not updated:
    .specify/scripts/bash/setup-tasks.sh
    ...
    .specify/scripts/bash/check-prerequisites.sh
    .specify/scripts/bash/setup-plan.sh
    ...
To refresh shared infrastructure, run specify init --here --force or specify
integration upgrade --force.
Upgrading integration: opencode
Updated execute permissions on 6 script(s) recursively

✓ Integration 'opencode' upgraded successfully
```

```text
 .specify/init-options.json                   |  2 +-
 .specify/integration.json                    |  2 +-
 .specify/integrations/opencode.manifest.json |  4 ++--
 .specify/integrations/speckit.manifest.json  |  6 +++---
 .specify/scripts/bash/check-prerequisites.sh |  6 ++++++
 .specify/scripts/bash/setup-plan.sh          | 20 ++++++++++++--------
 6 files changed, 25 insertions(+), 15 deletions(-)
```

> **Confusion point: "were not updated" isn't true.** The warning lists `check-prerequisites.sh` and `setup-plan.sh` as "not updated", but those are exactly the two files that *did* change. They were unchanged managed copies, so the upgrade refreshed them and recorded their new hashes in `speckit.manifest.json`. The other ten are identical upstream, so there was nothing to update. **`--force` isn't needed.** It would overwrite any template you've customised. Trust `git diff`, not the warning.

The four JSON files change only the version stamps (`1.1.3` → `1.2.3`), one `installed_at` timestamp, and the two script hashes. The upgrade does *not* add the new `allow_symlinks` key to an existing `init-options.json`. Only a fresh `init` writes it (see the recapture below).

## 4. Verify: nothing you own moved

```bash
sha256sum .specify/memory/constitution.md                       # compare with the value before the upgrade
find specs -type f | sort | xargs sha256sum > /tmp/specs-after.sha
diff /tmp/specs-before.sha /tmp/specs-after.sha && echo "specs unchanged"   # take specs-before.sha before step 3
git diff --quiet HEAD -- .opencode .specify/templates .specify/memory && echo "agent commands, templates, memory unchanged"
specify-new integration status                                  # OK, 0 modified, 0 missing
python -m pytest -q                                             # same count as before
```

Then run **one** real Spec Kit command through your agent, read-only, on an existing feature. This proves the upgraded scripts still find the feature and the agent still loads the commands:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/004-deterministic-followup-queue
export SPECIFY_FEATURE_NO_PERSIST=1
opencode run --auto -m opencode/deepseek-v4.1-flash-free --command speckit.analyze \
  "Read-only smoke test after the Spec Kit upgrade. Do not modify any files." < /dev/null
git status --short                                              # still only the upgrade's files
```

`--auto` approves the agent's permission requests without stopping, so only use it in a checkout you can throw away.

**Our real run:**

| Check | Result |
|---|---|
| Constitution v2.0.0 sha256 | `3bb25f11291337e2…a784a8c` before and after |
| `specs/` (001–004), every file | same sha256 before and after |
| `.opencode/commands/` (10 files), `.specify/templates/` | unchanged |
| `specify integration status` (1.2.3) | OK, opencode only, multi-install safe, 0 modified / 0 missing (before and after) |
| `python -m pytest -q` | **205 passed** (same as before) |
| Smoke run, dry-run clone | `/speckit.analyze` on 004, exit 0, about 2 minutes, 0 CRITICAL, no files changed |
| Smoke run, upgrade branch (12:30–12:31 EDT) | exit 0, about 1 minute. `check-prerequisites.sh` resolved 004 from `SPECIFY_FEATURE_DIRECTORY`. 0 CRITICAL, 0 HIGH, 4 MEDIUM, 2 LOW, all known drift items. No files changed, no `.specify/feature.json` |

The two smoke reports don't match line for line, and they won't. The model is free and nondeterministic. What you check is: exit 0, the right feature directory, no new CRITICAL, and no file changes.

## 5. Do it for real on its own branch, then open a PR

Name the branch after the target version and base it on the branch you're upgrading. Repeat steps 3 and 4 there, then commit the upgrade output separately from your hand edits:

```bash
git switch -c speckit-$NEW-upgrade origin/l3h-handoff
specify-new integration upgrade opencode            # NO --force
git diff --stat                                     # must match the dry run; if anything else changed, stop
git commit -am "chore(speckit): upgrade Spec Kit $OLD -> $NEW via 'specify integration upgrade opencode'"
# README pins + a sanitized run.log receipt in a second commit (step 6)
git push -u origin speckit-$NEW-upgrade
gh pr create --base l3h-handoff --title "chore(speckit): upgrade Spec Kit $OLD -> $NEW"
```

A human reviews and merges it. The agent that ran the upgrade doesn't merge its own PR.

**Our real run:** branch `speckit-1.2.3-upgrade` from `8c302ee`, run between 12:29 and 12:32 EDT on Oct 24, 2026. It produced the same 6 files as the dry run, with only a different `installed_at` timestamp. The commits are `ae15359` (upgrade) and `aad75d8` (README and `run.log`): 8 files, +47 / −17 in total. That's [PR #12](https://github.com/tosin2013/invoice-exception-desk/pull/12).

## 6. Update the doc pins, but only for the current toolchain

Grep every branch for the old version:

```bash
for b in $(git branch -r | grep -v HEAD); do
  echo "## $b"; git grep -n -I "$OLD" "$b" -- . ':!*.manifest.json' ':!run.log'
done
```

Then sort each hit into one of three kinds:

| Kind of line | Example from our grep | What to do |
|---|---|---|
| **Current toolchain**, telling a reader what to install *now* | `README.md` on `l3h-handoff`: `uv tool install … @v1.1.3` | bump it to `$NEW` on the upgrade branch |
| **Historical**, recording what a past run used | "Our real run: … 1.1.3" in L3.5 and L4; the L4 preflight alias | keep it. It's a fact about that run |
| **Spec artifacts** | `specs/004-…/handoff.md` (the frozen L3.5 packet) | never edit. Specs are history the upgrade must not touch |
| Unrelated | `1.1.3` in python-slugify's own changelog on `l0-*` | ignore |

**Old lesson branches stay pinned** to the version they were recorded with (`l0-*` to `l4-start` keep 1.1.3). A reader reproducing L2 should get the CLI that L2 was recorded on, and the same templates. Only the branch you upgraded moves forward. L1 to L4 on this site still say 1.1.3 on purpose.

## Recapture: what L1 shows, on 1.2.3

[L1](L1-setup.md) quotes `specify init --help` and the `init-options.json` keys from 1.1.3, and it stays labelled that way. Here is the same material from 1.2.3 (captured Oct 24, 2026 with `uvx … @v1.2.3`).

`specify --help`. The commands are the same as in 1.1.3, and only the `mcp` description changed:

```text
 init         Initialize a new Specify project.
 check        Check that all required tools are installed.
 version      Display version and system information.
 mcp          Run the experimental MCP server over stdio.
 self         Manage the specify CLI itself: check for newer releases,
              preview upgrades with --dry-run, and upgrade in place.
 extension    Manage spec-kit extensions
 integration  Manage coding agent integrations
 event        Manage and execute event-driven commands
 preset       Manage spec-kit presets
 artifact     Introspect commands, templates, scripts, and hooks Spec Kit
              exposes.
 bundle       Discover, install, and author Spec Kit bundles
 workflow     Manage and run automation workflows
```

`specify init --help` options, with each description cut to one line (run it yourself for the full text). The only difference from 1.1.3 is the new `--allow-symlinks` option:

```text
 --script                      <str>  Script type to use: sh, ps, or py
 --ignore-agent-tools                 Skip checks for coding agent tools like Claude Code
 --here                               Initialize project in the current directory instead of creating a new one
 --force                              Force merge/overwrite when using --here (skip confirmation)
 --allow-symlinks                     Persist permission for contained symlinks in migrated
                                      FileHelper operations (default: deny).
 --non-interactive                    Never prompt. Use documented defaults ...
 --preset                      <str>  Install a preset during initialization (by preset ID)
 --integration                 <str>  AI coding agent integration to use (e.g. --integration copilot)
 --integration-options         <str>  Options for the integration
 --extension                   <str>  Install an extension during initialization. Repeatable.
 --trust-extension-urls               Pre-authorize installing extensions from external URLs
 --trust-integration                  Authorize executing a reviewed external integration package
```

`specify integration --help` is identical to 1.1.3. A fresh `specify init --here --integration opencode --script sh --non-interactive` on 1.2.3 writes this `.specify/init-options.json`:

```json
{
  "ai": "opencode",
  "allow_symlinks": false,
  "feature_numbering": "sequential",
  "here": true,
  "integration": "opencode",
  "script": "sh",
  "speckit_version": "1.2.3"
}
```

Compared with L1's 1.1.3 list, there's one new key, `"allow_symlinks": false`, and the new version stamp. An *upgraded* project keeps its old key set, apart from the version.

## 7. Checklist and rollback

### Checklist

- [ ] Release notes and the compare view read; `$NEW` exists and you know if it's the latest
- [ ] `templates/` and command prompts diffed between tags; risk decided (identical: smoke only; changed: re-run one lesson)
- [ ] Every `specify` call pinned with `uvx …@v$NEW`; `uv tool install` isn't assumed to upgrade
- [ ] Dry run in a throwaway clone: `specify integration upgrade <agent>`, **no `--force`**, `git diff --stat` recorded
- [ ] Constitution sha256 and every `specs/` file hash unchanged
- [ ] `specify integration status`: OK, 0 modified, 0 missing
- [ ] Tests: same count, all passing
- [ ] One read-only smoke command through your agent: exit 0, right feature directory, no file changes
- [ ] Real upgrade on `speckit-$NEW-upgrade`, diff identical to the dry run, the upgrade output committed on its own
- [ ] Current-toolchain pins bumped; historical lines, old lesson branches and `specs/` left alone
- [ ] Sanitized receipt in `run.log`; raw transcripts kept off the repo
- [ ] PR opened; a human merges

### Rollback

- **Before merge:** close the PR and delete the branch. Nothing else moved.
- **After merge:** `git revert` the upgrade commit. It only touches Spec Kit-managed files, so the old manifest hashes come back with it. Then run `specify-old integration status` and expect 0 modified, 0 missing. Re-run the tests.
- Old lesson branches never moved, so they don't need rolling back.

## What went wrong, and how we handled it

- **A misleading warning.** "12 paths … were not updated" plus a hint to use `--force`. We checked `git diff` and the manifest hashes instead and didn't use `--force` (step 3).
- **A broken link, already live.** Spec Kit 1.2.x moved its integrations reference, and our L1 link returned 404 before we'd upgraded anything. Upstream docs change with releases, so re-check outbound links every upgrade. Fixed in [PR #11](https://github.com/tosin2013/invoice-exception-desk/pull/11).
- **A version that matched nothing.** The machine's default `specify` was 1.2.2.dev0. Without the `uvx` pin we'd have tested a third version.
- **Stricter plan setup.** After 1.2.x, a missing or empty plan template stops `/speckit.plan` with an error, where it used to carry on with an empty `plan.md`. That's better, but if you've customised or deleted `plan-template.md`, expect the error.

Compare the branch with the upgrade: [`l3h-handoff...speckit-1.2.3-upgrade`](https://github.com/tosin2013/invoice-exception-desk/compare/l3h-handoff...speckit-1.2.3-upgrade). Next: [L5: Letting an agent loop run unattended](L5-agent-loop.md). Back: [L4: Changing a spec after code exists](L4-maintenance.md). Back to [Home](index.md).
