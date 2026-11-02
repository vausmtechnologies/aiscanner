"""Category-agnostic metadata: picks up "Label: value" lines from any document."""

from __future__ import annotations

import re

MAX_FIELDS = 15
_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /&.'()-]{1,40}?)\s*:\s*(\S.{0,119}?)\s*$")


def extract_generic_metadata(text: str) -> dict[str, str | None]:
    """Return {snake_case_label: value} for the first labelled lines in the text."""
    fields: dict[str, str | None] = {}
    for line in text.splitlines():
        match = _LINE.match(line)
        if not match:
            continue
        key = re.sub(r"[^a-z0-9]+", "_", match.group(1).lower()).strip("_")
        if key and key not in fields:
            fields[key] = match.group(2)
        if len(fields) >= MAX_FIELDS:
            break
    return fields
