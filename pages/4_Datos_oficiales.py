"""Datos oficiales de turismo (Rol 4) — indicadores mensuales CCAA×mes y
contexto estructural anual. Real, no de prueba."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.real_data import load_oficial, load_catalogo, load_contexto_anual
from utils.theme import apply_plotly_template, ccaa_color, CCAA_COLORS_DEFAULT, CATEGORICAL, CHROME
from utils.components import sidebar_filters
from data.mock_data import generate_absa_breakdown

st.set_page_config(page_title="TuriSense · Datos oficiales", layout="wide")
apply_plotly_template()

st.title("Datos oficiales de turismo (Rol 4)")
st.caption(
    "11 indicadores mensuales por CCAA (INE, AENA, AEMET, Frontur, Egatur, Eurostat, BOE) más "
    "contexto estructural anual. Real — `R4_DASHBOARD_OFICIAL_TIDY_CCAA_MES.parquet` (17.556 filas) "
    "y `R4_DASHBOARD_CONTEXTO_ANUAL_CCAA.parquet` (133 filas)."
)

# Reutilizamos el filtro de región de la barra lateral para que sea coherente
# con el resto de la app; no reutilizamos su rango de fechas (pensado para los
# 24 meses de prueba de ABSA) porque los datos oficiales cubren 2019-2025.
df_absa_mock = generate_absa_breakdown()
filters = sidebar_filters(df_absa_mock)

df_of = load_oficial()
catalogo = load_catalogo()

indicadores = (
    df_of[["indicator_id", "indicator_label", "family", "quality_tier", "unit",
           "source_organization", "source_url", "tooltip"]]
    .drop_duplicates("indicator_id")
    .sort_values(["family", "indicator_label"])
)

st.subheader("1. Indicador mensual")

label_options = [f"{r.indicator_label}  ·  {r.family}" for r in indicadores.itertuples()]
choice = st.selectbox("Indicador", options=label_options, index=0)
row = indicadores.iloc[label_options.index(choice)]
indicator_id = row["indicator_id"]

badge_map = {"A": "🟢 Calidad A", "B": "🟠 Calidad B", "C": "🔴 Calidad C"}
c1, c2, c3 = st.columns([1, 1, 2])
c1.metric("Calidad del dato", badge_map.get(row["quality_tier"], row["quality_tier"]))
c2.metric("Unidad", row["unit"])
c3.metric("Fuente", row["source_organization"])
st.caption(f"{row['tooltip']}  ·  [Fuente original]({row['source_url']})")

d = df_of[df_of["indicator_id"] == indicator_id].copy()

flags_presentes = []
if d["provisional_flag"].any():
    flags_presentes.append("⚠️ contiene periodos **provisionales**")
if d["method_break_flag"].any():
    flags_presentes.append("⚠️ **ruptura de metodología** en algún periodo")
if d["experimental_flag"].any():
    flags_presentes.append("⚠️ estadística **experimental**")
if flags_presentes:
    st.warning(" · ".join(flags_presentes) + " — revisar antes de interpretar picos o caídas como reales.")

ccaas_disponibles = sorted(d["ccaa"].unique())
default_sel = [c for c in CCAA_COLORS_DEFAULT if c in ccaas_disponibles][:8]
seleccion = st.multiselect(
    "Comparar regiones (máx. recomendado: 8, para que los colores sigan siendo distinguibles)",
    options=ccaas_disponibles, default=default_sel or ccaas_disponibles[:6],
)
if len(seleccion) > 8:
    st.caption(
        "🎨 Mostrando más de 8 regiones a la vez: las que no tienen un color identitario asignado "
        "se pintan en gris para no generar tonos indistinguibles."
    )

d_sel = d[d["ccaa"].isin(seleccion)].sort_values("period_start")

fig = go.Figure()
for ccaa in seleccion:
    dd = d_sel[d_sel["ccaa"] == ccaa]
    if dd.empty:
        continue
    fig.add_trace(go.Scatter(
        x=dd["period_start"], y=dd["value"], name=ccaa, mode="lines",
        line=dict(width=2, color=ccaa_color(ccaa)),
        hovertemplate=f"{ccaa}<br>%{{x|%b %Y}}: %{{y:.2f}} {row['unit']}<extra></extra>",
    ))
fig.update_layout(
    yaxis=dict(title=row["unit"]), xaxis=dict(title=None),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    height=440,
)
st.plotly_chart(fig, width='stretch')

with st.expander("Ver tabla (con estado del periodo, percentil, anomalía-z y variación interanual)"):
    cols = ["ccaa", "period", "value", "position_pct", "anomaly_z", "yoy_change",
            "period_quality_status", "analysis_regime"]
    st.dataframe(
        d_sel[cols].rename(columns={
            "ccaa": "CCAA", "period": "Periodo", "value": "Valor",
            "position_pct": "Percentil (%)", "anomaly_z": "Anomalía-z",
            "yoy_change": "Var. interanual", "period_quality_status": "Estado del periodo",
            "analysis_regime": "Régimen",
        }),
        width='stretch', hide_index=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Contexto estructural ANUAL — deliberadamente separado del bloque mensual de
# arriba (regla no negociable del Rol 4: no presentar datos anuales como
# mensuales).
# ---------------------------------------------------------------------------
st.subheader("2. Contexto estructural anual (no mensual)")
st.caption(
    "Una fila por CCAA y año — escala vs. intensidad turística, estacionalidad y concentración. "
    "No interpolar a meses: úsalo como retrato de fondo de cada región, no como serie temporal fina."
)

df_ctx = load_contexto_anual()
years = sorted(df_ctx["year"].unique())
year_sel = st.select_slider("Año", options=years, value=years[-1])
d_ctx = df_ctx[df_ctx["year"] == year_sel]

quadrant_colors = {
    "escala_alta__intensidad_alta": CATEGORICAL[0],
    "escala_alta__intensidad_moderada": CATEGORICAL[2],
    "escala_moderada__intensidad_alta": CATEGORICAL[3],
    "escala_moderada__intensidad_moderada": CHROME["muted"],
}
quadrant_labels = {
    "escala_alta__intensidad_alta": "Escala alta · Intensidad alta",
    "escala_alta__intensidad_moderada": "Escala alta · Intensidad moderada",
    "escala_moderada__intensidad_alta": "Escala moderada · Intensidad alta",
    "escala_moderada__intensidad_moderada": "Escala moderada · Intensidad moderada",
}

fig2 = go.Figure()
for q, color in quadrant_colors.items():
    dq = d_ctx[d_ctx["scale_intensity_quadrant"] == q]
    if dq.empty:
        continue
    fig2.add_trace(go.Scatter(
        x=dq["regulated_scale_percentile"], y=dq["regulated_intensity_percentile"],
        mode="markers+text", text=dq["ccaa"], textposition="top center",
        textfont=dict(size=10, color=CHROME["text_secondary"]),
        marker=dict(size=12, color=color, line=dict(width=1, color=CHROME["surface"])),
        name=quadrant_labels[q],
        hovertemplate="%{text}<br>Percentil escala: %{x:.0%}<br>Percentil intensidad: %{y:.0%}<extra></extra>",
    ))
fig2.update_layout(
    xaxis=dict(title="Percentil de escala (volumen de pernoctaciones)", tickformat=".0%", range=[-0.05, 1.05]),
    yaxis=dict(title="Percentil de intensidad (ocupación)", tickformat=".0%", range=[-0.05, 1.05]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    height=520,
)
st.plotly_chart(fig2, width='stretch')

with st.expander("Ver tabla de contexto anual completa"):
    cols2 = ["ccaa", "regulated_overnights_annual_total", "hotel_occupancy_annual_weighted_pct",
             "regulated_overnights_peak_month_label", "regulated_overnights_top3_share",
             "regulated_overnights_hhi_normalized", "scale_intensity_quadrant"]
    st.dataframe(
        d_ctx[cols2].rename(columns={
            "ccaa": "CCAA", "regulated_overnights_annual_total": "Pernoctaciones (año)",
            "hotel_occupancy_annual_weighted_pct": "Ocupación hotelera media (%)",
            "regulated_overnights_peak_month_label": "Mes pico",
            "regulated_overnights_top3_share": "% en los 3 meses top",
            "regulated_overnights_hhi_normalized": "Concentración (HHI norm.)",
            "scale_intensity_quadrant": "Cuadrante",
        }),
        width='stretch', hide_index=True,
    )

st.info(
    "**Para qué sirve esto en el proyecto**: es el contexto que pidió el Rol 4 para contrastar el "
    "sentimiento de las reseñas con lo que pasó de verdad — si el sentimiento sobre una región cae "
    "un mes, ¿coincide con una anomalía climática, una caída de ocupación real, o parece un fallo "
    "del modelo? Cruce pendiente: todavía no se combina automáticamente con las páginas de ABSA."
)
