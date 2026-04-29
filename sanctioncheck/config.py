"""Configuration: source URLs, defaults, and runtime paths."""
from __future__ import annotations

from pathlib import Path

from platformdirs import user_cache_dir

APP_NAME = "sanctioncheck"

# Source URLs (verified accessible 2026-04-29).
SOURCE_URLS: dict[str, str] = {
    "EU": "https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
    "UN": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
    "OFAC": "https://www.treasury.gov/ofac/downloads/sdn.xml",
    # DGT public API has been moving; we keep the documented endpoint but ship a
    # bundled fallback file for offline use.
    "DGT": "https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publications/derniere-publication-et-historique",
}

ALL_SOURCES = tuple(SOURCE_URLS.keys())

DEFAULT_THRESHOLD = 85
DEFAULT_TIMEOUT = 30
CACHE_TTL_SECONDS = 24 * 3600

CACHE_DIR = Path(user_cache_dir(APP_NAME))
PACKAGE_DATA_DIR = Path(__file__).resolve().parent / "data"
