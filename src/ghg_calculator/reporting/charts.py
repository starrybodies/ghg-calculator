"""Plotly chart generators for GHG emissions reports."""

import plotly.graph_objects as go

from ..models.activity import ActivityRecord
from ..models.enums import Scope3Category
from ..models.results import InventoryResult

# ── Color palette: green + black ─────────────────────────────────────────────

PALETTE = {
    "green_dark": "#0D1F0D",
    "green_deep": "#1B3A1B",
    "green_primary": "#2D6A2D",
    "green_mid": "#3D8B3D",
    "green_bright": "#4CAF50",
    "green_light": "#81C784",
    "green_pale": "#A5D6A7",
    "green_wash": "#C8E6C9",
    "accent_lime": "#7CB342",
    "accent_emerald": "#00897B",
    "accent_gold": "#C6A700",
    "black": "#0A0A0A",
    "charcoal": "#1A1A1A",
    "gray_dark": "#2C2C2C",
    "gray_mid": "#555555",
    "gray_light": "#888888",
    "white": "#F5F5F0",
    "cream": "#FAFAF5",
}

SCOPE_COLORS = [PALETTE["green_bright"], PALETTE["green_deep"], PALETTE["accent_emerald"]]
SCOPE_COLORS_EXTENDED = [
    PALETTE["green_bright"],
    PALETTE["green_deep"],
    PALETTE["accent_emerald"],
    PALETTE["accent_lime"],
    PALETTE["green_mid"],
    PALETTE["green_pale"],
    PALETTE["accent_gold"],
    PALETTE["green_light"],
]

_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'Playfair Display', 'Georgia', 'Times New Roman', serif", color=PALETTE["cream"], size=13),
    title_font=dict(family="'Playfair Display', 'Georgia', 'Times New Roman', serif", size=20, color=PALETTE["cream"]),
    margin=dict(l=60, r=40, t=60, b=60),
    legend=dict(font=dict(color=PALETTE["cream"]), bgcolor="rgba(0,0,0,0)"),
)


def _apply_layout(fig: go.Figure, **overrides) -> go.Figure:
    """Apply consistent dark theme layout to a figure."""
    layout = {**_LAYOUT_DEFAULTS, **overrides}
    fig.update_layout(**layout)
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.1)",
        tickfont=dict(color=PALETTE["gray_light"]),
        title_font=dict(color=PALETTE["cream"]),
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.1)",
        tickfont=dict(color=PALETTE["gray_light"]),
        title_font=dict(color=PALETTE["cream"]),
    )
    return fig


def scope_donut_chart(inventory: InventoryResult) -> go.Figure:
    """Donut chart showing emission distribution by scope."""
    labels = ["Scope 1", "Scope 2 (Location)", "Scope 3"]
    values = [
        inventory.scope1.total_co2e_tonnes,
        inventory.scope2_location.total_co2e_tonnes,
        inventory.scope3.total_co2e_tonnes,
    ]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(
            colors=SCOPE_COLORS,
            line=dict(color=PALETTE["black"], width=2),
        ),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(color=PALETTE["cream"], size=12),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} tCO2e<br>%{percent}<extra></extra>",
    )])

    total = sum(values)
    fig = _apply_layout(fig,
        title="Emissions by Scope",
        annotations=[dict(
            text=f"<b>{total:,.0f}</b><br><span style='font-size:12px'>tCO2e</span>",
            x=0.5, y=0.5, font=dict(size=22, color=PALETTE["green_bright"], family="'Playfair Display', serif"),
            showarrow=False,
        )],
    )
    return fig


