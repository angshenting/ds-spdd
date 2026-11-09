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
