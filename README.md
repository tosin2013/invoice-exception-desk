# L2 start: first feature, end to end

This branch is the starting point for **L2: First feature, end to end** in the [Spec Kit Developer Guide](https://tosin2013.github.io/invoice-exception-desk/L2-first-feature.html).

It is the finished L1 project (`bill_split` with `split_bill`, initialised with specify-cli 1.1.3 and the OpenCode integration). In L2 you add a second feature, `split_weighted`, and go through **every** Spec Kit phase once: constitution check, specify, clarify, plan, tasks, implement, and analyze. Then a reviewer grades it with an independent answer key.

What to do:
1. Install the CLI pinned to the guide's version: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.1.3`
2. Check it: `specify version` and `specify check`
3. Run the L1 tests: `python -m pytest -q`
4. Follow the L2 page step by step.

The finished result is on the `l2-solution` branch.
