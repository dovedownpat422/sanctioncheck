"""OFAC SDN list parser (XML)."""
from __future__ import annotations

import logging

from lxml import etree

from sanctioncheck.config import SOURCE_URLS
from sanctioncheck.models import SanctionEntry
from sanctioncheck.sources.base import SanctionSource

logger = logging.getLogger(__name__)

NS = {"o": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"}


def _join(*parts: str | None) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


class OFACSource(SanctionSource):
    name = "OFAC"
    url = SOURCE_URLS["OFAC"]

    def parse(self, raw: bytes) -> list[SanctionEntry]:
        root = etree.fromstring(raw)
        # OFAC ships either with or without default namespace depending on year.
        ns = NS if "sanctionslistservice" in (root.tag or "") else None
        path = ".//o:sdnEntry" if ns else ".//sdnEntry"

        entries: list[SanctionEntry] = []
        for entry in root.iterfind(path, ns):
            parsed = self._parse_entry(entry, ns)
            if parsed is not None:
                entries.append(parsed)

        logger.info("OFAC: parsed %d entries", len(entries))
        return entries

    def _parse_entry(
        self, entry: etree._Element, ns: dict[str, str] | None
    ) -> SanctionEntry | None:
        def text(tag: str, parent: etree._Element | None = None) -> str:
            parent = parent if parent is not None else entry
            if ns:
                el = parent.find(f"o:{tag}", ns)
            else:
                el = parent.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        sdn_type = text("sdnType")
        entity_type = "person" if sdn_type == "Individual" else (
            "entity" if sdn_type == "Entity" else "unknown"
        )

        primary = _join(text("firstName"), text("lastName")) if entity_type == "person" else text("lastName")
        if not primary:
            return None

        aliases: list[str] = []
        aka_list = entry.find("o:akaList", ns) if ns else entry.find("akaList")
        if aka_list is not None:
            iter_path = "o:aka" if ns else "aka"
            for aka in aka_list.iterfind(iter_path, ns) if ns else aka_list.iterfind(iter_path):
                aka_name = _join(text("firstName", aka), text("lastName", aka))
                if aka_name:
                    aliases.append(aka_name)

        program = ""
        program_list = entry.find("o:programList", ns) if ns else entry.find("programList")
        if program_list is not None:
            programs: list[str] = []
            iter_path = "o:program" if ns else "program"
            for prog in program_list.iterfind(iter_path, ns) if ns else program_list.iterfind(iter_path):
                if prog.text:
                    programs.append(prog.text.strip())
            program = ", ".join(programs)

        uid = text("uid")
        return SanctionEntry(
            source=self.name,
            entry_id=uid,
            name=primary,
            entity_type=entity_type,
            aliases=aliases,
            sanctions_program=program,
            reference_url=f"https://sanctionssearch.ofac.treas.gov/Details.aspx?id={uid}" if uid else "",
        )
