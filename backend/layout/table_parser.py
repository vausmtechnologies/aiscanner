"""Normalise raw table data from pdfplumber into flat key-value dicts.

Tables from pdfplumber come back as list[list[str | None]].
This module converts them into flat {key: value} dicts and merges
multiple tables from the same document into a single mapping.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Regex to collapse runs of whitespace / newlines inside a cell value
_WHITESPACE = re.compile(r'\s+')


def _clean_cell(cell: str | None) -> str:
    """Strip and normalise whitespace in a single table cell."""
    if not cell:
        return ""
    return _WHITESPACE.sub(" ", str(cell)).strip()


def parse_table_rows(table: list[list[str | None]]) -> dict[str, str]:
    """Convert a single table (list of rows) into a {key: value} dict.

    Rules:
    - Skip rows with fewer than 2 cells.
    - Use the first non-empty cell as the key, second as value.
    - Keys are lower-cased for case-insensitive downstream mapping.
    - Rows where key or value is blank after cleaning are skipped.
    - For rows with more than 2 cells, all remaining cells are appended
      to the value separated by a space (handles merged-header tables).
    """
    parsed: dict[str, str] = {}

    for row in table:
        cells = [_clean_cell(c) for c in row]
        # Find first non-empty cell index as key position
        key_idx = next((i for i, c in enumerate(cells) if c), None)
        if key_idx is None:
            continue
        # Value is everything after the key cell, joined
        value_parts = [c for c in cells[key_idx + 1:] if c]
        if not value_parts:
            continue
        key = cells[key_idx].lower()
        value = " ".join(value_parts)
        parsed[key] = value

    return parsed


def merge_tables(parsed_tables: list[dict[str, str]]) -> dict[str, str]:
    """Merge multiple parsed table dicts into a single mapping.

    Later tables win on key conflicts (tables near the top of the document
    are typically more authoritative, so callers should pass them first).
    """
    merged: dict[str, str] = {}
    for table in parsed_tables:
        merged.update(table)
    return merged
