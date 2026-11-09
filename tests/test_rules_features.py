from canvas_factory import valid_canvas
from ds_canvas import parse, validate


def canvas_with_e_fields(extra_fields: str) -> str:
    text = valid_canvas()
    anchor = (
        "      - name: charge_log\n        type: float\n        derived_from: [monthly_charges]\n"
    )
    assert anchor in text
    return text.replace(anchor, anchor + extra_fields)


def test_derived_from_must_reference_declared_fields():
    text = canvas_with_e_fields(
        "      - name: ghost_ratio\n        type: float\n        derived_from: [not_a_field]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities" and f.severity == "error" and "not_a_field" in f.message
        for f in findings
    )


def test_transitive_target_leakage_in_derived_fields():
    text = canvas_with_e_fields(
        "      - name: churn_history\n"
        "        type: float\n"
        "        derived_from: [churned_next_30d]\n"
        "      - name: churn_proxy\n"
        "        type: float\n"
        "        derived_from: [churn_history]\n"
    )
    findings = validate(parse(text))
    leaked = [f for f in findings if f.severity == "error" and "leakage" in f.message]
    assert {f.path.split(".")[-1] for f in leaked} == {"churn_history", "churn_proxy"}


def test_target_must_not_declare_derived_from():
    text = valid_canvas().replace(
        "      - name: churned_next_30d\n        type: integer\n        role: target\n",
        "      - name: churned_next_30d\n"
        "        type: integer\n"
        "        role: target\n"
        "        derived_from: [monthly_charges]\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "churned_next_30d" in f.message
        and "derived_from" in f.message
        for f in findings
    )


def test_derive_op_requires_fn_and_output():
    text = valid_canvas().replace(
        "  - op: derive\n    fields: [monthly_charges]\n    fn: log1p\n    output: charge_log\n",
        "  - op: derive\n    fields: [monthly_charges]\n",
    )
    findings = validate(parse(text))
    paths = {f.path for f in findings if f.severity == "error"}
    assert "cleaning[2].fn" in paths and "cleaning[2].output" in paths


def test_derive_op_fn_must_be_known():
    text = valid_canvas().replace("fn: log1p", "fn: transmogrify")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[2].fn"
        and "transmogrify" in f.message
        for f in findings
    )


def test_derive_output_must_be_declared_in_entities():
    text = valid_canvas().replace("output: charge_log", "output: charge_ln")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[2].output"
        and "charge_ln" in f.message
        for f in findings
    )


def test_aggregate_requires_group_by_lookback_and_fn():
    text = valid_canvas().replace(
        "  - op: aggregate\n"
        "    fields: [support_tickets]\n"
        "    group_by: [customer_id]\n"
        "    lookback: 3\n"
        "    fn: mean\n"
        "    output: tickets_3m_mean\n",
        "  - op: aggregate\n    fields: [support_tickets]\n    output: tickets_3m_mean\n",
    )
    findings = validate(parse(text))
    paths = {f.path for f in findings if f.severity == "error"}
    assert {"cleaning[3].group_by", "cleaning[3].lookback", "cleaning[3].fn"} <= paths


def test_aggregate_lookback_must_be_positive():
    text = valid_canvas().replace("lookback: 3", "lookback: 0")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure" and f.severity == "error" and f.path == "cleaning[3].lookback"
        for f in findings
    )


def test_aggregate_in_preprocessing_is_an_error():
    text = valid_canvas().replace(
        "preprocessing:\n",
        "preprocessing:\n"
        "  - op: aggregate\n"
        "    fields: [support_tickets]\n"
        "    group_by: [customer_id]\n"
        "    lookback: 3\n"
        "    fn: mean\n"
        "    output: tickets_3m_mean\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "preprocessing[0]"
        and "cleaning" in f.message
        for f in findings
    )


def test_derived_field_without_producing_op_is_a_warning():
    text = canvas_with_e_fields(
        "      - name: orphan_feature\n        type: float\n        derived_from: [monthly_charges]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities" and f.severity == "warning" and "orphan_feature" in f.message
        for f in findings
    )


def test_factory_feature_ops_are_recognized():
    findings = validate(parse(valid_canvas()))
    assert findings == []
