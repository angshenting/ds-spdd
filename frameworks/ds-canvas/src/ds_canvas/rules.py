from ds_canvas.model import Canvas, Finding

LETTERS = {
    "requirements": "R",
    "entities": "E",
    "approach": "A",
    "structure": "S",
    "operations": "O",
    "norms": "N",
    "safeguards": "S",
}


def _missing_sections(canvas: Canvas) -> list[Finding]:
    return [
        Finding(
            severity="error",
            dimension=key,
            path="",
            message=f"canvas must contain section '{LETTERS[key]} — {key.capitalize()}'",
        )
        for key in LETTERS
        if key not in canvas.sections
    ]


def _frontmatter_name(canvas: Canvas) -> list[Finding]:
    if canvas.name:
        return []
    return [
        Finding(
            severity="error",
            dimension="frontmatter",
            path="name",
            message="frontmatter must declare a non-empty name",
        )
    ]


def _error(dimension: str, path: str, message: str) -> Finding:
    return Finding(severity="error", dimension=dimension, path=path, message=message)


def datasets_of(canvas: Canvas) -> list:
    section = canvas.sections.get("entities")
    if section is None or not isinstance(section.data, dict):
        return []
    datasets = section.data.get("datasets")
    return datasets if isinstance(datasets, list) else []


FIELD_TYPES = {"string", "integer", "float", "boolean", "datetime"}

TASKS = {"binary_classification", "multiclass_classification", "regression"}

SPLIT_METHODS = {"random", "stratified", "temporal", "grouped"}

SPLIT_RATIO_KEYS = ("train", "validation", "test")

METRIC_DIRECTIONS = {"maximize", "minimize"}

TARGET_OPS = {">=", ">", "<=", "<"}

MODEL_ROLES = {"baseline", "candidate"}

SEARCH_METHODS = {"grid", "random"}

CALIBRATION_METHODS = {"sigmoid", "isotonic"}

REQUIRED_SAFEGUARDS = (
    "target_excluded_from_features",
    "test_set_single_use",
    "split_before_fit",
)

FITTED_OPS = {
    "impute_mean",
    "impute_median",
    "impute_constant",
    "one_hot_encode",
    "target_encode",
    "scale_standard",
    "scale_minmax",
    "winsorize",
}

QUALITY_RULES = {"unique", "non_negative", "missing_at_most", "allowed_values"}

CLEANING_OPS = {"deduplicate", "coerce_type", "clip", "derive", "aggregate"}

DERIVE_FNS = {"product", "ratio", "log1p", "indicator"}

