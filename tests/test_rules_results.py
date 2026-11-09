from canvas_factory import valid_canvas_with_results
from ds_canvas import parse, validate


def test_undeclared_metric_in_results_is_reported():
    text = valid_canvas_with_results().replace(
        "  - metric: recall_at_30\n    achieved: 0.68",
        "  - metric: f1_at_30\n    achieved: 0.68",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "results" and f.path == "results[0].metric" and f.severity == "error"
        for f in findings
    )


def test_results_must_include_primary_metric():
    text = valid_canvas_with_results().replace("  - metric: recall_at_30\n    achieved: 0.68\n", "")
    findings = validate(parse(text))
    assert any(
        f.dimension == "results"
        and f.path == "results"
        and f.severity == "error"
        and "recall_at_30" in f.message
        for f in findings
    )


def test_achieved_value_must_meet_declared_target():
    text = valid_canvas_with_results().replace("achieved: 0.68", "achieved: 0.5")
    findings = validate(parse(text))
    assert any(
        f.dimension == "results" and f.path == "results[0].achieved" and f.severity == "error"
        for f in findings
    )


def test_canvas_with_satisfied_results_validates_clean():
    findings = validate(parse(valid_canvas_with_results()))
    assert findings == []
