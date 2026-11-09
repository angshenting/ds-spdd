from canvas_factory import valid_canvas
from ds_canvas import parse, validate


def test_missing_norms_section_is_reported_as_error():
    canvas_text = valid_canvas().replace("## N — Norms", "## N — Notes")
    findings = validate(parse(canvas_text))
    errors = [f for f in findings if f.severity == "error"]
    assert any(f.dimension == "norms" for f in errors)


def test_complete_canvas_validates_with_no_findings():
    findings = validate(parse(valid_canvas()))
    assert findings == []


def test_missing_frontmatter_name_is_reported_as_error():
    canvas_text = valid_canvas().replace("name: churn-prediction\n", "")
    findings = validate(parse(canvas_text))
    errors = [f for f in findings if f.severity == "error"]
    assert any(f.dimension == "frontmatter" and f.path == "name" for f in errors)
