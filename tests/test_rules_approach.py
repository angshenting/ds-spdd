from canvas_factory import valid_canvas
from ds_canvas import parse, validate


def test_unknown_task_is_reported():
    text = valid_canvas().replace("task: binary_classification", "task: prediction")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "task" and f.severity == "error" for f in findings
    )


def test_target_must_be_a_declared_field():
    text = valid_canvas().replace("target: churned_next_30d", "target: not_a_field")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "target" and f.severity == "error" for f in findings
    )


def test_split_ratios_must_sum_to_one():
    text = valid_canvas().replace("train: 0.7", "train: 0.8")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "split.ratios" and f.severity == "error"
        for f in findings
    )


def test_temporal_split_requires_column():
    text = valid_canvas().replace("  column: month\n", "")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "split.column" and f.severity == "error"
        for f in findings
    )


def test_unknown_split_method_is_reported():
    text = valid_canvas().replace("method: temporal", "method: funky")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "split.method" and f.severity == "error"
        for f in findings
    )


def test_primary_metric_direction_must_be_known():
    text = valid_canvas().replace("direction: maximize", "direction: up", 1)
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach"
        and f.path == "metrics.primary.direction"
        and f.severity == "error"
        for f in findings
    )


def test_metric_target_op_must_be_comparison():
    text = valid_canvas().replace('op: ">="', 'op: "=~"', 1)
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach"
        and f.path == "metrics.primary.target.op"
        and f.severity == "error"
        for f in findings
    )


def test_model_families_need_baseline_and_candidate():
    text = valid_canvas().replace("role: baseline", "role: candidate")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "model_families" and f.severity == "error"
        for f in findings
    )


def test_primary_metric_must_be_key_metric_in_requirements():
    text = valid_canvas().replace("key_metrics:\n  - recall_at_30", "key_metrics: []")
    findings = validate(parse(text))
    assert any(
        f.dimension == "approach" and f.path == "metrics.primary" and f.severity == "error"
        for f in findings
    )
