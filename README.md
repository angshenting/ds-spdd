# ds-spdd

[![CI](https://github.com/angshenting/ds-spdd/actions/workflows/ci.yml/badge.svg)](https://github.com/angshenting/ds-spdd/actions/workflows/ci.yml)

Spec-driven development for data science and machine learning projects, built
for AI coding agents.

This is my take on SPDD (Structured Prompt-Driven Development) for data
science workloads, using [Open-SPDD](https://github.com/gszhangwei/open-spdd)
as the base reference. A project gets a design contract, `ds/canvas.md`, which
follows the REASONS canvas. The agent writes the contract before any pipeline
code, keeps it in sync when the code changes, and checks it with a validator.
Every claim in the final report should trace back to the contract.

## What's in here

| Path | What it is |
|---|---|
| `skills/` | Agent skills (`SKILL.md` files) that encode the DS/ML workflow |
| `frameworks/ds-canvas/` | Python package and CLI that validates canvas files |
| `examples/churn-demo/` | Worked example: a churn-prediction project delivered with the skills |
| `examples/mnist-digits/` | Test run of `spec-driven-ds` on scikit-learn's handwritten digits, with a findings log on the skills |
| `tests/` | pytest suite for `ds-canvas` |
| `AGENTS.md` | Working rules for AI agents contributing to this repo |

### Skills

| Skill | Use it when |
|---|---|
| `spec-driven-ds` | Starting a DS/ML project from a business goal or dataset, when requirements, data or model choices change, or when an existing project needs its design contract reconstructed |
| `ds-canvas-sync` | Pipeline code has drifted from `ds/canvas.md` and the canvas needs to catch up (code to canvas) |
| `data-cleaning` | Data-quality findings need to become validated contract rules and a pipeline that fails loudly |
| `feature-engineering` | Adding derived features: hypothesis first, selected on validation, losers removed from the contract |
| `model-enhancements` | Targets are unmet on clean data and the model layer needs iterating under an explicit budget |

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/angshenting/ds-spdd.git
cd ds-spdd
uv sync
```

Scaffold a canvas, fill in the `REPLACE` placeholders, then validate it:

```bash
uv run ds-canvas init ds/canvas.md
uv run ds-canvas validate ds/canvas.md
```

To use the skills with an agent, copy or symlink the directories under
`skills/` into the agent's skills folder (for Claude Code, `.claude/skills/`).
The skills call the `ds-canvas` CLI, so install it in the project the agent is
working on:

```bash
uv add "ds-canvas @ git+https://github.com/angshenting/ds-spdd#subdirectory=frameworks/ds-canvas"
```

For a full run-through, start with
[`examples/churn-demo/README.md`](examples/churn-demo/README.md).

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Conventions (TDD, skill authoring rules, framework boundaries) are in
[`AGENTS.md`](AGENTS.md).

## Acknowledgements

Builds on [Open-SPDD](https://github.com/gszhangwei/open-spdd) by gszhangwei,
released under the MIT License. It is the base reference for the SPDD method
and the REASONS canvas used here.

## License

[MIT](LICENSE) © 2026 Shen Ting Ang