def category_stacked_bar(inventory: InventoryResult) -> go.Figure:
    """Horizontal bar chart of emission categories."""
    categories = []
    values = []
    colors = []

    # Scope 1 by category
    s1_cats: dict[str, float] = {}
    for r in inventory.scope1.results:
        cat = r.scope1_category.name.replace("_", " ").title() if r.scope1_category else "Other"
        s1_cats[cat] = s1_cats.get(cat, 0) + r.total_co2e_tonnes
    for cat, val in sorted(s1_cats.items(), key=lambda x: -x[1]):
        categories.append(f"S1: {cat}")
        values.append(val)
        colors.append(PALETTE["green_bright"])

    categories.append("Scope 2 (Location)")
    values.append(inventory.scope2_location.total_co2e_tonnes)
    colors.append(PALETTE["green_deep"])

    # Scope 3 by category
    s3_cats: dict[str, float] = {}
    for r in inventory.scope3.results:
        if r.scope3_category:
            cat_name = f"S3.{r.scope3_category.value}: {r.scope3_category.name.replace('_', ' ').title()}"
        else:
            cat_name = "S3: Other"
        s3_cats[cat_name] = s3_cats.get(cat_name, 0) + r.total_co2e_tonnes
    ci = 0
    s3_palette = [PALETTE["accent_emerald"], PALETTE["accent_lime"], PALETTE["green_mid"], PALETTE["green_pale"], PALETTE["accent_gold"]]
    for cat, val in sorted(s3_cats.items(), key=lambda x: -x[1]):
        categories.append(cat)
        values.append(val)
        colors.append(s3_palette[ci % len(s3_palette)])
        ci += 1

    fig = go.Figure(data=[go.Bar(
        y=categories,
        x=values,
        orientation="h",
        marker=dict(color=colors, line=dict(color=PALETTE["black"], width=1)),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} tCO2e<extra></extra>",
    )])
    fig = _apply_layout(fig,
        title="Emissions by Category",
        xaxis_title="tCO2e",
        height=max(400, len(categories) * 38 + 120),
        margin=dict(l=240, r=40, t=60, b=60),
    )
    return fig


def waterfall_chart(inventory: InventoryResult) -> go.Figure:
    """Waterfall chart showing buildup from Scope 1 through Scope 3."""
    fig = go.Figure(go.Waterfall(
        x=["Scope 1", "Scope 2 (Location)", "Scope 3", "Total"],
        y=[
            inventory.scope1.total_co2e_tonnes,
            inventory.scope2_location.total_co2e_tonnes,
            inventory.scope3.total_co2e_tonnes,
            0,
        ],
        measure=["relative", "relative", "relative", "total"],
        connector=dict(line=dict(color=PALETTE["gray_mid"], width=1)),
        increasing=dict(marker=dict(color=PALETTE["green_bright"], line=dict(color=PALETTE["black"], width=1))),
        decreasing=dict(marker=dict(color=PALETTE["accent_emerald"], line=dict(color=PALETTE["black"], width=1))),
        totals=dict(marker=dict(color=PALETTE["green_deep"], line=dict(color=PALETTE["green_bright"], width=2))),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} tCO2e<extra></extra>",
    ))
    fig = _apply_layout(fig, title="Emission Buildup by Scope", yaxis_title="tCO2e")
    return fig


def scope3_treemap(inventory: InventoryResult) -> go.Figure:
    """Treemap of Scope 3 categories."""
    labels = []
    values = []
    parents = []
    colors = []

    by_cat: dict[int, float] = {}
    for r in inventory.scope3.results:
        cat_val = r.scope3_category.value if r.scope3_category else 0
        by_cat[cat_val] = by_cat.get(cat_val, 0) + r.total_co2e_tonnes

    labels.append("Scope 3")
    values.append(0)
    parents.append("")
    colors.append(PALETTE["charcoal"])

    treemap_colors = [
        PALETTE["green_bright"], PALETTE["green_deep"], PALETTE["accent_emerald"],
        PALETTE["accent_lime"], PALETTE["green_mid"], PALETTE["green_pale"],
        PALETTE["accent_gold"], PALETTE["green_light"],
    ]

    ci = 0
    for cat in Scope3Category:
        tonnes = by_cat.get(cat.value, 0)
        if tonnes > 0:
            name = f"{cat.value}. {cat.name.replace('_', ' ').title()}"
            labels.append(name)
            values.append(tonnes)
            parents.append("Scope 3")
            colors.append(treemap_colors[ci % len(treemap_colors)])
            ci += 1

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors, line=dict(color=PALETTE["black"], width=2)),
        textfont=dict(family="'Playfair Display', serif", size=14),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} tCO2e<br>%{percentParent:.1%} of Scope 3<extra></extra>",
    ))
    fig = _apply_layout(fig, title="Scope 3 Category Breakdown")
    return fig


# ── Geographic map ────────────────────────────────────────────────────────────