AGGREGATE_FNS = {"sum", "mean", "min", "max", "count"}


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _op_fields_findings(
    op_name: str, fields: object, path: str, known_fields: set[str]
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(fields, list) or not fields:
        findings.append(
            _error(
                "structure",
                f"{path}.fields",
                f"op '{op_name}' must list the fields it applies to",
            )
        )
        return findings
    unknown = [f for f in fields if f not in known_fields]
    if unknown:
        findings.append(
            _error(
                "structure",
                f"{path}.fields",
                f"fields {unknown} are not declared in E (entities)",
            )
        )
    return findings


def _output_findings(op_name: str, op: dict, path: str, known_fields: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    output = op.get("output")
    if not isinstance(output, str) or not output:
        findings.append(
            _error(
                "structure",
                f"{path}.output",
                f"{op_name} must declare the output field it creates",
            )
        )
    elif output not in known_fields:
        findings.append(
            _error(
                "structure",
                f"{path}.output",
                f"output field '{output}' is not declared in E (entities)",
            )
        )
    return findings


def _derive_findings(op: dict, path: str, known_fields: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    fn = op.get("fn")
    if fn not in DERIVE_FNS:
        findings.append(
            _error(
                "structure",
                f"{path}.fn",
                f"derive fn must be one of {sorted(DERIVE_FNS)}, got '{fn}'",
            )
        )
    findings += _output_findings("derive", op, path, known_fields)
    return findings


def _aggregate_findings(op: dict, path: str, known_fields: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    group_by = op.get("group_by")
    if not isinstance(group_by, list) or not group_by:
        findings.append(
            _error("structure", f"{path}.group_by", "aggregate must declare group_by fields")
        )
    else:
        unknown = [f for f in group_by if f not in known_fields]
        if unknown:
            findings.append(
                _error(
                    "structure",
                    f"{path}.group_by",
                    f"fields {unknown} are not declared in E (entities)",
                )
            )
    lookback = op.get("lookback")
    if not isinstance(lookback, int) or isinstance(lookback, bool) or lookback < 1:
        findings.append(
            _error(
                "structure",
                f"{path}.lookback",
                "aggregate lookback must be a positive integer (prior rows within the group)",
            )
        )
    fn = op.get("fn")
    if fn not in AGGREGATE_FNS:
        findings.append(
            _error(
                "structure",
                f"{path}.fn",
                f"aggregate fn must be one of {sorted(AGGREGATE_FNS)}, got '{fn}'",
            )
        )
    findings += _output_findings("aggregate", op, path, known_fields)
    return findings


def _cleaning_rules(canvas: Canvas) -> list[Finding]:
    findings: list[Finding] = []
    data = structure_data(canvas)
    ops = data.get("cleaning")
    if ops is None:
        return findings
    if not isinstance(ops, list):
        return [_error("structure", "cleaning", "cleaning must be a list of ops")]
    known_fields = declared_field_names(canvas)
    target = approach_data(canvas).get("target")
    for i, op in enumerate(ops):
        path = f"cleaning[{i}]"
        if not isinstance(op, dict) or not op.get("op"):
            findings.append(_error("structure", path, "cleaning step must declare an op"))
            continue
        op_name = op["op"]
        if op_name not in CLEANING_OPS:
            findings.append(
                _warning(
                    "structure",
                    f"{path}.op",
                    f"unknown cleaning op '{op_name}' (known: {sorted(CLEANING_OPS)})",
                )
            )
        if op_name in FITTED_OPS:
            findings.append(
                _error(
                    "structure",
                    path,
                    f"fitted op '{op_name}' belongs in preprocessing with fit_on: train",
                )
            )
        if "fit_on" in op:
            findings.append(
                _error(
                    "structure",
                    path,
                    "cleaning runs before the split and must not declare fit_on",
                )
            )
        fields = op.get("fields")
        findings += _op_fields_findings(op_name, fields, path, known_fields)
        if isinstance(fields, list) and target in fields:
            findings.append(
                _error(
                    "structure",
                    f"{path}.fields",
                    f"target '{target}' must not appear in cleaning (target leakage)",
                )
            )
        if op_name == "derive":
            findings += _derive_findings(op, path, known_fields)
        if op_name == "aggregate":
            findings += _aggregate_findings(op, path, known_fields)
        if op_name == "clip":
            lo = op.get("min")
            hi = op.get("max")
            if lo is None and hi is None:
                findings.append(_error("structure", path, "clip must declare min or max (or both)"))
            elif (lo is not None and not _is_number(lo)) or (hi is not None and not _is_number(hi)):
                findings.append(_error("structure", path, "clip bounds must be numbers"))
            elif lo is not None and hi is not None and lo > hi:
                findings.append(_error("structure", path, "clip min must not exceed max"))
    return findings


def structure_data(canvas: Canvas) -> dict:
    section = canvas.sections.get("structure")
    if section is None or not isinstance(section.data, dict):
        return {}
    return section.data


def _warning(dimension: str, path: str, message: str) -> Finding:
    return Finding(severity="warning", dimension=dimension, path=path, message=message)


def _preprocessing_rules(canvas: Canvas) -> list[Finding]:
    findings: list[Finding] = []
    data = structure_data(canvas)
    ops = data.get("preprocessing")
    if not isinstance(ops, list):
        if data:
            findings.append(
                _error("structure", "preprocessing", "pipeline must declare preprocessing steps")
            )
        return findings
    known_fields = declared_field_names(canvas)
    target = approach_data(canvas).get("target")
    for i, op in enumerate(ops):
        path = f"preprocessing[{i}]"
        if not isinstance(op, dict) or not op.get("op"):
            findings.append(_error("structure", path, "preprocessing step must declare an op"))
            continue
        op_name = op["op"]
        if op_name == "deduplicate":
            findings.append(
                _error(
                    "structure",
                    path,
                    "row-removing op 'deduplicate' must run before the split "
                    "(declare it under cleaning)",
                )
            )
        if op_name == "aggregate":
            findings.append(
                _error(
                    "structure",
                    path,
                    "aggregate windows need the full ordered history before the "
                    "split (declare it under cleaning)",
                )
            )
        if op_name not in FITTED_OPS and op_name not in {"drop", "passthrough", "derive"}:
            findings.append(
                _warning(
                    "structure",
                    f"{path}.op",
                    f"unknown preprocessing op '{op_name}' (known: "
                    f"{sorted(FITTED_OPS | {'drop', 'passthrough'})})",
                )
            )
        if op_name in FITTED_OPS and op.get("fit_on") != "train":
            findings.append(
                _error(
                    "structure",
                    path,
                    f"fitted op '{op_name}' must declare fit_on: train",
                )
            )
        fields = op.get("fields")
        findings += _op_fields_findings(op_name, fields, path, known_fields)
        if isinstance(fields, list) and target and op_name != "drop" and target in fields:
            findings.append(
                _error(
                    "structure",
                    f"{path}.fields",
                    f"target '{target}' must not appear in non-drop preprocessing (target leakage)",
                )
            )
        if op_name == "derive":
            findings += _derive_findings(op, path, known_fields)
    return findings


def approach_data(canvas: Canvas) -> dict:
    section = canvas.sections.get("approach")
    if section is None or not isinstance(section.data, dict):
        return {}
    return section.data


def declared_field_names(canvas: Canvas) -> set[str]:
    names: set[str] = set()
    for dataset in datasets_of(canvas):
        if isinstance(dataset, dict):
            for field in fields_of(dataset):
                if isinstance(field, dict):
                    name = field.get("name")
                    if isinstance(name, str):
                        names.add(name)
    return names


def _split_rules(split: object) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(split, dict):
        findings.append(_error("approach", "split", "split must be a mapping"))
        return findings
    method = split.get("method")
    if method not in SPLIT_METHODS:
        findings.append(
            _error(
                "approach",
                "split.method",
                f"split method must be one of {sorted(SPLIT_METHODS)}",
            )
        )
    if method in {"temporal", "grouped"} and not split.get("column"):
        findings.append(
            _error(
                "approach",
                "split.column",
                f"'{method}' split must declare the column to split on",
            )
        )
    ratios = split.get("ratios")
    if not isinstance(ratios, dict) or not ratios:
        findings.append(
            _error("approach", "split.ratios", "split must declare train/validation/test ratios")
        )
        return findings
    total = 0.0
    for key in SPLIT_RATIO_KEYS:
        value = ratios.get(key, 0)
        if not isinstance(value, int | float) or value <= 0:
            findings.append(
                _error(
                    "approach",
                    f"split.ratios.{key}",
                    f"split ratio '{key}' must be a positive number",
                )
            )
        elif key in ratios:
            total += value
    if ratios and abs(total - 1.0) > 1e-9:
        findings.append(
            _error(
                "approach",
                "split.ratios",
                f"split ratios must sum to 1.0 (got {round(total, 6)})",
            )
        )
    return findings


def requirements_data(canvas: Canvas) -> dict:
    section = canvas.sections.get("requirements")
    if section is None or not isinstance(section.data, dict):
        return {}
    return section.data


def _metric_rules(canvas: Canvas, data: dict) -> list[Finding]:
    findings: list[Finding] = []
    metrics = data.get("metrics")
    primary = metrics.get("primary") if isinstance(metrics, dict) else None
    if not isinstance(primary, dict):
        findings.append(
            _error("approach", "metrics.primary", "approach must declare metrics.primary")
        )
        return findings
    if primary.get("direction") not in METRIC_DIRECTIONS:
        findings.append(
            _error(
                "approach",
                "metrics.primary.direction",
                f"primary metric direction must be one of {sorted(METRIC_DIRECTIONS)}",
            )
        )
    name = primary.get("name")
    key_metrics = requirements_data(canvas).get("key_metrics")
    if name and (not isinstance(key_metrics, list) or name not in key_metrics):
        findings.append(
            _error(
                "approach",
                "metrics.primary",
                f"primary metric '{name}' must be listed in R key_metrics",
            )
        )
    target = primary.get("target")
    if isinstance(target, dict):
        if target.get("op") not in TARGET_OPS:
            findings.append(
                _error(
                    "approach",
                    "metrics.primary.target.op",
                    f"target op must be one of {sorted(TARGET_OPS)}",
                )
            )
        if not isinstance(target.get("value"), int | float):
            findings.append(
                _error(
                    "approach",
                    "metrics.primary.target.value",
                    "target value must be a number",
                )
            )
    return findings


def _search_rules(family: dict, path: str) -> list[Finding]:
    search = family.get("search")
    if search is None:
        return []
    spath = f"{path}.search"
    if not isinstance(search, dict):
        return [
            _error(
                "approach",
                spath,
                "search must be a mapping with method, budget and space",
            )
        ]
    findings: list[Finding] = []
    method = search.get("method")
    if method not in SEARCH_METHODS:
        findings.append(
            _error(
                "approach",
                f"{spath}.method",
                f"search method must be one of {sorted(SEARCH_METHODS)}, got '{method}'",
            )
        )
    budget = search.get("budget")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
        findings.append(
            _error(
                "approach",
                f"{spath}.budget",
                "search budget must be a positive integer (the declared trial cap)",
            )
        )
    space = search.get("space")
    if not isinstance(space, dict) or not space:
        findings.append(
            _error(
                "approach",
                f"{spath}.space",
                "search must declare a space mapping of parameter grids",
            )
        )
    else:
        for param, values in space.items():
            if not isinstance(values, list) or not values:
                findings.append(
                    _error(
                        "approach",
                        f"{spath}.space.{param}",
                        f"search space for '{param}' must be a non-empty list",
                    )
                )
    if (
        method == "grid"
        and isinstance(space, dict)
        and space
        and isinstance(budget, int)
        and not isinstance(budget, bool)
    ):
        combos = 1
        for values in space.values():
            if not isinstance(values, list):
                combos = 0
                break
            combos *= len(values)
        if combos and budget < combos:
            findings.append(
                _error(
                    "approach",
                    f"{spath}.budget",
                    f"grid search is exhaustive: budget {budget} is below the "
                    f"{combos} declared combinations (raise the budget or use "
                    "method: random)",
                )
            )
    return findings


def _calibration_rules(data: dict) -> list[Finding]:
    calibration = data.get("calibration")
    if calibration is None:
        return []
    if not isinstance(calibration, dict):
        return [
            _error(
                "approach",
                "calibration",
                "calibration must be a mapping with method and fit_on",
            )
        ]
    findings: list[Finding] = []
    method = calibration.get("method")
    if method not in CALIBRATION_METHODS:
        findings.append(
            _error(
                "approach",
                "calibration.method",
                f"calibration method must be one of {sorted(CALIBRATION_METHODS)}, got '{method}'",
            )
        )
    if calibration.get("fit_on") != "train":
        findings.append(
            _error(
                "approach",
                "calibration.fit_on",
                "calibration must declare fit_on: train (threshold semantics are "
                "contract; fitting calibration on test invalidates the round)",
            )
        )
    return findings


def _model_family_rules(data: dict) -> list[Finding]:
    findings: list[Finding] = []
    families = data.get("model_families")
    if not isinstance(families, list) or not families:
        return [
            _error(
                "approach",
                "model_families",
                "approach must declare at least one model family",
            )
        ]
    roles = {family.get("role") for family in families if isinstance(family, dict)}
    for expected in MODEL_ROLES:
        if expected not in roles:
            findings.append(
                _error(
                    "approach",
                    "model_families",
                    f"model families must include at least one with role '{expected}'",
                )
            )
    for i, family in enumerate(families):
        if isinstance(family, dict):
            findings += _search_rules(family, f"model_families[{i}]")
    return findings


def _approach_rules(canvas: Canvas) -> list[Finding]:
    findings: list[Finding] = []
    data = approach_data(canvas)
    if not data:
        return findings
    if data.get("task") not in TASKS:
        findings.append(_error("approach", "task", f"task must be one of {sorted(TASKS)}"))
    target = data.get("target")
    if target and target not in declared_field_names(canvas):
        findings.append(
            _error(
                "approach",
                "target",
                f"target '{target}' must be a field declared in E (entities)",
            )
        )
    findings += _split_rules(data.get("split"))
    findings += _metric_rules(canvas, data)
    findings += _model_family_rules(data)
    findings += _calibration_rules(data)
    findings += _preprocessing_rules(canvas)
    findings += _cleaning_rules(canvas)
    return findings


def fields_of(dataset: dict) -> list:
    fields = dataset.get("fields")
    return fields if isinstance(fields, list) else []


def _quality_rule_rules(dataset: dict, path: str, field_names: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    rules = dataset.get("quality_rules")
    if rules is None:
        return findings
    if not isinstance(rules, list):
        return [_error("entities", f"{path}.quality_rules", "quality_rules must be a list")]
    for i, rule in enumerate(rules):
        rule_path = f"{path}.quality_rules[{i}]"
        if not isinstance(rule, dict):
            findings.append(
                _error(
                    "entities",
                    rule_path,
                    "quality rule must be a mapping with rule and fields",
                )
            )
            continue
        name = rule.get("rule")
        if name not in QUALITY_RULES:
            findings.append(
                _error(
                    "entities",
                    f"{rule_path}.rule",
                    f"unknown quality rule '{name}' (known: {sorted(QUALITY_RULES)})",
                )
            )
            continue
        fields = rule.get("fields")
        if not isinstance(fields, list) or not fields:
            findings.append(
                _error(
                    "entities",
                    f"{rule_path}.fields",
                    f"quality rule '{name}' must list the fields it applies to",
                )
            )
            continue
        unknown = [f for f in fields if f not in field_names]
        if unknown:
            findings.append(
                _error(
                    "entities",
                    f"{rule_path}.fields",
                    f"fields {unknown} are not declared in dataset '{dataset.get('name')}'",
                )
            )
        if name == "missing_at_most":
            max_rate = rule.get("max")
            if (
                not isinstance(max_rate, int | float)
                or isinstance(max_rate, bool)
                or not (0 <= max_rate <= 1)
            ):
                findings.append(
                    _error(
                        "entities",
                        f"{rule_path}.max",
                        "missing_at_most must declare max as a ratio between 0 and 1",
                    )
                )
        if name == "allowed_values":
            values = rule.get("values")
            if not isinstance(values, list) or not values:
                findings.append(
                    _error(
                        "entities",
                        f"{rule_path}.values",
                        "allowed_values must declare a non-empty values list",
                    )
                )
    return findings


def _provenance_map(canvas: Canvas) -> dict[str, object]:
    provenance: dict[str, object] = {}
    for dataset in datasets_of(canvas):
        if not isinstance(dataset, dict):
            continue
        for field in fields_of(dataset):
            if (
                isinstance(field, dict)
                and isinstance(field.get("name"), str)
                and "derived_from" in field
            ):
                provenance[field["name"]] = field["derived_from"]
    return provenance


def _closure(start: str, provenance: dict[str, object]) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        refs = provenance.get(current)
        if isinstance(refs, list):
            stack.extend(refs)
    return seen


def _produced_fields(canvas: Canvas) -> set[str]:
    produced: set[str] = set()
    data = structure_data(canvas)
    for key in ("cleaning", "preprocessing"):
        ops = data.get(key)
        if not isinstance(ops, list):
            continue
        for op in ops:
            if isinstance(op, dict) and isinstance(op.get("output"), str):
                produced.add(op["output"])
    return produced


def _derived_field_rules(canvas: Canvas) -> list[Finding]:
    findings: list[Finding] = []
    provenance = _provenance_map(canvas)
    known_fields = declared_field_names(canvas)
    target = approach_data(canvas).get("target")
    produced = _produced_fields(canvas)
    for dataset in datasets_of(canvas):
        if not isinstance(dataset, dict):
            continue
        dataset_path = f"datasets[{dataset.get('name')}]"
        for field in fields_of(dataset):
            if not isinstance(field, dict) or "derived_from" not in field:
                continue
            name = field.get("name")
            if not isinstance(name, str):
                continue
            path = f"{dataset_path}.{name}"
            refs = field["derived_from"]
            if not isinstance(refs, list) or not refs:
                findings.append(
                    _error(
                        "entities",
                        f"{path}.derived_from",
                        f"field '{name}' must declare derived_from as a non-empty list",
                    )
                )
                continue
            unknown = [f for f in refs if f not in known_fields]
            if unknown:
                findings.append(
                    _error(
                        "entities",
                        f"{path}.derived_from",
                        f"fields {unknown} are not declared in E (entities)",
                    )
                )
                continue
            if target and name == target:
                findings.append(
                    _error(
                        "entities",
                        f"{path}.derived_from",
                        f"target field '{name}' must not declare derived_from",
                    )
                )
                continue
            if target and target in _closure(name, provenance):
                findings.append(
                    _error(
                        "entities",
                        path,
                        f"field '{name}' is derived (transitively) from the target "
                        f"'{target}' (target leakage)",
                    )
                )
            if name not in produced:
                findings.append(
                    _warning(
                        "entities",
                        path,
                        f"derived field '{name}' has no derive/aggregate op that produces it",
                    )
                )
    return findings


def _entities_rules(canvas: Canvas) -> list[Finding]:
    findings: list[Finding] = []
    datasets = datasets_of(canvas)
    if not datasets:
        findings.append(
            _error("entities", "datasets", "entities must declare at least one dataset")
        )
        return findings
    for i, dataset in enumerate(datasets):
        if not isinstance(dataset, dict):
            findings.append(_error("entities", f"datasets[{i}]", "dataset must be a mapping"))
            continue
        name = dataset.get("name")
        path = f"datasets[{name if name else i}]"
        fields = fields_of(dataset)
        if not fields:
            findings.append(
                _error(
                    "entities",
                    f"{path}.fields",
                    f"dataset '{name}' must declare at least one field",
                )
            )
            continue
        seen: set[str] = set()
        for field in fields:
            if not isinstance(field, dict):
                findings.append(
                    _error("entities", path, "field must be a mapping with name and type")
                )
                continue
            field_name = field.get("name")
            if isinstance(field_name, str) and field_name in seen:
                findings.append(
                    _error(
                        "entities",
                        f"{path}.fields",
                        f"duplicate field name '{field_name}' in dataset '{name}'",
                    )
                )
            if isinstance(field_name, str):
                seen.add(field_name)
            if field.get("type") not in FIELD_TYPES:
                findings.append(
                    _error(
                        "entities",
                        f"{path}.{field_name}.type",
                        f"field '{field_name}' must have a type in {sorted(FIELD_TYPES)}",
                    )
                )
        findings += _quality_rule_rules(dataset, path, seen)
    findings += _derived_field_rules(canvas)
    return findings


def _norms_rules(canvas: Canvas) -> list[Finding]:
    section = canvas.sections.get("norms")
    if section is None:
        return []
    data = section.data if isinstance(section.data, dict) else {}
    findings: list[Finding] = []
    seed = data.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        findings.append(
            _error("norms", "seed", "norms must declare seed as a non-negative integer")
        )
    return findings


def _safeguards_rules(canvas: Canvas) -> list[Finding]:
    section = canvas.sections.get("safeguards")
    if section is None:
        return []
    data = section.data if isinstance(section.data, dict) else {}
    findings: list[Finding] = []
    for flag in REQUIRED_SAFEGUARDS:
        if data.get(flag) is not True:
            findings.append(_error("safeguards", flag, f"safeguard '{flag}' must be declared true"))
    known_fields = declared_field_names(canvas)
    pii = data.get("pii_fields", [])
    if not isinstance(pii, list):
        findings.append(_error("safeguards", "pii_fields", "pii_fields must be a list"))
    else:
        unknown = [f for f in pii if f not in known_fields]
        if unknown:
            findings.append(
                _error(
                    "safeguards",
                    "pii_fields",
                    f"fields {unknown} are not declared in E (entities)",
                )
            )
    return findings


def declared_metrics(canvas: Canvas) -> dict[str, dict]:
    metrics = approach_data(canvas).get("metrics")
    if not isinstance(metrics, dict):
        return {}
    declared: dict[str, dict] = {}
    primary = metrics.get("primary")
    if isinstance(primary, dict) and primary.get("name"):
        declared[primary["name"]] = primary
    guardrails = metrics.get("guardrails")
    if isinstance(guardrails, list):
        for guardrail in guardrails:
            if isinstance(guardrail, dict) and isinstance(guardrail.get("name"), str):
                declared[guardrail["name"]] = guardrail
    return declared


def _target_met(achieved: float, target: dict) -> bool:
    value = target.get("value")
    op = target.get("op")
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    if not isinstance(op, str):
        return False
    return {
        ">=": achieved >= value,
        ">": achieved > value,
        "<=": achieved <= value,
        "<": achieved < value,
    }.get(op, False)


def _results_rules(canvas: Canvas) -> list[Finding]:
    section = canvas.sections.get("results")
    if section is None:
        return []
    data = section.data if isinstance(section.data, dict) else {}
    findings: list[Finding] = []
    results = data.get("results")
    if not isinstance(results, list) or not results:
        return [_error("results", "results", "Results section must declare results entries")]
    declared = declared_metrics(canvas)
    for i, result in enumerate(results):
        if not isinstance(result, dict):
            findings.append(_error("results", f"results[{i}]", "result must be a mapping"))
            continue
        name = result.get("metric")
        spec = declared.get(name) if isinstance(name, str) else None
        if spec is None:
            findings.append(
                _error(
                    "results",
                    f"results[{i}].metric",
                    f"metric '{name}' is not declared in A (metrics)",
                )
            )
            continue
        achieved = result.get("achieved")
        if not isinstance(achieved, int | float) or isinstance(achieved, bool):
            findings.append(
                _error(
                    "results",
                    f"results[{i}].achieved",
                    "achieved must be a number",
                )
            )
            continue
        target = spec.get("target")
        if isinstance(target, dict) and not _target_met(achieved, target):
            findings.append(
                _error(
                    "results",
                    f"results[{i}].achieved",
                    f"achieved {achieved} does not meet target "
                    f"'{target.get('op')} {target.get('value')}' for '{name}'",
                )
            )
    metrics = approach_data(canvas).get("metrics")
    primary = metrics.get("primary", {}).get("name") if isinstance(metrics, dict) else None
    reported = {result.get("metric") for result in results if isinstance(result, dict)}
    if primary and primary not in reported:
        findings.append(
            _error(
                "results",
                "results",
                f"results must include the primary metric '{primary}'",
            )
        )
    return findings


def validate(canvas: Canvas) -> list[Finding]:
    findings = _missing_sections(canvas) + _frontmatter_name(canvas)
    if "entities" in canvas.sections:
        findings += _entities_rules(canvas)
    if "approach" in canvas.sections:
        findings += _approach_rules(canvas)
    findings += _norms_rules(canvas)
    findings += _safeguards_rules(canvas)
    findings += _results_rules(canvas)
    return findings
