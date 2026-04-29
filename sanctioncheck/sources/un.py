"""UN Security Council consolidated sanctions list parser (XML)."""
from __future__ import annotations

import logging

from lxml import etree

from sanctioncheck.config import SOURCE_URLS
from sanctioncheck.models import SanctionEntry
from sanctioncheck.sources.base import SanctionSource

logger = logging.getLogger(__name__)


def _join(*parts: str | None) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


class UNSource(SanctionSource):
    name = "UN"
    url = SOURCE_URLS["UN"]

    def parse(self, raw: bytes) -> list[SanctionEntry]:
        root = etree.fromstring(raw)
        entries: list[SanctionEntry] = []

        for individual in root.iterfind(".//INDIVIDUAL"):
            entries.append(self._parse_individual(individual))

        for entity in root.iterfind(".//ENTITY"):
            entries.append(self._parse_entity(entity))

        entries = [e for e in entries if e is not None]
        logger.info("UN: parsed %d entries", len(entries))
        return entries

    def _parse_individual(self, node: etree._Element) -> SanctionEntry | None:
        primary = _join(
            node.findtext("FIRST_NAME"),
            node.findtext("SECOND_NAME"),
            node.findtext("THIRD_NAME"),
            node.findtext("FOURTH_NAME"),
        )
        if not primary:
            return None

        aliases: list[str] = []
        for alias_node in node.iterfind("INDIVIDUAL_ALIAS"):
            alias_name = alias_node.findtext("ALIAS_NAME") or ""
            alias_name = alias_name.strip()
            if alias_name:
                aliases.append(alias_name)

        return SanctionEntry(
            source=self.name,
            entry_id=node.findtext("DATAID") or node.findtext("REFERENCE_NUMBER") or "",
            name=primary,
            entity_type="person",
            aliases=aliases,
            sanctions_program=node.findtext("UN_LIST_TYPE") or "",
            reference_url=node.findtext("INTERPOL_LINK") or "",
        )

    def _parse_entity(self, node: etree._Element) -> SanctionEntry | None:
        primary = (node.findtext("FIRST_NAME") or "").strip()
        if not primary:
            return None

        aliases: list[str] = []
        for alias_node in node.iterfind("ENTITY_ALIAS"):
            alias_name = alias_node.findtext("ALIAS_NAME") or ""
            alias_name = alias_name.strip()
            if alias_name:
                aliases.append(alias_name)

        return SanctionEntry(
            source=self.name,
            entry_id=node.findtext("DATAID") or node.findtext("REFERENCE_NUMBER") or "",
            name=primary,
            entity_type="entity",
            aliases=aliases,
            sanctions_program=node.findtext("UN_LIST_TYPE") or "",
            reference_url="",
        )
