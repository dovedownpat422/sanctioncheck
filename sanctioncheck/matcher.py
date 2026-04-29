"""Fuzzy matching against sanctions entries."""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from rapidfuzz import fuzz

from sanctioncheck.models import MatchResult, SanctionEntry

_NON_WORD_RE = re.compile(r"[^\w\s]+", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalize(name: str) -> str:
    """Lowercase, strip diacritics and punctuation, collapse whitespace."""
    if not name:
        return ""
    decomposed = unicodedata.normalize("NFKD", name)
    no_diacritics = "".join(c for c in decomposed if not unicodedata.combining(c))
    no_punct = _NON_WORD_RE.sub(" ", no_diacritics.lower())
    return _WS_RE.sub(" ", no_punct).strip()


def _score(query_norm: str, candidate_norm: str) -> float:
    """Score a single candidate name using token_set_ratio.

    token_set_ratio handles both name inversion ("Lastname, Firstname") and
    extra tokens such as patronyms ("Viktor Anatolijevitch Bout"), while still
    yielding low scores when token sets differ — required for AML screening.
    """
    if not candidate_norm:
        return 0.0
    return fuzz.token_set_ratio(query_norm, candidate_norm)


def match_entry(query: str, entry: SanctionEntry, threshold: float) -> MatchResult | None:
    """Return the best MatchResult for ``query`` against ``entry`` if above threshold."""
    query_norm = normalize(query)
    if not query_norm:
        return None

    best_score = _score(query_norm, normalize(entry.name))
    best_alias: str | None = None

    for alias in entry.aliases:
        alias_score = _score(query_norm, normalize(alias))
        if alias_score > best_score:
            best_score = alias_score
            best_alias = alias

    if best_score < threshold:
        return None

    return MatchResult(
        source=entry.source,
        matched_name=entry.name,
        query_name=query,
        score=float(best_score),
        entity_type=entry.entity_type,
        aliases=entry.aliases,
        sanctions_program=entry.sanctions_program,
        reference_url=entry.reference_url,
        matched_alias=best_alias,
    )


def match_all(
    query: str, entries: Iterable[SanctionEntry], threshold: float = 85
) -> list[MatchResult]:
    """Match ``query`` against each entry and return results sorted by score desc."""
    results: list[MatchResult] = []
    for entry in entries:
        result = match_entry(query, entry, threshold)
        if result is not None:
            results.append(result)
    results.sort(key=lambda r: r.score, reverse=True)
    return results
