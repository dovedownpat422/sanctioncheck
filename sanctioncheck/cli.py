"""Typer CLI entry point."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sanctioncheck import cache, matcher
from sanctioncheck.config import ALL_SOURCES, DEFAULT_THRESHOLD
from sanctioncheck.models import MatchResult, SanctionEntry
from sanctioncheck.sources import ALL as SOURCE_REGISTRY

app = typer.Typer(
    name="sanctioncheck",
    help="Screen names against EU, UN, OFAC and DGT (France) sanctions lists.",
    no_args_is_help=True,
)
console = Console()
logger = logging.getLogger(__name__)


def _selected_sources(filter_value: str) -> list[str]:
    if filter_value == "all":
        return list(ALL_SOURCES)
    requested = {s.strip().upper() for s in filter_value.split(",") if s.strip()}
    invalid = requested - set(ALL_SOURCES)
    if invalid:
        raise typer.BadParameter(f"Unknown source(s): {', '.join(sorted(invalid))}")
    return [s for s in ALL_SOURCES if s in requested]


async def _ensure_entries(source: str, refresh: bool) -> list[SanctionEntry]:
    if not refresh and cache.is_fresh(source):
        cached = cache.load(source)
        if cached is not None:
            return cached

    src_cls = SOURCE_REGISTRY[source]
    src = src_cls()
    try:
        entries = await src.fetch_and_parse()
    except Exception as exc:
        logger.warning("Fetch failed for %s: %s", source, exc)
        cached = cache.load(source)
        if cached is not None:
            console.print(f"[yellow]⚠ {source}: using stale cache ({exc.__class__.__name__})[/yellow]")
            return cached
        console.print(f"[red]✗ {source}: unavailable and no cache[/red]")
        return []
    cache.save(source, entries)
    return entries


async def _run_check(
    query: str, sources: list[str], threshold: int, refresh: bool
) -> list[MatchResult]:
    tasks = [_ensure_entries(s, refresh) for s in sources]
    all_entries = await asyncio.gather(*tasks)
    flat = [e for group in all_entries for e in group]
    return matcher.match_all(query, flat, threshold=threshold)


def _render_results(
    query: str, sources: list[str], threshold: int, results: list[MatchResult],
    elapsed: float, verbose: bool,
) -> None:
    header = (
        f"Recherche : \"{query}\"\n"
        f"Sources : {', '.join(sources)}\n"
        f"Seuil : {threshold}%"
    )
    console.print(Panel(header, title="SanctionCheck — Résultats", expand=False))

    if not results:
        console.print(f"\n[green]✓ 0 résultats trouvés en {elapsed:.1f}s — nom non listé.[/green]")
        return

    table = Table(show_lines=False)
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("Nom")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Programme")
    if verbose:
        table.add_column("Alias matché")
        table.add_column("Type")

    for r in results:
        row = [r.source, r.matched_name, f"{r.score:.0f}%", r.sanctions_program or "-"]
        if verbose:
            row.append(r.matched_alias or "-")
            row.append(r.entity_type)
        table.add_row(*row)

    console.print(table)
    console.print(f"\n[red]✓ {len(results)} résultat(s) trouvé(s) en {elapsed:.1f}s[/red]")


@app.command()
def check(
    query_parts: Annotated[
        list[str],
        typer.Argument(
            metavar="NAME",
            help='Name to screen. Multiple words may be passed unquoted: '
                 '`check John Doe` is equivalent to `check "John Doe"`. '
                 'Matching is case-insensitive and tolerant to diacritics.',
        ),
    ],
    threshold: Annotated[int, typer.Option("--threshold", "-t", min=0, max=100)] = DEFAULT_THRESHOLD,
    source: Annotated[str, typer.Option("--source", "-s", help="Comma-separated list (eu,un,ofac,dgt) or 'all'.")] = "all",
    refresh: Annotated[bool, typer.Option("--refresh", help="Force cache refresh.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON instead of table.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show matching details.")] = False,
) -> None:
    """Screen a name against the configured sanctions lists."""
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(message)s")

    query = " ".join(query_parts).strip()
    if not query:
        raise typer.BadParameter("NAME is required.")

    sources = _selected_sources(source)
    start = time.perf_counter()
    results = asyncio.run(_run_check(query, sources, threshold, refresh))
    elapsed = time.perf_counter() - start

    if json_output:
        typer.echo(json.dumps([r.model_dump() for r in results], ensure_ascii=False, indent=2))
        return

    _render_results(query, sources, threshold, results, elapsed, verbose)


@app.command()
def update(
    source: Annotated[str, typer.Option("--source", "-s")] = "all",
) -> None:
    """Re-download and re-cache all (or selected) sources."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sources = _selected_sources(source)

    async def _run() -> None:
        for s in sources:
            console.print(f"[cyan]↻ Refreshing {s}...[/cyan]")
            entries = await _ensure_entries(s, refresh=True)
            console.print(f"  [green]✓ {len(entries)} entries[/green]")

    asyncio.run(_run())


@app.command()
def stats() -> None:
    """Show cache status and entry counts per source."""
    table = Table(title="SanctionCheck — Cache")
    table.add_column("Source", style="cyan")
    table.add_column("Cached", justify="right")
    table.add_column("Entries", justify="right")
    table.add_column("Age")
    table.add_column("Fresh")

    for source in ALL_SOURCES:
        info = cache.cache_info(source)
        if info is None:
            table.add_row(source, "no", "-", "-", "-")
            continue
        entries = cache.load(source) or []
        age_h = info["age_seconds"] / 3600
        table.add_row(
            source,
            "yes",
            str(len(entries)),
            f"{age_h:.1f}h",
            "yes" if info["fresh"] else "no",
        )
    console.print(table)


if __name__ == "__main__":
    app()
