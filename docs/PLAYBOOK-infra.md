---
title: "PLAYBOOK companion: infrastructure repos"
description: "How to apply the Spec Kit controller/worker pattern to OpenShift and Kubernetes infrastructure repos: infra constitution principles, credentials, an evidence ladder beyond static CI, onboard.yml and a repeatability check."
---

# PLAYBOOK companion: infrastructure repos (OpenShift / Kubernetes)

This is a companion to [PLAYBOOK.md](https://raw.githubusercontent.com/tosin2013/invoice-exception-desk/main/PLAYBOOK.md). Read that first. Everything there still applies: the controller/worker split, Spec Kit step by step, the keyless sandbox, the git bundle, the human merge. This file only covers what changes when the "code" is cluster state: Helm charts, GitOps (Argo CD) apps, AgnosticD/Ansible configs, operators, and ACM-style multicluster setups.

Items marked **[unverified]** are tool claims we have not tested in a run yet.

## 0. When to use it

Use it when all of these are true:

- The repo describes cluster state (manifests, charts, Argo CD Applications, Ansible roles, operator subscriptions, policies).
- "Done" can be checked: a rendered manifest, a synced app, a passing test, a clean teardown.
- The change is bigger than one sitting, or wrong-but-quiet is a real risk (RBAC, network policy, multicluster placement, secrets).
- Someone other than the worker can check the result.

Don't use it for a version bump, a one-line value change, or a throwaway lab. Those get a normal PR and normal CI.

**Existing repos: ROADMAP first.** As in PLAYBOOK.md, before any spec, the controller reads the repo and writes (or updates) `ROADMAP.md`: what the repo deploys, where, how it is synced, what tests exist, and what is broken. The human approves it. Specs then come from roadmap items, one at a time.

## 1. Same order, same human gates

Spec Kit order does not change: **constitution → specify → clarify → plan → tasks → implement**. The human answers every clarify question and reviews each step before the next starts. The controller (frontier model or human) writes and reviews; the worker (cheaper harness) implements one user story per pass in a sandbox on any approved host. The controller never holds the worker's credential. Work leaves as a `git bundle`; a human merges. Any harness pair works.

What's new for infra: the worker also never holds **cluster** credentials by default (section 4), and "tests pass" is not enough; you climb an evidence ladder (section 5).

### Two ways to build: with a worker, or without

Pick per spec, and say which in `plan.md`.

- **With a worker (default for routine stories).** The controller specs and reviews; a cheaper harness builds one story per pass in the sandbox, offline, rung 1 only. Saves tokens, keeps credentials away from the builder.
- **Without a worker (direct mode).** The controller, or you, builds straight from `tasks.md` on a branch and pushes it for a human to test. Use it when a worker adds more overhead than it saves: small changes, early pilots, or infra work that can't be checked offline anyway. Everything else stays the same: the Spec Kit order and review stops, no secrets in git, no cluster credentials held by the AI, the evidence ladder, `VERIFY.md`, and a human merge. The human runs rungs 2 to 6 and records the results. Nothing the AI built counts as tested until those artifacts exist.

Direct mode drops the sandbox and the `git bundle`, not the gates.

## 2. Constitution: infra principles

Add these to `.specify/memory/constitution.md` (keep the project's own principles too). Each is a rule a reviewer can check.

1. **Git is the source of truth.** Desired state lives in the repo and reaches clusters through GitOps (Argo CD) or a declared playbook run. No hand edits with `oc edit`/`kubectl apply` that aren't also in git. Drift is a bug.
2. **Declarative and idempotent.** Applying twice gives the same result as applying once. Ansible tasks are re-runnable with no "changed" on the second run; Helm renders are deterministic.
3. **Least privilege.** Every ServiceAccount, Role and operator gets only what it needs. No new `cluster-admin` bindings without a written reason in the spec. Workloads run under restricted pod security / the default restricted SCC unless the spec justifies otherwise.
4. **No secrets in git.** Not in values files, not in Ansible vars, not in examples. Use a secret store reference (External Secrets, Sealed Secrets, Vault, or the project's approved way). A secret scanner runs in CI.
5. **Reversible changes.** Every change has a rollback: revert the commit and let GitOps sync, or a documented `helm rollback` / playbook step. Destructive steps (CRD removal, PV deletion, namespace deletion) need explicit human approval in the spec.
6. **Teardown is part of done.** Whatever the change creates, the repo can remove, and a teardown run proves nothing is left behind (namespaces, CRs, cloud resources, ACM placements).
7. **Pinned versions.** Chart versions, image digests or tags, operator channels and `startingCSV`, collection versions: pinned, and bumped only on purpose.
8. **Setup is declared, not remembered.** The repo ships an `onboard.yml` listing prerequisites, config, validation, quota checks and the deploy step. Any change to setup updates it in the same PR. No step lives only in someone's head or laptop.
9. **Keep governance minimal.** As in PLAYBOOK.md rule 6: only gates that protect correctness and credentials.

## 3. Specify, plan, tasks: what changes for infra

**Specify** states the **desired cluster state** and the **evidence** that proves it, not the commands to get there.

- Desired state: "On every managed cluster labelled `env=edge`, namespace `X` exists with app `Y` Healthy and Synced, using image digest `Z`."
- Scope: which clusters (hub vs managed), which namespaces, which operators.
- Acceptance evidence: name the ladder rung (section 5) each requirement must reach, and the artifact that proves it.
- Out of scope and forbidden changes (e.g. "no changes to cluster-scoped RBAC").

**Clarify** questions worth asking every time: which cluster(s) and versions? who owns the namespace? what is the rollback? which rung is required before merge vs before production? where do secrets come from? what is the teardown cost/TTL limit?

**Plan** names the mechanism: Helm chart vs Kustomize overlay vs Argo CD ApplicationSet vs AgnosticD workload role vs ACM Policy/Placement. It lists sync order (waves/hooks), dependencies (operators before CRs), and the exact commands each rung uses.

**Tasks** are **small reconcilable units**: one task = one change that can render, sync and be reverted on its own (one chart template, one Application, one role, one policy). Each task lists its rung-1 check. Order tasks so each leaves the repo renderable. One user story per worker pass, same as PLAYBOOK.md.

## 4. Sandbox and credentials for infra workers

The PLAYBOOK.md box rules apply: one model-only, spend-capped credential; no GitHub token; no SSH keys; output as a `git bundle`. Add:

- **No cluster credentials by default.** No kubeconfig, no `oc login` token, no cloud keys, no ACM hub access. Nothing with `cluster-admin`, ever, in the worker box.
- **Offline first.** The worker renders, lints, and validates against schemas with no cluster (rungs 1). It needs only CLIs and vendored schemas/charts, so it can run with network limited to the model endpoint and chart/schema mirrors.
- **Live apply by a human, or a disposable target.** Rungs 2 and up touch a cluster. Either a human runs them, or the run gets a **scoped, disposable** target: a throwaway cluster or a namespace-scoped ServiceAccount token, with its own spend cap and a TTL that auto-destroys it. That credential is not the model credential, is not held by the controller, and cannot reach production.
- **No live writes to shared clusters from the loop.** Server-side dry-run against a shared cluster uses a read-mostly, namespace-scoped identity, run by a human or CI, not the worker.

| Step | Who runs it | Credential |
|---|---|---|
| Rung 1 static | worker in sandbox, CI | none |
| Rung 2 dry-run | human or CI | read / dry-run, namespace-scoped |
| Rungs 3–6 | human, or CI against a disposable cluster | scoped, disposable, TTL + spend cap |
| Production sync | GitOps after human merge | GitOps controller's own identity |

## 5. Evidence ladder (beyond static CI)

Green CI is rung 1 only. The spec says which rung each requirement needs. Every rung leaves an artifact in `docs/evidence/<spec-id>/` (or attached to the PR), reviewed by the controller or human, never accepted by the worker.

| Rung | What | Example tools | Artifact that proves it |
|---|---|---|---|
| 1 Static | lint, render, schema, policy | `helm lint`, `helm template`, `kustomize build`, `kubeconform`, `yamllint`, `ansible-lint`, `conftest` (OPA), `kyverno` CLI (`kyverno apply`/`test`), secret scan (e.g. `gitleaks`) | rendered manifests + tool logs with exit 0, saved per chart/overlay |
| 2 Dry-run | API-server acceptance and diff vs live | `oc/kubectl apply --dry-run=server`, `kubectl diff`, `argocd app diff`, `ansible-playbook --check --diff` | dry-run output and diff, with the cluster version it ran against |
| 3 Reconcile | sync on a disposable cluster, healthy, no drift | `argocd app sync` / `argocd app wait --health --sync`, ACM policy compliance status, second Ansible run with `changed=0` | app status (Synced/Healthy) captured, then a second diff showing no drift |
| 4 Security | RBAC, images, pod security | RBAC review (`oc adm policy who-can`, `kubectl auth can-i --list`), image scan (e.g. `trivy`, `grype`) **[unverified in our runs]**, restricted pod security / SCC admission (`oc get pod -o yaml` shows `openshift.io/scc`) | RBAC diff reviewed by a human, scan report, SCC/pod-security result per workload |
| 5 Functional | the thing works | smoke tests (route returns 200, operator CR reaches Ready), test playbooks, project test suite | test output with timestamps and cluster ID |
| 6 Teardown | clean removal | delete Application / `helm uninstall` / AgnosticD destroy; then list leftover namespaces, CRs, PVs, cloud resources | before/after resource list showing nothing left; cloud console or CLI listing empty |

### Repeatability check (the real test)

A deployment is repeatable when this works with no hand steps, on a fresh machine and a fresh disposable cluster:

1. Clone the repo, run onboard (`project-onboard` skill, or the generated `bootstrap.sh`) with defaults.
2. Deploy, then capture rung 3 and 5 evidence.
3. Tear down (rung 6), then deploy again.
4. Compare the two runs: same Synced/Healthy state, same test results, second diff empty.

Save it under `docs/evidence/<spec>/repeat/`. Require it before calling a roadmap milestone done, and whenever a spec changes setup or `onboard.yml`. Anything you had to do by hand is a bug: add it to `onboard.yml` or the deploy script.

Rules:

- A rung counts only with its artifact. "It worked on my cluster" is not evidence.
- Don't skip rungs: a rung-3 claim needs rung 1 and 2 artifacts first.
- Record tool versions and cluster version in each artifact.
- Exact flags (e.g. `argocd app diff` exit codes, `kyverno` CLI subcommands) change between versions **[unverified: check `--help` for your version]**.

## 6. Harness-agnostic notes

- The worker needs: the CLIs for rung 1 in its image (`helm`, `kustomize`, `kubeconform`, `yamllint`, `ansible-lint`, `conftest`/`kyverno`, a secret scanner), vendored or mirrored schemas (OpenShift and operator CRD schemas are not in kubeconform's default set; the `static-validation` skill pins a source (`datreeio/CRDs-catalog`) and documents how to refresh it), and the spec/plan/tasks files.
- Loop caps from PLAYBOOK.md apply (iteration cap, time cap, stop on repeated failure). Add: stop if any rung-1 check fails twice on the same task.
- The loop driver and model are settings. Ralph only drives `copilot`, `codex`, `claude`, `opencode` (per PLAYBOOK.md); use a wrapper script otherwise.
- CI stays read-only with no secrets for rung 1. Rungs 2+ live in a separate, manually triggered job with the scoped credential, or are run by a human.

## 7. Optional skills: rhel-devops-skills-cli

[tosin2013/rhel-devops-skills-cli](https://github.com/tosin2013/rhel-devops-skills-cli) installs Agent Skills (`SKILL.md`) for Claude Code, Cursor, and the cross-tool `~/.agents/skills/` path. They are **optional**: give them to the controller (and the worker, if its harness reads skills) when the repo uses that tooling. Install from a clone, e.g. `./install.sh install --skill agnosticd` or `./install.sh install --all --ide agents`; `./install.sh available` lists them.

Skills in the repo (as of Oct 2026), mapped to this playbook:

| Need | Skill(s) | Use at |
|---|---|---|
| AgnosticD v2 configs, `agd` CLI | `agnosticd`, `agnosticd-refactor` | plan, tasks, review |
| AgnosticD end-to-end validation incl. stop/start | `agnosticd-deploy-test` | rungs 3, 5, 6 |
| Hub + per-student cluster topology, quota pre-flight | `agnosticd-hub-student` | plan (multicluster sizing) |
| Rung 1 static checks (render, schema, policy, secrets, lint), offline, no cluster creds | `static-validation` | implement (worker), CI |
| GitOps / Helm catalog items (RHDP) | `field-sourced-content` | plan, tasks |
| Validated Patterns (Argo CD based GitOps on OpenShift) | `patternizer`, `vp-refactor`, `vp-deploy-test`, `vp-deploy-validator`, `vp-submission` | ROADMAP, rungs 3 and 5 (Argo CD convergence, secrets, jobs) |
| Lab guides | `showroom`, `workshop-tester`, `student-readiness` | rung 5 for workshop repos |
| Repo audit, PASS/WARN/FAIL report | `rhel-devops-auditor` | ROADMAP for existing repos |
| Onboarding from `onboard.yml`, re-runnable, plus generated `bootstrap.sh` for people without an agent | `project-onboard` (listed as `onboard` in README) | setup, repeatability check |
| Fill research gaps in skills | `skill-researcher` | as needed |

Note: there is **no stand-alone generic "Helm", "OpenShift" or "Argo CD" skill**; Helm and GitOps knowledge sits inside `field-sourced-content` and the `vp-*` skills. Rung 1 is covered by `static-validation`, which runs all five checks offline, skips (and reports) any missing tool, and writes artifacts to `docs/evidence/<spec>/rung1/`. Skills inform; they never replace the ladder's artifacts or the human gates.

## 8. Minimal per-repo layout

```
ROADMAP.md                    # existing repos: written first, human-approved
onboard.yml                   # declared setup: prereqs, config, validation, deploy
.specify/memory/constitution.md   # project principles + section 2
specs/<NNN-name>/
  spec.md                     # desired state + required rung per requirement
  plan.md                     # mechanism, sync order, commands per rung
  tasks.md                    # small reconcilable units, rung-1 check each
docs/evidence/<NNN-name>/
  rung1/  rung2/  rung3/
  rung4/  rung5/  rung6/      # static, dry-run, reconcile, security, functional, teardown
  repeat/                     # onboard, deploy, teardown, redeploy on fresh targets
VERIFY.md                     # checklist below, ticked per spec in the PR
```

`VERIFY.md` template:

```
Spec: <NNN-name>   Cluster/version: ___   Tool versions: ___
[ ] Rung 1 static: render, lint, schema, policy, secret scan clean
[ ] Rung 2 dry-run: server-side dry-run + diff reviewed
[ ] Rung 3 reconcile: Synced/Healthy, second diff empty
[ ] Rung 4 security: RBAC diff reviewed, image scan, pod security/SCC
[ ] Rung 5 functional: smoke/functional tests pass
[ ] Rung 6 teardown: nothing left (k8s + cloud)
[ ] onboard.yml updated if setup changed; repeatability check run if required
[ ] No secrets in diff; no new cluster-admin; rollback written
[ ] Reviewed by: ___ (not the worker)   Merged by: ___ (human)
```

## 9. Reusing it on the next repo (checklist for an AI)

1. Read PLAYBOOK.md, then this file. Ask the user which controller/worker pair and which host runs the sandbox.
2. Run the decision gate (section 0). If it fails, say so and stop.
3. Existing repo: read it, write `ROADMAP.md` (what it deploys, how it syncs, current tests, gaps). Check for `onboard.yml`; list every hand step, laptop-only secret, and operator installed outside git. If there's no `onboard.yml`, make writing one the first roadmap item. Stop for human review.
4. Ask which optional skills (section 7) fit; install only those.
5. Add section 2 principles to the constitution. Stop for review.
6. Pick one roadmap item. Specify desired state + required rungs. Stop.
7. Clarify: ask the human the section 3 questions. Do not guess.
8. Plan and tasks. Stop for review after each.
9. Worker implements one story per pass, offline, rung 1 only (use the `static-validation` skill if installed), no cluster creds. Output a `git bundle`.
10. Controller reviews the bundle against the spec. A human or scoped CI runs rungs 2–6 on a disposable target and saves artifacts.
11. Tick `VERIFY.md`. Run the repeatability check when required. Human merges. GitOps syncs.
12. Note what broke in the process; fix this file, not just the repo.

Never: give the worker cluster-admin or production credentials, push from the loop, commit secrets, or accept work without its rung artifacts.
