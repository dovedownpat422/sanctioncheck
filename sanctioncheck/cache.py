"""Local cache for parsed sanctions lists (JSON, 24h TTL)."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from sanctioncheck.config import CACHE_DIR, CACHE_TTL_SECONDS
from sanctioncheck.models import SanctionEntry

logger = logging.getLogger(__name__)


def _path(source: str) -> Path:
    return CACHE_DIR / f"{source.lower()}.json"


def is_fresh(source: str, ttl: int = CACHE_TTL_SECONDS) -> bool:
    """True if the cached file exists and is younger than ``ttl`` seconds."""
    path = _path(source)
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) < ttl


def save(source: str, entries: list[SanctionEntry]) -> None:
    """Persist ``entries`` for ``source`` to the cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _path(source)
    payload = {
        "source": source,
        "fetched_at": time.time(),
        "entries": [e.model_dump() for e in entries],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.info("Cached %d entries for %s at %s", len(entries), source, path)


def load(source: str) -> list[SanctionEntry] | None:
    """Load cached entries; return ``None`` if missing or unreadable."""
    path = _path(source)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read cache for %s: %s", source, exc)
        return None
    return [SanctionEntry(**item) for item in payload.get("entries", [])]


def cache_info(source: str) -> dict | None:
    """Return metadata about the cache file (size, age) or ``None``."""
    path = _path(source)
    if not path.exists():
        return None
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "age_seconds": time.time() - stat.st_mtime,
        "fresh": is_fresh(source),
    }
