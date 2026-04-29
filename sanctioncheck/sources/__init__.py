"""Sanctions list source parsers."""
from sanctioncheck.sources.base import SanctionSource, SourceUnavailable
from sanctioncheck.sources.dgt import DGTSource
from sanctioncheck.sources.eu import EUSource
from sanctioncheck.sources.ofac import OFACSource
from sanctioncheck.sources.un import UNSource

ALL: dict[str, type[SanctionSource]] = {
    "EU": EUSource,
    "UN": UNSource,
    "OFAC": OFACSource,
    "DGT": DGTSource,
}

__all__ = [
    "ALL",
    "DGTSource",
    "EUSource",
    "OFACSource",
    "SanctionSource",
    "SourceUnavailable",
    "UNSource",
]
