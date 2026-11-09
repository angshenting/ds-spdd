# Canvas Sync Report

One report per sync. Overwrite the previous one — history lives in version
control.

## Divergence inventory

Compare `ds/canvas.md` against what the code actually does. Every dimension
gets at least one row.

| # | Dimension | Canvas says | Code does | Verdict |
|---|---|---|---|---|
| 1 | R | | | |
| 2 | E | | | |
| 3 | A | | | |
| 4 | S (structure) | | | |
| 5 | O | | | |
| 6 | N | | | |
| 7 | Safeguards | | | |

Verdicts: in-sync / safeguard-violation / requirement-change /
contract-change / refactor-only / canvas-only.

## Decisions

- Safeguard violations found (must be fixed in code, never synced):
- Contract changes applied to the canvas (sections + what changed):
- Canvas-only drift (implement in code or remove from canvas — which, and why):

## Results staleness

- Contract-relevant sections changed (E / A / S — list, or "none"):
- Verdict: Results kept / Results removed
- Reason:

## Post-sync validation

- `ds-canvas validate ds/canvas.md` exit code:
- `report.md` updated (yes/no) and why:
