# Spec Kit Developer Guide: Full Outline

Guide site: https://tosin2013.github.io/invoice-exception-desk/
Wiki (older drafts): https://github.com/tosin2013/invoice-exception-desk/wiki
Order: simple to complex. Voice: friendly, plain words, each term explained the first time it appears. The guide is written while learning, so each page records where things got confusing.
Status key: **published** (live on the guide site, in `docs/`), **wiki** (draft on the wiki only), **draft** (started or partly written), **todo** (not started). Published levels: L0, L1, L2, L3, L3.5, L4, L4.5, L5, L6 and L7 (see the levels table in `README.md` and `docs/index.md`). L7 (CI is the grader) is done. Next: L8 (Dependabot, with real-world setups), then `PLAYBOOK.md`.

---

## Home (published: [`docs/index.md`](docs/index.md))
**Purpose:** welcome readers, explain what Spec Kit is in one paragraph, and show the path through the levels.
- What Spec-Driven Development (SDD) means, in plain words
- Who this guide is for, and the "learning in public" promise
- Map of levels L0 to L7, Advanced, and Reference
- The example project: Invoice Exception Desk
**Where learners get confused:** whether Spec Kit is an agent itself (it isn't; it's a toolkit plus templates that agents use).

## L1: Setup (published: [`docs/L1-setup.md`](docs/L1-setup.md))
**Purpose:** get from zero to a working `specify init` project with one agent connected.
- Prerequisites (Python 3.11+, uv, a supported agent)
- Install the `specify` CLI
- `specify init` with an integration key
- Tour of the files it creates (constitution, templates, agent folder)
- Connect an agent and run your first `/speckit-*` command
**Where learners get confused:** integration keys versus agent names; slash-command syntax differs by agent (`/speckit-x` versus `$speckit-x`); one-shot `uvx` runs don't update the installed CLI.

## L2: First feature, end to end (published: [`docs/L2-first-feature.md`](docs/L2-first-feature.md))
**Purpose:** take one small feature through every phase once, slowly, explaining each artifact.
- Constitution: write 3 to 5 ground rules
- Specify: describe the *what* and *why* (no tech choices yet)
- Clarify: let the agent ask questions and record the answers
- Plan, then tasks: choose the *how*, then break it into a checklist (`plan.md`, `tasks.md`)
- Implement: work through `tasks.md` one item at a time, committing as you go
- Review/analyze: check the code against the spec, with an independent answer key
**Where learners get confused:** what belongs in the spec and what belongs in the plan; skipping clarify; green tests mistaken for "correct"; which files each command creates or edits.

## L3: Real project, the Invoice Exception Desk walkthrough (published: [`docs/L3-invoice-desk.md`](docs/L3-invoice-desk.md); R0 page on the wiki)
**Purpose:** apply L2 to a realistic multi-feature project, in phases R0 to R6.
- What the Desk does (duplicate, inconsistent and invalid invoice handling)
- R0 Discovery recap, linking R0 Results and Lessons
- R1 onward: one feature per phase, each with a sealed answer key
- Keeping data, oracle and acceptance tests in step with one schema
- Phase exit checklist
**Where learners get confused:** "oracle" and "answer key" jargon; why the builder mustn't see the answer key; how big a "feature" should be.

## L4: Maintenance and spec changes over time (published: [`docs/L4-maintenance.md`](docs/L4-maintenance.md))
**Purpose:** show how to change a spec after code exists, without the docs and the code drifting apart.
- When to edit an existing spec and when to start a new feature folder
- Re-running plan and tasks after a spec change
- Amending the constitution, and versioning it
- Upgrading Spec Kit itself (`specify version`, templates): written up as its own lesson, L4.5 ([`docs/L45-speckit-upgrade.md`](docs/L45-speckit-upgrade.md), published)
- Spotting and fixing drift between the spec and the code
**Where learners get confused:** whether old specs are history or living docs; merge conflicts in `tasks.md`; template upgrades overwriting local edits.

