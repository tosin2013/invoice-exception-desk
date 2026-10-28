---
title: "L4: Changing a spec after code exists"
description: "Change a rule in a feature that is already built and merged, keeping the spec, tests and code in step with a dated clarification, a drift log and a sealed answer key."
---

# L4: Changing a spec after code exists

[← Home](index.md)

- **You are here if** you finished [L3.5](L35-agent-handoff.md) and need to change a rule in a feature that's already built, tested and merged, without the spec, the tests and the code drifting apart.
- **You should already have** specify-cli 1.1.3 (we ran it through `uvx`, see section 2), OpenCode 1.19.3, Python 3.11+ with pytest, and a reviewer who can hold an answer key you never see.
- **You leave with** one real behaviour change, **FR-008 → FR-008a**: an invoice amount must now be a positive, canonical number (`0`, `00` and `0100` are rejected). It lands as a dated Clarification, a superseded requirement that's kept, flipped tests, a one-line code change, a drift log, and a pass against a sealed answer key written before the build.
- **Phases shown:** preflight, a hand-written spec edit, clarify, plan and tasks revision, implement (tests first), analyze on **two** features, drift log, review, sealed-key grading, merge. **Left out:** the Spec Kit 1.1.3 → 1.2.3 upgrade (its own lesson, [L4.5](L45-speckit-upgrade.md)), a new feature folder (`005-…`, not needed here), `/speckit.converge`, extensions, and teams of several developers.

> **Key idea:** a spec isn't finished when the code ships. When a rule changes, you **edit the spec that owns the rule**, say when and why it changed, keep the old text marked as superseded, and land the spec, tests and code **in one commit**. Then you go looking for every other place that still describes the old rule.

> **Start the exercise**
>
> ```bash
> git clone https://github.com/tosin2013/invoice-exception-desk.git
> cd invoice-exception-desk
> git switch l4-start                 # L3.5 code + constitution v2.0.0 (9044f2b)
> git switch -c my-l4                 # your own working branch
> ```

