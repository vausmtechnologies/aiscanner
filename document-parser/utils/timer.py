"""Timing helpers for processing metrics."""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


@contextmanager
def elapsed_timer() -> Iterator[callable[[], int]]:
	"""Yield a callback that returns elapsed milliseconds."""
	start = perf_counter()

	def elapsed_ms() -> int:
		return int((perf_counter() - start) * 1000)

	yield elapsed_ms
