"""Chart builders for PIMCO ABS Intelligence Platform."""
import plotly.graph_objects as go
import pandas as pd

NAVY   = "#0f1d2f"
SLATE  = "#64748b"
BORDER = "#e2e8f0"
WHITE  = "#ffffff"
GRID   = "#f1f5f9"

# Stable asset-class colors used consistently across asset-class charts.
ASSET_COLORS = {
    "auto_loans": "#244B78",
    "auto_loans_subprime": "#66897C",
    "cmbs": "#B18B55",
    "device_payment_revolving": "#77768D",
    "credit_card_revolving": "#6E91A6",
    "auto_leases": "#A3706D",
    "motorcycle_loans": "#789477",
}
PALETTE = list(ASSET_COLORS.values())

ASSET_LABELS = {
    "auto_loans":               "Auto Loans",
    "auto_loans_subprime":      "Subprime Auto",
    "cmbs":                     "CMBS",
    "device_payment_revolving": "Device Payment",
    "credit_card_revolving":    "Credit Card",
    "auto_leases":              "Auto Leases",
    "motorcycle_loans":         "Motorcycle",
}

_BASE = dict(
    paper_bgcolor=WHITE, plot_bgcolor=WHITE,
    font=dict(family="Inter, sans-serif", color=SLATE, size=12),
    showlegend=False,
)


def asset_donut(index: pd.DataFrame) -> go.Figure:
    counts = index["asset_type"].value_counts()
    labels = [ASSET_LABELS.get(k, k) for k in counts.index]
    fig = go.Figure(go.Pie(
        labels=labels, values=counts.values,
        hole=0.62,
        textinfo="none",
        textfont=dict(size=11, color=SLATE),
        marker=dict(colors=[ASSET_COLORS.get(key, SLATE) for key in counts.index], line=dict(color=WHITE, width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} filings (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        height=285,
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        font=dict(family="Inter, sans-serif", color=SLATE, size=12),
        showlegend=True,
        margin=dict(t=18, b=18, l=10, r=145),
        legend=dict(
            orientation="v", x=1.02, y=0.5, xanchor="left",
            font=dict(size=11, color=SLATE),
            bgcolor="rgba(0,0,0,0)",
            itemsizing="constant",
        ),
        annotations=[
            dict(x=0.5, y=0.54, text=f"<b>{len(index):,}</b>", showarrow=False,
                 font=dict(family="Inter, sans-serif", size=25, color="#172B45")),
            dict(x=0.5, y=0.43, text="filings", showarrow=False,
                 font=dict(family="Inter, sans-serif", size=11, color=SLATE)),
        ],
    )
    return fig


def principal_by_asset(index: pd.DataFrame) -> go.Figure:
    df = index.copy()
    df["p"] = pd.to_numeric(
        df["aggregate_principal_amount"].astype(str).str.replace(r"[$,]", "", regex=True),
        errors="coerce",
    )
    grp = df.groupby("asset_type")["p"].sum().sort_values(ascending=True) / 1e9
    labels = [ASSET_LABELS.get(k, k) for k in grp.index]
    colors = [ASSET_COLORS.get(key, SLATE) for key in grp.index]
    fig = go.Figure(go.Bar(
        x=grp.values.tolist(), y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>$%{x:.1f}B<extra></extra>",
        text=[f"${v:.1f}B" for v in grp.values],
        textposition="outside",
        textfont=dict(size=11, color=SLATE),
    ))
    max_val = grp.max() if len(grp) else 1
    fig.update_layout(
        height=285,
        **_BASE,
        margin=dict(t=10, b=10, l=10, r=70),
        xaxis=dict(
            showgrid=False, showticklabels=False, title="",
            range=[0, max_val * 1.22],
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color=SLATE), title=""),
        bargap=0.35,
    )
    return fig


def principal_by_year(index: pd.DataFrame) -> go.Figure:
    df = index.copy()
    df["p"] = pd.to_numeric(
        df["aggregate_principal_amount"].astype(str).str.replace(r"[$,]", "", regex=True),
        errors="coerce",
    )
    df["year"] = df["filing_date"].str[:4]
    grp = df.groupby("year")["p"].sum().sort_index() / 1e9
    years = grp.index.tolist()
    fig = go.Figure(go.Scatter(
        x=years, y=grp.values.tolist(),
        mode="lines+markers",
        line=dict(color=PALETTE[0], width=2.5),
        marker=dict(color=PALETTE[0], size=7, line=dict(color=WHITE, width=2)),
        fill="tozeroy",
        fillcolor="rgba(36,75,120,0.08)",
        hovertemplate="<b>%{x}</b><br>$%{y:.1f}B<extra></extra>",
    ))
    fig.update_layout(
        height=230,
        **_BASE,
        margin=dict(t=10, b=36, l=54, r=16),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11, color=SLATE),
            title="",
            tickmode="array",
            tickvals=years,
            ticktext=[str(y) for y in years],
        ),
        yaxis=dict(
            gridcolor=GRID,
            tickfont=dict(size=11, color=SLATE),
            title="",
            tickprefix="$", ticksuffix="B",
        ),
    )
    return fig


