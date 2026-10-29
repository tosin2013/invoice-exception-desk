# PLAYBOOK: the Invoice Exception Desk pattern on one page

This is the wrap-up of the [Spec Kit Developer Guide](https://tosin2013.github.io/invoice-exception-desk/). It sums up the whole pattern and links every lesson, so a person or an AI can pull this one file and apply the pattern to its own project.

- Raw file, for agents: <https://raw.githubusercontent.com/tosin2013/invoice-exception-desk/main/PLAYBOOK.md>
- On the guide site: <https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html>
- Guide index for agents: [`llms.txt`](https://tosin2013.github.io/invoice-exception-desk/llms.txt) (same content as [`llm.txt`](https://tosin2013.github.io/invoice-exception-desk/llm.txt))

Everything below comes from what the repo and its lessons actually show. Numbers are from our runs, not promises.

## 1. The pattern in a few sentences

Write down *what* to build and *why* before any code exists (a constitution once, then a spec per change), using [GitHub Spec Kit](https://github.com/github/spec-kit). A human (or a strong model) makes every decision **before** the run and writes it into one frozen ruling: a signed file in L5, a GitHub issue from L6 on. A cheap or free model then builds it unattended, inside a locked-down box with no keys, driven by a loop with hard caps. We used OpenCode with the Spec Kit **Ralph Loop** extension; any coding-agent harness that can run headless works (section 2). The result is graded by checks the builder never saw: a sealed answer key (L2 to L5), a hidden self-check (L6), then a read-only CI workflow (L7). A human merges every PR. Dependabot's PRs go through the same CI and the same human merge (L8).

> "Unattended" doesn't mean "unreviewed." Decide everything before the run, check everything after it. ([L5](https://tosin2013.github.io/invoice-exception-desk/L5-agent-loop.html))

**Should you use it at all?** Run the [decision gate on the Home page](https://tosin2013.github.io/invoice-exception-desk/) first. Short version: you need checkable "done" outcomes, work bigger than one sitting, someone other than the builder checking the result, quiet-wrongness risks, and one frozen example to specify against. Typos, config changes, dependency bumps and prototypes get a normal PR, not SDD.

## 2. Choose your harness

The pattern isn't tied to one coding agent. The builder step needs three things:

- **A coding agent that can run headless** (from a script, no prompts). Run unattended, it goes in a sandbox with no GitHub token, SSH keys or cloud credentials beyond a model-only, spend-capped identity ([when you need one](#do-i-always-need-a-sandbox), [which credential](#choose-a-model-provider-for-the-ralph-box)). Spec Kit has integrations for 40-plus agents, for example Claude Code (`claude`), Codex CLI (`codex`), GitHub Copilot (`copilot`), Gemini CLI (`gemini`), Cursor (`cursor-agent`), Goose (`goose`), Qwen Code (`qwen`) and opencode (`opencode`). The full list and keys are on the [Spec Kit integrations page](https://github.github.io/spec-kit/integrations/index.html); `generic` covers agents that aren't listed.
- **A loop driver with an iteration cap and a time cap** that starts a fresh agent call per work unit and stops on repeated failures. The [Ralph Loop](https://github.com/Rubiss-Projects/spec-kit-ralph) extension (v1.5.0) does this for `copilot`, `codex`, `claude` and `opencode` only, and refuses any other CLI. For anything else, use a small wrapper script with the same caps and stops (section 7).
- **The written inputs:** the issue (the ruling), then the spec, plan and tasks files.

This guide used **OpenCode 1.19.3 with the free model `opencode/deepseek-v4.1-flash-free`, driven by Ralph**. It stays the worked example throughout; notes marked "If you use OpenCode" or "If you use Ralph" apply only to that setup. Our box held no keys at all, because the free model needed none. If your model needs an API key, a subscription login or a cloud endpoint, see the key rule and [Choose a model provider for the Ralph box](#choose-a-model-provider-for-the-ralph-box) just below.

### Do I always need a sandbox?

No. A sandbox matters when an agent runs code **unattended**, with no person approving each step: the L5 to L7 builder loop, or any auto-approve ("yolo") mode. It limits the blast radius of a bad run: deleted files, a bad command, or the agent reading secrets.

| Situation | Sandbox? | Keys |
|---|---|---|
| A person approves each step (Claude Code, Cursor, Copilot and others in their normal ask-before-acting mode) | No; a normal dev machine is fine | your usual setup |
| Spec, plan and review work | No | your usual setup |
| The agent runs unattended (builder loop, auto-approve or "yolo" mode) | Yes: a container or VM with a copy of the repo; the work comes out as a `git bundle` ([L5](https://tosin2013.github.io/invoice-exception-desk/L5-agent-loop.html), [L6](https://tosin2013.github.io/invoice-exception-desk/L6-issue-to-pr.html)) | no GitHub token, SSH keys or cloud credentials beyond a model-only, spend-capped identity; at most one model credential (below) |
| CI grading | Nothing extra: [GitHub-hosted runners](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners) are already isolated | none; the workflow stays read-only with no secrets (section 5) |

**If the model needs an API key:** passing one into the container is fine if it's a dedicated, spend-capped key used only for that work, never one that can push code or reach production. A free or local model (for example [Ollama](https://ollama.com/)) needs no key. Subscription logins, Vertex AI, Bedrock, Azure and gateways: see [Choose a model provider for the Ralph box](#choose-a-model-provider-for-the-ralph-box).

**Rule of thumb:** sandbox the agent when nobody is watching each step, and give it only the one key it needs.

### Choose a model provider for the Ralph box

Our box held no credentials because the free model needed none. A paid, subscription or company model means **one** model credential goes into the box. Ralph doesn't manage it: it passes `--model` to the harness and stores no credentials ([Ralph README](https://github.com/Rubiss-Projects/spec-kit-ralph)). The harness reads them from its own env vars or files, so the box has to supply them.

**Ask the user first** (don't assume OpenCode or a free model):

1. **Harness:** `copilot`, `codex`, `claude` or `opencode` for Ralph, or another one behind a wrapper (section 2).
2. **Provider:** a paid API key, a subscription login (Claude Pro/Max, ChatGPT Plus/Pro, GitHub Copilot), a cloud endpoint (Google Vertex AI, Amazon Bedrock, Azure OpenAI), a gateway or proxy (LiteLLM, OpenRouter, a company gateway, any OpenAI-compatible URL), or a local model (Ollama, LM Studio, llama.cpp).
3. **Model:** the exact ID the harness expects (for OpenCode, a `provider/model` ID from `opencode models`).
4. **Spend cap:** the amount, and what enforces it (a key limit, a gateway budget, a cloud quota). Write it in the ruling (section 7, Spend).

Then dry-run one scripted call in the real container with that credential before you seal anything.

| Provider type | What goes into the box | How to pass it | Least-privilege notes |
|---|---|---|---|
| Free or local model (OpenCode free models, Ollama, LM Studio) | nothing, or a base URL | `baseURL` in the harness config, in the read-only tools mount | no key. Inside a container `localhost` is the container, so point at the host's address and open only that port |
| Paid API key (Anthropic, OpenAI, OpenRouter, OpenCode Zen, ...) | one env var | `docker run --env-file <file outside the repo>`, or `-e NAME` with no value so it's copied from the operator's shell | a new key for this work only, with a spend limit at the provider; revoke or rotate it after the run |
| Subscription login (Claude `setup-token`, Codex ChatGPT login, Copilot) | a user token or a login file | an env var, or the auth file mounted read-only (`-v <file>:<path>:ro`) | it's your personal account and plan, and the token can live a year. Prefer an API key for unattended runs. Check the provider's terms (OpenCode's docs say Anthropic prohibits using Pro/Max through OpenCode) |
| Google Vertex AI | project ID, region, a credential file | env vars plus the credential file mounted `:ro`, `GOOGLE_APPLICATION_CREDENTIALS` set to its path | a model-only identity (below) |
| Amazon Bedrock | region plus a short-term Bedrock API key or temporary AWS credentials | env vars | a model-only identity (below) |
| Azure OpenAI | resource name plus a key | env vars | a key for one resource that holds only the deployments you use. Entra ID sign-in needs the Azure CLI and its session in the box; if you use it, give that identity only Cognitive Services OpenAI User |
| Gateway (LiteLLM, OpenRouter, a company proxy) | the gateway URL plus a gateway key | URL in the harness config, key as an env var | the raw provider keys stay on the gateway (below) |

Never bake a credential into the image, commit it, or write its value into `ralph-config.yml` or the harness config. Use a reference instead (OpenCode: `{env:NAME}` or `{file:path}`).

**Per-harness cheat sheet.** Checked against each harness's docs on Oct 28, 2026. Names change, so check your version.

- **OpenCode** ([providers](https://opencode.ai/docs/providers/), [config](https://opencode.ai/docs/config/), [CLI](https://opencode.ai/docs/cli/)). `opencode auth login` (or `/connect`) saves keys in `~/.local/share/opencode/auth.json`. OpenCode also loads keys from the environment, so in the box skip the login and pass an env var. Key names come from [Models.dev](https://models.dev): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `OPENCODE_API_KEY` (Zen), and `AZURE_RESOURCE_NAME` with `AZURE_API_KEY` (Azure). Vertex AI: `GOOGLE_CLOUD_PROJECT`, `VERTEX_LOCATION` (default `global`) and `GOOGLE_APPLICATION_CREDENTIALS`. Bedrock: `AWS_REGION` plus `AWS_BEARER_TOKEN_BEDROCK` (wins over everything else), access keys or `AWS_PROFILE`. For Ollama, a gateway or any OpenAI-compatible URL, add a `provider` block with `"npm": "@ai-sdk/openai-compatible"` and `options.baseURL`. `OPENCODE_CONFIG` points at the config file (ours was the read-only `tools/opencode.json`), and `enabled_providers` limits OpenCode to the one provider you chose.
- **Claude Code** ([authentication](https://code.claude.com/docs/en/authentication), [Vertex AI](https://code.claude.com/docs/en/google-vertex-ai), [Bedrock](https://code.claude.com/docs/en/amazon-bedrock), [gateway](https://code.claude.com/docs/en/llm-gateway-connect)). API key: `ANTHROPIC_API_KEY`, always used in `-p` mode, which is how Ralph runs it. Subscription: `CLAUDE_CODE_OAUTH_TOKEN`, a one-year token from `claude setup-token` (Pro, Max, Team or Enterprise; not read with `--bare`). Vertex AI: `CLAUDE_CODE_USE_VERTEX=1`, `CLOUD_ML_REGION` and `ANTHROPIC_VERTEX_PROJECT_ID`, plus `GOOGLE_APPLICATION_CREDENTIALS`. Bedrock: `CLAUDE_CODE_USE_BEDROCK=1` and `AWS_REGION`, plus `AWS_BEARER_TOKEN_BEDROCK` or AWS credentials. Gateway: `ANTHROPIC_BASE_URL` plus `ANTHROPIC_AUTH_TOKEN` (bearer) or `ANTHROPIC_API_KEY` (`x-api-key`).
- **Codex CLI** ([auth](https://developers.openai.com/codex/auth), [non-interactive](https://developers.openai.com/codex/noninteractive), [advanced config](https://developers.openai.com/codex/config-advanced)). API key: `CODEX_API_KEY` for `codex exec`, which is what Ralph runs. A ChatGPT login lives in `~/.codex/auth.json` (under `CODEX_HOME`); the docs show copying it into a container, and say to treat it like a password. Other endpoints go in `config.toml`: `model_provider` plus a `[model_providers.<id>]` table with `base_url` and `env_key` (the docs' Azure example uses `env_key = "AZURE_OPENAI_API_KEY"`), `openai_base_url` for a proxy in front of OpenAI, and a built-in `amazon-bedrock` provider that uses the AWS credential chain.
- **Copilot CLI** ([authenticate](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli), [reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)). It authenticates with a GitHub token (`COPILOT_GITHUB_TOKEN`, then `GH_TOKEN`, then `GITHUB_TOKEN`), and the box allows no GitHub token. Two ways to stay within the rule. Bring your own key: `COPILOT_PROVIDER_BASE_URL` plus `COPILOT_PROVIDER_API_KEY` (or a `COPILOT_PROVIDERS_CONFIG` file), with `COPILOT_OFFLINE=true`, needs no GitHub sign-in. Or, for Copilot's own models: a fine-grained token owned by your personal account with only the **Copilot Requests** account permission, public-repository access only and a short expiry, passed as `COPILOT_GITHUB_TOKEN` so no other tool picks it up. With no repository write permission it can't push. Classic `ghp_` tokens aren't supported.

**Docker specifics.**

- Keep the env file outside the repo and the run folder (for example `~/.config/ralph-box/model.env`, `chmod 600`). Add `*.env` and `.env*` to `.gitignore` anyway, as a backstop. Never write `-e NAME=value` on the command line, where it ends up in shell history and `ps`.
- Nothing secret at build time: no `ARG` or `ENV` holding a key and no `COPY` of an auth file. [Docker's docs](https://docs.docker.com/build/building/secrets/) say build args and env vars persist in the final image. The image is built with no credentials at all.
- Env values show up in `docker inspect`. For files (a Vertex credential, `auth.json`), mount them read-only from a folder outside the run folder (the builder can write to the run folder) and point the harness at that path.
- Our preflight fails on any credential-like env var or auth file (probes P02 and P04). Allow exactly the one variable or file you chose, keep failing on everything else (`GH_*`, SSH agent, `~/.aws`, `~/.config/gcloud`), and record names, never values, in the receipt.
- Network: our box used `--network bridge` with no domain limit. If you can, allow egress only to the provider's endpoint (a host firewall rule or an egress proxy), so code can only go to the model.
- After the run: delete the env file or file copy, revoke short-lived tokens, rotate the key if anything looked off, and check the provider's usage page against the cap. `--rm` and the tmpfs `HOME` already discard anything the harness saved during the run.

**Vertex AI and Bedrock: a model-only identity.** These need cloud credentials, which the box otherwise never holds. Allow one identity that can call the model and nothing else:

- **A dedicated project or account** for the builder (Claude Code's docs recommend a dedicated GCP project), with billing alerts and quotas. Google's [budget alerts don't stop spending](https://cloud.google.com/billing/docs/how-to/budgets); add a spend-cap budget if your service supports one, or route through a gateway with a hard budget.
- **Vertex AI:** a service account with only Vertex AI User (`roles/aiplatform.user`) on that project, or narrower: a custom role with `aiplatform.endpoints.predict`, which Claude Code's docs name as the permission model calls need. Prefer a credential that isn't a long-lived key, such as a workload identity federation credential file. If you must use a key file, create it for the run, mount it read-only, and delete the key in IAM afterwards.
- **Bedrock:** a role or user whose policy allows only `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on the models you use (Claude Code's [example policy](https://code.claude.com/docs/en/amazon-bedrock) adds inference-profile reads). Prefer a [short-term Bedrock API key](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html) (up to 12 hours) or temporary STS credentials; AWS calls long-term Bedrock keys "for exploration only". Set an AWS budget alert.
- **Never** your personal `gcloud auth application-default login` credentials, an admin or owner identity, or a mounted `~/.aws` or `~/.config/gcloud` folder.

**Or put a gateway in front.** A gateway ([LiteLLM](https://docs.litellm.ai/docs/proxy/virtual_keys), [OpenRouter](https://openrouter.ai/docs/api-reference/api-keys/create-api-key), or your company's proxy) holds the real provider keys or cloud identity *outside* the box. The box gets only the gateway URL and a virtual key with its own budget and expiry (LiteLLM: `max_budget`; OpenRouter: a per-key `limit`). That puts the spend cap in one place you control, keeps Vertex or Bedrock credentials off the build machine, and lets you allow egress to a single host. Every harness above can point at one (`baseURL`, `ANTHROPIC_BASE_URL`, `base_url`, `COPILOT_PROVIDER_BASE_URL`).

**Rule of thumb:** one model credential per box: dedicated, spend-capped, short-lived where possible, passed at run time and never built in. If you can't say what it costs at worst and how to revoke it, it doesn't go in.

## 3. Prerequisites

What our runs used (pin your own versions and trust your own `--help` over ours):

| Thing | What we used | First needed in |
|---|---|---|
| Git, Python 3.11+, [uv](https://github.github.io/spec-kit/install/uv.html), pytest | Python 3.12 in CI | L0 / L1 |
| Spec Kit CLI (`specify`) | 1.1.3 for L1 to L4, 1.2.3 from L4.5 on | L1 |
| An AI coding agent with a Spec Kit integration and a headless mode (section 2) | OpenCode 1.19.3 (`--integration opencode`), free model `opencode/deepseek-v4.1-flash-free` | L1 |
| A reviewer who isn't the builder | a separate model or a human | L2 |
| A loop driver with iteration and time caps | [Ralph Loop](https://github.com/Rubiss-Projects/spec-kit-ralph) v1.5.0 (`specify extension add ralph`) plus a wrapper for timeouts | L5 |
| For the unattended builder loop: Docker on a machine with **no keys, tokens or push access** beyond the one model credential ([when you need it](#do-i-always-need-a-sandbox)) | a separate Ubuntu host | L5 |
| GitHub Actions turned on | the [`ci.yml`](https://github.com/tosin2013/invoice-exception-desk/blob/l5-setup/.github/workflows/ci.yml) workflow on `l5-setup` | L7 |
| Push access to the default branch | for [`.github/dependabot.yml`](https://github.com/tosin2013/invoice-exception-desk/blob/main/.github/dependabot.yml) | L8 |

**If you use OpenCode:** the scripted `opencode run --command speckit.<command>` worked on 1.19.3; there is an open report that OpenCode v2 removed it ([spec-kit #4639](https://github.com/github/spec-kit/issues/4639)). When scripting OpenCode yourself, add `< /dev/null` or it can hang waiting for input ([L0](https://tosin2013.github.io/invoice-exception-desk/L0-existing-repo.html)). Ralph sends its prompt to `opencode run` on stdin and passes `--auto`, so check that your version's `opencode run --help` lists `--auto`. Other harnesses have their own headless quirks; dry-run one scripted call before you seal anything.

### PM: plan the roadmap first

Spec Kit starts at **one feature**: `/speckit.specify` takes a single "what and why". Nothing in core breaks a product into features, orders them or tracks which ones are finished. Spec Kit's own docs fill that gap with a plain-Markdown convention, not a command: [Spec of Specs](https://github.github.io/spec-kit/concepts/spec-of-specs.html), which describes a roadmap pass, a roadmap table, and links both ways between the roadmap and each spec. Use it when the product is bigger than one feature. A single small change doesn't need a roadmap. The PM owns the roadmap without touching code: it's one file, editable in the GitHub web UI.

**One roadmap of record: `ROADMAP.md` at the repo root.** It's the record for this repo's technical roadmap. It names and orders features; it doesn't design them. Issues and PRs are *linked* from it, not a second place to keep status. **Boards are views, not records:** a GitHub Projects, Jira or Linear board can show the rows, but status of record stays in `ROADMAP.md`.

Columns:

| ID | Feature | One-line scope (in / out) | Outcome | Depends on | Order | Milestone | Status | Spec dir | Issue / PR |
|---|---|---|---|---|---|---|---|---|---|
| R1 | short name | what's in / what's deferred to a sibling | what's observably true when done | R0 | 1 | MVP | planned | — | — |

- **ID** (`R1`, `R2`, ...) never changes once a spec cites it. **Order** is the PM's priority, lowest first. **Milestone** is a release name, or a GitHub milestone if you use them.
- **Spec dir** and **Issue / PR** may each hold several entries; a row often needs more than one spec. If specs live on a different branch from the roadmap, name the branch too: `l5-setup:specs/003-desk-import/`. A `planned` row leaves Spec dir unset (`—`) until its spec exists; don't put in a path or branch that isn't there yet.
- Every `spec.md` opens with an `Input:` line naming its row, for example `**Input**: Parent roadmap -> R2. <feature description>`, so you can grep from a spec to its row and back.

**Status** (one per row):

- `planned`: no reviewed spec yet. The row is a candidate for `/speckit.specify`, not a build job.
- `specified`: the row has a usable, reviewed spec. Implementation hasn't started.
- `building`: implementation is underway, but the row's exit criteria aren't all met yet.
- `blocked — <reason>; reopen when <condition>`: something outside the row's own work stops it. We keep `blocked` as a status rather than a separate field because it's one column the PM reads at a glance, and a blocked row is never eligible to run. The reason and reopen condition go in the same cell.
- `done`: the row's **full** exit criteria are met, and the row's accountable reviewer has accepted it. Only the change that meets them sets `done`. A PR or commit link proves that a change exists, not that it was accepted. A row finished before Spec Kit was used can show `— (pre-Spec Kit)` as its Spec dir, with a commit link as evidence. Our R0 is `done` on its self-graded freeze record; that is a labeled historical exception, not a precedent for new rows.
- `dropped — <reason>`: removed on purpose. A dropped dependency is **not** satisfied, so re-plan the rows that depend on it.

**Planning the roadmap, not just keeping it.**

- **Outcome first.** A row is ready for the roadmap when you can state its outcome in one line. If you can't, it's an idea, not a row yet.
- **Horizons.** Fully scope the next 1 or 2 rows: scope in and out, outcome, dependencies. Sketch the rows after those. Give far rows one line each. Detail is earned by proximity, and over-specified far rows are how roadmaps rot.
- **Order.** Dependencies first, then the riskiest assumption earliest, then value.
- **Replan** on triggers and on a cadence. Triggers: a row finishes, a dependency slips, a milestone arrives, or building a row shows its scope was wrong. Cadence: a regular review, for example each milestone or monthly. Keep, reorder, split or drop rows, and write down why.
- **Drop deliberately.** Drop a row when its outcome stops mattering or its cost outgrows its value. Set `dropped — <reason>`. A roadmap that only grows isn't a plan.

**Long-term walkthrough:**

1. **Start with the destination.** Who the user is, their problem, and what success looks like in roughly 6 to 12 months. Make it measurable if you can, but it's a direction, not a delivery promise.
2. **Work backward** to the outcomes needed to get there, their dependencies, and the riskiest assumptions. Say why each row belongs and what's out of scope.
3. **Now / Next / Later.** Only Now and Next get enough scope to specify. Later stays at the outcome level.
4. **Choose the next slice deliberately** by readiness, user value, risk reduction and effort. The PM shows that reasoning in `Order`; the loop never decides it.
5. **Replan from evidence.** After each delivery, compare the result with the row's outcome, then keep, reorder, split or drop rows. Label any user results you haven't observed as hypothetical.

**HYPOTHETICAL worked example** (made up to show the method; not this repo's history, and no real user results):

- **Idea and user:** help the one accounts-receivable clerk at a small services company stop missing overdue invoices.
- **6–12 month outcome:** within 9 months, the clerk's weekly overdue review takes under 30 minutes (today: about 3 hours in a spreadsheet), and no invoice over 60 days goes unreviewed.

Initial roadmap:

| ID | Horizon | Feature | Outcome | Depends on | Order | Status | Spec dir |
|---|---|---|---|---|---|---|---|
| R1 | Now | Import one CSV export; aging list | every open invoice appears once, in the right bucket | — | 1 | specified | `specs/001-overdue-list/` |
| R2 | Next | Match payments from the bank export | balances reflect partial payments | R1 | 2 | planned | — |
| R3 | Next | Owner and note per invoice | every overdue invoice has an owner | R1 | 3 | planned | — |
| R4 | Later | Draft reminder emails | one line until R2 and R3 land | R2, R3 | 4 | planned | — |

- **Trade-off:** R3 is cheaper, and the clerk asked for it first. But R2 tests the riskiest assumption: can we read real bank exports at all? Both depend only on R1, so the riskiest one goes first and R2 comes before R3.
- **First slice (R1), spec `specs/001-overdue-list/spec.md`** with `**Input**: Parent roadmap -> R1.`
  - Scope: import one CSV export, then compute days overdue and the bucket as of a given date. Out of scope: payments, owners and reminders.
  - Acceptance criteria: given the 40-row sample export, every open invoice appears exactly once in the right bucket; an invalid row is listed with a reason, never dropped; importing the same file twice gives the same list.
- **Hypothetical evidence:** after R1 is done and accepted, the clerk's review takes about 50 minutes, and most of that is checking which invoices were partly paid. A spike on three bank exports matched about 70% of payments by invoice number and failed on the rest.
- **Decision: split R2.**
  - **R2a** (Now): "match payments by invoice number", outcome "partly paid invoices show the right balance", depends on R1, Order 2, `planned`, Spec dir unset.
  - **R2b** (Later): "fuzzy matching", one line.
  - R3 keeps its place. The plan change and the reason are recorded in the roadmap.
- **Revised next row:** R2a, which goes to `/speckit.specify` next.

**Who updates what.**

| When | Who | Change |
|---|---|---|
| Plan or replan | the PM | Add, reorder, re-scope, block or drop rows. Update the roadmap first, then the specs it affects. |
| After `/speckit.specify` and review | whoever ran it | `planned` → `specified`, add the spec dir, in the same commit as the spec |
| A build starts | the operator | → `building` |
| A PR finishes one of the row's specs | that PR's author | add the PR link; the row stays `building` |
| The change that meets the row's full exit criteria | its author proposes, the row's reviewer accepts, a human merges | → `done`, with the evidence links |
| Inside the Ralph loop | **never** | the loop doesn't edit `ROADMAP.md`, just as it doesn't edit the spec or plan |

**How it feeds Ralph: the operator picks the next eligible row.** A row is eligible to build when all of these hold:

- its status is `specified` or `building`;
- every `Depends on` row is `done` (a `dropped` dependency doesn't count);
- its spec, plan and tasks exist and are approved, and analyze has run;
- its required approvals are in place (from L6 on, the ruling issue has `agent-ready`);
- the run preflight passes.

Among eligible rows, take the lowest `Order`. A `planned` row is a candidate for `/speckit.specify` ([step by step](#run-spec-kit-step-by-step-no-assumptions)), not a Ralph job. If any input is ambiguous, missing or `blocked`, stop and ask the PM; don't pick around it. Then start Ralph with `--spec-dir specs/<the spec you're building>` ([how the Ralph loop runs each spec](#how-the-ralph-loop-runs-each-spec)). Ralph builds what it's given and never picks the row.

**Worked example.** Our own [`ROADMAP.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/ROADMAP.md) had drifted: R1 still said `planned` after its two specs were built and merged.

- **R1 is now `building`, not `done`.** Both of its spec dirs and all of its PRs are linked, but its exit criteria also cover AT-09 and AT-10, and no spec covers those yet.
- **R2 follows R1** because R1 computes the remaining balance and R2's payment events recalculate it.
- **R5 waits for R2 and R3** because it migrates the v2a and v2b schemas they introduce.
- **Where the file gives no reason, we say so.** It doesn't say why R4 comes after R3, or which assumption is riskiest.
- **R0 has its own note.** Its `done` is the original freeze record, which was self-graded.

**Completion check before you set `done`.** For each spec the row needs, record:

- the roadmap ID, spec dir and revision;
- the acceptance evidence;
- what happened to each task (done, or deferred with the owner's OK and a reason);
- the PR and target branch;
- the reviewer and any remaining gap.

Check both directions: no required spec is missing from the row, and no in-scope spec sits outside it. Confirm the work is merged into the intended branch, and that the spec, tasks, roadmap and linked issues describe the same scope. Ticked boxes, a green suite or a merged PR alone are not completion. Missing or contradictory evidence means not `done`.

- **Read back after each relevant merge and at milestone review.** Reconcile the spec, tasks, roadmap and issue/PR, and record the revision reviewed and any mismatch.
- **Deferrals:** a deferral must name where the work goes or when it reopens, and it must update the row's scope. It can't waive required exit criteria.
- **Implemented, merged and deployed are different.** Deployment counts toward `done` only if the row's acceptance scope requires it.

The drift check below is structural only and never proves this check passed.

**Roadmap prompt.** Paste this into any harness:

```text
You are helping a product manager plan a roadmap. Don't write code or specs.
1. Read the constitution (.specify/memory/constitution.md), README, and any NON_GOALS or PRD file. List the dirs under specs/ on every branch I tell you holds specs.
2. Ask me for the destination: the user, their problem, and what success looks like in 6-12 months. Restate the outcome in one or two sentences and ask me to confirm.
3. Propose features: 4-10 is a starting range, not a quota. Each must be independently testable and small enough for one /speckit.specify run, with a one-line outcome (if you can't state one, it's an idea, not a row). Fully scope only the next 1-2 rows (scope in/out, dependencies); sketch the rest.
4. Order them: dependencies first, then the riskiest assumption, then value. Ask me about priority and milestones one question at a time, and wait for each answer. Don't guess.
5. Map every existing specs/NNN-* dir to a row (a row may have several) and list any dir that fits no row. Don't invent rows to absorb them; ask me.
6. Write ROADMAP.md at the repo root with this table:
   | ID | Feature | One-line scope (in / out) | Outcome | Depends on | Order | Milestone | Status | Spec dir | Issue / PR |
   Status is one of planned, specified, building, blocked — <reason>, done, dropped — <reason>. IDs (R1, R2, ...) never change. Don't set done unless I confirm the whole row's exit criteria were met and accepted.
7. STOP. Show me the table and wait for my approval. Don't run /speckit.specify.
8. After I approve, ask: "Which platform hosts this repo (GitHub, GitLab, Bitbucket, other)?" Offer to open or update one issue per row, as in "Open issues against the roadmap". First search for existing issues by roadmap ID and show me which you'd reuse, update or create. Creating or editing issues needs its own OK from me; approving the roadmap is not that OK.
The next step after that is /speckit.specify for the first planned row whose dependencies are done, with an Input line citing its ID.
```

**Open issues against the roadmap (optional).** Issues are where people discuss and rule on a row; status still lives in `ROADMAP.md`. Each issue names its row ID (a title starting `R2:` and `Roadmap: R2` in the body), and the row's `Issue / PR` column gets the link. **Reuse before you create:** search for the ID first, so a rerun doesn't make duplicates, and update an issue you find rather than opening another. Creating or editing issues needs the user's explicit OK, separate from approving the roadmap.

- **On GitHub:**
  - **Rows:** first run `gh issue list --state all --search "R2 in:title"`. If nothing comes back, run `gh issue create --title "R2: Payment events" --body "Roadmap: R2 in ROADMAP.md. <scope and outcome from the row>"`, adding `--milestone` or `--label` if you use them. Paste the URL into the row.
  - **Tasks:** for a feature's **tasks** (not rows), Spec Kit v1.2.4 has a bundled, opt-in [`github` extension](https://github.com/github/spec-kit/tree/main/extensions/github). Run `specify extension add github`, then `/speckit.github.taskstoissues` (spelled `/speckit-github-taskstoissues` or `$speckit-github-taskstoissues` in some harnesses).
  - **What that command does:** it reads the feature's `tasks.md` and stops unless the git remote is GitHub. It needs the GitHub MCP server. It skips tasks that already have an issue and creates `T001: ...` issues for the rest.
  - **The older command:** core `/speckit.taskstoissues` still works in v1.2.4 but is deprecated ([extensions reference](https://github.github.io/spec-kit/reference/extensions.html)).
- **Not on GitHub** (GitLab, Bitbucket, Azure DevOps, Jira, ...):
  - **Search the catalog** for your platform: `specify extension search <platform>`, or the [community extensions page](https://github.github.io/spec-kit/community/extensions.html). Community entries are discovery-only: read one first, then install it with `specify extension add <id> --from <release archive URL>`.
  - **What we found** on 2026-10-28: the catalog listed, among others, [azure-devops](https://github.com/pragya247/spec-kit-azure-devops), [jira](https://github.com/mbachorik/spec-kit-jira) and [linear](https://github.com/ashbrener/spec-kit-linear-sync); we haven't tried them. We found no GitLab or Bitbucket issue extension.
  - **If there's none** for your platform, use its CLI or web UI, search by ID first, and paste the link into the `Issue / PR` column.

> **Sidebar: optional automation (last checked 2026-10-28).** Neither tool is needed for anything above.
>
> - **[speckit-roadmap](https://github.com/srobroek/speckit-roadmap)**. *Maturity:* early; v0.1.1, one maintainer; the catalog still lists v0.1.0, which doesn't install on Spec Kit 1.x.
>   - *What it does:* adds `/speckit.roadmap.write`, plus read-only `brief`, `debrief` and `sync`, which reconcile a roadmap ledger with `specs/*/`.
>   - *Install:* `specify extension add roadmap --from https://github.com/srobroek/speckit-roadmap/archive/refs/tags/v0.1.1.zip`, then `specify extension enable roadmap`.
>   - **Known bug:** open issues [#4](https://github.com/srobroek/speckit-roadmap/issues/4) and [#10](https://github.com/srobroek/speckit-roadmap/issues/10) report that the archive ships its own `.specify/`, so its config loader can read the extension's roadmap instead of yours. Check which file it resolves before you trust it.
>   - *Limits:* the default ledger is `.specify/memory/roadmap.md` (configurable), and there's no priority or milestone field.
> - **[repo-governor](https://github.com/tosin2013/repo-governor)**, for unattended or high-assurance repos. *Maturity:* v0.8.0; its README says "architecture ready, thesis under validation".
>   - *What it does:* answers a different question: is this feature *admitted* now (for example, on the current GitHub milestone), and is it done, so the agent stops? It doesn't own the roadmap.
>   - **Its Spec Kit extension isn't built yet:** [ADR-037](https://github.com/tosin2013/repo-governor/blob/main/docs/adrs/037-a-spec-kit-extension-delivers-governance-at-spec-kits-steps.md) is Proposed, and issues [#265](https://github.com/tosin2013/repo-governor/issues/265) to [#270](https://github.com/tosin2013/repo-governor/issues/270) are open.
>   - *Install for now, as an agent skill:* `git clone --branch v0.8.0 https://github.com/tosin2013/repo-governor /tmp/rg && /tmp/rg/tools/install-skill.sh /path/to/your/repo .claude/skills`. Pick the skills folder your harness reads; see its README.

**Drift check.** [`roadmap-drift.yml`](https://github.com/tosin2013/invoice-exception-desk/blob/main/.github/workflows/roadmap-drift.yml) runs [`roadmap_drift.py`](https://github.com/tosin2013/invoice-exception-desk/blob/main/.github/scripts/roadmap_drift.py). It uses only the Python standard library, has no network access, and gets a `contents: read` token. It runs on PRs and pushes that touch `ROADMAP.md` or `specs/**`.

- **Warnings** (it never fails on these):
  - a `specs/NNN-*` dir has no row;
  - a row at `specified` or later names a spec dir that doesn't exist;
  - a `done` row has no PR or commit link;
  - a status isn't in the list above;
  - a `blocked` or `dropped` row gives no reason;
  - a dependency is unknown or `dropped`.
- **Errors fail the check.** A git failure, a branch it can't resolve, or a table it can't parse prints `ERROR (result UNKNOWN)`, so a check that didn't run never looks clean. Naming a branch that doesn't exist yet fails the check by design: leave a planned row's Spec dir unset until the spec exists.
- **How it finds specs:** with `git ls-tree`, always from committed trees, and it prints each tree's commit SHA.
  - A branch-qualified spec dir is read from `origin/<branch>` (or a local branch).
  - An unqualified `specs/...` is read from the committed tree at HEAD, so uncommitted spec dirs aren't seen. `ROADMAP.md` itself is read from the file, uncommitted edits included.
  - It tells a missing path apart from a branch it can't read.
- **What it doesn't check:** whether a link means acceptance. It never decides a row is `done`.
- **Where it runs:** only where the workflow file exists. Here that's `main` and branches made from it, so a spec added on `l5-setup` is caught the next time `ROADMAP.md` changes, or on a manual run.
- **Making it blocking:** do that once the team trusts it, for example after about four weeks with no false positives.

### Run Spec Kit step by step (no assumptions)

Use this when a person, or an AI working with one, runs Spec Kit in a chat session. Checked against Spec Kit v1.2.4 and its docs on 2026-10-28. If your `specify --help` says something different, trust it and tell the user. The unattended loop works differently; see the end of this subsection.

**A. Setup, exact commands.** Run these in a terminal, in this order. **If a command fails or a flag isn't in your `--help`, stop and show the user the exact error.** Don't try another installer, version or flag on your own.

1. **Ask** which harness (coding agent) the user runs, and whether this is a new project or an existing repo. Don't assume.
2. **Check the prerequisites.** If one is missing, tell the user and stop.
   ```bash
   git --version
   python3 --version        # 3.11 or newer
   uv --version             # https://docs.astral.sh/uv/
   command -v <harness>     # e.g. claude, codex, copilot, gemini, cursor-agent, opencode
   ```
3. **Install the CLI,** pinned to a [release tag](https://github.com/github/spec-kit/releases) the user agrees to (keep the `v`):
   ```bash
   uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
   specify version
   ```
   `uv tool install specify-cli` (from PyPI) is also official. For a one-off run with nothing installed, put `uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z` in front of each `specify` command instead.
4. **Initialize** with the user's integration key (`specify integration list`, or the [integrations page](https://github.github.io/spec-kit/integrations/index.html)):
   ```bash
   specify init my-project --integration <key>   # new project: creates ./my-project
   specify init --here --integration <key>       # existing repo: run from its root
   ```
   Use `--here` only in the repo the user named, with a clean `git status` ([L0](https://tosin2013.github.io/invoice-exception-desk/L0-existing-repo.html)). If it warns that the folder isn't empty, show the warning; add `--force` only if the user says so. `--script sh|ps|py` picks the script type (default `sh`; `ps` on Windows). An AI in a terminal that can't answer prompts adds `--non-interactive`, and must still pass `--integration`, or it silently gets Copilot. Old CLIs used `--ai`; v1.2.4 rejects it ("No such option"), so report the version rather than switching flags.
5. **Run `specify check`.** It lists the agent tools it finds.
6. **Confirm the commands show up** in the harness, opened in the project folder (type `/`, or look for the folder below). If they don't, stop.

The steps are the same everywhere; only the spelling changes ([command invocation](https://github.github.io/spec-kit/integrations/cli.html#command-invocation)). This playbook writes the dotted form.

| Harness | Type it as | Installed in |
|---|---|---|
| OpenCode, Gemini CLI | `/speckit.plan` | `.opencode/commands/`, `.gemini/commands/` |
| Claude Code, GitHub Copilot, Cursor | `/speckit-plan` | `.claude/skills/`, `.github/skills/`, `.cursor/skills/` |
| Codex CLI | `$speckit-plan` | `.agents/skills/` |
| Any other | see its page on the [integrations list](https://github.github.io/spec-kit/integrations/index.html) | |

**If you use Claude Code:** its Spec Kit skills are model-invocable by default, so the model can start one on its own. `--integration-options="--no-model-invocation"` at init makes the core ones run only when the user types them (trade-offs on the [Claude page](https://github.github.io/spec-kit/integrations/claude.html)).

**B. Fixed order.** Never skip or reorder. **One command per turn.** Never run implement until `tasks.md` exists and the user has approved it.

| Step | Command | What it produces | Who decides | Stop and wait for |
|---|---|---|---|---|
| 1 | `/speckit.constitution <principles>` (once per project) | `.specify/memory/constitution.md` (init leaves a template there) | the user: the rules | approval of the constitution |
| 2 | `/speckit.specify <what and why>` | `specs/<NNN-feature>/spec.md` and `checklists/requirements.md` | the user: what to build | approval of the spec |
| 3 | `/speckit.clarify` | answers written into `spec.md` under `## Clarifications` (up to 5 questions a run) | the user answers every question (C below) | each answer, then approval of the updated spec |
| 4 | `/speckit.plan <tech stack>` | `plan.md`, plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md` as needed | the user: the tech stack | approval of the plan |
| 5 | `/speckit.tasks` | `tasks.md` | the AI drafts, the user approves | approval of `tasks.md` |
| 6 (optional) | `/speckit.analyze` | a report only; it edits nothing | the user picks the fixes; fix at the step that owns them, then rerun | the user says the findings are handled |
| 7 | `/speckit.implement` | code and tests; tasks ticked in `tasks.md` | the AI builds only what `tasks.md` says | the user reviews the diff and the test results |

Spec Kit calls clarify, checklist and analyze optional quality gates. In this playbook clarify runs whenever the spec has open questions, and analyze always runs before implement, with HIGH findings fixed. Two more optional commands: `/speckit.checklist` (after plan; writes `checklists/<name>.md`, and only the user ticks its boxes) and `/speckit.converge` (after implement; it adds any missing tasks to `tasks.md`, then you implement again until it says "Converged"). Each is its own turn with its own review. A big feature can run implement one phase at a time, each phase a turn.

**C. Clarify rule.** Put every `/speckit.clarify` question to the user, one at a time, and wait for the answer. Never answer for the user, and never take the "Recommended" option without saying so. If the user says "you pick", state your pick and why, and wait for an explicit OK before writing it into the spec.

**D. Review gates.** After each command, show what changed: each file path created or edited, with a two- or three-line summary (a `git diff --stat` helps). Then ask: "Approve, or what should change?" Wait. Only a clear yes ("approved", "go on") counts. Silence, "I'll look later" or an unrelated question isn't approval. If the user asks for edits, make them (or rerun the same command), show the change and ask again. Commit after each approval if the user wants a checkpoint.

**Unattended runs (L5 and up).** Nobody is there to answer mid-run, so the gates come before the loop starts. The approved ruling (the issue with `agent-ready`) answers every clarify question in advance. Anything it doesn't answer is a stop, not a guess. If a human or strong model writes the spec, plan and tasks first (as in L1 to L4), the user approves them before the loop starts. The loop keeps the same command order ([how the Ralph loop runs each spec](#how-the-ralph-loop-runs-each-spec)), and the result is checked after: bundle, grader commit, CI, human merge (section 4).

**E. Guardrail prompt.** Paste this at the start of a session, in any harness:

```text
Follow GitHub Spec Kit exactly, as in "Run Spec Kit step by step (no assumptions)":
https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html#run-spec-kit-step-by-step-no-assumptions
Rules for this session:
1. Ask me which coding agent I use and whether this is a new project or an existing repo. Don't assume.
2. Setup: use only these commands: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<tag I approve>, then specify init with --integration <my key> (add --here only for an existing repo), then specify check. If anything fails or a flag differs, stop and show me the exact error. Don't try another install method.
3. Order: constitution, specify, clarify, plan, tasks, analyze (if I want it), implement. Never skip or reorder. Never implement before I approve tasks.md.
4. One Spec Kit command per turn, spelled the way my agent shows it (/speckit.plan, /speckit-plan or $speckit-plan).
5. Clarify: ask me every question, one at a time, and wait. Never answer for me or quietly take the recommended option. If I say "you pick", tell me your pick and wait for my OK.
6. After each command: list the files changed (path and a short summary) and ask me to approve or request edits. Wait. Silence is not approval.
7. If anything is unclear or conflicts, stop and ask.
Start by asking your first question.
```

## 4. The end-to-end loop

```mermaid
flowchart LR
  C[Constitution<br/>once] --> R[Ruling<br/>issue + agent-ready]
  R --> S[Spec, plan, tasks<br/>+ analyze]
  S --> B[Builder run<br/>capped loop in a keyless box]
  B -->|git bundle| G[Grader commit<br/>acceptance tests]
  G --> CI[CI grades the PR<br/>read-only]
  CI --> H[Human merges]
  H -->|next change| R
```

1. **Constitution (once, then amended with a version bump).** Start with 3 to 5 plain rules your agents follow, each tied to the real code (ours grew to eight). Ours ([`.specify/memory/constitution.md`](https://github.com/tosin2013/invoice-exception-desk/blob/l5-setup/.specify/memory/constitution.md), v2.0.0) says, for example: money is integer cents; computation is pure and never reads the clock; standard library only; spec, tests and code land together; every behaviour change is graded against a key the builder never sees; builder-written tests alone never mean "done".
2. **Ruling.** Every choice the agent would otherwise guess goes in writing first: the rule, types, what other rows get, forbidden files, which existing test edits are allowed (exactly), given/when/then acceptance checks with exact inputs, the expected Spec Kit trail, a size limit, "stop and ask if anything conflicts", how it's graded, and any constitution exception for this change. From L6 on the ruling is a GitHub issue; a human adds the `agent-ready` label only when it's final. No label, no run.
3. **Spec, plan, tasks.** `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, then `/speckit.analyze` **before** implement, fixing HIGH findings. Run them in that order, one at a time, with a review after each ([step by step](#run-spec-kit-step-by-step-no-assumptions)). A rule change edits the spec that owns the rule: a dated Clarification, the old requirement kept but marked superseded, a new ID ([L4](https://tosin2013.github.io/invoice-exception-desk/L4-maintenance.html)). In L1 to L4 a human or strong model wrote the spec and plan; in L5 to L7 the free-model builder wrote them inside the box from the frozen ruling (a phase-1 prompt), then the loop (Ralph) implemented.
4. **Builder run in a sandbox.** Your agent, driven by a capped loop (ours: OpenCode on a free model, driven by Ralph), in a locked-down container (non-root, read-only root, no capabilities, no credentials, no git remote) on a keyless host. Preflight probes must all pass first (18 in L5, 13 in L6). Scope is checked after every agent call. The work comes out as a [`git bundle`](https://git-scm.com/docs/git-bundle), with its SHA-256 in a receipt.
5. **Grader commit.** The acceptance tests were written from the issue and kept out of the builder's folder until the bundle was sealed. The bundle is pushed **unchanged**, and the acceptance tests are added as **one separate commit** under `acceptance/issue-<N>/` (example: [`f916383`](https://github.com/tosin2013/invoice-exception-desk/commit/f916383)). The PR then shows who wrote what.
6. **CI is the grader.** The read-only `ci` workflow runs on every PR: the full suite, the `acceptance/` tests when present, a check that every base test ID still exists, and a diff-size summary ([L7](https://tosin2013.github.io/invoice-exception-desk/L7-ci-grader.html)).
7. **Human merge.** A human merges on green, and closes the issue by hand when the PR targets a branch other than the default (`Closes #N` only auto-closes on the default branch).

Our L7 run, end to end: issue #22 → 3-minute run, 1 Ralph iteration → local self-check PASS → grader commit → CI green in 9 s (223 passed, acceptance 8/8, all 215 base tests present) → merged by [PR #23](https://github.com/tosin2013/invoice-exception-desk/pull/23).

## 5. Roles and trust boundaries

| Role | Does | Never does |
|---|---|---|
| **Human** | rules on every change, approves the issue, adds `agent-ready`, says go, merges every PR | lets anything merge without looking at the result |
| Operator / kit | builds the box, runs preflight and the run, verifies the bundle, adds the grader commit, opens the PR | edits the builder's commits |
| Builder (agent + loop driver; ours: free model + Ralph) | writes the spec trail and the code inside the box | sees sealed keys or acceptance tests, touches `.github/`, `acceptance/`, `.specify/`, its own agent folder (`.opencode/` for us), pushes, or reports sizes and counts |
| Grader (sealed key, self-check, or CI) | decides pass or fail with checks written outside the builder's reach | gets edited by the builder |
| Reviewer (optional from L7) | checks the PR against the issue, rerunning checks with the issue's exact inputs | reviews its own work |
| Dependabot | opens dependency PRs on a schedule | merges anything |

The boundaries that matter:

- **The builder never sees the answer.** Sealed keys live outside the repo and off the build machine; acceptance tests stay in the kit until the bundle is sealed. A builder that can edit its grader isn't being graded.
- **A human merges every PR.** No auto-merge, for agents or Dependabot.
- **CI is read-only with no secrets.** `permissions: contents: read`, no deploys. Dependabot-triggered workflows get a read-only token anyway.
- **Only what's committed crosses a handoff.** Agents don't share memory; a decision that isn't in the spec, plan, tasks or ruling doesn't exist for the next agent ([L3.5](https://tosin2013.github.io/invoice-exception-desk/L35-agent-handoff.html)).
- **Take numbers from the receipt or CI, not the agent.** In L6 the builder's notes said 167 diff lines; the real diff was 253.

## 6. The levels

Pages links are the published lesson; repo links are the Markdown source on `main`.

| Level | One-line lesson | Page | Source |
|---|---|---|---|
| Home | Decision gate, the Spec Kit loop, how much SDD to use, and a router by project stage | [Home](https://tosin2013.github.io/invoice-exception-desk/) | [`docs/index.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/index.md) |
| L0 | Adopt Spec Kit in an existing repo: inventory first, constitution from the real code, record a test baseline, pilot one feature | [L0](https://tosin2013.github.io/invoice-exception-desk/L0-existing-repo.html) | [`docs/L0-existing-repo.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L0-existing-repo.md) |
| L1 | Install `specify`, `specify init --integration opencode`, write a constitution, build a tiny feature with the human / free-model split | [L1](https://tosin2013.github.io/invoice-exception-desk/L1-setup.html) | [`docs/L1-setup.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L1-setup.md) |
| L2 | One feature through specify, clarify, plan, tasks, analyze, implement; green tests aren't "correct" until a hidden answer key agrees | [L2](https://tosin2013.github.io/invoice-exception-desk/L2-first-feature.html) | [`docs/L2-first-feature.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L2-first-feature.md) |
| L3 | Same loop on a real project with frozen data and a sealed key, which caught a bug 119 green tests missed | [L3](https://tosin2013.github.io/invoice-exception-desk/L3-invoice-desk.html) | [`docs/L3-invoice-desk.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L3-invoice-desk.md) |
| L3.5 | Hand work between two agents: only what's committed (spec, plan, tasks, a frozen packet) crosses the handoff | [L3.5](https://tosin2013.github.io/invoice-exception-desk/L35-agent-handoff.html) | [`docs/L35-agent-handoff.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L35-agent-handoff.md) |
| L4 | Change a spec after code exists: dated Clarification, superseded-but-kept requirement, tests first, one commit, `drift.md` | [L4](https://tosin2013.github.io/invoice-exception-desk/L4-maintenance.html) | [`docs/L4-maintenance.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L4-maintenance.md) |
| L4.5 | Upgrade Spec Kit itself like a dependency bump: diff tags, dry run in a throwaway clone, no `--force`, own branch and PR | [L4.5](https://tosin2013.github.io/invoice-exception-desk/L45-speckit-upgrade.html) | [`docs/L45-speckit-upgrade.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L45-speckit-upgrade.md) |
| L5 | Let a free-model Ralph loop build a ruled change unattended in a keyless box, graded against a sealed key | [L5](https://tosin2013.github.io/invoice-exception-desk/L5-agent-loop.html) | [`docs/L5-agent-loop.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L5-agent-loop.md) |
| L6 | The issue is the ruling; a self-check the builder never sees grades it; a human merges | [L6](https://tosin2013.github.io/invoice-exception-desk/L6-issue-to-pr.html) | [`docs/L6-issue-to-pr.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L6-issue-to-pr.md) |
| L7 | CI is the grader: full suite, acceptance tests in a separate grader commit, base test IDs still present | [L7](https://tosin2013.github.io/invoice-exception-desk/L7-ci-grader.html) | [`docs/L7-ci-grader.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L7-ci-grader.md) |
| L8 | Dependabot is just another author: low-noise config, same CI, human merge | [L8](https://tosin2013.github.io/invoice-exception-desk/L8-dependabot.html) | [`docs/L8-dependabot.md`](https://github.com/tosin2013/invoice-exception-desk/blob/main/docs/L8-dependabot.md) |

Each level has real branches to check out; see the [README levels table](https://github.com/tosin2013/invoice-exception-desk/blob/main/README.md#the-levels). The latest code is on [`l5-setup`](https://github.com/tosin2013/invoice-exception-desk/tree/l5-setup).

## 7. Loop tuning (the builder loop)

Whatever the harness, the loop should start a **fresh agent call per work unit**, read `tasks.md` to see what's left, keep compact notes, and commit each finished unit. That keeps context from piling up. Ralph does exactly this, with memory in `ralph-memory.md` and an audit trail in `progress.md`. Tune it like this.

**Caps (write them in the ruling before the run).** Cap each of these, whatever enforces it in your harness. Our values are from L5 ([`request-v1.md`](https://github.com/tosin2013/invoice-exception-desk/blob/l5-setup/specs/003-desk-import/request-v1.md), section 5):

| Cap | Why | L5 value | Where it lived for us |
|---|---|---|---|
| Loop iterations | a loop that never finishes burns time and quota | 10 max | Ralph `max_iterations`, or `--max-iterations` / `SPECKIT_RALPH_MAX_ITERATIONS` |
| Consecutive failures | a stuck agent rarely unsticks itself | 3 | Ralph's circuit breaker |
| Fix tries | stops thrashing on one failing check | 3 | the ruling |
| Per agent call | one hung call shouldn't stall the run | 15 min | wrapper `timeout` |
| Per run | bounds the whole thing | 90 min, plus a hard wall-clock timeout | wrapper |
| Empty-output retries | a provider hiccup isn't a result | 5, 10 min apart (count against time, not fix tries) | wrapper |
| Diff size | keeps the change reviewable | 300 counted lines, tests included, the loop's notes and `run.log` excluded | scope check |
| Spend | no surprise bills | $0, free model only | the ruling |

The loop driver should also refuse to call itself complete unless every task is checked off and `git status --short --untracked-files=all` is empty, exit non-zero on every stop, and be safe to interrupt and rerun (skipping checked-off tasks). Ralph does all of this.

**Install the loop in its own commit,** before anything is sealed, and set the agent and model from outside the tree. **If you use Ralph:** the installed `ralph-config.yml` defaults to Copilot and a paid model. We left the file alone and set the agent and model with `--model` and `SPECKIT_RALPH_AGENT_CLI`, so the one setup commit stayed the only change under `.specify/`. Provider credentials never go in that file (its own header says so); pass them at run time ([Choose a model provider for the Ralph box](#choose-a-model-provider-for-the-ralph-box)).

**Self-check and scope checks.**

- After **every** agent call: hard stop on forbidden files (the issue's list, `.specify/`, the agent's folder (`.opencode/` for us), `.github/`, `acceptance/`, `data/`, `pyproject.toml`, `uv.lock`, other test files) or a diff at or over the cap. Other unexpected files are flagged in the receipt, not stopped (L6).
- **Before** any agent call: run the baseline tests, then stop if the tree isn't clean. In L5 run r3, `uv run` quietly created a `uv.lock`, and a run that passed every sealed case was graded FAIL on scope. The fix was `UV_NO_PROJECT=1` plus this clean-tree check, not a looser rule. Neutralize lockfiles and caches before you seal.
- **After** the run: a self-check the builder never sees, in a throwaway container: verify the bundle, run the acceptance checks with the issue's exact inputs, the full suite, the base tests unchanged, and the base test IDs. When existing tests may change, compare the base tests byte by byte and allow only the approved edit (L7).
- Tell the builder to use the issue's exact rows in its tests and **not** to report sizes or counts. CI and the receipt do that.

**When to stop, retry or rerun.**

| Situation | Do |
|---|---|
| Empty output or a provider hiccup ("Connection reset", "Free usage limit reached") | retry after a wait; an empty run is not a clean result (L0, L4) |
| The agent hits a contract question or a conflict | stop and ask on the issue; don't let it guess. Answer by editing the ruling, then start again |
| Scope breach, even a harmless generated file | fail the run; fix the kit, not the rule; rerun from a fresh preflight (and a fresh seal if you use one) |
| Any config change after sealing | fresh preflight and a new seal; a seal never covers a different config |
| Iteration cap or failure cap hit | stop; a human reads the loop's notes (`progress.md` and `ralph-memory.md` with Ralph) and decides: split the task, tighten the ruling, or rerun |
| Builder asked nothing and finished in one iteration | that's the goal; it means the ruling settled everything (L6, L7 both ran ~3 minutes, 1 Ralph iteration) |

Record the container image's **config digest**, not just its ID; the ID changed on every rebuild even with identical layers (L5).

### How the Ralph loop runs each spec

Checked against [Ralph Loop](https://github.com/Rubiss-Projects/spec-kit-ralph) v1.5.0, the latest tag. Its README, `commands/iterate.md` and `scripts/bash/ralph-loop.sh` are the same files installed on [`l5-setup`](https://github.com/tosin2013/invoice-exception-desk/tree/l5-setup/.specify/extensions/ralph). A wrapper loop for another harness should behave the same way.

**Input: approved spec files only.** The loop works from `.specify/memory/constitution.md` and `specs/<NNN-feature>/spec.md`, `plan.md` and `tasks.md`. A human approves them before the loop starts. The loop never plans. **Our runs differed:** in L5 to L7 a phase-1 prompt wrote the spec change, plan and tasks inside the box from the approved ruling, and Ralph started right after. That made the ruling the only approval up front, and the human reviewed the spec trail in the PR. If you can, review the spec, plan and tasks before you start the loop.

**Order.** Ralph runs **one feature per run**: the one you pass with `--spec-dir` and `--tasks-path`, not every folder under `specs/`. With several features, run them one at a time in number order (001, 002, ...), each one finished before the next starts. Inside a feature, **each iteration works one user story** (one phase of `tasks.md`): the first one with unchecked tasks. Its tasks go in order, dependencies first, then the `[P]` (parallel) tasks. It never starts a second story in the same iteration. L6 and L7 each finished their whole story (L6: 4 tasks) in 1 iteration. If a story isn't finished, the tasks that passed are committed and the next iteration picks up the rest of that story. Set `max_iterations` to about the number of user stories plus a small margin (ours: 10).

**One iteration.** Each one is a fresh agent process that knows only what's in the files.

1. Read `ralph-memory.md` first, then the constitution, `spec.md`, `plan.md`, `tasks.md`, and any `research.md`, `data-model.md` or `contracts/`. Ralph's own instructions don't name `spec.md` or the constitution; the loop prompt adds them.
2. Pick the next user story (phase) in `tasks.md` with unchecked tasks, and implement its tasks in order, respecting `[P]` markers and dependencies.
3. Run the tests (ours: `uv run --with pytest python -m pytest -q`).
4. Tick `[x]` only the tasks whose tests pass, update the handoff in `ralph-memory.md`, and add an entry to `progress.md`.
5. Make one commit with the change, `tasks.md`, `ralph-memory.md` and `progress.md`.
6. End. Ralph starts the next iteration, for the next story, as a new process. If no task passes, nothing is ticked and nothing is committed.

**What the loop never does.** It never runs `/speckit.specify`, `/speckit.clarify`, `/speckit.plan` or `/speckit.tasks`. It never edits `spec.md`, `plan.md`, the constitution, `.specify/` or its agent folder; its only spec-folder edits are `tasks.md` checkboxes, `ralph-memory.md` and `progress.md`. If a task is unclear, conflicts with the spec or is blocked, it writes the question down (`BLOCKED: <task ID>: <question>` in `progress.md`, and in the run's `questions.md` if there is one) and ends with no commit. Left alone, Ralph v1.5.0 would note it and try again or skip to another task. So your wrapper checks for the note after every call and stops the run. That's our "stop on a contract question" (`questions.md` stayed empty in L6 and L7). A human answers by editing the ruling or the spec, then reruns.

**Stop conditions.**

| Stop | Checked by | Exit |
|---|---|---|
| Every task `[x]`, tests green, `git status --short --untracked-files=all` empty, handoff reads `- Feature complete; no handoff required.`, and the agent prints `<promise>COMPLETE</promise>` on its own line | Ralph checks the tasks, handoff and clean tree itself; the agent runs the tests, and the self-check or CI reruns them | 0 |
| `max_iterations` reached (ours: 10) | Ralph | 1 |
| 3 failed agent calls in a row | Ralph | 1 |
| A `BLOCKED` note or a question | your wrapper | non-zero |
| Time cap, scope or size breach (section 7) | your wrapper | non-zero |
| Ctrl+C | Ralph | 130 |

**Start it.** Install Ralph in its own commit, then run the script from the repo root. The agent CLI must be `copilot`, `codex`, `claude` or `opencode`, or a path to one, such as our `opencode` wrapper.

```bash
specify extension add ralph --from https://github.com/Rubiss-Projects/spec-kit-ralph/archive/refs/tags/v1.5.0.zip
SPECKIT_RALPH_AGENT_CLI=<agent cli or wrapper path> \
bash .specify/extensions/ralph/scripts/bash/ralph-loop.sh \
  --feature-name 003-desk-import --tasks-path specs/003-desk-import/tasks.md \
  --spec-dir specs/003-desk-import --max-iterations 10 --model <model>
```

Inside an agent session, `/speckit.ralph.run --max-iterations 10` does the same in a new terminal window; on a headless box, use the script. The install also registers an optional `after_tasks` hook that offers to start Ralph. The operator decides when Ralph starts, not the hook.

**Loop prompt.** Ralph v1.5.0 has no setting for extra instructions. Each iteration it sends `.specify/extensions/ralph/commands/iterate.md` as installed, and the launcher ignores free text. Leave that file alone. Put the rules below where the agent reads them on every fresh call: commit them in the setup commit as the project instructions file your harness loads (for example `AGENTS.md`, or `CLAUDE.md` for Claude Code; check your harness), or have your wrapper add them in front of Ralph's prompt.

```text
Ralph loop rules. Follow them in every iteration. Where they are stricter than Ralph's iterate command, these win.
Inputs: .specify/memory/constitution.md and specs/<NNN-feature>/spec.md, plan.md and tasks.md. A human approved them. Read them and ralph-memory.md before you change anything.
1. Work only in the feature folder Ralph gave you.
2. Take the first user story (phase) in tasks.md that still has unchecked tasks. Implement its tasks in order, dependencies first, non-[P] tasks before [P] ones. Work on that one story only.
3. Run the tests: <test command>. If they fail, fix them within this story, at most 3 tries. Tick only the tasks whose tests pass; if none pass, tick nothing, commit nothing, end your turn.
4. Tick the completed tasks [x] in tasks.md, update ralph-memory.md and progress.md, and make one commit with the change, tasks.md, ralph-memory.md and progress.md. Then end your turn. Don't start the next story.
5. Never run /speckit.specify, /speckit.clarify, /speckit.plan or /speckit.tasks. Never edit spec.md, plan.md, the constitution, .specify/ or your own agent folder. Don't add, reword or delete tasks.
6. If a task is unclear, conflicts with the spec or plan, or needs something that isn't done: don't guess and don't skip ahead. Append "BLOCKED: <task ID>: <question>" to progress.md (and to <questions file> if this run has one), commit nothing, and end your turn.
7. Print <promise>COMPLETE</promise> on its own line only when every task is [x], the tests pass and git status is clean.
8. Don't report sizes or counts; the receipt and CI do that.
```

## 8. Dependency hygiene (the L8 recipe)

1. **Make every dependency visible.** Dependabot reads manifest files, not CLI flags. We moved `--with pytest` into a one-line [`requirements-dev.txt`](https://github.com/tosin2013/invoice-exception-desk/blob/l5-setup/requirements-dev.txt) (`pytest==9.1.1`) and pointed CI at it with an absolute path (`--with-requirements "$GITHUB_WORKSPACE/requirements-dev.txt"`), because the base-test-ID step runs in a worktree of the older base commit.
2. **Put `.github/dependabot.yml` on the default branch.** If code lives elsewhere, set `target-branch` on each block. Ours: GitHub Actions weekly and grouped, plus `pip` with `allow: pytest` only, both targeting `l5-setup`; and a monthly grouped Actions block for the Pages workflow on `main`.
3. **Keep the noise low:** `groups` with `patterns: ["*"]`, `allow`, `ignore` majors, weekly or monthly. Start with Actions-only plus at most one more block.
4. **Grade bot PRs with the same CI.** Our L7 workflow graded Dependabot's PR #27 without a single change.
5. **A human merges every Dependabot PR on green.** No auto-merge. Don't leave them sitting, or Dependabot pauses.
6. **"No PR" can be correct.** Version updates have a 3-day default cooldown; read the update job's log before assuming something's broken.
7. **Alerts and security updates are a separate, deliberate choice.** Security updates always target the default branch. We left both off (no runtime dependencies); turn them on for real apps.

Branches without CI (our `main`) are ungraded; schedule their bumps less often. Recipes for other repo types (grouped minor/patch, Docker, security-only, `uv`) are in [L8](https://tosin2013.github.io/invoice-exception-desk/L8-dependabot.html#real-world-recipes).

## 9. Apply this to a new project: checklist for an AI

1. **Ask the user which harness they use:** the coding agent or CLI, the model, and the budget. Or check what's installed (for example `command -v claude codex copilot gemini cursor-agent opencode`) and confirm with them. Don't assume OpenCode. Also ask which model provider (a paid key, a subscription login, a cloud endpoint such as Vertex AI, Bedrock or Azure, a gateway, or a local model) and the spend cap ([Choose a model provider for the Ralph box](#choose-a-model-provider-for-the-ralph-box)), and whether they'll run the builder unattended or approve each step; that decides whether they need a sandbox ([Do I always need a sandbox?](#do-i-always-need-a-sandbox)).
2. **Map the loop to that harness** (section 2). Find its Spec Kit integration key and its headless command. If Ralph supports it (`copilot`, `codex`, `claude`, `opencode`), use Ralph; otherwise use a small wrapper with the caps and stops in section 7. If it has no headless mode or no loop driver, run the builder step by step instead: a human drives the loop, one fresh session per task, approving each step (a normal dev machine is fine, see [Do I always need a sandbox?](#do-i-always-need-a-sandbox); acceptance tests and sealed keys still stay out of the builder's reach), counting the same caps and running the same scope checks after each step. Everything after the builder (bundle, grader commit, CI, human merge) stays the same.
3. **Run the decision gate** ([Home](https://tosin2013.github.io/invoice-exception-desk/)). If the answer is "no SDD" or "light SDD", stop here and use a normal PR or a short spec.
4. **Set up Spec Kit** with the harness's key, using the exact commands in [Run Spec Kit step by step](#run-spec-kit-step-by-step-no-assumptions); if one fails, stop and show the user the error. New repo: `specify init <project-name> --integration <key>` ([L1](https://tosin2013.github.io/invoice-exception-desk/L1-setup.html)). Existing repo: inventory first, change nothing, then `specify init --here --integration <key>` and record the test baseline ([L0](https://tosin2013.github.io/invoice-exception-desk/L0-existing-repo.html)). Pin the `specify` version.
5. **Have a human or strong model write the constitution,** 3 to 5 rules, each citing real code. Include "builder-written tests alone never mean done." The user approves it before any spec.
6. **Pick a small, already-decided first change,** ideally a known gap your specs already name, additive, and checkable by a script. For a whole product, have the PM write `ROADMAP.md` first and take its first ready row ([PM: plan the roadmap first](#pm-plan-the-roadmap-first)).
7. **Write the ruling as a GitHub issue** with everything in section 4, step 2. Have the human approve it and add `agent-ready`.
8. **Write the acceptance tests from the issue,** with its exact inputs, and keep them outside the builder's reach.
9. **Add a read-only CI workflow** (no secrets): full suite, `acceptance/` when present, base test IDs still present, diff-size summary. Merge it before the first run. Copy ours: [`ci.yml`](https://github.com/tosin2013/invoice-exception-desk/blob/l5-setup/.github/workflows/ci.yml).
10. **Build the box** (for an unattended run): a container on a host with no keys or tokens beyond the one model credential, passed at run time, and no push remote; the issue snapshot hash-checked; preflight probes; scope checks after every call; clean-tree check after the baseline tests; output as a `git bundle`.
11. **Install the loop driver in its own commit** (Ralph or your wrapper), set the agent and model from outside the tree, and set the caps in section 7.
12. **Run.** The builder writes the spec trail (dated Clarification, spec, plan, tasks, analyze) in the fixed order, then implements. Unattended, the approved ruling is the gate: it answers every clarify question in advance, and anything it doesn't answer is a stop. The loop works one user story per iteration and never edits the spec or plan ([how the Ralph loop runs each spec](#how-the-ralph-loop-runs-each-spec)). Step by step, use the review gates in [Run Spec Kit step by step](#run-spec-kit-step-by-step-no-assumptions).
13. **Verify the bundle** (hash and head), run the local self-check once, push the bundle unchanged, add the grader commit, open the PR.
14. **Let CI grade it.** If the PR touches existing tests, also keep a byte-level compare or a review.
15. **A human merges** on green, and closes the issue if it targets a non-default branch.
16. **Add Dependabot** (section 8) once CI exists.
17. **When a rule changes later,** follow [L4](https://tosin2013.github.io/invoice-exception-desk/L4-maintenance.html); when Spec Kit itself updates, follow [L4.5](https://tosin2013.github.io/invoice-exception-desk/L45-speckit-upgrade.html).

## 10. Known gaps

Honest limits of what's here today:

- **CI checks that base test IDs exist, not what they contain.** A builder could weaken a test and keep its name, and every CI step would pass. The local byte-level self-check of the base tests covers that; CI alone doesn't. Keep the self-check (in the kit or as a CI step) or a review for any PR that touches existing tests.
- **Branch protection and required checks are off.** Turning on the `tests` check as required is the real-world next step from L7; until then "CI is the grader" is a habit, not a rule.
- **No automatic pickup of `agent-ready` issues,** no `needs-human` label after repeated failures, and no several issues at once. A human starts each run.
- **The L7 review was skipped** (merged on green CI); that was a judgment call for an additive change with one approved test edit.
- **`main` has no CI,** so Pages and Dependabot PRs into `main` are ungraded.
- **The unattended builder loop only ran on OpenCode with Ralph.** (L3.5's handoff also used an OpenAI agent, but not in a loop.) Other harnesses should fit the same steps, but we haven't tried them; Ralph v1.5.0 drives only `copilot`, `codex`, `claude` and `opencode`.
- **The run kits (container, preflight, self-check) aren't in the repo.** The lessons describe them; you build your own.
- **Results are from our own free-model runs,** graded against our keys, self-checks and CI. They aren't independently certified, and the R0 phase shows how self-graded tests can mislead ([R0 Results and Lessons](https://github.com/tosin2013/invoice-exception-desk/wiki/R0-Results-and-Lessons)).

## 11. Links

- Guide site: <https://tosin2013.github.io/invoice-exception-desk/>
- For agents: [`llms.txt`](https://tosin2013.github.io/invoice-exception-desk/llms.txt) and its copy [`llm.txt`](https://tosin2013.github.io/invoice-exception-desk/llm.txt)
- Repository: <https://github.com/tosin2013/invoice-exception-desk> ([README](https://github.com/tosin2013/invoice-exception-desk/blob/main/README.md), [GUIDE_OUTLINE](https://github.com/tosin2013/invoice-exception-desk/blob/main/GUIDE_OUTLINE.md))
- Spec Kit: <https://github.com/github/spec-kit> ([agent integrations](https://github.github.io/spec-kit/integrations/index.html)); Ralph Loop: <https://github.com/Rubiss-Projects/spec-kit-ralph>
