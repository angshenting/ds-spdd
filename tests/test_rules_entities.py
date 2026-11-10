import pytest
from canvas_factory import valid_canvas, with_section_yaml
from ds_canvas import parse, validate


def test_empty_datasets_list_is_reported():
    text = with_section_yaml(valid_canvas(), "## E — Entities (Data Definitions)", "datasets: []")
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities" and f.path == "datasets" and f.severity == "error"
        for f in findings
    )


def test_dataset_without_fields_is_reported():
    text = with_section_yaml(
        valid_canvas(),
        "## E — Entities (Data Definitions)",
        "datasets:\n  - name: subscriptions\n    source: data/raw/subscriptions.csv",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.path == "datasets[subscriptions].fields"
        and f.severity == "error"
        for f in findings
    )


def test_unknown_field_type_is_reported():
    text = valid_canvas().replace("type: float", "type: numeric")
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.path == "datasets[subscriptions].monthly_charges.type"
        and f.severity == "error"
        for f in findings
    )


PLAN_TYPE = "      - name: plan_type\n        type: string\n"

ROLE_CASES = [
    # description, role given to plan_type, expected path, expected text in the message
    ("unknown role", "banana", "datasets[subscriptions].plan_type.role", "feature"),
    (
        "role target on a field that is not A's target",
        "target",
        "datasets[subscriptions].plan_type.role",
        "churned_next_30d",
    ),
]


@pytest.mark.parametrize(("description", "role", "path", "expected"), ROLE_CASES)
def test_field_role_is_checked(description, role, path, expected):
    text = valid_canvas().replace(PLAN_TYPE, PLAN_TYPE + f"        role: {role}\n", 1)
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.path == path
        and f.severity == "error"
        and expected in f.message
        for f in findings
    ), description


def test_duplicate_field_name_is_reported():
    text = valid_canvas().replace(
        "      - name: monthly_charges\n        type: float\n        unit: USD\n",
        "      - name: monthly_charges\n        type: float\n        unit: USD\n"
        "      - name: monthly_charges\n        type: float\n",
    )
    findings = validate(parse(text))
    assert any(
        f.dimension == "entities"
        and f.path == "datasets[subscriptions].fields"
        and f.severity == "error"
        for f in findings
    )
