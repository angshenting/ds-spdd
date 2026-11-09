import re

import yaml

from ds_canvas.model import Canvas, Section

SECTION_TITLES = {
    "requirements": "Requirements",
    "entities": "Entities",
    "approach": "Approach",
    "structure": "Structure",
    "operations": "Operations",
    "norms": "Norms",
    "safeguards": "Safeguards",
    "results": "Results",
}

_HEADING = re.compile(r"^## (?:[A-Z] — )?(.+)$", re.MULTILINE)


def _frontmatter(markdown: str) -> dict:
    if not markdown.startswith("---"):
        return {}
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}
    loaded = yaml.safe_load(parts[1])
    return loaded if isinstance(loaded, dict) else {}


def _section_key(title: str) -> str | None:
    lowered = title.lower()
    for key, keyword in SECTION_TITLES.items():
        if keyword.lower() in lowered:
            return key
    return None


def _strip_frontmatter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return markdown
    return parts[2]


def _yaml_blocks(markdown: str) -> list[dict]:
    blocks = re.findall(r"```yaml\n(.*?)```", markdown, re.DOTALL)
    loaded = [yaml.safe_load(block) for block in blocks]
    return [block for block in loaded if isinstance(block, dict)]


def _merge_yaml_blocks(markdown: str) -> dict | None:
    blocks = _yaml_blocks(markdown)
    if not blocks:
        return None
    data: dict = {}
    for block in blocks:
        data.update(block)
    return data


def _sections(markdown: str) -> dict[str, Section]:
    sections: dict[str, Section] = {}
    matches = list(_HEADING.finditer(markdown))
    for i, match in enumerate(matches):
        key = _section_key(match.group(1))
        if key is None:
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        content = markdown[start:end].strip()
        sections[key] = Section(markdown=content, data=_merge_yaml_blocks(content))
    return sections


def parse(markdown: str) -> Canvas:
    frontmatter = _frontmatter(markdown)
    body = _strip_frontmatter(markdown)
    return Canvas(
        name=frontmatter.get("name"),
        frontmatter=frontmatter,
        sections=_sections(body),
    )
