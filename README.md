# L3 start: a real multi-feature project (Invoice Exception Desk)

This branch is the starting point for **L3: Invoice Exception Desk walkthrough** in the [Spec Kit Developer Guide](https://tosin2013.github.io/invoice-exception-desk/L3-invoice-desk.html).

It is the finished L2 project (`bill_split`, specify-cli 1.1.3, OpenCode integration) plus the frozen **R0 discovery kit** for the Invoice Exception Desk:

- `ROADMAP.md`: phases R0 to R6. L3 builds the first slice of **R1**.
- `ACCEPTANCE.md`: acceptance items AT-01 to AT-10. L3 covers AT-01 to AT-04.
- `NON_GOALS.md`: what the Desk must never do.
- `data/invoices.csv`: 30 synthetic rows (valid, duplicate, invalid, empty), plus the deterministic generator that wrote them.

The oracle (`data/oracle.json` and `data/compute_oracle.py`) is **deliberately not on this branch**. It's the reviewer's sealed answer key, so the builder never sees it.

What to do:
1. Install the pinned CLI: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.1.3`
2. Run the existing tests: `python -m pytest -q`
3. Follow the L3 page step by step.

The finished result is on the `l3-solution` branch.
