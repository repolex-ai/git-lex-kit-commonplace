"""Where bookmarks come from.

A source is one module with a `NAME` and a `fetch_items() -> list[Item]` function. To add a
source (Pocket, Raindrop, a browser export…), add a module here and register it in SOURCES.
Nothing in the ontology changes: `source` is a plain string.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Item:
    url: str
    source: str
    source_id: str = ""
    title: str = ""
    saved: datetime | None = None
    note: str = ""  # what the person wrote when they saved it
    details: list[str] = field(default_factory=list)  # lines for the "From the source" section


def get(name: str):
    from . import pinboard, x

    sources = {pinboard.NAME: pinboard, x.NAME: x}
    if name not in sources:
        raise SystemExit(f"Unknown source '{name}'. Known: {', '.join(sorted(sources))}.")
    return sources[name]
