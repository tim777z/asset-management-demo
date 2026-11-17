"""Input validation helpers shared by the CSV loader and the CLI.

Centralising validation keeps the trust boundary in one place: every value that
enters the library from an untrusted source (a CSV file or command-line
argument) is checked here before it reaches the analytics code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

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


@dataclass
class CsvRowSchema:
    """Validated schema for a single CSV row in portfolio data.

    Enforces explicit field types and bounds at the trust boundary, replacing
    ad-hoc manual checks in ``portfolio.py``'s ``from_csv`` with a single,
    centrally maintained validation contract.
    """

    symbol: str
    shares: float
    avg_cost: float
    current_price: float = field(default=0.0, repr=False)
    asset_class: str = "equity"

    def __post_init__(self) -> None:
        if not is_valid_symbol(self.symbol):
            raise ValueError(
                f"Invalid symbol {self.symbol!r}: expected 1-{MAX_SYMBOL_LENGTH} "
                "alphanumeric characters ('.', '_' and '-' allowed after "
                "the first)"
            )
        if self.shares < 0:
            raise ValueError("shares cannot be negative")
        if self.avg_cost < 0:
            raise ValueError("avg_cost cannot be negative")
        if self.current_price < 0:
            raise ValueError("current_price cannot be negative")


def is_valid_symbol(symbol: str) -> bool:
    """Return ``True`` if *symbol* is a well-formed ticker."""
    if not symbol or len(symbol) > MAX_SYMBOL_LENGTH:
        return False
    return _SYMBOL_RE.match(symbol) is not None


def parse_decimal(value: str, field: str) -> float:
    """Parse *value* as a finite decimal float, raising on ``nan``/``inf``/non-numeric.

    Uses :class:`decimal.Decimal` for exact arithmetic; converts to ``float``
    at the end so the rest of the codebase is unaffected.
    """
    try:
        d = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if not d.is_finite():
        raise ValueError(f"Invalid numeric value for {field}: {value!r} is not finite")
    if d < 0:
        raise ValueError(f"{field} cannot be negative")
    return float(d)


def parse_non_negative_float(value: str, field: str) -> float:
    """Parse *value* as a finite, non-negative float.

    Raises :class:`ValueError` with a message naming *field* when the value is
    not numeric, is not finite (``nan``/``inf``), or is negative.

    .. deprecated: Use :func:`parse_decimal` for exact decimal arithmetic.
    """
    return parse_decimal(value, field)
