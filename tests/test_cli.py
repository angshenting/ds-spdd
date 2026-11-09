from canvas_factory import valid_canvas


def write(tmp_path, text, name="canvas.md"):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def test_validate_clean_canvas_exits_zero(tmp_path, capsys):
    from ds_canvas.cli import main

    path = write(tmp_path, valid_canvas())
    assert main(["validate", path]) == 0
    assert "valid" in capsys.readouterr().out.lower()


def test_validate_canvas_with_errors_exits_one(tmp_path, capsys):
    from ds_canvas.cli import main

    path = write(tmp_path, valid_canvas().replace("seed: 42", "seed: nope"))
    assert main(["validate", path]) == 1
    out = capsys.readouterr().out
    assert "error" in out
    assert "seed" in out


def test_init_writes_canvas_scaffold(tmp_path):
    from ds_canvas.cli import main

    path = tmp_path / "canvas.md"
    assert main(["init", str(path)]) == 0
    text = path.read_text()
    assert "## R — Requirements" in text
    assert "## S — Safeguards" in text


def test_init_scaffold_reports_missing_contract_parts_until_filled(tmp_path):
    from ds_canvas.cli import main

    path = tmp_path / "canvas.md"
    main(["init", str(path)])
    assert main(["validate", str(path)]) == 1


def test_init_refuses_to_overwrite(tmp_path):
    from ds_canvas.cli import main

    path = tmp_path / "canvas.md"
    main(["init", str(path)])
    assert main(["init", str(path)]) == 1
