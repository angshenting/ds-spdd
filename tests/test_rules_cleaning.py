from canvas_factory import valid_canvas
from ds_canvas import parse, validate

CLEANING_BLOCK = """\
cleaning:
  - op: deduplicate
    fields: [customer_id, month]
  - op: clip
    fields: [monthly_charges]
    min: 0
"""


def canvas_with_cleaning(block: str) -> str:
    text = valid_canvas()
    start = text.index("cleaning:")
    end = text.index("preprocessing:", start)
    return text[:start] + block.rstrip("\n") + "\n" + text[end:]


def test_fitted_op_in_cleaning_is_an_error():
    text = canvas_with_cleaning("cleaning:\n  - op: impute_median\n    fields: [monthly_charges]\n")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[0]"
        and "preprocessing" in f.message
        for f in findings
    )


def test_cleaning_op_must_not_declare_fit_on():
    text = canvas_with_cleaning(
        "cleaning:\n  - op: deduplicate\n    fields: [customer_id, month]\n    fit_on: train\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[0]"
        and "fit_on" in f.message
        for f in findings
    )


def test_deduplicate_in_preprocessing_is_an_error():
    text = valid_canvas().replace(
        "preprocessing:\n",
        "preprocessing:\n  - op: deduplicate\n    fields: [customer_id, month]\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "preprocessing[0]"
        and "cleaning" in f.message
        for f in findings
    )


def test_unknown_cleaning_op_is_a_warning():
    text = canvas_with_cleaning("cleaning:\n  - op: frobnicate\n    fields: [monthly_charges]\n")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure" and f.path == "cleaning[0].op" and f.severity == "warning"
        for f in findings
    )


def test_cleaning_fields_must_be_declared_in_entities():
    text = canvas_with_cleaning(
        "cleaning:\n  - op: deduplicate\n    fields: [customer_id, month_id]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[0].fields"
        and "month_id" in f.message
        for f in findings
    )


def test_target_must_not_appear_in_cleaning():
    text = canvas_with_cleaning(
        "cleaning:\n  - op: clip\n    fields: [churned_next_30d]\n    min: 0\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[0].fields"
        and "leakage" in f.message
        for f in findings
    )


def test_clip_requires_bounds():
    text = canvas_with_cleaning("cleaning:\n  - op: clip\n    fields: [monthly_charges]\n")
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[0]"
        and "min or max" in f.message
        for f in findings
    )


def test_clip_min_must_not_exceed_max():
    text = canvas_with_cleaning(
        "cleaning:\n  - op: clip\n    fields: [monthly_charges]\n    min: 10\n    max: 5\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.severity == "error"
        and f.path == "cleaning[0]"
        and "min" in f.message
        and "max" in f.message
        for f in findings
    )