def apr_by_asset(index: pd.DataFrame) -> go.Figure:
    df = index.copy()
    df["apr"] = pd.to_numeric(df["wa_apr"], errors="coerce")
    grp = df.groupby("asset_type")["apr"].mean().dropna().sort_values(ascending=False)
    labels = [ASSET_LABELS.get(k, k) for k in grp.index]
    colors = [ASSET_COLORS.get(key, SLATE) for key in grp.index]
    fig = go.Figure(go.Bar(
        x=labels, y=grp.values.tolist(),
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>WA APR: %{y:.2f}%<extra></extra>",
        text=[f"{v:.1f}%" for v in grp.values],
        textposition="outside",
        textfont=dict(size=11, color=SLATE),
    ))
    max_val = grp.max() if len(grp) else 1
    fig.update_layout(
        height=230,
        **_BASE,
        margin=dict(t=24, b=72, l=44, r=16),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11, color=SLATE),
            title="",
            tickangle=-30,
        ),
        yaxis=dict(
            gridcolor=GRID,
            tickfont=dict(size=11, color=SLATE),
            title="",
            ticksuffix="%",
            range=[0, max_val * 1.2],
        ),
        bargap=0.38,
    )
    return fig


def issuer_activity(index: pd.DataFrame) -> go.Figure:
    """Horizontal bar: filing count per issuer, sorted descending."""
    SHORT = {
        "AFS_SENSUB_CORP_": "AFS SenSub",
        "Ally_Auto_Assets_LLC": "Ally Auto",
        "AMERICAN_EXPRESS_CREDIT_ACCOUNT_MASTER_TRUST": "Amex",
        "AMERICAN_HONDA_RECEIVABLES_LLC": "Honda",
        "BMW_AUTO_LEASING_LLC": "BMW",
        "Bridgecrest_Auto_Funding_LLC": "Bridgecrest",
        "CARMAX_AUTO_FUNDING_LLC": "CarMax",
        "FORD_CREDIT_AUTO_RECEIVABLES_TWO_LLC": "Ford Credit",
        "HARLEY-DAVIDSON_CUSTOMER_FUNDING_CORP_": "Harley-Davidson",
        "HYUNDAI_ABS_FUNDING_LLC": "Hyundai",
        "SANTANDER_DRIVE_AUTO_RECEIVABLES_LLC": "Santander",
        "TOYOTA_AUTO_FINANCE_RECEIVABLES_LLC": "Toyota",
        "Verizon_ABS_II_LLC": "Verizon",
        "WELLS_FARGO_COMMERCIAL_MORTGAGE_SECURITIES_INC": "Wells Fargo CMBS",
        "WORLD_OMNI_AUTO_RECEIVABLES_LLC": "World Omni",
    }
    counts = index["company"].value_counts().sort_values(ascending=True)
    labels = [SHORT.get(c, c.replace("_", " ").title()) for c in counts.index]
    colors = [SLATE] * len(counts)
    fig = go.Figure(go.Bar(
        x=counts.values.tolist(), y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x} filings<extra></extra>",
        text=counts.values.tolist(),
        textposition="outside",
        textfont=dict(size=11, color=SLATE),
    ))
    max_val = counts.max() if len(counts) else 1
    fig.update_layout(
        height=max(280, len(counts) * 22),
        **_BASE,
        margin=dict(t=10, b=10, l=10, r=40),
        xaxis=dict(
            showgrid=False, showticklabels=False, title="",
            range=[0, max_val * 1.18],
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color=SLATE), title=""),
        bargap=0.3,
    )
    return fig


def fico_distribution(index: pd.DataFrame) -> go.Figure:
    """Scatter: WA FICO vs WA APR, coloured by asset type."""
    df = index.copy()
    df["fico"] = pd.to_numeric(df["wa_fico"], errors="coerce")
    df["apr"]  = pd.to_numeric(df["wa_apr"],  errors="coerce")
    df = df.dropna(subset=["fico", "apr"])
    if df.empty:
        fig = go.Figure()
        fig.update_layout(height=230, **_BASE, margin=dict(t=10, b=10, l=10, r=10))
        return fig

    asset_types = df["asset_type"].unique().tolist()
    color_map = {a: ASSET_COLORS.get(a, SLATE) for a in asset_types}

    fig = go.Figure()
    for atype in asset_types:
        sub = df[df["asset_type"] == atype]
        fig.add_trace(go.Scatter(
            x=sub["fico"], y=sub["apr"],
            mode="markers",
            name=ASSET_LABELS.get(atype, atype),
            marker=dict(color=color_map[atype], size=7, opacity=0.75,
                        line=dict(color=WHITE, width=1)),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "FICO: %{x:.0f}<br>"
                "APR: %{y:.2f}%<extra></extra>"
            ),
            text=sub["company"].str.replace("_", " "),
        ))
    fig.update_layout(
        height=230,
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        font=dict(family="Inter, sans-serif", color=SLATE, size=12),
        showlegend=True,
        margin=dict(t=10, b=36, l=54, r=10),
        legend=dict(
            font=dict(size=10, color=SLATE),
            bgcolor="rgba(0,0,0,0)",
            orientation="h", x=0, y=-0.22,
        ),
        xaxis=dict(
            gridcolor=GRID, tickfont=dict(size=11, color=SLATE),
            title=dict(text="WA FICO", font=dict(size=11, color=SLATE)),
        ),
        yaxis=dict(
            gridcolor=GRID, tickfont=dict(size=11, color=SLATE),
            title=dict(text="WA APR (%)", font=dict(size=11, color=SLATE)),
            ticksuffix="%",
        ),
    )
    return fig
