"""Por región y por tipo de establecimiento — incluye el marcador de posición
del Opportunity Score (pendiente de la Persona 5)."""

import plotly.graph_objects as go
import streamlit as st

from data.mock_data import generate_places, opportunity_score_placeholder, generate_absa_breakdown
from utils.theme import apply_plotly_template, SEQUENTIAL_BLUE, CATEGORY_COLORS, DIVERGING_NEGATIVE, CHROME
from utils.components import sidebar_filters, apply_filters, render_top_caveats, render_mock_badge

st.set_page_config(page_title="TuriSense · Por región", layout="wide")
apply_plotly_template()

st.title("Por región y por tipo de establecimiento")
render_top_caveats()

# Los filtros globales viven en generate_absa_breakdown (para que persistan
# entre páginas); esta página solo usa el filtro de región de ese mismo estado.
df_absa = generate_absa_breakdown()
filters = sidebar_filters(df_absa)

df_places = generate_places()
df_places = df_places[df_places["ccaa"].isin(filters["ccaas"])]
df_opp = opportunity_score_placeholder(df_places)

st.info(
    "Esta pantalla usa un catálogo sintético de ~260 lugares (no las 4,14M reseñas reales) "
    "para poder mostrar ya la granularidad **por lugar individual** que pidió el Rol 3 para el "
    "motor de recomendación. Solo se aplica el filtro de región de la barra lateral; "
    "plataforma/aspecto/fecha no tienen equivalente en esta tabla de prueba."
)

tab_region, tab_tipo = st.tabs(["Por región", "Por tipo de establecimiento"])

with tab_region:
    render_mock_badge("Opportunity Score — MARCADOR DE POSICIÓN, no la fórmula final de la Persona 5")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Opportunity Score medio (mock) por región**")
        by_ccaa_opp = df_opp.groupby("ccaa")["opportunity_score_mock"].mean().sort_values(ascending=True)
        fig = go.Figure(go.Bar(
            x=by_ccaa_opp.values, y=by_ccaa_opp.index, orientation="h",
            marker_color=SEQUENTIAL_BLUE[7],
            hovertemplate="%{y}: %{x:.2f}<extra></extra>",
        ))
        fig.update_layout(xaxis=dict(title="Opportunity Score (mock, 0–1)"), yaxis=dict(title=None), height=520)
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.markdown("**Sentimiento sobre Masificación por región**")
        st.caption("Datos de prueba, con presión de masificación más alta en destinos de mayor afluencia.")
        by_ccaa_mas = (
            (1 - df_opp.groupby("ccaa")["sentimiento_masificacion"].mean())
            .sort_values(ascending=True)
        )
        fig2 = go.Figure(go.Bar(
            x=by_ccaa_mas.values, y=by_ccaa_mas.index, orientation="h",
            marker_color=DIVERGING_NEGATIVE,
            hovertemplate="%{y}: %{x:.1%} negativo<extra></extra>",
        ))
        fig2.update_layout(
            xaxis=dict(title="% aprox. de sentimiento negativo sobre masificación", tickformat=".0%"),
            yaxis=dict(title=None), height=520,
        )
        st.plotly_chart(fig2, width='stretch')

    st.markdown("**Lugares con mayor riesgo de masificación (mock)**")
    st.caption("Volumen relativo alto dentro de su categoría+territorio y sentimiento de masificación bajo.")
    riesgo = (
        df_opp[df_opp["riesgo_masificacion_mock"]]
        .sort_values("volumen_relativo", ascending=False)
        .head(15)
        [["nombre", "ccaa", "categoria", "n_resenas", "volumen_relativo", "sentimiento_masificacion", "opportunity_score_mock"]]
    )
    st.dataframe(
        riesgo, width='stretch', hide_index=True,
        column_config={
            "volumen_relativo": st.column_config.ProgressColumn("Volumen relativo", min_value=0, max_value=1, format="%.2f"),
            "sentimiento_masificacion": st.column_config.ProgressColumn("Sent. masificación", min_value=0, max_value=1, format="%.2f"),
            "opportunity_score_mock": st.column_config.NumberColumn("Opportunity Score (mock)", format="%.2f"),
            "n_resenas": st.column_config.NumberColumn("Nº reseñas"),
        },
    )

with tab_tipo:
    render_mock_badge("Catálogo sintético de lugares — datos de prueba")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Volumen de reseñas por tipo de establecimiento**")
        by_cat = df_places.groupby("categoria")["n_resenas"].sum().sort_values(ascending=False)
        fig3 = go.Figure(go.Bar(
            x=by_cat.index, y=by_cat.values,
            marker_color=[CATEGORY_COLORS[c] for c in by_cat.index],
            hovertemplate="%{x}: %{y:,}<extra></extra>",
        ))
        fig3.update_layout(xaxis=dict(title=None), yaxis=dict(title="Nº de reseñas"), height=420)
        st.plotly_chart(fig3, width='stretch')

    with col2:
        st.markdown("**Sentimiento general medio por tipo de establecimiento**")
        by_cat_sent = df_places.groupby("categoria")["sentimiento_general"].mean().sort_values(ascending=False)
        fig4 = go.Figure(go.Bar(
            x=by_cat_sent.index, y=by_cat_sent.values,
            marker_color=[CATEGORY_COLORS[c] for c in by_cat_sent.index],
            hovertemplate="%{x}: %{y:.1%}<extra></extra>",
        ))
        fig4.update_layout(
            xaxis=dict(title=None), yaxis=dict(title="Sentimiento general medio", tickformat=".0%", range=[0, 1]),
            height=420,
        )
        st.plotly_chart(fig4, width='stretch')

    st.caption(
        "En el corpus real, el alojamiento domina ampliamente el volumen de reseñas con texto "
        "(Rol 1) — este catálogo de prueba respeta esa proporción aproximada."
    )
