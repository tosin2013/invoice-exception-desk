> **This is the code branch for L5 to L8** ([L5](https://tosin2013.github.io/invoice-exception-desk/L5-agent-loop.html), [L6](https://tosin2013.github.io/invoice-exception-desk/L6-issue-to-pr.html), [L7](https://tosin2013.github.io/invoice-exception-desk/L7-ci-grader.html), [L8](https://tosin2013.github.io/invoice-exception-desk/L8-dependabot.html), and the [PLAYBOOK](https://tosin2013.github.io/invoice-exception-desk/PLAYBOOK.html) wrap-up). CI grades every PR into it.
>
> Run the tests (223 pass) from the repo root: `uv run --no-project --with-requirements requirements-dev.txt python -m pytest -q`
>
> The L3-start text below is kept for history; it describes how this branch began.

# L3 start: a real multi-feature project (Invoice Exception Desk)

This branch is the starting point for **L3: Invoice Exception Desk walkthrough** in the [Spec Kit Developer Guide](https://tosin2013.github.io/invoice-exception-desk/L3-invoice-desk.html).

It is the finished L2 project (`bill_split`, recorded with specify-cli 1.1.3, OpenCode integration; this branch's Spec Kit files were later upgraded to 1.2.3, see `run.log`) plus the frozen **R0 discovery kit** for the Invoice Exception Desk:

- `ROADMAP.md`: phases R0 to R6. L3 builds the first slice of **R1**.
- `ACCEPTANCE.md`: acceptance items AT-01 to AT-10. L3 covers AT-01 to AT-04.
- `NON_GOALS.md`: what the Desk must never do.
- `data/invoices.csv`: 30 synthetic rows (valid, duplicate, invalid, empty), plus the deterministic generator that wrote them.

The oracle (`data/oracle.json` and `data/compute_oracle.py`) is **deliberately not on this branch**. It's the reviewer's sealed answer key, so the builder never sees it.

What to do:
1. Install the pinned CLI: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3`
   (Already have an older `specify`? Re-running `uv tool install` doesn't upgrade it. Add `--force`, or run it once without installing: `uvx --from git+https://github.com/github/spec-kit.git@v1.2.3 specify`.)
2. Run the existing tests: `python -m pytest -q`
3. Follow the L3 page step by step.

The finished result is on the `l3-solution` branch.
