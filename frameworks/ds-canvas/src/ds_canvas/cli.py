import sys
from importlib import resources
from pathlib import Path

from ds_canvas.model import Canvas
from ds_canvas.parser import parse
from ds_canvas.rules import validate

USAGE = "usage: ds-canvas <validate FILE | init PATH>"


def _validate_command(path: str) -> int:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 1
    canvas = parse(text)
    findings = validate(canvas)
    _print_findings(canvas, findings)
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = len(findings) - errors
    if findings:
        print(f"\n{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def _print_findings(canvas: Canvas, findings: list) -> None:
    name = canvas.name or "<unnamed>"
    if not findings:
        print(f"canvas '{name}' is valid")
        return
    print(f"canvas '{name}' has {len(findings)} finding(s):")
    for finding in findings:
        location = f" [{finding.dimension}]" if finding.dimension else ""
        path = f" {finding.path}:" if finding.path else ":"
        print(f"{finding.severity}{location}{path} {finding.message}")


def _init_command(path: str) -> int:
    target = Path(path)
    if target.exists():
        print(f"error: refusing to overwrite existing {path}", file=sys.stderr)
        return 1
    template = (resources.files("ds_canvas") / "templates" / "canvas.md").read_text(
        encoding="utf-8"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template, encoding="utf-8")
    print(f"canvas scaffold written to {path}")
    print("fill in REPLACE placeholders, then run: ds-canvas validate " + path)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    command, target = args
    if command == "validate":
        return _validate_command(target)
    if command == "init":
        return _init_command(target)
    print(USAGE, file=sys.stderr)
    return 2
