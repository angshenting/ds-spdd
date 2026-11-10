import pytest
from canvas_factory import valid_canvas
from ds_canvas import parse, validate

GROUPS = "    field_groups:\n      charges: [monthly_charges, charge_log]\n"
QUALITY_ANCHOR = "    quality_rules:\n"
NON_NEGATIVE = "      - rule: non_negative\n        fields: [monthly_charges]\n"
IMPUTE = "  - op: impute_median\n    fields: [monthly_charges]\n"


def canvas_with_groups(groups: str = GROUPS) -> str:
    return valid_canvas().replace(QUALITY_ANCHOR, groups + QUALITY_ANCHOR, 1)


def referencing(text: str, anchor: str, group: str) -> str:
    return text.replace(anchor, anchor.replace("[monthly_charges]", f"[{group}]"), 1)


CASES = [
    # description, canvas text, expected text in an error message (None = no errors)
    ("group declared and unused", canvas_with_groups(), None),
    (
        "group referenced in a quality rule",
        referencing(canvas_with_groups(), NON_NEGATIVE, "charges"),
        None,
    ),
    (
        "group referenced in a preprocessing op",
        referencing(canvas_with_groups(), IMPUTE, "charges"),
        None,
    ),
    (
        "group expands to its members, so the target inside it is still leakage",
        referencing(
            canvas_with_groups(
                "    field_groups:\n      charges: [monthly_charges, churned_next_30d]\n"
            ),
            IMPUTE,
            "charges",
        ),
        "leakage",
    ),
    (
        "reference to an undeclared group",
        referencing(canvas_with_groups(), IMPUTE, "chargs"),
        "chargs",
    ),
    (
        "group member not declared in the dataset",
        canvas_with_groups("    field_groups:\n      charges: [monthly_fee]\n"),
        "monthly_fee",
    ),
    (
        "group that is not a non-empty list",
        canvas_with_groups("    field_groups:\n      charges: []\n"),
        "non-empty list",
    ),
    (
        "group named like a field",
        canvas_with_groups("    field_groups:\n      plan_type: [monthly_charges]\n"),
        "same name as a field",
    ),
]


@pytest.mark.parametrize(
    ("description", "text", "expected"), CASES, ids=[case[0] for case in CASES]
)
def test_field_groups(description, text, expected):
    messages = [f.message for f in validate(parse(text)) if f.severity == "error"]
    if expected is None:
        assert messages == [], description
    else:
        assert any(expected in m for m in messages), description
