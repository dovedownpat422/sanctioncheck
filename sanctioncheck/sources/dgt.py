"""DGT (Direction Générale du Trésor, France) sanctions list parser.

The DGT public API at gels-avoirs.dgtresor.gouv.fr is intermittently unreachable;
when the network call fails, we transparently fall back to a bundled JSON file.
"""
from __future__ import annotations

import json
import logging

import httpx

from sanctioncheck.config import DEFAULT_TIMEOUT, PACKAGE_DATA_DIR, SOURCE_URLS
from sanctioncheck.models import SanctionEntry
from sanctioncheck.sources.base import SanctionSource

logger = logging.getLogger(__name__)

FALLBACK_PATH = PACKAGE_DATA_DIR / "dgt_fallback.json"


class DGTSource(SanctionSource):
    name = "DGT"
    url = SOURCE_URLS["DGT"]

    async def fetch_raw(self) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                return response.content
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("DGT API unreachable (%s) - using local fallback file", exc)
            return FALLBACK_PATH.read_bytes()

    def parse(self, raw: bytes) -> list[SanctionEntry]:
        data = json.loads(raw.decode("utf-8", errors="replace"))
        publications = data.get("Publications") or {}
        details = publications.get("PublicationDetail") or []

        entries: list[SanctionEntry] = []
        for item in details:
            nature = (item.get("Nature") or "").lower()
            entity_type = "person" if "physique" in nature else (
                "entity" if "morale" in nature else "unknown"
            )

            nom = (item.get("Nom") or "").strip()
            prenom = (item.get("Prenom") or "").strip()
            primary = (f"{prenom} {nom}".strip() if prenom else nom).strip()
            if not primary:
                continue

            aliases_raw = item.get("Alias") or []
            if isinstance(aliases_raw, str):
                aliases = [a.strip() for a in aliases_raw.split(";") if a.strip()]
            else:
                aliases = [str(a).strip() for a in aliases_raw if str(a).strip()]

            entries.append(
                SanctionEntry(
                    source=self.name,
                    entry_id=str(item.get("IdRegistre") or ""),
                    name=primary,
                    entity_type=entity_type,
                    aliases=aliases,
                    sanctions_program=item.get("FondementJuridique") or "",
                    reference_url="https://gels-avoirs.dgtresor.gouv.fr/",
                )
            )

        logger.info("DGT: parsed %d entries", len(entries))
        return entries
