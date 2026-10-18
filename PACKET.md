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
