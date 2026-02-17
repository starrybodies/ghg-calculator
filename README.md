# GHG Emissions Calculator

**The open-source GHG Protocol Corporate Standard calculator with 967 embedded emission factors, a CLI, an MCP server, and a Claude Code skill.**

Calculate greenhouse gas emissions across all three scopes — from a single natural gas bill to an entire corporate carbon inventory — without paid APIs, proprietary databases, or spreadsheet templates.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 92 passing](https://img.shields.io/badge/tests-92%20passing-brightgreen.svg)]()
[![Emission Factors: 967](https://img.shields.io/badge/emission%20factors-967-orange.svg)]()

---

## What This Tool Does

`ghg-calculator` is a complete GHG Protocol implementation that:

1. **Calculates emissions** for any fuel, electricity, refrigerant, material, or spend category
2. **Covers all 3 scopes** — Scope 1 (direct combustion, fugitive), Scope 2 (purchased electricity with dual location + market-based), Scope 3 (all 15 value chain categories)
3. **Ships 967 emission factors** from 6 free, peer-reviewed databases — no API keys needed
4. **Generates interactive HTML reports** with Plotly charts (scope donut, waterfall, treemap, trend lines)
5. **Works as a Claude Code skill** — type `/ghg-analyze` to research and calculate emissions for any scenario

## Quick Start

```bash
# Install (requires Python 3.11+ and uv)
git clone https://github.com/starrybodies/ghg-calculator.git
cd ghg-calculator
uv sync

# Calculate emissions from 1,000 therms of natural gas
uv run ghg calculate --scope 1 --category stationary_combustion \
  --fuel natural_gas --quantity 1000 --unit therm
# → 5,307 kg CO2e (5.3 tCO2e)

# Search the emission factor database
uv run ghg factors "diesel"

# Generate an HTML report from activity data
uv run ghg report sample.json --output report.html
open report.html
```

## Claude Code Skill: `/ghg-analyze`

The fastest way to calculate emissions for any scenario. Install once, use from any project:

```bash
# Install the skill globally
cp -r .claude/skills/ghg-analyze ~/.claude/skills/
```

Then use natural language to analyze anything:

```
/ghg-analyze hyperscaler data center buildout in Texas 2025
/ghg-analyze my company's 200-truck diesel fleet in Ohio
/ghg-analyze Bitcoin mining operation 50MW in Iceland
/ghg-analyze commercial real estate portfolio 500,000 sqft in NYC
/ghg-analyze semiconductor fab construction in Arizona
```

**What the skill does automatically:**
- Researches real-world data for your scenario (electricity rates, fuel consumption, grid factors)
- Builds structured activity records across all applicable scopes
- Runs calculations with per-gas breakdown (CO2, CH4, N2O)
- Generates an interactive HTML report with charts
- Summarizes results with context comparisons (e.g., "equivalent to X passenger cars")

---

## Emission Factor Database (967 Factors)

All factors are embedded as versioned JSON — no external API calls, no rate limits, no costs.

| Source | Factors | Coverage | Use Case |
|--------|---------|----------|----------|
| **EPA Hub** | 113 | US stationary/mobile combustion, refrigerants | Scope 1: natural gas, diesel, gasoline, propane, jet fuel |
| **eGRID** | 122 | US electricity grid (27 subregions) | Scope 2: US electricity by region (ERCT, CAMX, RFCE, etc.) |
| **DEFRA** | 117 | UK/international transport, materials, waste | Scope 1/3: vehicles, flights, shipping, construction materials |
| **USEEIO** | 264 | US spend-based by NAICS sector | Scope 3: purchased goods/services via economic input-output |
| **Ember** | 120 | International electricity (120 countries) | Scope 2: global electricity by country (GB, DE, CN, JP, etc.) |
| **EXIOBASE** | 231 | Multi-regional input-output (EU, CN, JP, IN, BR, RU) | Scope 3: international spend-based estimates |

### Reference Emission Factors

| Activity | Factor | Source |
|----------|--------|--------|
| Natural gas | 5.3 kg CO2e/therm | EPA Hub |
| Diesel | 10.21 kg CO2/gallon | EPA Hub |
| Gasoline | 8.78 kg CO2/gallon | EPA Hub |
| US grid average | 0.37 kg CO2/kWh | eGRID |
| ERCOT (Texas) | 0.37 kg CO2/kWh | eGRID |
| CAMX (California) | 0.24 kg CO2/kWh | eGRID |
| UK grid | 0.21 kg CO2/kWh | Ember |
| Germany grid | 0.35 kg CO2/kWh | Ember |

---

## Use Cases

### Corporate Sustainability Teams

Calculate your organization's full Scope 1 + 2 + 3 carbon footprint for annual ESG reporting. Build activity records from utility bills, fleet data, and procurement spend, then generate GHG Protocol-compliant reports.

```bash
# Validate your activity data
uv run ghg validate company_2025.json

# Generate a corporate inventory report
uv run ghg report company_2025.json --output "Annual GHG Report 2025.html" \
  --title "Acme Corp GHG Inventory 2025"
```

### ESG Consultants

Run emissions analyses for multiple clients using the same standardized methodology. The embedded factor database means no per-client API costs. Export to GHG Protocol, CDP, or GRI 305 formats.

### Climate Tech Developers

Integrate the MCP server or Python API into your own applications. The calculation engine is fully programmable:

```python
from ghg_calculator.engine.calculator import GHGCalculator
from ghg_calculator.models.activity import ActivityRecord

calc = GHGCalculator()
result = calc.calculate_single(ActivityRecord(
    scope="scope_2",
    quantity=1_000_000,
    unit="kWh",
    grid_subregion="ERCT"
))
print(f"{result.total_co2e_tonnes:,.0f} tCO2e")
```

### AI Agent Integration

Use the MCP server to give any AI agent access to emissions calculations:

```bash
uv run ghg-mcp  # Starts the MCP server with 8 tools
```

Tools available: `calculate_emissions`, `calculate_single`, `get_emission_factors`, `list_scopes`, `list_factor_sources`, `generate_report`, `get_gwp_values`, `convert_units`

### Education and Research

Study GHG Protocol methodology with a transparent, open-source implementation. Every calculation shows the factor used, the source database, and the per-gas breakdown.

### Scenario Modeling

Compare emissions across different energy mixes, locations, or operational choices:

```bash
# Texas data center on ERCOT grid
uv run ghg calculate --scope 2 --quantity 1000000 --unit kWh --region ERCT
# → 373 tCO2e

# Same data center in California (CAMX)
uv run ghg calculate --scope 2 --quantity 1000000 --unit kWh --region CAMX
# → 241 tCO2e
```

---

## CLI Reference

### `ghg calculate` — Calculate emissions for a single activity

```bash
uv run ghg calculate --scope 1 --category stationary_combustion \
  --fuel natural_gas --quantity 1000 --unit therm
```

Options: `--scope`, `--category`, `--fuel`, `--quantity`, `--unit`, `--region`, `--custom-factor`, `--json`

### `ghg factors` — Search the emission factor database

```bash
uv run ghg factors "natural gas"
uv run ghg factors "diesel" --source epa_hub
uv run ghg factors "electricity" --source egrid
```

### `ghg gwp` — Look up Global Warming Potential values

```bash
uv run ghg gwp co2        # → 1
uv run ghg gwp ch4        # → 28 (AR5)
uv run ghg gwp r-410a     # → 2088
```

### `ghg convert` — Convert between units

```bash
uv run ghg convert 1000 therm MWh    # → 29.31 MWh
uv run ghg convert 1 short_ton kg    # → 907.18 kg
```

### `ghg validate` — Validate a JSON activity file

```bash
uv run ghg validate my_activities.json
```

### `ghg report` — Generate an interactive HTML report

```bash
uv run ghg report activities.json --output report.html --title "2025 GHG Inventory"
```

---

## Activity Record Format

Every calculation starts with an activity record — a JSON object describing what happened:

### Scope 1: Direct Emissions

```json
{
  "scope": "scope_1",
  "scope1_category": "stationary_combustion",
  "fuel_type": "natural_gas",
  "quantity": 1000,
  "unit": "therm"
}
```

Categories: `stationary_combustion`, `mobile_combustion`, `fugitive_emissions`, `process_emissions`

Fuel types: `natural_gas`, `diesel`, `gasoline`, `propane`, `jet_fuel`, `kerosene`, `coal_bituminous`, `fuel_oil_2`, `fuel_oil_6`, `lpg`, `ethanol`, `biodiesel`

Refrigerants: `r-410a`, `hfc-134a`, `r-404a`, `r-407c`, `r-507a`, `r-32`, and 20+ more

### Scope 2: Purchased Electricity

```json
{
  "scope": "scope_2",
  "quantity": 500000,
  "unit": "kWh",
  "grid_subregion": "ERCT"
}
```

US eGRID subregions: `AKGD`, `AKMS`, `AZNM`, `CAMX`, `ERCT`, `FRCC`, `HIMS`, `HIOA`, `MROE`, `MROW`, `NEWE`, `NWPP`, `NYCW`, `NYLI`, `NYUP`, `PRMS`, `RFCE`, `RFCM`, `RFCW`, `RMPA`, `SPNO`, `SPSO`, `SRMV`, `SRMW`, `SRSO`, `SRTV`, `SRVC`

International (120 countries): use `"country": "GB"` instead of `grid_subregion`

Scope 2 automatically produces both **location-based** and **market-based** results per GHG Protocol Scope 2 Guidance.

### Scope 3: Value Chain

```json
{
  "scope": "scope_3",
  "scope3_category": 1,
  "quantity": 1000000,
  "unit": "USD",
  "spend_amount": 1000000,
  "naics_code": "334111"
}
```

All 15 Scope 3 categories supported:
1. Purchased goods and services
2. Capital goods
3. Fuel- and energy-related activities
4. Upstream transportation
5. Waste generated in operations
6. Business travel
7. Employee commuting
8. Upstream leased assets
9. Downstream transportation
10. Processing of sold products
11. Use of sold products
12. End-of-life treatment
13. Downstream leased assets
14. Franchises
15. Investments

---

## How It Works

### Core Formula

```
CO2e = Activity Data × Emission Factor × Global Warming Potential
```

For each activity, the calculator:

1. **Matches an emission factor** from the 967-factor database (by fuel type, region, category, or NAICS code)
2. **Converts units** using pint (handles therms ↔ kWh ↔ MMBtu ↔ MJ, gallons ↔ litres, short tons ↔ tonnes, etc.)
3. **Calculates per-gas emissions** — CO2, CH4, and N2O are computed separately
4. **Applies GWP conversion** — each gas is converted to CO2-equivalent using AR5 or AR6 Global Warming Potentials
5. **Aggregates results** — totals by scope, category, and gas type

### GWP Values (AR5)

| Gas | GWP (100-year) |
|-----|-----------------|
| CO2 | 1 |
| CH4 | 28 |
| N2O | 265 |
| HFC-134a | 1,300 |
| R-410A | 2,088 |
| SF6 | 23,500 |

Both AR5 and AR6 assessment reports are supported. AR5 is the default per current GHG Protocol guidance.

---

## MCP Server

The MCP server exposes the full calculator to any AI agent or MCP-compatible client:

```bash
uv run ghg-mcp
```

### Available Tools

| Tool | Description |
|------|-------------|
| `calculate_emissions` | Calculate emissions for multiple activities |
| `calculate_single` | Calculate emissions for one activity |
| `get_emission_factors` | Search and retrieve emission factors |
| `list_scopes` | List available scopes and categories |
| `list_factor_sources` | List all factor databases and their coverage |
| `generate_report` | Generate an HTML report from activity data |
| `get_gwp_values` | Look up GWP for any greenhouse gas |
| `convert_units` | Convert between energy, mass, and volume units |

### MCP Configuration

Add to your Claude Code or MCP client configuration:

```json
{
  "mcpServers": {
    "ghg-calculator": {
      "command": "uv",
      "args": ["--directory", "/path/to/ghg-calculator", "run", "ghg-mcp"]
    }
  }
}
```

---

## Comparison with Alternatives

| Feature | ghg-calculator | Climatiq API | Spreadsheets | Persefoni/Sweep |
|---------|---------------|-------------|--------------|-----------------|
| **Price** | Free (MIT) | $0.01/calc | Free | $50K+/year |
| **Emission factors** | 967 embedded | 40,000+ (API) | Manual entry | Proprietary |
| **Offline capable** | Yes | No | Yes | No |
| **API keys required** | No | Yes | N/A | Yes |
| **All 3 scopes** | Yes | Yes | Manual | Yes |
| **Dual Scope 2** | Automatic | Manual | Manual | Yes |
| **Per-gas breakdown** | Yes | Some | No | Yes |
| **AI agent integration** | MCP + Skill | REST API | No | No |
| **Open source** | Yes | No | N/A | No |
| **Interactive reports** | Plotly HTML | No | Charts | Dashboard |

---

## Frequently Asked Questions

### How do I calculate Scope 3 emissions?

Scope 3 covers your value chain — everything from purchased goods (category 1) to investments (category 15). The easiest method is spend-based: provide your procurement spend in USD with a NAICS code, and the calculator uses USEEIO input-output factors. For more accuracy, use activity-based methods with specific quantities (tonnes of steel, km of transport, etc.) and custom emission factors.

### What emission factor databases are included?

Six free, peer-reviewed databases: EPA Emission Factors Hub (US combustion), eGRID (US electricity grid), DEFRA (UK government factors for transport, materials, waste), USEEIO (US economic input-output), Ember (international electricity for 120 countries), and EXIOBASE (multi-regional input-output for EU, China, Japan, India, Brazil, Russia).

### How accurate are the calculations?

The calculator follows GHG Protocol Corporate Standard methodology exactly. Accuracy depends on your input data quality. Calculations using direct activity data (fuel consumption, meter readings) with source-specific factors are the most accurate. Spend-based Scope 3 estimates are inherently less precise but useful for screening.

### Can I add custom emission factors?

Yes. Use the `custom_factor` field on any activity record to provide your own kg CO2e per unit value. This overrides the database lookup.

### What units are supported?

Energy: kWh, MWh, therm, MMBtu, MJ, GJ, CCF, MCF. Mass: kg, tonne, short_ton, lb. Volume: gallon, litre, barrel. Distance: km, mile. Currency: USD. The pint-based converter handles all standard conversions automatically.

### How does dual Scope 2 work?

Every electricity activity automatically produces two results: location-based (using the grid average for your region) and market-based (using your supplier's specific factor, or the residual mix if none provided). This follows GHG Protocol Scope 2 Guidance requirements.

---

## Architecture

```
src/ghg_calculator/
├── models/          # Pydantic data models (activity, factors, results, quality)
├── factors/         # Emission factor database (967 factors in versioned JSON)
│   ├── registry.py  # Factor search and retrieval
│   ├── gwp.py       # AR5 + AR6 Global Warming Potential tables
│   └── data/        # EPA Hub, eGRID, DEFRA, USEEIO, Ember, EXIOBASE
├── engine/          # Calculation engine (Strategy pattern)
│   ├── calculator.py  # Orchestrator
│   ├── scope1/      # Stationary, mobile, fugitive, process
│   ├── scope2/      # Location-based + market-based electricity
│   └── scope3/      # All 15 value chain categories
├── units/           # pint-based unit converter
├── reporting/       # Plotly charts + Jinja2 HTML templates
├── cli/             # Typer CLI (ghg command)
└── mcp/             # FastMCP server (ghg-mcp command)
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run all 92 tests
uv run pytest

# Run specific test suites
uv run pytest tests/unit/          # 46 unit tests
uv run pytest tests/integration/   # 15 integration tests
uv run pytest tests/e2e/           # 17 end-to-end CLI tests

# Lint
uv run ruff check src/
```

## Dependencies

- **pydantic** — data validation and models
- **pint** — unit conversion
- **pandas** — summary tables
- **plotly** — interactive charts
- **typer + rich** — CLI interface
- **fastmcp** — MCP server
- **jinja2** — HTML report templates

## License

MIT — free for commercial and personal use.

---

**Built for the GHG Protocol Corporate Standard. 967 emission factors. Zero API costs. One command.**