# eGRID subregion approximate centroids (lat, lon)
_EGRID_COORDS: dict[str, tuple[float, float]] = {
    "AKGD": (61.2, -149.9), "AKMS": (58.3, -134.4),
    "AZNM": (33.4, -112.0), "CAMX": (36.8, -119.4),
    "ERCT": (31.5, -97.5), "FRCC": (28.0, -82.5),
    "HIMS": (20.8, -156.3), "HIOA": (21.3, -157.8),
    "MROE": (43.0, -89.4), "MROW": (44.9, -93.3),
    "NEWE": (42.4, -71.4), "NWPP": (46.6, -120.5),
    "NYCW": (40.7, -74.0), "NYLI": (40.8, -73.3),
    "NYUP": (42.7, -75.5), "PRMS": (18.2, -66.5),
    "RFCE": (40.0, -76.3), "RFCM": (42.7, -84.6),
    "RFCW": (40.0, -83.0), "RMPA": (39.7, -105.0),
    "SPNO": (39.1, -95.7), "SPSO": (35.5, -97.5),
    "SRMV": (30.5, -91.2), "SRMW": (38.6, -90.2),
    "SRSO": (33.5, -86.8), "SRTV": (36.2, -86.8),
    "SRVC": (35.8, -79.0),
}

# Country ISO → approximate centroid
_COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "US": (39.8, -98.6), "GB": (54.0, -2.0), "DE": (51.2, 10.4),
    "FR": (46.6, 2.2), "JP": (36.2, 138.3), "CN": (35.9, 104.2),
    "IN": (20.6, 79.0), "BR": (-14.2, -51.9), "AU": (-25.3, 133.8),
    "CA": (56.1, -106.3), "KR": (35.9, 128.0), "IT": (41.9, 12.6),
    "ES": (40.5, -3.7), "MX": (23.6, -102.6), "RU": (61.5, 105.3),
    "ZA": (-30.6, 22.9), "SE": (60.1, 18.6), "NO": (60.5, 8.5),
    "DK": (56.3, 9.5), "FI": (61.9, 25.7), "PL": (51.9, 19.1),
    "NL": (52.1, 5.3), "BE": (50.5, 4.5), "AT": (47.5, 14.6),
    "CH": (46.8, 8.2), "IE": (53.1, -8.0), "PT": (39.4, -8.2),
    "CZ": (49.8, 15.5), "GR": (39.1, 21.8), "SA": (23.9, 45.1),
    "AE": (23.4, 53.8), "SG": (1.4, 103.8), "IS": (64.1, -18.0),
    "NZ": (-40.9, 174.9), "CL": (-35.7, -71.5), "AR": (-38.4, -63.6),
    "CO": (4.6, -74.3), "TH": (15.9, 100.9), "VN": (14.1, 108.3),
    "ID": (-0.8, 113.9), "PH": (12.9, 121.8), "MY": (4.2, 101.9),
    "TW": (23.7, 121.0), "IL": (31.0, 34.9), "EG": (26.8, 30.8),
    "NG": (9.1, 8.7), "KE": (-0.0, 37.9),
}


