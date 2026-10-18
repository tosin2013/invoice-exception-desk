---
title: Home
---

# Spec Kit Developer Guide

Welcome! This guide follows one real project, the **Invoice Exception Desk**, from simple to complex using [GitHub Spec Kit](https://github.com/github/spec-kit). It's written while learning, so it also records the places where things got confusing.

## Who this is for

- **Mainly:** senior engineers, tech leads and architects who already build with an AI coding agent (Copilot, Claude Code, OpenCode and so on), but are new to Spec Kit and **Spec-Driven Development (SDD)**. SDD means writing down *what* to build and *why* before deciding *how*. You want a flow you can trust on a real project.
- **Also:** mid-level developers who are adopting agents and want a guided first run. Read L1 and L2 in order.
- **Also:** leads deciding whether SDD fits their team. Start with the decision gate below.

## Should this work use SDD at all?

> **Draft, pending Muse's text.** This gate is a short summary and will be replaced by the full "Spec Kit guide additions v0.1" text.

Ask yourself five questions:

1. Will anyone have to maintain this?
2. What does it cost if it's wrong?
3. Does it cross a service, team or data-schema boundary?
4. Can you describe the requirement before the code exists?
5. How much important context lives outside the prompt?

Then pick a tier:

| Tier | When | What it looks like |
|---|---|---|
| **Full SDD** | Heavy, risky work: money paths, cross-service changes, public APIs | Constitution, spec, clarify, plan, tasks, and an independent answer key |
| **Light SDD** | Ordinary features | A short spec and a brief plan |
| **No SDD** | Typo, config change, dependency bump, one-line fix, prototype | A normal pull request |

**Honest costs:** SDD is slower on day one. The main failure is "spec theatre", meaning writing specs nobody uses. And a stale spec is worse than no spec, because it misleads the next agent that reads it.

## Where are you in your project?

| You are… | Go to |
|---|---|
| Adding Spec Kit to an existing repo | **L0: Start from an existing repo** *(coming soon)* |
| Starting fresh and need to install | [L1: Setup](L1-setup.md) |
| Ready to build your first feature | **L2: First feature, end to end** *(coming soon)* |
| Working on a real multi-feature project | **L3: Invoice Exception Desk walkthrough** *(coming soon)* |
| Changing specs after code exists | **L4: Maintenance** *(coming soon)* |
| Mixing agents or using the Copilot coding agent | **Advanced** *(coming soon)* |

Until those pages move here, the [project wiki](https://github.com/tosin2013/invoice-exception-desk/wiki) has the current drafts, including R0 Results and Lessons and Multi-Agent Workflow.
