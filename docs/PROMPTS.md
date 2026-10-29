---
title: "Prompts: what to say to your AI"
description: "Copy-paste prompts for the Invoice Exception Desk pattern, one per situation: a new project, an existing repo, a controller/worker run, picking a harness and model, turning roadmap rows into issues, picking up after a break, and moving the roadmap forward."
---

# Prompts: what to say to your AI

These are ready-to-paste prompts for the most common situations. Each one points your AI at the matching part of the [PLAYBOOK](PLAYBOOK.md), so it follows the written steps instead of guessing.

**Before you paste:**

- **Any harness works.** The prompts write Spec Kit commands in the dotted form (`/speckit.plan`). Your agent may spell them differently: `/speckit.plan` (OpenCode, Gemini CLI), `/speckit-plan` (Claude Code, GitHub Copilot, Cursor) or `$speckit-plan` (Codex CLI). Type whatever your agent shows when you press `/` ([command spelling](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#run-spec-kit-step-by-step-no-assumptions)).
- **Fill in the `<angle brackets>`** with your own details, or delete them and let the AI ask.
- **You stay in charge.** Every prompt asks the AI to stop and wait for your OK after each step. Silence isn't approval, and a clear "approved" or "go on" is.

## 1. Start a new project from an idea

**When to use this:** you have an idea and an empty folder, and you want Spec Kit to take it from a constitution all the way to working code.

```text
I want to start a new project with GitHub Spec Kit. My idea: <one or two sentences on what and why>.
Follow "Run Spec Kit step by step (no assumptions)" exactly:
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#run-spec-kit-step-by-step-no-assumptions

Rules for this session:
1. First ask me which coding agent (harness) I use. Don't assume.
2. Setup: use only the exact commands in section A of that page. Never guess a setup step. If a command fails or a flag isn't in your --help, stop and show me the exact error. Don't try another installer, version or flag on your own.
3. Run the steps in this exact order, one per turn: /speckit.constitution, /speckit.specify, /speckit.clarify, /speckit.plan, /speckit.tasks, then /speckit.implement. (Run /speckit.analyze before implement if I ask for it.) Never skip or reorder a step.
4. Clarify questions are mine to answer. Ask me each one, one at a time, and wait. Never answer for me or quietly take the "Recommended" option. If I say "you pick", tell me your pick and why, then wait for my OK.
5. After every step, stop for my review: list each file you created or changed with a two- or three-line summary, then ask "Approve, or what should change?" Wait for a clear yes.
6. Never run implement until tasks.md exists and I've approved it.
7. If anything is unclear or conflicts, stop and ask.
Start by asking your first question.
```

Read more: [Run Spec Kit step by step](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#run-spec-kit-step-by-step-no-assumptions) · [L1: Setup](L1-setup.md)

## 2. Bring Spec Kit into an existing (or messy) repo

**When to use this:** the repo already has code, maybe a lot of it, and you want a roadmap first so you know which feature to spec next.

```text
This repo already has code: <repo path or URL>. Before we spec anything, help me plan the roadmap.
Follow "PM: plan the roadmap first":
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#pm-plan-the-roadmap-first
and then "Run Spec Kit step by step (no assumptions)":
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#run-spec-kit-step-by-step-no-assumptions

Rules:
1. Ask me which coding agent I use. Check that git status is clean before any `specify init --here`, and only run it in this repo.
2. Read the code and docs first. Then draft ROADMAP.md at the repo root with the playbook's columns (ID, Feature, scope in/out, Outcome, Depends on, Order, Milestone, Status, Spec dir, Issue / PR). Mark work that already exists as done (pre-Spec Kit) only if I confirm it.
3. Optional tooling: if I want it, use the speckit-roadmap extension pinned to its v0.1.1 tag (https://github.com/srobroek/speckit-roadmap/archive/refs/tags/v0.1.1.zip), as the playbook does, and repo-governor only if I ask for it. Check the playbook's notes on each before you trust them; the plain ROADMAP.md works without either.
4. STOP and show me the roadmap. Wait for my approval.
5. After I approve, spec exactly one feature: the first planned row whose dependencies are done. Run /speckit.specify with an Input line citing its row ID, then clarify, plan, tasks, implement in that order, one per turn.
6. Ask me every clarify question yourself, one at a time. After each step, show me what changed and wait for my OK.
Start by asking your first question.
```

Read more: [PM: plan the roadmap first](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#pm-plan-the-roadmap-first) · [L0: Start from an existing repo](L0-existing-repo.md)

## 3. Run a controller and a worker

**When to use this:** you want a strong (frontier) model to own the thinking and a cheaper model to do the typing in a sandbox, so you save tokens without giving up review.

```text
Act as the controller in the controller/worker pattern:
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#the-philosophy-controller-and-worker

Your job (controller):
1. Write and keep the spec, plan and tasks with me, using /speckit.specify, /speckit.clarify, /speckit.plan, /speckit.tasks and /speckit.analyze. I answer every clarify question, and I approve each file before the worker starts.
2. Help me set up the worker: a cheaper model in a headless harness, run in a sandbox (container or VM) on any host I approve, with a capped loop that builds one user story per pass:
   https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#how-the-ralph-loop-runs-each-spec
3. You never hold the worker's credential. The worker's box gets one dedicated, spend-capped model credential at run time, no push access and no other keys. Don't ask me to paste it to you.
4. The worker's output leaves the box as a git bundle. Nothing pushes on its own.
5. When the bundle comes back, review it against the spec and the acceptance checks the worker never saw. The worker never reviews its own work.
6. I merge. You never merge, push or open a PR unless I tell you to.
First ask me which controller and worker harnesses and which host I have. If anything is unclear, stop and ask.
```

Read more: [The philosophy: controller and worker](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#the-philosophy-controller-and-worker) · [Do I always need a sandbox?](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#do-i-always-need-a-sandbox) · [4. The end-to-end loop](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#4-the-end-to-end-loop) · [L5](L5-agent-loop.md)

## 4. Choose a harness and a model provider

**When to use this:** you're about to set up the worker (or any headless run) and need to pick the coding agent and the model it uses.

```text
Help me pick a harness and a model provider, following:
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#2-choose-your-harness
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#choose-a-model-provider-for-the-ralph-box

Before you recommend anything, ask me:
1. Which harnesses I already have (for example Claude Code, Codex CLI, Copilot CLI, OpenCode, Gemini CLI, Cursor), or check with `command -v` and confirm with me.
2. Which model credentials I have: a paid API key, a subscription login, a cloud endpoint (Vertex AI, Bedrock, Azure OpenAI), a gateway, or a free/local model.
3. The exact model ID and my spend cap, and what enforces it.
Then recommend one pairing and explain why. Native login (a subscription sign-in) is optional; prefer a dedicated, spend-capped key for unattended runs. Never ask me to paste a credential into this chat, and never write one into a config file or image. Suggest a one-task dry run before anything unattended.
```

Read more: [2. Choose your harness](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#2-choose-your-harness) · [Choose a model provider](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#choose-a-model-provider-for-the-ralph-box)

## 5. Turn roadmap rows into issues

**When to use this:** your ROADMAP.md is approved and you want an issue per row (or per task) where people can discuss and rule on the work.

```text
Open or update issues for the rows in ROADMAP.md, following "Open issues against the roadmap" in:
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#pm-plan-the-roadmap-first

1. Ask me which platform hosts this repo (GitHub, GitLab, Bitbucket, Azure DevOps, Jira, other).
2. GitHub: for rows, search first (gh issue list --state all --search "R2 in:title") and reuse what exists. For a feature's tasks, use Spec Kit's bundled github extension (specify extension add github, then /speckit.github.taskstoissues).
   Other platforms: search for that platform's extension first (specify extension search <platform>, or the community extensions page) and show me what you find before installing. If there's none, use the platform's own CLI or web UI.
3. Each issue title starts with the row ID ("R2: ...") and the body says "Roadmap: R2". Paste each link into the row's Issue / PR column.
4. Show me the list you'd reuse, update or create, and wait. Creating or editing issues needs my explicit OK; approving the roadmap isn't that OK. Status stays in ROADMAP.md, not in the issues.
```

Read more: [PM: plan the roadmap first](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#pm-plan-the-roadmap-first)

## 6. Pick up after a break or a hand-off

**When to use this:** you're coming back after time away, or a different agent (or person) is taking over the work.

```text
I'm picking this work back up (or handing it over). Agents don't share memory, so only what's committed counts:
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#5-roles-and-trust-boundaries

1. Don't rely on anything from an earlier chat. Read the committed record: ROADMAP.md, .specify/memory/constitution.md, and the current feature's spec.md, plan.md and tasks.md (plus any handoff or progress notes in the repo), and run git status and git log.
2. Tell me, briefly: which roadmap row and Spec Kit step we're on, which tasks are ticked, what's uncommitted, and anything that looks out of date or conflicting.
3. Propose the single next step, spelled the way my agent shows it. Don't run it yet.
4. Wait for my OK. If a decision isn't written down anywhere, ask me; don't guess.
```

Read more: [5. Roles and trust boundaries](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#5-roles-and-trust-boundaries) · [L3.5: Handing work between coding agents](L35-agent-handoff.md)

## 7. Move the roadmap forward

**When to use this:** you have a ROADMAP.md and want to know what's done, what's next, and fix drift.

```text
Read ROADMAP.md, the open issues and merged PRs, and the specs/ folder.
1. Tell me which roadmap rows are done, in progress or blocked, with evidence (PR, spec, test results). Don't mark anything done without evidence.
2. Recommend the next 1–3 rows to start, based on priority, dependencies and what's unblocked. Explain each choice in one line.
3. Flag any drift: specs with no roadmap row, rows with no spec, or a stale status.
4. Propose the ROADMAP.md edits as a diff, and keep any integrity steps the repo uses (hashes, drift check).
Stop there. Don't edit files, open issues or start a spec until I approve. Once I pick a row, start /speckit.specify for that row only.
```

Read more: [PM: plan the roadmap first](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#pm-plan-the-roadmap-first)
