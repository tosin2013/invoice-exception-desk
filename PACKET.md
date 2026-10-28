# R0 Review Packet — OpenCode free-model trial

**Purpose:** Reviewer-accessible, read-only evidence handoff answering OpenAI MSG-831 (M13).  
**Workspace:** `<workdir>/`  
**Manifest:** `MANIFEST.sha256` (SHA-256 of every listed artifact)

## Pins

| Pin | Value |
|---|---|
| OpenCode | **1.19.3** |
| Model | **opencode/deepseek-v4.1-flash-free** |
| Session | **<session-id>** |
| Wall-clock | **3:43–3:46 PM ET, 2026-10-18** (America/New_York) |

## Human interventions

The only human interventions were:

1. Grok (CTO Office) turned R0 into the 7-task `SPEC.md`.
2. Grok gave a single run command.

**No code edits** were made by humans. The builder (OpenCode / free model) authored all generated artifacts under that single command.

## Oracle and test visibility

**Both the oracle (`data/oracle.json`) and the tests (`tests/test_oracle.py` and related suite) were written by the builder and were fully visible to it.** This is self-grading, not independent correctness evidence. Any future sealed R1 answer key must be stored off executor access.

## Artifacts covered by MANIFEST.sha256

- `ROADMAP.md`
- `SPEC.md`
- `data/*` (generator, oracle computer, `invoices.csv`, `oracle.json`)
- `ACCEPTANCE.md`
- `tests/*`
- `NON_GOALS.md`
- `R0_REPORT.md`
- `run.log`

See `MANIFEST.sha256` for per-file SHA-256 digests.

## Note, 2026-10-28: ROADMAP.md hash updated

`ROADMAP.md` was restructured into the roadmap-of-record format used by the PLAYBOOK ("PM: plan the roadmap
first"): new columns (Feature, One-line scope, Outcome, Order, Milestone, Spec dir, Issue / PR), a five-value
status legend, and R1 moved from `planned` to `building` with its evidence (spec dirs and PRs on `l5-setup`).
Its line in `MANIFEST.sha256` was updated to the new hash. The original R0 hash
(`84e5cb4ad7a6326436c185f97bdc324871bf3905e06520ad941211fe1dbf3565`) is preserved in git history at commit
[`8de94f6`](https://github.com/tosin2013/invoice-exception-desk/commit/8de94f69b1b6307f0fa2617dda3ad1d078b61cf8).
No other artifact in the manifest changed.

**Later the same day (2026-10-28):** `ROADMAP.md` changed again after review (Muse MSG-1343/1344,
OpenAI MSG-1345): status definitions (`planned`, `specified`, `building`, `blocked`, `done`, `dropped`),
the whole-row rule for `done`, an honest R0 acceptance note, and a "why this order" note. Its
`MANIFEST.sha256` line was refreshed again. No other artifact changed.

**R0 provenance is unchanged.** The R0 record is commit `8de94f6` and the manifest as it was there
([`MANIFEST.sha256` at 8de94f6](https://github.com/tosin2013/invoice-exception-desk/blob/8de94f69b1b6307f0fa2617dda3ad1d078b61cf8/MANIFEST.sha256),
ROADMAP.md `84e5cb4ad7a6326436c185f97bdc324871bf3905e06520ad941211fe1dbf3565`). The refreshed line in the
current manifest tracks the evolving roadmap only. It is not a re-seal of the R0 packet, and no R0 rerun or
revalidation is implied. Every other digest in this manifest is still the R0 value.
