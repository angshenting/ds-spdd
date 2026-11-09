from canvas_factory import valid_canvas
from ds_canvas import parse, validate

SEARCH_BLOCK = """\
    search:
      method: grid
      budget: 4
      space:
        learning_rate: [0.05, 0.1]
        max_leaf_nodes: [31, 63]
"""

CALIBRATION_BLOCK = """\
calibration:
  method: sigmoid
  fit_on: train
"""


def canvas_with_search(block: str) -> str:
    text = valid_canvas()
    assert SEARCH_BLOCK in text
    return text.replace(SEARCH_BLOCK, block)


def canvas_with_calibration(block: str) -> str:
    text = valid_canvas()
    assert CALIBRATION_BLOCK in text
    return text.replace(CALIBRATION_BLOCK, block)


def test_search_method_must_be_known():
    findings = validate(
        parse(
            canvas_with_search(
                "    search:\n      method: vibes\n      budget: 4\n      space:\n        learning_rate: [0.05, 0.1]\n"
            )
        )
    )
    assert any(
        f.dimension == "approach"
        and f.severity == "error"
        and f.path == "model_families[1].search.method"
        and "vibes" in f.message
        for f in findings
    )


def test_search_budget_must_be_a_positive_integer():
    findings = validate(
        parse(
            canvas_with_search(
                "    search:\n      method: grid\n      budget: 0\n      space:\n        learning_rate: [0.05, 0.1]\n"
            )
        )
    )
    assert any(
        f.dimension == "approach"
        and f.severity == "error"
        and f.path == "model_families[1].search.budget"
        for f in findings
    )


def test_grid_budget_must_cover_the_declared_space():
    findings = validate(
        parse(
            canvas_with_search(
                "    search:\n      method: grid\n      budget: 2\n      space:\n        learning_rate: [0.05, 0.1]\n        max_leaf_nodes: [31, 63]\n"
            )
        )
    )
    assert any(
        f.dimension == "approach"
        and f.severity == "error"
        and f.path == "model_families[1].search.budget"
        and "grid" in f.message
        and "4" in f.message
        for f in findings
    )


def test_search_space_must_be_non_empty_lists():
    findings = validate(
        parse(
            canvas_with_search(
                "    search:\n      method: grid\n      budget: 1\n      space:\n        learning_rate: 0.1\n"
            )
        )
    )
    assert any(
        f.dimension == "approach"
        and f.severity == "error"
        and f.path == "model_families[1].search.space.learning_rate"
        for f in findings
    )


def test_search_requires_a_space():
    findings = validate(
        parse(canvas_with_search("    search:\n      method: random\n      budget: 10\n"))
    )
    assert any(
        f.dimension == "approach"
        and f.severity == "error"
        and f.path == "model_families[1].search.space"
        for f in findings
    )


def test_calibration_method_must_be_known():
    findings = validate(
        parse(canvas_with_calibration("calibration:\n  method: vibes\n  fit_on: train\n"))
    )
    assert any(
        f.dimension == "approach"
        and f.severity == "error"
        and f.path == "calibration.method"
        and "vibes" in f.message
        for f in findings
    )


def test_calibration_must_fit_on_train():
    findings = validate(
        parse(canvas_with_calibration("calibration:\n  method: sigmoid\n  fit_on: all\n"))
    )
    assert any(
        f.dimension == "approach" and f.severity == "error" and f.path == "calibration.fit_on"
        for f in findings
    )
