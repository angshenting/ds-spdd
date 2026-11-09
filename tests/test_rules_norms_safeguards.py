from canvas_factory import valid_canvas
from ds_canvas import parse, validate


def test_seed_must_be_a_non_negative_integer():
    text = valid_canvas().replace("seed: 42", "seed: tomorrow")
    findings = validate(parse(text))
    assert any(
        f.dimension == "norms" and f.path == "seed" and f.severity == "error" for f in findings
    )


def test_safeguard_flags_must_be_true():
    text = valid_canvas().replace("split_before_fit: true", "split_before_fit: false")
    findings = validate(parse(text))
    assert any(
        f.dimension == "safeguards" and f.path == "split_before_fit" and f.severity == "error"
        for f in findings
    )


def test_pii_fields_must_be_declared_in_entities():
    text = valid_canvas().replace("pii_fields: []", "pii_fields: [email]")
    findings = validate(parse(text))
    assert any(
        f.dimension == "safeguards"
        and f.path == "pii_fields"
        and f.severity == "error"
        and "email" in f.message
        for f in findings
    )
