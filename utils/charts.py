"""Gráficos reutilizables entre páginas (para no repetir la misma figura)."""

import plotly.graph_objects as go

from utils.theme import SENTIMENT_COLORS, CHROME


def diverging_stacked_bar(
    df, label_col, pos_col="pct_positivo", neu_col="pct_neutro", neg_col="pct_negativo",
    sort_by=None, unit_suffix="%",
) -> go.Figure:
    """Bar divergente centrada en 'neutro' — la forma recomendada por la skill
    dataviz para escalas ordenadas de sentimiento (Likert, positivo/neutro/negativo).
    Espera pos/neu/neg ya en la misma escala (p.ej. 0-100 o 0-1)."""
    sort_by = sort_by or pos_col
    d = df.sort_values(sort_by, ascending=True).reset_index(drop=True)
    neg = d[neg_col].to_numpy()
    neu = d[neu_col].to_numpy()
    pos = d[pos_col].to_numpy()
    labels = d[label_col].to_numpy()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=neg, base=-(neg + neu / 2), orientation="h", name="Negativo",
        marker_color=SENTIMENT_COLORS["Negativo"],
        hovertemplate=f"%{{y}} · Negativo: %{{x:.1f}}{unit_suffix}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=labels, x=neu, base=-(neu / 2), orientation="h", name="Neutro",
        marker_color=SENTIMENT_COLORS["Neutro"],
        hovertemplate=f"%{{y}} · Neutro: %{{x:.1f}}{unit_suffix}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=labels, x=pos, base=neu / 2, orientation="h", name="Positivo",
        marker_color=SENTIMENT_COLORS["Positivo"],
        hovertemplate=f"%{{y}} · Positivo: %{{x:.1f}}{unit_suffix}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=1, line_color=CHROME["baseline"])
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(title=f"% de menciones (centrado en neutro)", ticksuffix=unit_suffix),
        yaxis=dict(title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=60 + 42 * max(len(labels), 1),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig
