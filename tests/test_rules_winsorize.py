from canvas_factory import valid_canvas
from ds_canvas import parse, validate


def test_winsorize_without_fit_on_is_an_error():
    text = valid_canvas().replace(
        "  - op: impute_median\n    fields: [monthly_charges]\n    fit_on: train\n",
        "  - op: winsorize\n    fields: [monthly_charges]\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "structure"
        and f.path == "preprocessing[0]"
        and f.severity == "error"
        and "fit_on: train" in f.message
        for f in findings
    )


def test_winsorize_with_fit_on_train_is_recognized():
    text = valid_canvas().replace("op: impute_median", "op: winsorize")
    findings = validate(parse(text))
    assert not any(f.severity == "warning" and "winsorize" in f.message for f in findings)
