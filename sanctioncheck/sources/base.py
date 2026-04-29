"""Abstract base class for sanctions list sources."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from sanctioncheck.config import DEFAULT_TIMEOUT
from sanctioncheck.models import SanctionEntry

logger = logging.getLogger(__name__)


class SourceUnavailable(Exception):
    """Raised when a remote source cannot be reached and no fallback exists."""


class SanctionSource(ABC):
    """Abstract sanctions list parser."""

    name: str = ""
    url: str = ""

    async def fetch_raw(self) -> bytes:
        """Download the raw bytes of the list. Override for custom logic."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.content

    @abstractmethod
    def parse(self, raw: bytes) -> list[SanctionEntry]:
        """Parse the raw bytes into a list of SanctionEntry."""

    async def fetch_and_parse(self) -> list[SanctionEntry]:
        """Fetch the source and return parsed entries."""
        raw = await self.fetch_raw()
        return self.parse(raw)