> **Inspect our solution**
>
> - The L4 commits were merged into [`l3h-handoff`](https://github.com/tosin2013/invoice-exception-desk/tree/l3h-handoff) by [PR #8](https://github.com/tosin2013/invoice-exception-desk/pull/8). The `l4-solution` branch was deleted after the merge; its head `f6a9b5a` is fully inside `l3h-handoff`. See the steps with `git log --oneline l4-start..l3h-handoff`.
> - [`drift.md`](https://github.com/tosin2013/invoice-exception-desk/blob/l3h-handoff/specs/003-desk-import/drift.md) lists every mismatch we found and what we did about it.
> - [`run.log`](https://github.com/tosin2013/invoice-exception-desk/blob/l3h-handoff/run.log) ends with a short, sanitized receipt of the L4 run (timings, commands, results). The raw OpenCode transcripts were kept off the repo this time.
> - Compare everything: [`l4-start...l3h-handoff`](https://github.com/tosin2013/invoice-exception-desk/compare/l4-start...l3h-handoff).
>
> ```mermaid
> flowchart LR
>   s["l4-start<br/>9044f2b<br/>constitution v2.0.0"] --> c1["FR-008a: spec, tests, code<br/>2526069"]
>   c1 --> c2["drift fixes + drift.md<br/>1a3d6a4"] --> c3["004 re-check<br/>3c2aa44"] --> c4["run.log receipt<br/>271cd2d"]
>   c4 --> g(["sealed key<br/>PASS"])
>   c4 --> r1["review L1<br/>0ea7ffc"] --> r2["review L2<br/>f6a9b5a"] --> m["PR #8 merged<br/>8c302ee"]
> ```

## Who did what in our run

| Role | Who | Did |
|---|---|---|
| **You** (the human) | Tosin | ruled on the amount policy, ratified constitution v2.0.0, chose the 004 note, merged PR #8 |
| Operator | the Spec Kit bot (strong-model side) | wrote the spec edit and the plan revision by hand, drove OpenCode, wrote `drift.md` and the `run.log` receipt |
| Free model | OpenCode 1.19.3 with `opencode/deepseek-v4.1-flash-free` | clarify, tasks, implement, analyze, one docs-only drift fix |
| Reviewer | Grok Bot | read-only review of the result |
| Key holder and grader | OpenAI/Codex | wrote and sealed the L4 answer key before the build, then graded |

## The change we made

[L3](L3-invoice-desk.md) ended with an "Open policy questions (your call)" box: a zero amount, a leading zero, and lower-case `usd`. L4 is that mission done for real. Tosin answered them:

| Question | Ruling |
|---|---|
| Is an `amount_cents` of `0` valid? | **No.** `invalid_amount`. A zero-amount "invoice" isn't money anyone owes. |
| Is a leading zero, such as `0100`, valid? | **No.** `invalid_amount`. One amount should have one spelling. |
| Is lower-case `usd` valid? | **No change.** It was already rejected by FR-009 (exactly `USD`). |

Everything else stays as it was: `paid_cents` parsing (a leading zero is still fine there), the order in which errors are reported (precedence), whitespace trimming, and duplicate handling. A fully paid invoice with a positive amount still lands in the `paid` bucket.

**Why this is a good maintenance exercise.** It changes a shipped feature (`specs/003-desk-import`). It flips an existing test (`test_zero_amount_is_valid_and_lands_in_paid`). And it ripples into a second feature: 004's follow-up queue used to be able to receive a zero-amount invoice in its `paid` bucket, and now it can't. The frozen fixture (`data/invoices.csv`) has none of these values, so AT-01 to AT-04 must not move.

### Edit the old spec, or start a new one?

- **Edit the owning spec** when the change alters a rule that feature already promises. That's our case: FR-008 lives in 003.
- **Start a new feature folder** (`005-…`) when you add a new capability or a new version of a stored format or API. That folder links back to the specs it changes.

## 1. Constitution first (v2.0.0)

Before touching the feature, Tosin ratified constitution **v2.0.0** (commit `9044f2b`, which *is* `l4-start`). It's a **MAJOR** version because rule II was redefined: computation stays pure, but a persistence step named by its spec and plan (like 004's annotation file) is now allowed. The two rules this lesson runs on:

- **Rule V, specs are living.** A behaviour change lands in one commit with its spec change and its tests. Inside an existing feature you add a **dated Clarification** (what changed, who decided, why). You mark the old requirement **superseded** and keep it, with the date and the one requirement that replaces it. You don't delete it.
- **Rule VIII, a sealed answer key per behaviour change.** Someone who isn't the builder writes the key and seals it **before implementation starts**. It stays outside anything the builder can reach. Builder-written tests alone never mean "done".

A **sealed** key is one whose files are hashed (fingerprinted with SHA-256) and the hashes written down, so anyone can later prove the key wasn't changed after the build.

## 2. Preflight

Record the tool versions and the starting test count before you change anything.

```bash
alias specify='uvx --from git+https://github.com/github/spec-kit.git@v1.1.3 specify'
specify version                  # expect 1.1.3
specify integration status       # expect opencode, 0 modified or missing managed files
python -m pytest -q              # expect 190 passed
```

We pinned Spec Kit with `uvx` because the machine's default `specify` was a newer development build (1.2.2.dev0). Pin the version the earlier lessons used, or your templates may not match ours.

Then point Spec Kit at the feature you're changing, without writing `.specify/feature.json` (see [L3.5](L35-agent-handoff.md)):

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/003-desk-import
export SPECIFY_FEATURE_NO_PERSIST=1
```

**Our real run:** 07:08 EDT on Oct 24, 2026: 1.1.3, `opencode` with 0 modified managed files, **190 passed**. (That's L3.5's 188 plus two tests from a fix merged just before L4, PR #7.)

## 3. Edit the spec by hand

You write this part, not the free model. It's the decision, and the decision is yours. In one go:

1. Add a **dated Clarification session** to `spec.md`.
2. Mark **FR-008** superseded and add **FR-008a**.
3. Revise the edge cases.
4. Add an amount-policy note under AT-02 in `ACCEPTANCE.md`.

Here's what the Clarification looks like (shortened from our [`spec.md`](https://github.com/tosin2013/invoice-exception-desk/blob/l3h-handoff/specs/003-desk-import/spec.md)):

```markdown
### Session 2026-10-24 (L4 revision, decided by Tosin Akinosho)

- Q: Is an `amount_cents` of `0` a valid invoice amount? → A: No. Only positive face
  amounts are valid; `0` is rejected as `invalid_amount`. Why: a zero-amount "invoice"
  is not a receivable, and accepting it silently placed a non-debt in the `paid` bucket
  (and, through 004, in the follow-up queue's `paid` bucket). ... Replaces FR-008 with FR-008a.
```

And here's a **superseded requirement**. The old text stays, struck through and labelled, right above the one that replaces it:

```markdown
- **FR-008** *(SUPERSEDED 2026-10-24 by FR-008a; non-normative, kept for history)*:
  ~~`amount_cents` MUST be one or more ASCII digits `[0-9]+` ...~~
- **FR-008a** *(added 2026-10-24, Clarification session 2026-10-24, decided by Tosin Akinosho;
  replaces FR-008)*: After trimming (FR-030), `amount_cents` MUST be a positive, canonical
  ASCII decimal integer: it MUST match `[1-9][0-9]*` ...
```

"Non-normative" means "no longer a rule; kept so readers can see what it used to say". Keeping the ID (FR-008) means old links, tests and reviews that cite it still make sense.

## 4. Clarify (free model asks, you answer)

```bash
opencode run --auto -m opencode/deepseek-v4.1-flash-free --command speckit.clarify \
  "Ask your questions about the revised amount policy. Do not answer them yourself and do not change any files." < /dev/null
```

(The prompts on this page are short versions. Our exact prompts aren't published, but the clarify one did tell the model not to answer its own questions.) `--auto` approves the agent's permission requests without stopping, so only use it in a checkout you can throw away.

**Our real run:** about 3 minutes (07:09 to 07:12), exit 0, no files changed. Five questions, and **the model answered none of them itself**:

1. How is `paid_cents` parsed, and are `0100` and `100` the same for duplicate checks?
2. Does "a blank required field" mean all seven fields, or only `issuer` and `invoice_id`?
3. Which whitespace characters are trimmed?
4. Does 004's promise that import "remains unchanged" (004 FR-021, SC-010) need an amendment?
5. The frozen fixture has none of the new invalid values, so how is the new rule tested?

Each came with options. For example, question 5 offered:

> **A.** Add synthetic unit tests for `0`, `00`, `0100`, `+100`, and similar values while keeping the frozen fixture and oracle byte-identical.
> **B.** Add new rows to `data/invoices.csv` and regenerate the oracle and sealed key.

Questions 1 to 3 were already covered by the rulings: **unchanged**. Questions 4 and 5 weren't covered by any ruling, so they were answered from the approved run brief and the constitution, and the spec says so. Q4: no change to 004's requirements, because the revision is owned by 003 and the ripple is recorded. Q5: synthetic tests written first, the fixture byte-unchanged, and grading against the sealed key.

The useful part is that clarify found the two questions a human hadn't ruled on. Write down **who** answered each one. Later, review flagged Q4 as a governance call the human should confirm, and Tosin chose to go one step further (section 8).

## 5. Revise the plan, regenerate the tasks

- **Plan (by hand).** We added an **"L4 revision (2026-10-24)"** section to the end of 003's `plan.md`. It covers what changes (one new amount pattern in `_validate_row`, with `paid_cents` keeping its old pattern), which tests flip, which tests get added, and the **004 ripple**. We also added one inline "superseded" note. Nothing else in the plan was rewritten.
- **Tasks (free model).**

  ```bash
  opencode run --auto -m opencode/deepseek-v4.1-flash-free --command speckit.tasks \
    "Append an L4 phase for FR-008a. Do not change T001-T020, spec.md or plan.md." < /dev/null
  ```

  **Our real run:** about a minute (07:13 to 07:14). It **appended** "Phase 7: L4 revision" with **T021 to T030** (+24 lines). T001 to T020 were unchanged. The phase says the test tasks (T021 to T027) must be written and **fail** before the code task (T028).

Rule V says to *regenerate* the plan. We edited it by hand, append-only, and the reviewer accepted that as the intended reading. If you regenerate instead, diff the result against the old plan before you commit.

## 6. Implement, tests first

```bash
opencode run --auto -m opencode/deepseek-v4.1-flash-free --command speckit.implement \
  "Implement Phase 7 (T021-T030) only. Tests first; run python -m pytest -q." < /dev/null
```

**Our real run:** about a minute (07:14 to 07:15), one call, exit 0. The model changed the tests first and ran them against the old code:

```text
8 failed, 197 passed in 0.36s
TDD confirmed: 8 Phase 7 tests fail against current code. Implementing T028.
```

Then the code change, one new pattern:

```python
_AMOUNT_PATTERN = re.compile(r"[1-9][0-9]*\Z")   # amount_cents (FR-008a)
_INTEGER_PATTERN = re.compile(r"[0-9]+\Z")       # paid_cents, unchanged (FR-010)
```

Result: **205 passed** (190 + 15 new test cases).

**The flip.** The old test said a zero amount was valid. It was **changed, not deleted**:

```diff
-def test_zero_amount_is_valid_and_lands_in_paid():
+def test_zero_amount_is_rejected_as_invalid_amount():
```

Its assertions were inverted (now `rejected` / `invalid_amount`, no accepted fields, an empty `paid` bucket). The rejection table gained `0`, `00`, `0100` and ` 0100 `. New tests check that canonical amounts are accepted, that a fully paid positive invoice still lands in `paid`, that `paid_cents` of `0100` still works, the precedence cases, and that a rejected zero row doesn't count as a duplicate.

Why "change, not delete"? A deleted test leaves no trace that the old behaviour was ever promised. A renamed, inverted test shows the reviewer exactly which promise changed.

The spec, plan, tasks, `ACCEPTANCE.md`, tests and code went into **one commit**, `2526069`, as rule V asks.

## 7. Look for drift (analyze both features, then grep)

**Drift** is when two documents, or a document and the code, no longer say the same thing. A behaviour change creates drift in places you didn't edit. `/speckit.analyze` is read-only and checks one feature at a time, so run it on **every feature the change touches**:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/003-desk-import
opencode run --auto -m opencode/deepseek-v4.1-flash-free --command speckit.analyze \
  "Read-only. Do not modify any file." < /dev/null

export SPECIFY_FEATURE_DIRECTORY=specs/004-deterministic-followup-queue
opencode run --auto -m opencode/deepseek-v4.1-flash-free --command speckit.analyze \
  "Read-only. Do not modify any file." < /dev/null
```

**Our real run:** 003 found 1 HIGH, 1 MEDIUM and 3 LOW. 004 found 3 HIGH, 3 MEDIUM and 1 LOW. That's **4 HIGH** (3 distinct, because one 004 finding repeated the 003 one). **All four were stale text, not wrong code:**

| ID | What analyze found | Fix |
|---|---|---|
| 003-I1 | Task T005 still stated the old `[0-9]+` amount rule, with no superseded marker | dated historical note under T005; T005 text kept as is |
| 004-C1 | 004's plan still checked against constitution v1.1.0 | old check marked historical; v2.0.0 re-check added |
| 004-I1 | The ripple wasn't recorded on the 004 side, and 004's plan said `tests/test_invoice_desk.py` "must remain unchanged" | ripple recorded in 004's `plan.md`; "unchanged" explained as 004's own build scope |
| 004-I3 | Same as 003-I1 | fixed with 003-I1 |

This is how analyze reported the first one:

> T005 still defines `amount_cents` as invalid only when it does not match `[0-9]+`, which makes `0`, `00`, and `0100` valid. This contradicts FR-008a and the later T028, and—unlike FR-008—is not marked superseded/non-normative.

The fixes were docs-only, made by one OpenCode run with a tightly scoped prompt (no `.py` files, no tests, never delete text, add dated notes), and committed as `1a3d6a4`. Then we **re-ran analyze on both features**: 0 CRITICAL, 0 HIGH, and all four earlier HIGHs reported **RESOLVED** (`3c2aa44`).

**Then grep by hand.** Analyze reads specs, not your whole repo. We searched specs, docs, `ACCEPTANCE.md`, README, ROADMAP, NON_GOALS, code and tests for `zero amount`, `[0-9]+`, `leading zero`, `0100` and similar. What we found was either already fixed, intended (`paid_cents` still uses `[0-9]+`), or unrelated and older than L4.

**`drift.md`.** Every mismatch goes in [`specs/003-desk-import/drift.md`](https://github.com/tosin2013/invoice-exception-desk/blob/l3h-handoff/specs/003-desk-import/drift.md): what, where, how it was found, and either **Fixed** or **Accepted, why**. Lower findings we left alone are there too. For example, 004-G1 (no 004-side test for a zero-amount row) is accepted, because 003's tests cover the rejection and 004 already tests that rejected rows stay out of the queue. Merge conflicts: none, and `drift.md` says so.

## 8. Review

Grok Bot reviewed the result read-only at `271cd2d`. **Verdict: accept with notes**, no CRITICAL or HIGH findings. It reproduced the tests-first claim by running the new tests against the old code (8 failed, 197 passed), and confirmed that the constitution and the fixture were byte-unchanged. It also re-ran the L3 sealed key: **core 295/295** (no regressions). The probes went from **19/35 to 28/35**. All seven still failing come from the lower-case `usd` row, which stays rejected on purpose.

Two notes were fixed in docs-only commits after the graded head:

- **L1:** `run.log` said "Builder had no access to any answer key." True for the L4 key, but the L3 key folder sat on the same machine, readable by the builder (no sign it was read). Reworded in `0ea7ffc`.
- **L2:** clarify Q4 ("no amendment to 004") was a governance call made from the brief, not by Tosin. Tosin chose to add a dated **L4 note** under 004's FR-021 and SC-010, plus a 004 Clarification, without changing their requirement text or any 004 code (`f6a9b5a`).

## 9. Grade against the sealed key

This is rule VIII in practice. OpenAI/Codex wrote **L4-key-v1.0.0** for the new rules and sealed it at **06:50 EDT** on Oct 24, 2026 (10:50 UTC), before the build started at 07:08 EDT. It kept the key in its own environment, outside the builder's machine and the repo. Only the seal receipt (hashes, no contents) and, later, the grade came back. The L3 key stayed byte-unchanged and is reused for regression.

| File | sha256 |
|---|---|
| `author.py` | `4c68c39895e2d9e157528e7bb9a31394849239d27cc4a00949126947ece4e40c` |
| `key.json` | `71e7bfce750b55ac6b8aafd06fea8c7d5736690df35a6a0da90978348948b830` |
| `grade.py` | `75a48406a3551f7a8aecc2efca6409af1fbc620bae630a14411022ec476f7edc` |
| `provenance.json` | `2e474e411c883a86ee51b97c50e983708a724abf2f77eb50695c3d1332a00800` |

The key reports three **buckets** separately, so an approved policy change is never counted as a fix:

| Bucket | What it checks | Result at `271cd2d` |
|---|---|---|
| L3 regression | old behaviour that must not move | **86/86** |
| Approved L4 policy | the new FR-008a rules | **38/38** |
| Intentional divergence | where we knowingly differ from the older R0 policy (lower-case `usd`) | **1/1** confirmed |

**Verdict: PASS.** The grader first checked that all four files matched the seal hashes, then graded a fresh clone at `271cd2d`. The two review-note commits after it touch only `run.log` and 004's `spec.md`. You can't reproduce these numbers yourself, because the key isn't published. A published key stops being a key.

Then Tosin merged [PR #8](https://github.com/tosin2013/invoice-exception-desk/pull/8) at 10:23 AM EDT.

## What went wrong, and how we handled it

- **Free-model usage limits.** Analyze on 003 returned nothing on runs 1 to 4; run 5 worked. The 004 re-check returned nothing three times; the fourth worked. The docs-only fix needed three tries (one empty, one started without its prompt). An empty run isn't a clean result. Our wrapper put a 15-minute `timeout` on each call and watched OpenCode's log for "Free usage limit reached", then retried later.
- **The session was interrupted twice.** Each time we resumed from the state on disk, not from chat memory. That's the L3.5 lesson again: only what's written down survives.
- **A stale line about key access.** `run.log` claimed no access to *any* key while the L3 key sat on the same machine. Review caught it and we reworded it. Say exactly what isolation you have.
- **Stale "unchanged" lines.** 004's plan, quickstart and research, and 003's T018/T030, say files "must remain unchanged" that L4 changed. They were scope rules for an earlier build. We accepted them, with a reason, in `drift.md`, rather than rewriting history.
- **A pre-existing bug found before the start.** While planning L4, a probe showed that `set_owner` and `set_notes` failed on a one-shot iterator. It was fixed and reviewed on its own (PR #7) **before** `l4-start` was cut, so the L4 change didn't mix with an unrelated fix.

## Checklist

- [ ] Working on your own branch (`git switch -c my-l4`)
- [ ] Preflight recorded: pinned `specify version`, `specify integration status`, starting test count
- [ ] The human rules on the change first. Each ruling is written down with the date and who decided
- [ ] The **owning** spec gets a dated Clarification. The old requirement is marked superseded and kept; the new one has a new ID
- [ ] Clarify asks, it doesn't answer. Each answer says who gave it
- [ ] Plan revised, tasks appended. Old tasks keep their text
- [ ] The answer key for the change is sealed **before** implement, by someone other than the builder
- [ ] Tests change first and fail against the old code. Flipped tests are changed, not deleted
- [ ] Spec, tests and code land in one commit
- [ ] Analyze on **every** feature the change touches, then grep for the old rule by hand
- [ ] Every mismatch in `drift.md`: fixed, or accepted with a reason. Empty analyze runs are retried, not counted
- [ ] Grade on three buckets: regression, approved policy, intentional divergence

Compare the start branch with the finished steps: [`l4-start...l3h-handoff`](https://github.com/tosin2013/invoice-exception-desk/compare/l4-start...l3h-handoff). Next: [L4.5: Upgrading Spec Kit itself](L45-speckit-upgrade.md). Back: [L3.5: Handing work between coding agents](L35-agent-handoff.md). Back to [Home](index.md).
