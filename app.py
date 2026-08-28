"""
TuriSense — Cuadro de mando (Rol 6)
Prototipo con datos de prueba — Vista general.

Ejecutar con:  streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.mock_data import (
    get_aspect_national_stats, generate_absa_breakdown, CORPUS_TOTAL_RESENAS,
    CORPUS_RESENAS_CON_ASPECTO, CORPUS_PARES_ASPECTO_SENTIMIENTO, CARDIFF_VALIDATION,
    COBERTURA_DICCIONARIO, PLATFORM_VOLUME_REAL,
)
from utils.theme import apply_plotly_template, SEQUENTIAL_BLUE, SENTIMENT_COLORS, CHROME
from utils.components import sidebar_filters, apply_filters, render_top_caveats, render_mock_badge

st.set_page_config(page_title="TuriSense · Vista general", layout="wide")
apply_plotly_template()

st.title("TuriSense — Cuadro de mando")
st.caption(
    "Prototipo (Rol 6) · construido con datos de prueba, listo para enchufar los datos reales "
    "conforme lleguen (índice de la Persona 5, motor de recomendación, parquet del Rol 3)."
)

render_top_caveats()

df_absa = generate_absa_breakdown()
filters = sidebar_filters(df_absa)
df_f = apply_filters(df_absa, filters)

# ---------------------------------------------------------------------------
# KPI row — cifras reales agregadas (no mock)
# ---------------------------------------------------------------------------
st.subheader("Cifras clave del corpus (reales, agregadas — Roles 1 y 3)")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Reseñas totales", f"{CORPUS_TOTAL_RESENAS:,}".replace(",", "."))
c2.metric(
    "Con aspecto detectado",
    f"{CORPUS_RESENAS_CON_ASPECTO:,}".replace(",", "."),
    help="Cobertura del diccionario ABSA sobre el corpus completo.",
)
c3.metric("Cobertura ABSA", f"{COBERTURA_DICCIONARIO:.1%}")
c4.metric(
    "Acuerdo humano (κ sentimiento)", f"{CARDIFF_VALIDATION['kappa_sentimiento']:.3f}",
    help="Kappa de Cohen de la muestra Gold (Rol 3) — 'casi perfecto' según la escala estándar.",
)
c5.metric(
    "Recall de negativo (Cardiff)", f"{CARDIFF_VALIDATION['recall_negativo']:.1%}",
    help="De 39 reseñas negativas reales en la muestra Gold, Cardiff solo detectó 10. Ver aviso arriba.",
    delta="punto ciego conocido", delta_color="inverse",
)

st.divider()

# ---------------------------------------------------------------------------
# Tendencia temporal del sentimiento (datos de prueba, filtrable)
# ---------------------------------------------------------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("Evolución del sentimiento en el tiempo")
    render_mock_badge("Desglose mensual — datos de prueba, calibrados sobre las cifras nacionales reales")

    trend = (
        df_f.groupby("mes")[["n_positivo", "n_neutro", "n_negativo"]].sum().reset_index()
    )
    trend["total"] = trend[["n_positivo", "n_neutro", "n_negativo"]].sum(axis=1)
    for col, label in [("n_positivo", "pct_positivo"), ("n_neutro", "pct_neutro"), ("n_negativo", "pct_negativo")]:
        trend[label] = np.where(trend["total"] > 0, 100 * trend[col] / trend["total"], np.nan)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["mes"], y=trend["pct_positivo"], name="Positivo", stackgroup="one",
        line=dict(width=1, color=SENTIMENT_COLORS["Positivo"]), fillcolor=SENTIMENT_COLORS["Positivo"],
        hovertemplate="Positivo: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=trend["mes"], y=trend["pct_neutro"], name="Neutro", stackgroup="one",
        line=dict(width=1, color=SENTIMENT_COLORS["Neutro"]), fillcolor=SENTIMENT_COLORS["Neutro"],
        hovertemplate="Neutro: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=trend["mes"], y=trend["pct_negativo"], name="Negativo", stackgroup="one",
        line=dict(width=1, color=SENTIMENT_COLORS["Negativo"]), fillcolor=SENTIMENT_COLORS["Negativo"],
        hovertemplate="Negativo: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="% de menciones", ticksuffix="%", range=[0, 100]),
        xaxis=dict(title=None),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=380,
    )
    st.plotly_chart(fig, width='stretch')

with right:
    st.subheader("Volumen por plataforma")
    st.caption("Cifras reales (Rol 1) — nº de pares aspecto-sentimiento")
    plat = pd.Series(PLATFORM_VOLUME_REAL).sort_values(ascending=True)
    fig2 = go.Figure(go.Bar(
        x=plat.values, y=plat.index, orientation="h",
        marker_color=SEQUENTIAL_BLUE[7],
        text=[f"{v:,}".replace(",", ".") for v in plat.values],
        textposition="outside", textfont=dict(color=CHROME["text_secondary"]),
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    fig2.update_layout(
        xaxis=dict(title=None, type="log", showticklabels=False),
        yaxis=dict(title=None),
        height=380, margin=dict(l=10, r=60, t=10, b=10),
    )
    st.plotly_chart(fig2, width='stretch')

st.divider()

# ---------------------------------------------------------------------------
# Volumen por región (datos de prueba)
# ---------------------------------------------------------------------------
st.subheader("Volumen de menciones por región")
render_mock_badge("Distribución regional — datos de prueba")

by_ccaa = df_f.groupby("ccaa")["n_total"].sum().sort_values(ascending=True)
fig3 = go.Figure(go.Bar(
    x=by_ccaa.values, y=by_ccaa.index, orientation="h",
    marker_color=SEQUENTIAL_BLUE[6],
    hovertemplate="%{y}: %{x:,}<extra></extra>",
))
fig3.update_layout(
    xaxis=dict(title="Pares aspecto-sentimiento"), yaxis=dict(title=None),
    height=520, margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig3, width='stretch')

st.divider()
st.subheader("Qué hay ya conectado, y qué falta")
st.markdown(
    "- **✅ Datos oficiales de turismo (Rol 4)** — 11 indicadores mensuales CCAA×mes + contexto "
    "estructural anual, ya conectados. Ver la pestaña **Datos oficiales**.\n"
    "- **✅ Opinión real por región (Rol 4)** — sentimiento agregado por fuente×CCAA×mes(×aspecto), "
    "ya conectado en la pestaña **ABSA por aspecto** → *Datos reales del Rol 4*. Todavía marcado "
    "como exploratorio por el propio Rol 4 (`eligible_final=False` en toda la tabla) — ver el "
    "aviso en esa pestaña.\n"
    "- **⏳ Opportunity Score real** (Persona 5, apartado 5.1) — este prototipo usa un marcador "
    "de posición ilustrativo (pestaña *Motor de recomendación*), no la fórmula final.\n"
    "- **⏳ Parquet real del Rol 3** (`reviews_aspectos_geo.parquet`, 4.099.623 filas, a nivel de "
    "reseña individual) — sustituirá el desglose por región/plataforma/mes que en la vista general "
    "sigue siendo de prueba."
)
