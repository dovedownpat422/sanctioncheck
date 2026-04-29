# SanctionCheck

> Designed by **@twux-sec**.

> **Disclaimer.** This tool is for compliance and research purposes only.

A command-line screening tool that checks a person or entity name against the
public consolidated sanctions lists of the **EU**, **UN**, **OFAC (US)** and
**DGT (France)** in real time. Built for AML / KYC / due-diligence workflows
that need a fast, scriptable check without relying on commercial vendors.

## Features

- Four authoritative sources, parsed natively (no third-party API key required).
- Fuzzy matching tolerant to typos, name inversion, diacritics and translitterations
  (powered by `rapidfuzz`).
- Local cache with 24h TTL — `update` to refresh, `--refresh` to force.
- Fallback to a bundled file when an upstream source is unreachable.
- Pretty `rich` table output, plus `--json` for piping into other tools.

## Installation

```bash
git clone https://github.com/twux-sec/sanctioncheck.git
cd sanctioncheck
pip install -e .
```

Python 3.11+ is required.

## Usage

```bash
# Default: query all four sources, threshold 85%
sanctioncheck check "Viktor Bout"

# Filter source(s)
sanctioncheck check "Bank Melli Iran" --source ofac,un

# Lower the threshold and show alias matches
sanctioncheck check "John Smith" -t 70 -v

# Force a re-download of all lists
sanctioncheck update

# Inspect the local cache
sanctioncheck stats

# Pipe results to jq
sanctioncheck check "Viktor Bout" --json | jq '.[0]'
```

### Name syntax

- **Case-insensitive** — `Viktor Bout`, `viktor bout` and `VIKTOR BOUT` all match the same record.
- **Diacritics-insensitive** — `Élise Müller` and `Elise Muller` are equivalent.
- **Quotes are optional** for multi-word names — both forms work:
  ```bash
  sanctioncheck check Viktor Bout
  sanctioncheck check "Viktor Bout"
  ```
  Use quotes when the name contains shell metacharacters (`&`, `|`, `;`, `*`, `(`, `)`).

## Sources

| List | Authority                                    | Format | URL                                                                                                               |
| ---- | -------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------- |
| EU   | European External Action Service             | XML    | https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw |
| UN   | UN Security Council                          | XML    | https://scsanctions.un.org/resources/xml/en/consolidated.xml                                                      |
| OFAC | US Treasury (Specially Designated Nationals) | XML    | https://www.treasury.gov/ofac/downloads/sdn.xml                                                                   |
| DGT  | French Treasury (Gel des avoirs)             | JSON   | https://gels-avoirs.dgtresor.gouv.fr/ — bundled fallback ships when the public API is unreachable                 |

## License

MIT — see [LICENSE](LICENSE).

## Topics

`osint` `sanctions` `aml` `compliance` `lcb-ft` `kyc` `ofac` `finint` `python` `screening`
