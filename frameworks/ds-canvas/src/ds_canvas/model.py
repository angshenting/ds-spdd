from dataclasses import dataclass, field
from typing import Any


@dataclass
class Section:
    markdown: str
    data: dict | None = None


@dataclass
class Canvas:
    name: str | None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, Section] = field(default_factory=dict)


@dataclass
class Finding:
    severity: str
    dimension: str
    path: str
    message: str
