"""GHG Calculator CLI — Typer application."""

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..engine.calculator import GHGCalculator
from ..factors.gwp import get_gwp, list_gases
from ..factors.registry import FactorRegistry
from ..models.activity import ActivityRecord
from ..models.enums import (
    FactorSource,
    FuelType,
    GWPAssessment,
    Scope,
    Scope1Category,
    Scope3Category,
)
from ..units.converter import converter

app = typer.Typer(
    name="ghg",
    help="GHG Protocol emissions calculator",
    no_args_is_help=True,
)
console = Console()


@app.command()
def calculate(
    scope: Annotated[int, typer.Option(help="Emission scope (1, 2, or 3)")] = 1,
    category: Annotated[Optional[str], typer.Option(help="Emission category")] = None,
    fuel: Annotated[Optional[str], typer.Option(help="Fuel type")] = None,
    quantity: Annotated[float, typer.Option(help="Activity quantity")] = 0,
    unit: Annotated[str, typer.Option(help="Unit of quantity")] = "therm",
    region: Annotated[Optional[str], typer.Option(help="Grid subregion or country")] = None,
    custom_factor: Annotated[Optional[float], typer.Option("--factor", help="Custom emission factor (kg CO2e/unit)")] = None,
    refrigerant: Annotated[Optional[str], typer.Option(help="Refrigerant type")] = None,
    gwp: Annotated[str, typer.Option(help="GWP assessment (ar5 or ar6)")] = "ar5",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Calculate GHG emissions for a single activity."""
    if quantity <= 0:
        console.print("[red]Error: --quantity must be positive[/red]")
        raise typer.Exit(1)

    scope_enum = {1: Scope.SCOPE_1, 2: Scope.SCOPE_2, 3: Scope.SCOPE_3}[scope]
    gwp_assessment = GWPAssessment(gwp)

    # Build activity record
    scope1_cat = None
    scope3_cat = None
    fuel_type = None
    grid_subregion = None

    if scope == 1 and category:
        try:
            scope1_cat = Scope1Category(category)
        except ValueError:
            console.print(f"[red]Unknown Scope 1 category: {category}[/red]")
            console.print(f"Valid: {[c.value for c in Scope1Category]}")
            raise typer.Exit(1)

    if scope == 3 and category:
        try:
            scope3_cat = Scope3Category(int(category))
        except (ValueError, KeyError):
            console.print(f"[red]Unknown Scope 3 category: {category}[/red]")
            raise typer.Exit(1)

    if fuel:
        try:
            fuel_type = FuelType(fuel)
        except ValueError:
            pass  # Will use as custom_fuel

    if scope == 2 and region:
        grid_subregion = region

    activity = ActivityRecord(
        scope=scope_enum,
        scope1_category=scope1_cat,
        scope3_category=scope3_cat,
        quantity=quantity,
        unit=unit,
        fuel_type=fuel_type,
        custom_fuel=fuel if fuel_type is None else None,
        grid_subregion=grid_subregion,
        country=region if scope != 2 else None,
        custom_factor=custom_factor,
        refrigerant_type=refrigerant,
    )

    calc = GHGCalculator(gwp_assessment=gwp_assessment)
    results = calc.calculate_single(activity)

    if json_output:
        out = [r.model_dump(mode="json") for r in results]
        console.print_json(json.dumps(out, default=str))
        return

    for result in results:
        table = Table(title="Emission Calculation Result")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Scope", result.scope.value)
        if result.scope1_category:
            table.add_row("Category", result.scope1_category.value)
        if result.scope2_method:
            table.add_row("Method", result.scope2_method.value)
        if result.scope3_category:
            table.add_row("Category", f"{result.scope3_category.value} - {result.scope3_category.name}")

        table.add_row("Total CO2e (kg)", f"{result.total_co2e_kg:,.2f}")
        table.add_row("Total CO2e (tonnes)", f"{result.total_co2e_tonnes:,.4f}")

        if result.gas_breakdown:
            for gb in result.gas_breakdown:
                table.add_row(
                    f"  {gb.gas.value.upper()}",
                    f"{gb.mass_kg:,.4f} kg → {gb.co2e_kg:,.4f} kg CO2e (GWP={gb.gwp_used})",
                )

        if result.factor_id:
            table.add_row("Factor", f"{result.factor_id} ({result.factor_source})")
        if result.notes:
            table.add_row("Notes", "; ".join(result.notes))

        console.print(table)
        console.print()


@app.command()
def factors(
    search: Annotated[Optional[str], typer.Argument(help="Search query")] = None,
    source: Annotated[Optional[str], typer.Option(help="Filter by source")] = None,
    category: Annotated[Optional[str], typer.Option(help="Filter by category")] = None,
    limit: Annotated[int, typer.Option(help="Max results")] = 20,
):
    """Search emission factors database."""
    registry = FactorRegistry.load()

    source_enum = FactorSource(source) if source else None
    results = registry.search(
        query=search or "",
        source=source_enum,
        category=category,
        limit=limit,
    )

    if not results:
        console.print("[yellow]No factors found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Emission Factors ({len(results)} results)")
    table.add_column("ID", style="cyan", max_width=30)
    table.add_column("Name", style="white", max_width=40)
    table.add_column("CO2", style="green", justify="right")
    table.add_column("CH4", style="green", justify="right")
    table.add_column("N2O", style="green", justify="right")
    table.add_column("Unit", style="yellow")
    table.add_column("Source", style="magenta")

    for f in results:
        co2e_str = f"{f.co2e_factor:.4f}" if f.co2e_factor is not None else ""
        table.add_row(
            f.id,
            f.name,
            f"{f.co2_factor:.4f}" if f.co2_factor else co2e_str,
            f"{f.ch4_factor:.6f}" if f.ch4_factor else "",
            f"{f.n2o_factor:.6f}" if f.n2o_factor else "",
            f.activity_unit,
            f.source.value,
        )

    console.print(table)
    console.print(f"\nTotal factors in registry: {registry.factor_count}")


@app.command(name="gwp")
def gwp_cmd(
    gas: Annotated[Optional[str], typer.Argument(help="Gas name (e.g., ch4, hfc-134a)")] = None,
    assessment: Annotated[str, typer.Option(help="AR5 or AR6")] = "ar5",
):
    """Look up Global Warming Potential values."""
    gwp_assessment = GWPAssessment(assessment.lower())

    if gas:
        try:
            value = get_gwp(gas, gwp_assessment)
            console.print(f"GWP of [cyan]{gas}[/cyan] ({gwp_assessment.value}): [green]{value:,.0f}[/green]")
        except KeyError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    else:
        gases = list_gases(gwp_assessment)
        table = Table(title=f"GWP Values ({gwp_assessment.value})")
        table.add_column("Gas", style="cyan")
        table.add_column("100-yr GWP", style="green", justify="right")
        for g in gases:
            table.add_row(g, f"{get_gwp(g, gwp_assessment):,.0f}")
        console.print(table)


@app.command()
def convert(
    value: Annotated[float, typer.Argument(help="Value to convert")],
    from_unit: Annotated[str, typer.Argument(help="Source unit")],
    to_unit: Annotated[str, typer.Argument(help="Target unit")],
):
    """Convert between units."""
    try:
        result = converter.convert(value, from_unit, to_unit)
        console.print(f"{value} {from_unit} = [green]{result:,.6g}[/green] {to_unit}")
    except Exception as e:
        console.print(f"[red]Conversion error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    file: Annotated[Path, typer.Argument(help="JSON file with activity records")],
):
    """Validate a JSON file of activity records."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    with open(file) as f:
        data = json.load(f)

    records = data if isinstance(data, list) else [data]
    errors = []
    valid = 0

    for i, record in enumerate(records):
        try:
            ActivityRecord(**record)
            valid += 1
        except Exception as e:
            errors.append((i, str(e)))

    console.print(f"[green]{valid} valid records[/green]")
    if errors:
        console.print(f"[red]{len(errors)} invalid records:[/red]")
        for idx, err in errors:
            console.print(f"  Record {idx}: {err}")
        raise typer.Exit(1)


@app.command()
def report(
    file: Annotated[Path, typer.Argument(help="JSON file with activity records")],
    output: Annotated[Path, typer.Option(help="Output file path")] = Path("report.html"),
    title: Annotated[str, typer.Option(help="Report title")] = "GHG Emissions Report",
    format: Annotated[str, typer.Option(help="Report format: ghg_protocol, cdp, gri_305")] = "ghg_protocol",
):
    """Generate an emissions report from activity data."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    with open(file) as f:
        data = json.load(f)

    records = data if isinstance(data, list) else [data]
    activities = [ActivityRecord(**r) for r in records]

    calc = GHGCalculator()
    inventory = calc.calculate_inventory(activities, name=title)

    # Import here to avoid circular imports and heavy deps at startup
    from ..reporting.generator import ReportGenerator
    from ..models.report import ReportConfig, ReportFormat

    config = ReportConfig(
        title=title,
        format=ReportFormat(format),
    )

    generator = ReportGenerator()
    generator.generate(inventory, config, output, activities=activities)
    console.print(f"[green]Report generated: {output}[/green]")


if __name__ == "__main__":
    app()
