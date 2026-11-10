import pytest
from canvas_factory import valid_canvas
from ds_canvas import parse, validate

QUALITY_RULES = """\
    quality_rules:
      - rule: unique
        fields: [customer_id, month]
      - rule: non_negative
        fields: [monthly_charges]
      - rule: missing_at_most
        fields: [monthly_charges]
        max: 0.05
      - rule: allowed_values
        fields: [plan_type]
        values: [basic, standard, premium]
"""


def canvas_with_quality_rules(block: str) -> str:
    text = valid_canvas()
    start = text.index("    quality_rules:")
    end = text.index("\n```", start)
    return text[:start] + block.rstrip("\n") + text[end:]


def test_string_quality_rule_entry_is_an_error():
    text = canvas_with_quality_rules("    quality_rules:\n      - monthly_charges >= 0\n")
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "quality_rules" in f.path
        and "mapping" in f.message
        for f in findings
    )


def test_unknown_quality_rule_is_an_error():
    text = canvas_with_quality_rules(
        "    quality_rules:\n      - rule: be_nice\n        fields: [monthly_charges]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "quality_rules" in f.path
        and "be_nice" in f.message
        for f in findings
    )


def test_quality_rule_fields_must_be_declared_in_the_dataset():
    text = canvas_with_quality_rules(
        "    quality_rules:\n      - rule: non_negative\n        fields: [monthly_fee]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "quality_rules" in f.path
        and "monthly_fee" in f.message
        and "subscriptions" in f.message
        for f in findings
    )


def test_missing_at_most_requires_max_ratio():
    text = canvas_with_quality_rules(
        "    quality_rules:\n      - rule: missing_at_most\n        fields: [monthly_charges]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "quality_rules" in f.path
        and "max" in f.message
        for f in findings
    )


def test_missing_at_most_max_must_be_a_ratio():
    text = canvas_with_quality_rules(
        "    quality_rules:\n"
        "      - rule: missing_at_most\n"
        "        fields: [monthly_charges]\n"
        "        max: 1.5\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "quality_rules" in f.path
        and "0 and 1" in f.message
        for f in findings
    )


RANGE_CASES = [
    # description, keys under the range rule, expected text in the message (None = no finding)
    ("min and max", "        min: 0\n        max: 500\n", None),
    ("max only", "        max: 500\n", None),
    ("no bound", "", "min or max"),
    ("non-numeric bound", "        min: low\n", "numbers"),
    ("min above max", "        min: 9\n        max: 1\n", "must not exceed"),
]


@pytest.mark.parametrize(("description", "keys", "expected"), RANGE_CASES)
def test_range_rule_bounds(description, keys, expected):
    text = canvas_with_quality_rules(
        "    quality_rules:\n      - rule: range\n        fields: [monthly_charges]\n" + keys
    )
    messages = [
        f.message
        for f in validate(parse(text))
        if f.dimension == "entities" and f.severity == "error" and "quality_rules" in f.path
    ]
    if expected is None:
        assert messages == [], description
    else:
        assert any(expected in m for m in messages), description


def test_allowed_values_requires_a_non_empty_list():
    text = canvas_with_quality_rules(
        "    quality_rules:\n      - rule: allowed_values\n        fields: [plan_type]\n"
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.severity == "error"
        and "quality_rules" in f.path
        and "values" in f.message
        for f in findings
    )