## L5: Walk away — unattended issue-to-PR automation (published in part: [`docs/L5-agent-loop.md`](docs/L5-agent-loop.md), [`docs/L6-issue-to-pr.md`](docs/L6-issue-to-pr.md) and [`docs/L7-ci-grader.md`](docs/L7-ci-grader.md); automatic pickup and Dependabot still todo)
**Purpose:** the capstone. Once specs and tests are solid, let agents pick up ready issues, open pull requests, and fix routine dependency bumps while you're away. A human still makes the big calls.
- **The ready gate:** an issue is only fair game when it has the `agent-ready` label, clear acceptance criteria, and a link to its spec. No label, no robot.
- **Issues in, issues out:** the GitHub Issues Integration extension (https://speckit-community.github.io/extensions/github-issues) with `/speckit.github-issues.import`, `/speckit.github-issues.sync`, and `/speckit.github-issues.link`; plus `/speckit.taskstoissues` for turning `tasks.md` into issues (it's moving into the bundled `github` extension, so check your version).
- **The loop:** the Ralph Loop extension (https://github.com/Rubiss-Projects/spec-kit-ralph, `specify extension add ralph`) starts a fresh agent for each work unit, so old context doesn't pile up; `max_iterations` caps how long it keeps trying. It works with OpenCode free models.
- **One issue = one branch = one PR.** Small, easy-to-review changes; nothing bundled.
- **Checks before merge:** CI must pass, and a separate reviewer model (not the one that wrote the code) reviews the PR against the spec.
- **Knowing when to stop:** after a set number of retries, the agent stops and adds a `needs-human` label.
- **Dependabot PRs:** GitHub auto-merge plus branch protection merges safe bumps once checks pass; if a bump breaks the build, the agent tries a fix; major-version bumps always wait for a human. (Note: no Spec Kit Dependabot extension was found, so this uses plain GitHub features.)
- **Risks:** cost (loops can burn tokens or paid minutes), file collisions when two agents touch the same file, and weak tests that let bad code pass. Automation is only as good as your tests.
- **Ties in with:** the L4 workshop sample (`speckit-workshop-issues-sample`) and its sample issues may make a good starting set.
**Where learners get confused:** "unattended" doesn't mean "unreviewed"; which commands are core Spec Kit versus community extensions; why a fresh agent per task beats one long session.
**Status:** the first worked example is written up in [`docs/L5-agent-loop.md`](docs/L5-agent-loop.md): one sealed, unattended Ralph run on FR-007a (graded PASS, PR #14). The issue-driven parts of this outline (ready gate, issues in and out, Dependabot, `needs-human`) haven't been tried yet and aren't on that page. The second worked example, [`docs/L6-issue-to-pr.md`](docs/L6-issue-to-pr.md) (published as L6), tries part of it: a human-written issue with acceptance checks and the `agent-ready` label as the ruling, the same container, a post-run self-check instead of a sealed key (L6 ran without the Codex custodian), a separate reviewer, and a human merge (issue #16, PR #17). The third, [`docs/L7-ci-grader.md`](docs/L7-ci-grader.md) (published as L7, done), adds CI on PRs: a read-only GitHub Actions workflow grades every PR (full suite, the issue's acceptance tests added as a separate grader commit, base test IDs still present, diff size), on FR-033 (issue #22, PR #21 for the workflow, PR #23 for the change). Branch protection and required checks are mentioned there as the real-world next step but not turned on. Automatic pickup of labelled issues, `needs-human` and Dependabot are still untried. Next: L8 (Dependabot, with real-world setups), then `PLAYBOOK.md`.

## Advanced: Multi-Agent Workflow (wiki)
**Purpose:** save tokens by pairing strong models (judgment) with cheap or free models (mechanical work).
- Why mix agents
- Agent-neutral Markdown artifacts, and multiple integrations in one project
- Table mapping each phase to a model tier
- Handoff ground rules
- The R0 lesson, and a "Try it" section
**Where learners get confused:** default versus installed integrations; folders that aren't multi-install safe; extensions follow the default integration only.

## Advanced: GitHub Copilot coding agent on a Spec Kit repo (todo)
**Purpose:** turn `tasks.md` items into GitHub issues, assign them to the Copilot coding agent, and review the pull requests it opens.
- What the Copilot coding agent is (it works in the cloud and opens PRs), and that it needs a paid Copilot plan
- Turning tasks into well-scoped issues that link to the spec and plan
- Assigning issues, and what happens next
- Reviewing the PRs against the spec, with a different reviewer than the author
- Limits, costs, and when not to use it
**Where learners get confused:** the Copilot *chat* integration versus the *coding agent*; plan requirements; the agent can't see local, uncommitted specs.

## Use this in your own project: checklist (todo)
**Purpose:** a one-page checklist for adopting Spec Kit in an existing or new repo.
- Prerequisites and `specify init` (new repo) or adding Spec Kit to an existing repo
- Write the constitution first
- Pick a small first feature
- Decide on your agents and model tiers
- Set up an independent answer key and review rule
- Commit habits, and when to update specs
**Where learners get confused:** brownfield repos (existing code without specs); how much to spec up front.

## Reference: Agent Integrations vs Extensions (wiki, stub)
**Purpose:** explain the difference between an integration (which agent you use) and an extension (what Spec Kit can do).
- Definitions, with examples
- Presets, workflows and bundles (TODO)
- What this project uses
**Where learners get confused:** the similar names; installing an extension and expecting a new agent.

## Reference: R0 Results and Lessons (wiki)
**Purpose:** record an honest outcome from the free-model Discovery run.
- Setup pins
- Outputs
- Lessons: drift, schema mismatch, a self-graded oracle, independent answer keys
- Takeaway
**Where learners get confused:** "15 tests pass" doesn't mean the work is correct; unverified review points are marked TODO.
