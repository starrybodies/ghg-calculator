"""Report generator orchestrator — elegant green/black theme with maps."""

import json
from pathlib import Path

from jinja2 import Template

from ..models.activity import ActivityRecord
from ..models.report import ReportConfig, ReportFormat
from ..models.results import InventoryResult
from . import charts, tables

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <style>
        :root {
            --green-dark: #0D1F0D;
            --green-deep: #1B3A1B;
            --green-primary: #2D6A2D;
            --green-mid: #3D8B3D;
            --green-bright: #4CAF50;
            --green-light: #81C784;
            --green-pale: #A5D6A7;
            --green-wash: #C8E6C9;
            --accent-lime: #7CB342;
            --accent-emerald: #00897B;
            --accent-gold: #C6A700;
            --black: #0A0A0A;
            --charcoal: #1A1A1A;
            --gray-dark: #2C2C2C;
            --gray-mid: #555555;
            --gray-light: #888888;
            --cream: #F5F5F0;
            --cream-dim: #C8C8C0;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--black);
            color: var(--cream);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ── Hero ──────────────────────────────────────── */
        .hero {
            background: linear-gradient(135deg, var(--black) 0%, var(--green-dark) 50%, var(--green-deep) 100%);
            padding: 80px 40px 72px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                radial-gradient(ellipse at 20% 50%, rgba(76,175,80,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(0,137,123,0.06) 0%, transparent 50%);
            pointer-events: none;
        }
        .hero h1 {
            font-family: 'Inter', -apple-system, sans-serif;
            font-size: clamp(2rem, 5vw, 3.2rem);
            font-weight: 600;
            color: var(--cream);
            letter-spacing: -0.03em;
            margin-bottom: 16px;
            position: relative;
        }
        .hero h1 .accent {
            color: var(--green-bright);
        }
        .hero .meta-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        .hero .tag {
            display: inline-block;
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--green-light);
            border: 1px solid rgba(76,175,80,0.25);
            padding: 4px 14px;
            border-radius: 20px;
        }
        .hero .tag.tag-year {
            color: var(--green-bright);
            border-color: rgba(76,175,80,0.4);
        }

        /* ── Container ─────────────────────────────────── */
        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 24px;
        }

        /* ── Summary Cards ─────────────────────────────── */
        .cards-section {
            margin-top: -36px;
            position: relative;
            z-index: 2;
            padding: 0 24px;
            margin-bottom: 16px;
        }
        .cards-grid {
            max-width: 1280px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }
        .card {
            background: linear-gradient(145deg, var(--charcoal) 0%, var(--gray-dark) 100%);
            border: 1px solid rgba(76,175,80,0.15);
            border-radius: 12px;
            padding: 28px 24px 24px;
            text-align: center;
            transition: border-color 0.3s, transform 0.3s;
        }
        .card:hover {
            border-color: rgba(76,175,80,0.4);
            transform: translateY(-2px);
        }
        .card.card-total {
            background: linear-gradient(145deg, var(--green-dark) 0%, var(--green-deep) 100%);
            border-color: rgba(76,175,80,0.3);
        }
        .card-value {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--green-bright);
            line-height: 1.1;
        }
        .card-total .card-value {
            font-size: 2.6rem;
        }
        .card-unit {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--green-light);
            margin-top: 2px;
        }
        .card-label {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 0.95rem;
            color: var(--cream-dim);
            margin-top: 10px;
            font-style: italic;
        }

        /* ── Sections ──────────────────────────────────── */
        section {
            padding: 40px 0 48px;
        }
        section:first-child {
            padding-top: 32px;
        }
        section + section {
            border-top: 1px solid rgba(76,175,80,0.08);
        }
        h2 {
            font-family: 'Playfair Display', Georgia, 'Times New Roman', serif;
            font-size: 1.8rem;
            font-weight: 600;
            color: var(--cream);
            margin-bottom: 20px;
            letter-spacing: -0.01em;
        }
        h2 .section-number {
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 400;
            font-style: italic;
            color: var(--green-bright);
            margin-right: 12px;
            font-size: 1.4rem;
        }

        /* ── Tables ────────────────────────────────────── */
        .table-wrapper {
            overflow-x: auto;
            border-radius: 10px;
            border: 1px solid rgba(76,175,80,0.12);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        thead th {
            background: var(--green-dark);
            color: var(--green-light);
            padding: 14px 16px;
            text-align: left;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            border-bottom: 2px solid var(--green-primary);
        }
        tbody td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(76,175,80,0.06);
            color: var(--cream-dim);
            font-family: 'Inter', sans-serif;
        }
        tbody tr {
            background: var(--charcoal);
            transition: background 0.15s;
        }
        tbody tr:nth-child(even) {
            background: rgba(26,26,26,0.5);
        }
        tbody tr:hover {
            background: var(--green-dark);
        }
        tbody tr:last-child td {
            font-weight: 600;
            color: var(--cream);
            border-top: 2px solid var(--green-primary);
            background: var(--green-dark);
        }

        /* ── Chart containers ──────────────────────────── */
        .chart-container {
            background: linear-gradient(145deg, var(--charcoal) 0%, rgba(26,26,26,0.8) 100%);
            border: 1px solid rgba(76,175,80,0.12);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
        }
        .chart-container.chart-map {
            padding: 12px 0;
            overflow: hidden;
        }
        .chart-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .chart-row .chart-container {
            margin: 0;
        }
        @media (max-width: 900px) {
            .chart-row { grid-template-columns: 1fr; }
        }

        /* ── Methodology ───────────────────────────────── */
        .methodology {
            background: linear-gradient(145deg, var(--green-dark), var(--charcoal));
            border: 1px solid rgba(76,175,80,0.15);
            border-radius: 12px;
            padding: 32px;
        }
        .methodology h3 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.2rem;
            color: var(--green-light);
            margin-bottom: 16px;
        }
        .methodology ul {
            list-style: none;
            padding: 0;
        }
        .methodology li {
            padding: 6px 0 6px 24px;
            position: relative;
            color: var(--cream-dim);
            font-size: 0.9rem;
        }
        .methodology li::before {
            content: '';
            position: absolute;
            left: 0;
            top: 14px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green-bright);
        }
        .methodology p {
            color: var(--cream-dim);
            font-size: 0.9rem;
            margin-top: 12px;
        }

        /* ── Footer ────────────────────────────────────── */
        .footer {
            text-align: center;
            padding: 48px 24px 40px;
            border-top: 1px solid rgba(76,175,80,0.1);
            margin-top: 24px;
        }
        .footer-brand {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.1rem;
            color: var(--green-bright);
            font-weight: 600;
        }
        .footer-sub {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            color: var(--gray-mid);
            margin-top: 6px;
            letter-spacing: 0.05em;
        }
        .footer-links {
            margin-top: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 24px;
            flex-wrap: wrap;
        }
        .footer-links a {
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
            color: var(--green-light);
            text-decoration: none;
            letter-spacing: 0.02em;
            transition: color 0.2s;
        }
        .footer-links a:hover {
            color: var(--green-bright);
        }
        .footer-links .sep {
            color: rgba(76,175,80,0.25);
            font-size: 0.7rem;
        }
        .footer-built-by {
            margin-top: 20px;
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
            color: var(--gray-light);
            letter-spacing: 0.03em;
        }
        .footer-built-by a {
            color: var(--green-bright);
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }
        .footer-built-by a:hover {
            color: var(--green-light);
        }

        /* ── Gauge wrapper ──────────────────────────── */
        .gauge-row {
            display: flex;
            justify-content: center;
            margin: 24px 0 8px;
        }
        .gauge-container {
            background: linear-gradient(145deg, var(--charcoal) 0%, rgba(26,26,26,0.8) 100%);
            border: 1px solid rgba(76,175,80,0.12);
            border-radius: 12px;
            padding: 16px;
            max-width: 500px;
            width: 100%;
        }

        /* ── Print ─────────────────────────────────────── */
        @media print {
            body { background: white; color: #1a1a1a; }
            .hero { background: #1B3A1B; -webkit-print-color-adjust: exact; }
            .card, .chart-container, .methodology { border-color: #ccc; }
        }
    </style>
</head>
<body>

    <!-- Hero -->
    <header class="hero">
        <h1>{{ title }}</h1>
        <div class="meta-row">
            <span class="tag">GHG Protocol</span>
            <span class="tag">967 Factors</span>
            <span class="tag">Scope 1 + 2 + 3</span>
            {% if year %}<span class="tag tag-year">{{ year }}</span>{% endif %}
        </div>
    </header>

    <!-- Summary Cards -->
    <div class="cards-section">
        <div class="cards-grid">
            <div class="card card-total">
                <div class="card-value">{{ format_number(total_tonnes) }}</div>
                <div class="card-unit">tCO2e</div>
                <div class="card-label">Total Emissions</div>
            </div>
            <div class="card">
                <div class="card-value">{{ format_number(scope1_tonnes) }}</div>
                <div class="card-unit">tCO2e</div>
                <div class="card-label">Scope 1 &mdash; Direct</div>
            </div>
            <div class="card">
                <div class="card-value">{{ format_number(scope2_tonnes) }}</div>
                <div class="card-unit">tCO2e</div>
                <div class="card-label">Scope 2 &mdash; Electricity</div>
            </div>
            <div class="card">
                <div class="card-value">{{ format_number(scope3_tonnes) }}</div>
                <div class="card-unit">tCO2e</div>
                <div class="card-label">Scope 3 &mdash; Value Chain</div>
            </div>
        </div>
    </div>

    <div class="container">

        {% if gauge_json %}
        <!-- Gauge -->
        <div class="gauge-row">
            <div class="gauge-container">
                <div id="gauge_chart"></div>
                <script>
                    Plotly.newPlot('gauge_chart',
                        {{ gauge_json | safe }}.data,
                        {{ gauge_json | safe }}.layout,
                        {responsive: true, displayModeBar: false}
                    );
                </script>
            </div>
        </div>
        {% endif %}

        {% if map_json %}
        <!-- Geographic Map -->
        <section>
            <h2><span class="section-number">I.</span> Geographic Distribution</h2>
            <div class="chart-container chart-map">
                <div id="emissions_map"></div>
                <script>
                    Plotly.newPlot('emissions_map',
                        {{ map_json | safe }}.data,
                        {{ map_json | safe }}.layout,
                        {responsive: true, displayModeBar: false}
                    );
                </script>
            </div>
        </section>
        {% endif %}

        <!-- Scope Summary -->
        <section>
            <h2><span class="section-number">{{ section_num('scope') }}.</span> Scope Summary</h2>
            <div class="table-wrapper">
                {{ scope_table }}
            </div>

            <div class="chart-row" style="margin-top:20px;">
                {% if donut_json %}
                <div class="chart-container">
                    <div id="scope_donut"></div>
                    <script>
                        Plotly.newPlot('scope_donut',
                            {{ donut_json | safe }}.data,
                            {{ donut_json | safe }}.layout,
                            {responsive: true, displayModeBar: false}
                        );
                    </script>
                </div>
                {% endif %}
                {% if waterfall_json %}
                <div class="chart-container">
                    <div id="waterfall"></div>
                    <script>
                        Plotly.newPlot('waterfall',
                            {{ waterfall_json | safe }}.data,
                            {{ waterfall_json | safe }}.layout,
                            {responsive: true, displayModeBar: false}
                        );
                    </script>
                </div>
                {% endif %}
            </div>
        </section>

        {% if top_sources_json %}
        <!-- Top Sources -->
        <section>
            <h2><span class="section-number">{{ section_num('sources') }}.</span> Top Emission Sources</h2>
            <div class="chart-container">
                <div id="top_sources"></div>
                <script>
                    Plotly.newPlot('top_sources',
                        {{ top_sources_json | safe }}.data,
                        {{ top_sources_json | safe }}.layout,
                        {responsive: true, displayModeBar: false}
                    );
                </script>
            </div>
        </section>
        {% endif %}

        {% if category_json %}
        <!-- Category Breakdown -->
        <section>
            <h2><span class="section-number">{{ section_num('category') }}.</span> Category Breakdown</h2>
            <div class="chart-container">
                <div id="category_bar"></div>
                <script>
                    Plotly.newPlot('category_bar',
                        {{ category_json | safe }}.data,
                        {{ category_json | safe }}.layout,
                        {responsive: true, displayModeBar: false}
                    );
                </script>
            </div>
        </section>
        {% endif %}

        {% if scope3_table %}
        <!-- Scope 3 -->
        <section>
            <h2><span class="section-number">{{ section_num('scope3') }}.</span> Scope 3 Breakdown</h2>
            <div class="table-wrapper">
                {{ scope3_table }}
            </div>
            {% if treemap_json %}
            <div class="chart-container" style="margin-top:20px;">
                <div id="scope3_treemap"></div>
                <script>
                    Plotly.newPlot('scope3_treemap',
                        {{ treemap_json | safe }}.data,
                        {{ treemap_json | safe }}.layout,
                        {responsive: true, displayModeBar: false}
                    );
                </script>
            </div>
            {% endif %}
        </section>
        {% endif %}

        {% if gas_table %}
        <!-- Gas Breakdown -->
        <section>
            <h2><span class="section-number">{{ section_num('gas') }}.</span> Emissions by Gas</h2>
            <div class="table-wrapper">
                {{ gas_table }}
            </div>
        </section>
        {% endif %}

        {% if methodology %}
        <!-- Methodology -->
        <section>
            <h2><span class="section-number">{{ section_num('method') }}.</span> Methodology</h2>
            <div class="methodology">
                <h3>GHG Protocol Corporate Accounting &amp; Reporting Standard</h3>
                <ul>
                    <li><strong>Scope 1</strong> &mdash; Direct emissions from owned or controlled sources (combustion, fugitive, process)</li>
                    <li><strong>Scope 2</strong> &mdash; Indirect emissions from purchased electricity, reported as both location-based and market-based per Scope 2 Guidance</li>
                    <li><strong>Scope 3</strong> &mdash; All other indirect emissions across the value chain (15 categories)</li>
                </ul>
                <p><strong>Global Warming Potentials:</strong> IPCC {{ gwp_assessment | upper }} (100-year values). CO2 = 1, CH4 = 28, N2O = 265.</p>
                <p><strong>Report format:</strong> {{ report_format | replace('_', ' ') | title }}</p>
                <p><strong>Emission factors:</strong> EPA Hub, eGRID, DEFRA, USEEIO, Ember, EXIOBASE (967 factors embedded).</p>
            </div>
        </section>
        {% endif %}
    </div>

    <!-- Footer -->
    <div class="footer">
        <div class="footer-brand">GHG Calculator</div>
        <div class="footer-sub">GHG Protocol Corporate Standard &bull; 967 Emission Factors &bull; Open Source</div>
        <div class="footer-links">
            <a href="https://gaiaai.xyz" target="_blank" rel="noopener">gaiaai.xyz</a>
            <span class="sep">&bull;</span>
            <a href="https://x.com/reslashacc" target="_blank" rel="noopener">@reslashacc</a>
            <span class="sep">&bull;</span>
            <a href="https://github.com/gaiaaiagent" target="_blank" rel="noopener">GitHub</a>
        </div>
        <div class="footer-built-by">
            Built by <a href="https://gaiaai.xyz" target="_blank" rel="noopener">Gaia AI</a>
        </div>
    </div>

</body>
</html>"""


def _format_number(value: float) -> str:
    """Format large numbers with appropriate suffixes."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    elif abs(value) >= 1_000:
        return f"{value:,.0f}"
    elif abs(value) >= 1:
        return f"{value:,.1f}"
    else:
        return f"{value:,.2f}"


def _df_to_styled_html(df, highlight_last: bool = True) -> str:
    """Convert a pandas DataFrame to styled HTML matching the dark theme."""
    html = df.to_html(index=False, classes="", border=0)
    return html


class ReportGenerator:
    """Generates HTML reports with tables, charts, and maps."""

    def generate(
        self,
        inventory: InventoryResult,
        config: ReportConfig,
        output_path: Path,
        activities: list[ActivityRecord] | None = None,
    ) -> Path:
        """Generate a full HTML report."""
        # Build tables
        scope_df = tables.scope_summary_table(inventory)
        scope3_df = tables.scope3_breakdown_table(inventory)
        gas_df = tables.gas_breakdown_table(inventory)

        # Build charts
        donut_json = None
        waterfall_json = None
        category_json = None
        treemap_json = None
        top_sources_json = None
        map_json = None
        gauge_json = None

        try:
            fig = charts.scope_donut_chart(inventory)
            donut_json = fig.to_json()
        except Exception:
            pass

        try:
            fig = charts.waterfall_chart(inventory)
            waterfall_json = fig.to_json()
        except Exception:
            pass

        try:
            fig = charts.category_stacked_bar(inventory)
            category_json = fig.to_json()
        except Exception:
            pass

        if inventory.scope3.total_co2e_tonnes > 0:
            try:
                fig = charts.scope3_treemap(inventory)
                treemap_json = fig.to_json()
            except Exception:
                pass

        try:
            fig = charts.top_sources_bar(inventory)
            top_sources_json = fig.to_json()
        except Exception:
            pass

        # Geographic map (needs activities for location data)
        if activities:
            try:
                fig = charts.emissions_map(activities, inventory)
                if fig is not None:
                    map_json = fig.to_json()
            except Exception:
                pass

            try:
                fig = charts.carbon_intensity_gauge(inventory, activities)
                if fig is not None:
                    gauge_json = fig.to_json()
            except Exception:
                pass

        # Section numbering
        section_counter = [0]
        has_map = map_json is not None
        if has_map:
            # Map is section I, so scope starts at II
            section_counter[0] = 1

        _ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}

        def section_num(name: str) -> str:
            section_counter[0] += 1
            return _ROMAN.get(section_counter[0], str(section_counter[0]))

        # Render
        template = Template(_HTML_TEMPLATE)
        template.globals["section_num"] = section_num
        template.globals["format_number"] = _format_number

        html = template.render(
            title=config.title,
            year=inventory.year,
            total_tonnes=inventory.total_co2e_tonnes,
            scope1_tonnes=inventory.scope1.total_co2e_tonnes,
            scope2_tonnes=inventory.scope2_location.total_co2e_tonnes,
            scope3_tonnes=inventory.scope3.total_co2e_tonnes,
            scope_table=_df_to_styled_html(scope_df),
            scope3_table=_df_to_styled_html(scope3_df) if inventory.scope3.total_co2e_tonnes > 0 else "",
            gas_table=_df_to_styled_html(gas_df) if not gas_df.empty else "",
            donut_json=donut_json,
            waterfall_json=waterfall_json,
            category_json=category_json,
            treemap_json=treemap_json,
            top_sources_json=top_sources_json,
            map_json=map_json,
            gauge_json=gauge_json,
            methodology=config.include_methodology,
            gwp_assessment="ar5",
            report_format=config.format.value,
        )

        output_path = Path(output_path)
        output_path.write_text(html)
        return output_path
