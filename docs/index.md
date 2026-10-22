---
title: Home
---

# Spec Kit Developer Guide

Welcome! This guide teaches [GitHub Spec Kit](https://github.com/github/spec-kit) from simple to complex. It starts with two small onboarding exercises (L0 adds a feature to the open-source `python-slugify` library, and L1 builds a tiny `split_bill` app), then moves to one real multi-feature project, the **Invoice Exception Desk**, from L3 on. It's written while learning, so it also records the places where things got confusing.

## Who this is for

- **Mainly:** senior engineers, tech leads and architects who already build with an AI coding agent (Copilot, Claude Code, OpenCode and so on), but are new to Spec Kit and **Spec-Driven Development (SDD)**. SDD means writing down *what* to build and *why* before deciding *how*. You want a flow you can trust on a real project.
- **Also:** mid-level developers who are adopting agents and want a guided first run. Read L1 and L2 in order.
- **Also:** leads deciding whether SDD fits their team. Start with the decision gate below.

### Who does the work

Every level uses the same split. A human or a strong model writes the constitution, the spec, and the plan. A separate reviewer holds the answer key and grades the result. A free model runs the tasks and the implementation.

```mermaid
flowchart LR
  H["Human / strong model"] -->|constitution, spec, plan| S[(specs/)]
  R["Reviewer"] -->|answer key, grading| S
  F["Free model"] -->|tasks + implement| C[(code + tests)]
  S --> F
  C --> R
```

## The Spec Kit loop

Every feature goes around the same loop. The constitution is written once; then each change starts again at Specify.

```mermaid
flowchart LR
  lpA[Constitution] --> lpB[Specify]
  lpB --> lpC[Clarify]
  lpC --> lpD[Plan]
  lpD --> lpE[Tasks]
  lpE --> lpF[Implement]
  lpF --> lpG[Review]
  lpG -->|next change| lpB
```

## The Decision Gate: should this project use Spec Kit at all?

Spec Kit is not free. Writing the spec, the plan, and the acceptance tests costs real time before a line of code exists, and that cost is only repaid when the cost of building the WRONG thing is higher. Run this gate before Level 0. Answer honestly — the gate has no prize for yes.

**1. Can you say, in advance, what "done" looks like as checkable outcomes?**
Not a vibe — outcomes a test or a reviewer could pass or fail. If the work is exploratory ("let's see what's possible"), a spec will slow you down and teach you nothing the prototype wouldn't. Prototype first; specify when the shape is known.

**2. Is the work bigger than one sitting?**
If one person, or one agent session, can hold the whole change in mind and verify it by reading it, the ceremony buys nothing. Spec Kit earns its keep when the work spans sessions, agents, or weeks — when no single reader holds the whole thing.

**3. Will someone other than the builder check the result?**
This is the gate most projects fail quietly. In our own first trial, the model wrote the code, the oracle, AND the tests — and unsurprisingly passed. That demonstrates scaffolding, not capability. If the same hands write the spec, the code, and the answer key, label the result self-graded and do not call it verified. Independent checking can be a second model, a frozen fixture written before the run, or a human with the acceptance list — but it must be independent.

**4. Are the expensive mistakes the quiet kind?**
Crashes announce themselves. A totals column that is plausibly wrong, a rule applied almost everywhere, behavior that drifts a little each iteration — those are the failures specs and acceptance tests exist to catch. If your project's real risk is quiet wrongness, specify. If its risk is loud failure, ordinary tests are cheaper.

**5. Do you have one frozen example to specify against?**
A worked case — real data, a prior implementation, a hand-checked fixture — anchors everything. Specs written without an anchor drift into describing the system you wish you had.

**Reading your answers**

- **Mostly yes:** proceed to Level 0. The levels ahead assume these conditions.
- **Yes except #3:** proceed, but add an independent check before anything is called done — and say "self-graded" out loud until you do.
- **No on #1 or #2:** don't adopt yet. That's a real answer, not a failure; the guide will still be here when the project grows into the shape where specifying pays.

*Spec Kit doesn't make a model honest. It makes dishonesty easier to catch — if someone else is holding the answer key.*

### If you proceed: how much SDD?

Pick a tier:

| Tier | When | What it looks like |
|---|---|---|
| **Full SDD** | Heavy, risky work: money paths, cross-service changes, public APIs | Constitution, spec, clarify, plan, tasks, and an independent answer key |
| **Light SDD** | Ordinary features | A short spec and a brief plan |
| **No SDD** | Typo, config change, dependency bump, one-line fix, prototype | A normal pull request |

**Honest costs:** SDD is slower on day one. The main failure is "spec theatre", meaning writing specs nobody uses. And a stale spec is worse than no spec, because it misleads the next agent that reads it.

## How each level's branches work

A finished level is two branches. `lN-start` is the tree you begin from. `lN-solution` is the same work, one commit per step.

```mermaid
gitGraph
  commit id: "lN-start"
  branch solution
  commit id: "step: init"
  commit id: "step: constitution"
  commit id: "step: spec + plan"
  commit id: "step: implement"
```

Check out `lN-start` and follow the page. Compare with `lN-solution` when you want the finished steps. `git log --oneline` on the solution branch lists them. L0, L1, and L2 name the real branches in the table below.

## Where are you in your project?

Start at L0 when the repo already has code, and at L1 when it does not. L3 and L4 are paused pending review. L5 is an outline.

```mermaid
flowchart LR
  Q{Existing code?} -->|yes| L0["L0: adopt in existing repo"]
  Q -->|no| L1["L1: setup + tiny feature"]
  L0 --> L2["L2: first feature"]
  L1 --> L2
  L2 --> L3["L3: multi-feature (paused)"] --> L4["L4: maintenance (paused)"] --> L5["L5: unattended (outline)"]
```

| You are… | Go to | Branches |
|---|---|---|
| Adding Spec Kit to an existing repo | [L0: Start from an existing repo](L0-existing-repo.md) | [`l0-start`](https://github.com/tosin2013/invoice-exception-desk/tree/l0-start) → [`l0-solution`](https://github.com/tosin2013/invoice-exception-desk/tree/l0-solution) |
| Starting fresh and need to install | [L1: Setup](L1-setup.md) | [`l1-start`](https://github.com/tosin2013/invoice-exception-desk/tree/l1-start) → [`l1-solution`](https://github.com/tosin2013/invoice-exception-desk/tree/l1-solution) |
| Ready to build your first feature | [L2: First feature, end to end](L2-first-feature.md) | [`l2-start`](https://github.com/tosin2013/invoice-exception-desk/tree/l2-start) → [`l2-solution`](https://github.com/tosin2013/invoice-exception-desk/tree/l2-solution) |
| Working on a real multi-feature project | **L3: Invoice Exception Desk walkthrough** *(paused pending review)* | — |
| Changing specs after code exists | **L4: Maintenance** *(paused pending review)* | — |
| Ready to let agents work unattended | **L5: Walk away, unattended issue-to-PR automation** *(proposed — pending review; untested)* | — |
| Mixing agents or using the Copilot coding agent | **Advanced** *(coming soon)* | — |

Until those pages move here, the [project wiki](https://github.com/tosin2013/invoice-exception-desk/wiki) has the current drafts, including R0 Results and Lessons and Multi-Agent Workflow.
