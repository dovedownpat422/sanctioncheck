"""EU consolidated sanctions list parser (XML)."""
from __future__ import annotations

import logging

from lxml import etree

from sanctioncheck.config import SOURCE_URLS
from sanctioncheck.models import SanctionEntry
from sanctioncheck.sources.base import SanctionSource

logger = logging.getLogger(__name__)

NS = {"e": "http://eu.europa.ec/fpi/fsd/export"}


class EUSource(SanctionSource):
    name = "EU"
    url = SOURCE_URLS["EU"]

    def parse(self, raw: bytes) -> list[SanctionEntry]:
        root = etree.fromstring(raw)
        entries: list[SanctionEntry] = []

        for entity in root.iterfind(".//e:sanctionEntity", NS):
            entry_id = entity.get("logicalId") or entity.get("euReferenceNumber") or ""

            subject = entity.find("e:subjectType", NS)
            code = subject.get("code") if subject is not None else ""
            entity_type = "person" if code == "person" else (
                "entity" if code in {"enterprise", "entity"} else "unknown"
            )

            regulation = entity.find("e:regulation", NS)
            programme = regulation.get("programme", "") if regulation is not None else ""
            ref_url = ""
            if regulation is not None:
                pub = regulation.findtext("e:publicationUrl", default="", namespaces=NS)
                ref_url = pub or ""

            names: list[str] = []
            for alias in entity.iterfind("e:nameAlias", NS):
                whole = alias.get("wholeName", "").strip()
                if not whole:
                    parts = [
                        alias.get("firstName", ""),
                        alias.get("middleName", ""),
                        alias.get("lastName", ""),
                    ]
                    whole = " ".join(p for p in parts if p).strip()
                if whole:
                    names.append(whole)

            if not names:
                continue

            entries.append(
                SanctionEntry(
                    source=self.name,
                    entry_id=entry_id,
                    name=names[0],
                    entity_type=entity_type,
                    aliases=names[1:],
                    sanctions_program=programme,
                    reference_url=ref_url,
                )
            )

        logger.info("EU: parsed %d entries", len(entries))
        return entries
