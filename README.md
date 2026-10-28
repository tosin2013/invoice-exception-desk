# Invoice Exception Desk

Hi, and welcome! This is me **learning [GitHub Spec Kit](https://github.com/github/spec-kit) by building something real**, and writing it all down as I go.

If you're new to Spec Kit too, you're in the right place. Spec Kit helps you and an AI coding assistant write down *what* you want built (a "spec") before any code gets written. This repo and its [guide site](https://tosin2013.github.io/invoice-exception-desk/) are an honest, step-by-step record of trying that out, rough edges included.

## What you'll learn

- How to install Spec Kit and connect it to an AI coding assistant
- How to write a short "constitution", the ground rules your assistant follows
- How to take one small feature from idea to spec to plan to working code
- How a real project grows over several phases, and how to keep it on track
- What goes wrong along the way (it does!) and what to do about it

## Start here

1. Read the [guide Home page](https://tosin2013.github.io/invoice-exception-desk/) for the big picture, including a decision gate on whether Spec Kit fits your project at all.
2. Already have code? Start at [L0](https://tosin2013.github.io/invoice-exception-desk/L0-existing-repo.html). Starting fresh? Jump into [L1 Setup](https://tosin2013.github.io/invoice-exception-desk/L1-setup.html) to get your tools ready.

The guide lives in `docs/` and is published with GitHub Pages. The [wiki](https://github.com/tosin2013/invoice-exception-desk/wiki) holds older drafts.

## The levels

Each level has a page on the guide site and real branches you can check out.

| Level | What you do | Branches | Status |
|---|---|---|---|
| [L0 Existing repo](https://tosin2013.github.io/invoice-exception-desk/L0-existing-repo.html) | Add Spec Kit to a repo that already has code (python-slugify) | `l0-start` → `l0-solution` | Done |
| [L1 Setup](https://tosin2013.github.io/invoice-exception-desk/L1-setup.html) | Install Spec Kit, connect an assistant, build a tiny first feature | `l1-start` → `l1-solution` | Done |
| [L2 First feature](https://tosin2013.github.io/invoice-exception-desk/L2-first-feature.html) | Build one small feature, start to finish, graded by a hidden answer key | `l2-start` → `l2-solution` | Done |
| [L3 Real project](https://tosin2013.github.io/invoice-exception-desk/L3-invoice-desk.html) | Build the first slice of the Invoice Exception Desk (AT-01 to AT-04) | `l3-start` → `l3-solution` | Done |
| [L3.5 Agent handoff](https://tosin2013.github.io/invoice-exception-desk/L35-agent-handoff.html) | Hand work from one coding agent to another (AT-05) | `l3-solution` → `l3h-handoff` | Done (PR #5) |
| [L4 Maintenance](https://tosin2013.github.io/invoice-exception-desk/L4-maintenance.html) | Change a spec after code exists (FR-008a, constitution v2.0.0) | `l4-start` → `l3h-handoff` | Done (graded PASS, PR #8) |
| [L4.5 Upgrading Spec Kit](https://tosin2013.github.io/invoice-exception-desk/L45-speckit-upgrade.html) | A repeatable routine for upgrading Spec Kit itself (1.1.3 → 1.2.3) | `l3h-handoff` | Done (PR #12) |
| [L5 Unattended agent loop](https://tosin2013.github.io/invoice-exception-desk/L5-agent-loop.html) | Let a free-model agent loop (Spec Kit Ralph) build a ruled change in a locked-down box, graded against a sealed key, while a human keeps the big calls | `l5-setup` | One worked example done (FR-007a, graded PASS, PR #14); issue-to-PR automation not tried yet; Dependabot added in L8 |
| [L6 Issue to PR](https://tosin2013.github.io/invoice-exception-desk/L6-issue-to-pr.html) | Turn an approved GitHub issue into a PR you can trust: the issue is the ruling, a self-check the agent never sees grades it, and a human merges | `l5-setup` | One worked example done (FR-032, issue #16, self-check PASS, PR #17); automatic pickup of labelled issues not tried yet; CI added in L7 |
| [L7 CI is the grader](https://tosin2013.github.io/invoice-exception-desk/L7-ci-grader.html) | Let a read-only GitHub Actions workflow grade every PR: full suite, the issue's acceptance tests (added as a separate commit the builder never sees), and a check that no base test went missing | `l5-setup` | Done (FR-033, issue #22, CI green, PR #23) |
| [L8 Dependabot](https://tosin2013.github.io/invoice-exception-desk/L8-dependabot.html) | Let Dependabot send dependency bumps as PRs, graded by the same CI as agent PRs, with low noise and a human merge; plus real-world recipes | `l5-setup`, `main` | Done (PR #25 pin, PR #26 config; Dependabot PRs #27 and #28) |
| `PLAYBOOK.md` | The wrap-up: the whole loop in one page | — | Next |

**Who does the work:** a human or a strong model writes the constitution, the spec, and the plan. A separate reviewer holds the answer key and grades the result. A free model, running in OpenCode, runs the tasks and the implementation.

**Versions:** L1 to L4 were recorded on specify-cli 1.1.3 with OpenCode 1.19.3. L4.5 upgraded `l3h-handoff` to Spec Kit 1.2.3, and L5 to L7 run on 1.2.3 with the Ralph Loop extension v1.5.0. Older lesson branches stay on the version they were recorded with.

**Run the tests** from the repo root:

```bash
uv run --no-project --with pytest python -m pytest -q
```

`l5-setup`, the latest code, has 223 tests, and CI runs them on every PR (CI installs pytest from `requirements-dev.txt` on that branch, which Dependabot keeps up to date). `main` holds the guide and the R0 files, with 15 tests.

Curious how Spec Kit plugs into different assistants? See [Agent Integrations vs Extensions](https://github.com/tosin2013/invoice-exception-desk/wiki/Agent-Integrations-vs-Extensions).

## About the example

The project we build is an **Invoice Exception Desk**, a small tool that looks at a list of invoices and flags the ones that need attention: overdue, duplicated, or filled in wrong. It's a realistic but **fictional** business case. It's only here to give us real-world edge cases to practice on. It isn't a product, and it isn't financial advice.

## Where things stand

The files at the top of `main` come from the project's first phase (R0), a planning-only step. The code built in later levels is on the level branches above. They were **generated by a free AI model and haven't been checked by hand yet**. The model also wrote its own tests and its own expected answers, so passing tests here mostly show it agrees with itself. That turned out to be a useful lesson in its own right. Read [R0 Results and Lessons](https://github.com/tosin2013/invoice-exception-desk/wiki/R0-Results-and-Lessons) for the full story, or look at [PACKET.md](PACKET.md) and [R0_REPORT.md](R0_REPORT.md) if you want the details.

## Follow along or contribute

- Watch or star the repo to see new levels as they land.
- Spotted a mistake, or have a tip for a fellow learner? Please [open an issue](https://github.com/tosin2013/invoice-exception-desk/issues). Questions are very welcome.
- If you're working through Spec Kit too, I'd love to hear how it's going for you.

---

### Redactions

<sub>

Before publication, the following were redacted from `run.log`, `PACKET.md`, `SPEC.md`, and `ROADMAP.md`:

- Absolute home paths → `<home>/...`
- Trial working-directory path → `<workdir>`
- OpenCode session id → `<session-id>`
- Internal Notion plan/page ids → `<internal-plan-id>`

Original content and original `MANIFEST.sha256` hashes are retained privately (not in this repository).

</sub>
