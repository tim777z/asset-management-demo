"""Input validation helpers shared by the CSV loader and the CLI.

Centralising validation keeps the trust boundary in one place: every value that
enters the library from an untrusted source (a CSV file or command-line
argument) is checked here before it reaches the analytics code.
"""

from __future__ import annotations

import math
import re

#: Maximum accepted length of an asset symbol.
MAX_SYMBOL_LENGTH = 32

#: Upper bound on the number of data rows read from a single CSV file. This
#: caps memory use so a malformed or hostile file cannot exhaust the process.
MAX_CSV_ROWS = 100_000

# Symbols are short, human-readable tickers such as ``AAPL`` or ``BTC-USD``.
# The first character must be alphanumeric, which also rejects spreadsheet
# formula-injection prefixes (``=``, ``+``, ``-``, ``@``) that could be
# dangerous if the data is later exported to CSV and opened in Excel.
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def is_valid_symbol(symbol: str) -> bool:
    """Return ``True`` if *symbol* is a well-formed ticker."""
    if not symbol or len(symbol) > MAX_SYMBOL_LENGTH:
        return False
    return _SYMBOL_RE.match(symbol) is not None


def parse_non_negative_float(value: str, field: str) -> float:
    """Parse *value* as a finite, non-negative float.

    Raises :class:`ValueError` with a message naming *field* when the value is
    not numeric, is not finite (``nan``/``inf``), or is negative.
    """
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"Invalid numeric value for {field}: {value!r} is not finite")
    if number < 0:
        raise ValueError(f"{field} cannot be negative")
    return number
