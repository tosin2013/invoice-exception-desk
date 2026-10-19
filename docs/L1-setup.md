---
title: "L1: Setup"
---

# L1: Setup

[← Home](index.md)

- **You are here if** you're starting a new project with Spec Kit.
- **You should already have** Python 3.11+, [uv](https://github.github.io/spec-kit/install/uv.html), Git, and an AI coding agent.
- **You leave with** a Spec Kit project connected to one agent, plus a first constitution.
- **Existing code?** Do [L0: Start from an existing repo](L0-existing-repo.md) first.

> **Status: partly written.** Sections marked TODO aren't finished yet.

**Key terms**
- **Spec Kit**: GitHub's toolkit for Spec-Driven Development (SDD).
- **`specify` CLI**: the terminal tool that sets up a Spec Kit project.
- **Integration**: the connection between Spec Kit and a specific coding agent (Copilot, OpenCode, and so on).
- **Constitution**: a short list of project-wide principles that the agent follows in every feature.

## 1. Install the `specify` CLI

```bash
uv tool install specify-cli
specify version
```

This guide was checked against **specify-cli 1.1.3** (2026-10-18). If your version is different, trust your own `specify init --help` over this page.

## 2. Create a project and pick your agent

Taken from `specify init --help` (v1.1.3):

```bash
specify init my-project --integration copilot     # new folder
specify init . --integration opencode             # current folder
specify init --here --integration opencode        # same thing, other syntax
specify init my-project --non-interactive         # no prompts (defaults to Copilot)
```

- Run `specify check` to see the available integrations and which agent tools it can find.
- `--here --force` skips the confirmation when the folder isn't empty.

> **Confusion point: `--ai` or `--integration`?** Some blog posts and older write-ups use `--ai <agent>`. The v1.1.3 help only lists **`--integration <key>`**, so this guide uses that. Also note that the *integration key* isn't always the same as the agent's product name (OpenCode's key is `opencode`). See the [integrations reference](https://github.github.io/spec-kit/reference/integrations.html).

- [ ] TODO: show the output of `specify init` and explain the files it creates.

## 3. Use the agent commands

`/speckit-*` commands are run **in your agent's chat**, not in the terminal. The exact syntax depends on the agent. Skills-based agents use `/speckit-<command>` (or `$speckit-<command>`), while OpenCode's command integration uses **`/speckit.<command>`** with a dot (for example `/speckit.constitution`). Check your agent's command folder.

- [ ] TODO: note the model used in this project's trial (an OpenCode free model).

## 4. Write a constitution

In the agent chat, for example (OpenCode syntax shown):

```text
/speckit.constitution Create principles focused on code quality, testing, and maintainability.
```

- [ ] TODO: draft the Invoice Exception Desk constitution (integer cents, deterministic data, no PII, and an independent answer key per phase).

**Stuck?** Check `specify version` and `specify check`, then the [Installation docs](https://github.github.io/spec-kit/installation.html).

Next: L2 First feature *(coming soon)*. Back to [Home](index.md).
