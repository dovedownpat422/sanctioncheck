"""Pydantic data models."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EntityType = Literal["person", "entity", "unknown"]


class SanctionEntry(BaseModel):
    """A single record in a sanctions list."""

    source: str
    entry_id: str
    name: str
    entity_type: EntityType = "unknown"
    aliases: list[str] = Field(default_factory=list)
    sanctions_program: str = ""
    reference_url: str = ""


class MatchResult(BaseModel):
    """A match between a query and a SanctionEntry."""

    source: str
    matched_name: str
    query_name: str
    score: float
    entity_type: EntityType
    aliases: list[str] = Field(default_factory=list)
    sanctions_program: str = ""
    reference_url: str = ""
    matched_alias: str | None = None
