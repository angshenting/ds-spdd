from canvas_factory import valid_canvas
from ds_canvas import parse

SECTION_KEYS = [
    "requirements",
    "entities",
    "approach",
    "structure",
    "operations",
    "norms",
    "safeguards",
]


def test_parse_extracts_canvas_name_from_frontmatter():
    canvas = parse(valid_canvas())
    assert canvas.name == "churn-prediction"


def test_parse_extracts_all_seven_reasons_sections():
    canvas = parse(valid_canvas())
    assert set(canvas.sections) == set(SECTION_KEYS)


def test_parse_attaches_yaml_block_of_section_as_data():
    canvas = parse(valid_canvas())
    data = canvas.sections["approach"].data
    assert data is not None
    assert data["task"] == "binary_classification"


def test_parse_extracts_optional_results_section():
    from canvas_factory import valid_canvas_with_results

    canvas = parse(valid_canvas_with_results())
    data = canvas.sections["results"].data
    assert data is not None
    assert data["results"][0]["metric"] == "recall_at_30"