def emissions_map(activities: list[ActivityRecord], inventory: InventoryResult) -> go.Figure | None:
    """Create a geographic scatter map of emission sources.

    Groups activities by location (eGRID subregion or country) and plots
    bubble markers sized by emission magnitude.
    """
    # Build location → emissions mapping from activities and results
    location_data: dict[str, dict] = {}  # key → {lat, lon, tonnes, names, label}

    # Match activities to results by index/id for emission values
    result_map: dict[str, float] = {}
    for r in inventory.all_results:
        if r.activity_id:
            result_map[r.activity_id] = result_map.get(r.activity_id, 0) + r.total_co2e_tonnes

    for act in activities:
        lat, lon, label = None, None, None

        if act.grid_subregion and act.grid_subregion.upper() in _EGRID_COORDS:
            lat, lon = _EGRID_COORDS[act.grid_subregion.upper()]
            label = f"eGRID: {act.grid_subregion.upper()}"
        elif act.country and act.country.upper() in _COUNTRY_COORDS:
            lat, lon = _COUNTRY_COORDS[act.country.upper()]
            label = act.country.upper()

        if lat is None:
            continue

        # Try to get tonnes from results, fall back to 0
        tonnes = result_map.get(act.id, 0) if act.id else 0

        key = label
        if key not in location_data:
            location_data[key] = {"lat": lat, "lon": lon, "tonnes": 0, "names": [], "label": label}
        location_data[key]["tonnes"] += tonnes
        activity_label = act.name or act.id or f"{act.scope.value}"
        if activity_label not in location_data[key]["names"]:
            location_data[key]["names"].append(activity_label)

    if not location_data:
        return None

    lats = []
    lons = []
    sizes = []
    texts = []
    hover_texts = []

    max_tonnes = max(d["tonnes"] for d in location_data.values()) or 1

    for key, d in sorted(location_data.items(), key=lambda x: -x[1]["tonnes"]):
        lats.append(d["lat"])
        lons.append(d["lon"])
        # Scale bubble size: min 12, max 60
        rel = d["tonnes"] / max_tonnes if max_tonnes > 0 else 0.5
        sizes.append(max(12, int(rel * 55 + 5)))
        texts.append(f"{d['tonnes']:,.0f}")
        sources = "<br>".join(d["names"][:5])
        if len(d["names"]) > 5:
            sources += f"<br>+{len(d['names']) - 5} more"
        hover_texts.append(f"<b>{d['label']}</b><br>{d['tonnes']:,.0f} tCO2e<br><br>{sources}")

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lat=lats,
        lon=lons,
        text=texts,
        hovertext=hover_texts,
        hoverinfo="text",
        mode="markers+text",
        textposition="top center",
        textfont=dict(color=PALETTE["cream"], size=11, family="'Playfair Display', serif"),
        marker=dict(
            size=sizes,
            color=PALETTE["green_bright"],
            opacity=0.7,
            line=dict(color=PALETTE["green_light"], width=1),
            sizemode="diameter",
        ),
    ))

    # Determine map scope
    if all(25 < lat < 50 and -130 < lon < -60 for lat, lon in zip(lats, lons)):
        geo_scope = "usa"
    elif all(-60 < lat < 75 and -130 < lon < 50 for lat, lon in zip(lats, lons)):
        geo_scope = "north america"
    else:
        geo_scope = "world"

    geo_config = dict(
        bgcolor="rgba(0,0,0,0)",
        landcolor=PALETTE["green_dark"],
        oceancolor=PALETTE["charcoal"],
        lakecolor=PALETTE["charcoal"],
        coastlinecolor=PALETTE["green_primary"],
        countrycolor=PALETTE["green_primary"],
        subunitcolor=PALETTE["green_deep"],
        showland=True,
        showocean=True,
        showlakes=True,
        showcoastlines=True,
        showcountries=True,
        coastlinewidth=0.5,
        countrywidth=0.3,
    )

    if geo_scope == "usa":
        geo_config["scope"] = "usa"
        geo_config["showsubunits"] = True
        geo_config["subunitwidth"] = 0.3
    elif geo_scope == "north america":
        geo_config["scope"] = "north america"
    else:
        geo_config["projection_type"] = "natural earth"

    fig.update_layout(
        title=dict(text="Geographic Distribution of Emissions", font=dict(size=20, color=PALETTE["cream"], family="'Playfair Display', serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Playfair Display', serif", color=PALETTE["cream"]),
        geo=geo_config,
        margin=dict(l=0, r=0, t=50, b=0),
        height=500,
    )
    return fig


# ── Gauge chart ───────────────────────────────────────────────────────────────

def carbon_intensity_gauge(inventory: InventoryResult, activities: list[ActivityRecord]) -> go.Figure | None:
    """Gauge showing total emissions with context markers."""
    total = inventory.total_co2e_tonnes
    if total <= 0:
        return None

    # Auto-scale the gauge range
    if total < 100:
        max_val = 200
    elif total < 10000:
        max_val = total * 2.5
    elif total < 1000000:
        max_val = total * 2
    else:
        max_val = total * 1.5

    # Car equivalents (4.6 tCO2e/car/year)
    car_equiv = total / 4.6

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        number=dict(
            font=dict(size=42, color=PALETTE["green_bright"], family="'Playfair Display', serif"),
            suffix=" tCO2e",
        ),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(color=PALETTE["gray_light"])),
            bar=dict(color=PALETTE["green_bright"]),
            bgcolor=PALETTE["charcoal"],
            bordercolor=PALETTE["green_primary"],
            borderwidth=2,
            steps=[
                dict(range=[0, max_val * 0.33], color=PALETTE["green_dark"]),
                dict(range=[max_val * 0.33, max_val * 0.66], color=PALETTE["green_deep"]),
                dict(range=[max_val * 0.66, max_val], color="rgba(45,106,45,0.3)"),
            ],
        ),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Playfair Display', serif", color=PALETTE["cream"]),
        margin=dict(l=30, r=30, t=30, b=10),
        height=280,
        annotations=[dict(
            text=f"Equivalent to {car_equiv:,.0f} passenger cars/year",
            x=0.5, y=-0.05, font=dict(size=13, color=PALETTE["green_light"], family="'Playfair Display', serif"),
            showarrow=False, xref="paper", yref="paper",
        )],
    )
    return fig


