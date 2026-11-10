from canvas_factory import valid_canvas
from ds_canvas import parse, validate


def test_fitted_op_must_declare_fit_on_train():
    text = valid_canvas().replace(
        "  - op: impute_median\n    fields: [monthly_charges]\n    fit_on: train\n",
        "  - op: impute_median\n    fields: [monthly_charges]\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.path == "preprocessing[0]"
        and f.severity == "error"
        and "fit_on: train" in f.message
        for f in findings
    )


def test_preprocessing_op_must_list_fields():
    text = valid_canvas().replace(
        "  - op: drop\n    fields: [churned_next_30d]\n", "  - op: drop\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure" and f.path == "preprocessing[2].fields" and f.severity == "error"
        for f in findings
    )


def test_unknown_preprocessing_op_is_an_error():
    text = valid_canvas().replace("op: impute_median", "op: frobnicate")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.path == "preprocessing[0].op"
        and f.severity == "error"
        and "frobnicate" in f.message
        and "scale_standard" in f.message
        for f in findings
    )


def test_target_must_be_dropped_in_preprocessing():
    text = valid_canvas().replace(
        "  - op: drop\n    fields: [churned_next_30d]\n",
        "  - op: drop\n    fields: [customer_id]\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.path == "preprocessing"
        and f.severity == "error"
        and "churned_next_30d" in f.message
        and "drop" in f.message
        for f in findings
    )


def test_preprocessing_fields_must_be_declared_in_entities():
    text = valid_canvas().replace(
        "  - op: impute_median\n    fields: [monthly_charges]\n    fit_on: train\n",
        "  - op: impute_median\n    fields: [monthly_fee]\n    fit_on: train\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.path == "preprocessing[0].fields"
        and f.severity == "error"
        and "monthly_fee" in f.message
        for f in findings
    )


def test_target_must_not_appear_in_non_drop_preprocessing():
    text = valid_canvas().replace(
        "  - op: one_hot_encode\n    fields: [plan_type]\n    fit_on: train\n",
        "  - op: one_hot_encode\n    fields: [plan_type, churned_next_30d]\n    fit_on: train\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.path == "preprocessing[1].fields"
        and f.severity == "error"
        and "leakage" in f.message
        for f in findings
    )
