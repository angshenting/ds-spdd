# AGENTS.md

Guidance for AI agents working in this repository. Read this before making changes.

## Project purpose

This repo develops **skills** and **frameworks** for using AI agents to build
data science / machine learning projects.

- **Skills** are agent-facing instruction packages (`SKILL.md` plus supporting
  scripts/resources) that encode a repeatable DS/ML workflow: project
  scaffolding, exploratory data analysis, experiment tracking, model
  evaluation, reporting.
- **Frameworks** are the Python libraries and scaffolding that those skills
  direct agents to use when building real DS/ML projects.

Most files here are read by an AI agent, not a human. Write for that reader:
explicit procedures, exact commands, small self-contained steps.

## Layout

Keep this accurate as the repo grows.

- `skills/<skill-name>/` — one directory per skill, containing its `SKILL.md`
  and everything the skill needs
- `frameworks/<name>/` — reusable, installable Python packages
- `tests/` — pytest suite

## Tooling

Defaults; adjust deliberately and update this section when you do.

- Python 3.12+, managed with `uv`
- `pytest` for tests
- `ruff` for lint and format
- `pyright` for typechecking

## Commands

Agents run these verbatim. Change here first, then in CI, if ever.

```
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Run lint and typecheck after completing any task, and tests for every change
in behaviour.

## Working agreements

- **TDD.** Red → green → refactor for any change in behaviour. One failing
  test for the next small piece, watch it fail for the expected reason, then
  the simplest code that passes, then refactor on green. Bugs are missing
  test coverage: reproduce with a failing test before fixing. Exemptions
  (spikes, config/docs, generated code) — state which applies rather than
  skipping silently.
- **Simple design / YAGNI.** Build what is asked. Skills encode the workflow
  actually used; no speculative options or configurability nobody requested.
- **Ask when it changes what gets built.** Routine judgement calls are yours;
  real forks are worth a question.
- **Small vertical slices.** Prefer a thin skill or framework that works end
  to end over a broad half-finished one.
- Keep the build green. Never weaken, skip or delete a test to get there; if a
  test is wrong, change it deliberately and say why.
- Match existing style; no comments unless asked.

## Skill authoring rules

- One skill per directory under `skills/`, named for what it does
  (`eda-analysis`, `model-eval`), not for what it contains (`utils`).
- `SKILL.md` begins with frontmatter:

  ```markdown
  ---
  name: skill-name
  description: What the skill does and when to use it, with explicit
    triggers ("Use when ...").
  ---
  ```

  The description is all an agent sees before deciding to load the skill —
  make the triggers concrete.
- Skills are self-contained: no references to files outside the skill
  directory.
- Give the agent a procedure — numbered steps, exact commands, checkable
  exit conditions — not prose advice.
- If a skill depends on a framework in this repo, pin exact entry points
  (module paths, CLI commands) in the skill text, and update them in the same
  change as any public API change.

## Framework conventions

- Packages are installable (`pyproject.toml`) and driven through their public
  interface — skills never touch internals.
- Public interface is tested from outside; tests document behaviour, not
  implementation.