# ── Source-level horizontal bar ───────────────────────────────────────────────

def top_sources_bar(inventory: InventoryResult, n: int = 10) -> go.Figure:
    """Top N emission sources as a horizontal bar chart."""
    source_data: list[tuple[str, float]] = []
    for r in inventory.all_results:
        if r.scope2_method and r.scope2_method.value == "market_based":
            continue
        label = r.activity_name or r.activity_id or f"{r.scope.value}"
        # Truncate long names
        if len(label) > 60:
            label = label[:57] + "..."
        source_data.append((label, r.total_co2e_tonnes))

    # Merge duplicates
    merged: dict[str, float] = {}
    for label, val in source_data:
        merged[label] = merged.get(label, 0) + val

    sorted_sources = sorted(merged.items(), key=lambda x: x[1])[-n:]
    labels = [s[0] for s in sorted_sources]
    values = [s[1] for s in sorted_sources]

    # Color gradient
    n_items = len(values)
    max_v = max(values) if values else 1
    colors = []
    for v in values:
        intensity = v / max_v
        r_val = int(13 + intensity * (76 - 13))
        g_val = int(31 + intensity * (175 - 31))
        b_val = int(13 + intensity * (80 - 13))
        colors.append(f"rgb({r_val},{g_val},{b_val})")

    fig = go.Figure(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(color=colors, line=dict(color=PALETTE["black"], width=1)),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} tCO2e<extra></extra>",
    ))

    fig = _apply_layout(fig,
        title=f"Top {min(n, len(labels))} Emission Sources",
        xaxis_title="tCO2e",
        height=max(350, len(labels) * 38 + 120),
        margin=dict(l=320, r=40, t=60, b=60),
    )
    return fig


# ── Existing utilities ────────────────────────────────────────────────────────

def trend_line_chart(inventories: list[InventoryResult], target_year: int | None = None, target_value: float | None = None) -> go.Figure:
    """Line chart showing multi-year trend with optional target."""
    years = [inv.year or i for i, inv in enumerate(inventories)]
    totals = [inv.total_co2e_tonnes for inv in inventories]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=totals, mode="lines+markers", name="Actual",
        line=dict(color=PALETTE["green_bright"], width=3),
        marker=dict(color=PALETTE["green_bright"], size=10, line=dict(color=PALETTE["black"], width=2)),
    ))

    if target_year and target_value:
        fig.add_trace(go.Scatter(
            x=[years[0], target_year],
            y=[totals[0], target_value],
            mode="lines",
            name="Target Path",
            line=dict(dash="dash", color=PALETTE["accent_gold"], width=2),
        ))

    fig = _apply_layout(fig, title="Emissions Trend", xaxis_title="Year", yaxis_title="tCO2e")
    return fig


def intensity_chart(inventories: list[InventoryResult], denominators: list[float], denominator_label: str = "Revenue ($M)") -> go.Figure:
    """Emission intensity chart (tCO2e per unit of business metric)."""
    years = [inv.year or i for i, inv in enumerate(inventories)]
    intensities = [
        inv.total_co2e_tonnes / d if d > 0 else 0
        for inv, d in zip(inventories, denominators)
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=[inv.total_co2e_tonnes for inv in inventories],
        name="Absolute (tCO2e)", yaxis="y",
        marker=dict(color=PALETTE["green_bright"]),
    ))
    fig.add_trace(go.Scatter(
        x=years, y=intensities, mode="lines+markers",
        name=f"Intensity (tCO2e/{denominator_label})", yaxis="y2",
        line=dict(color=PALETTE["accent_gold"], width=2),
    ))

    fig = _apply_layout(fig,
        title="Absolute vs Intensity Emissions",
        yaxis=dict(title="tCO2e"),
        yaxis2=dict(title=f"tCO2e per {denominator_label}", overlaying="y", side="right"),
    )
    return fig
