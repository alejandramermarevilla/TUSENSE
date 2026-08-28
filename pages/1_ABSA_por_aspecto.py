"""ABSA por aspecto — sentimiento y fiabilidad del diccionario (Roles 1 y 2),
más la opinión real por región/plataforma del Rol 4."""

import numpy as np
import pandas as pd
import streamlit as st

from data.mock_data import (
    get_aspect_national_stats, get_aspect_reliability, generate_absa_breakdown, ASPECT_DISPLAY,
)
from data.real_data import load_opinion_aspecto, mask_low_support, PLATFORM_DISPLAY
from utils.theme import apply_plotly_template, CHROME
from utils.charts import diverging_stacked_bar
from utils.components import sidebar_filters, apply_filters, render_top_caveats, render_mock_badge

st.set_page_config(page_title="TuriSense · ABSA por aspecto", layout="wide")
apply_plotly_template()

st.title("ABSA — sentimiento por aspecto")
st.caption("Basado en el diccionario léxico de 11 aspectos (Rol 1) y su validación (Rol 2).")
render_top_caveats()

df_absa = generate_absa_breakdown()
filters = sidebar_filters(df_absa)
df_f = apply_filters(df_absa, filters)

tab1, tab_real, tab2 = st.tabs([
    "Cifras nacionales reales (Rol 1)", "Datos reales del Rol 4 (por región)", "Con tus filtros (datos de prueba)",
])

with tab1:
    st.caption(
        "Distribución de sentimiento por aspecto — corpus completo v3, troceo corregido con "
        "conectores adversativos. 4.099.623 pares aspecto-sentimiento. Cifras reales del informe del Rol 1."
    )
    national = get_aspect_national_stats()
    national = national[national["aspecto_display"].isin(filters["aspectos"])]
    if national.empty:
        st.info("Ningún aspecto seleccionado en el filtro coincide con las cifras nacionales.")
    else:
        st.plotly_chart(diverging_stacked_bar(national, "aspecto_display"), width='stretch')

with tab_real:
    st.caption(
        "Opinión real agregada por el Rol 4 (`R4_DASHBOARD_OPINION_ASPECTO_TIDY.parquet`, "
        "66.484 filas) — fuente × CCAA × mes × aspecto. Sustituye, para esta vista, al desglose "
        "de prueba de la pestaña siguiente."
    )

    df_op_asp = load_opinion_aspecto()
    ASPECT_KEY_BY_DISPLAY = {v: k for k, v in ASPECT_DISPLAY.items()}

    # Regla no negociable del contrato del Rol 4: la plataforma es un filtro
    # OBLIGATORIO en cualquier vista de opinión — no se puede promediar entre
    # fuentes sin un método explícito, así que aquí se elige una sola.
    c1, c2 = st.columns(2)
    with c1:
        plataforma_real = st.selectbox(
            "Plataforma (obligatorio — no se combinan fuentes)",
            options=list(PLATFORM_DISPLAY.values()), index=0, key="plataforma_real_absa",
        )
    with c2:
        aspecto_display_real = st.selectbox(
            "Aspecto", options=list(ASPECT_DISPLAY.values()),
            index=list(ASPECT_DISPLAY.values()).index(filters["aspectos"][0]) if filters["aspectos"] else 0,
            key="aspecto_real_absa",
        )
    source_key = {v: k for k, v in PLATFORM_DISPLAY.items()}[plataforma_real]
    aspecto_key = ASPECT_KEY_BY_DISPLAY[aspecto_display_real]

    d_base = df_op_asp[(df_op_asp["source"] == source_key) & (df_op_asp["aspecto"] == aspecto_key)]

    if d_base.empty:
        st.info(
            f"No hay datos reales de **{plataforma_real}** para el aspecto **{aspecto_display_real}** "
            f"en ninguna región/mes — combinación sin soporte en el parquet del Rol 4."
        )
        d = d_base
    else:
        min_p, max_p = d_base["period_dt"].min(), d_base["period_dt"].max()
        p_ini, p_fin = st.select_slider(
            "Rango de fechas (datos reales, 2019-2025)",
            options=list(pd.date_range(min_p, max_p, freq="MS")), value=(min_p, max_p),
            format_func=lambda x: x.strftime("%b %Y"), key="fechas_real_absa",
        )
        d = d_base[d_base["period_dt"].between(p_ini, p_fin) & d_base["ccaa"].isin(filters["ccaas"])]
        if d.empty:
            st.info("No hay datos reales para esta combinación de región/fecha (con esta plataforma y aspecto).")

    if not d.empty:
        wide = (
            d.pivot_table(index=["ccaa", "period"], columns="indicator_id", values="value", aggfunc="first")
            .reset_index()
        )
        support = d.groupby(["ccaa", "period"])["n_reviews"].first().reset_index()
        wide = wide.merge(support, on=["ccaa", "period"], how="left")

        agg = wide.groupby("ccaa").apply(
            lambda g: pd.Series({
                "positive_share": np.average(g["positive_share"], weights=g["n_reviews"]),
                "neutral_share": np.average(g["neutral_share"], weights=g["n_reviews"]),
                "negative_share": np.average(g["negative_share"], weights=g["n_reviews"]),
                "n_reviews": g["n_reviews"].sum(),
            }),
            include_groups=False,
        ).reset_index()

        agg["soporte_suficiente"] = agg["n_reviews"] >= 30
        visibles = agg[agg["soporte_suficiente"]].copy()
        ocultos = agg[~agg["soporte_suficiente"]]

        if not ocultos.empty:
            st.caption(
                f"🔒 {len(ocultos)} región(es) ocultas por soporte insuficiente "
                f"(<30 reseñas en el rango elegido — regla del contrato del Rol 4): "
                f"{', '.join(ocultos['ccaa'].tolist())}."
            )

        if visibles.empty:
            st.info("Ninguna región alcanza el soporte mínimo (30 reseñas) con estos filtros.")
        else:
            for c in ["positive_share", "neutral_share", "negative_share"]:
                visibles[c] = visibles[c] * 100
            st.plotly_chart(
                diverging_stacked_bar(
                    visibles, "ccaa",
                    pos_col="positive_share", neu_col="neutral_share", neg_col="negative_share",
                ),
                width='stretch',
            )
            with st.expander("Ver soporte (nº de reseñas) por región"):
                st.dataframe(
                    visibles[["ccaa", "n_reviews", "positive_share", "negative_share"]]
                    .rename(columns={"ccaa": "CCAA", "n_reviews": "Nº reseñas (soporte)",
                                      "positive_share": "% positivo", "negative_share": "% negativo"})
                    .sort_values("Nº reseñas (soporte)", ascending=False),
                    width='stretch', hide_index=True,
                )

    status_vals = d["absa_validation_status"].unique() if not d.empty else []
    elig_vals = d["eligible_final"].unique() if not d.empty else []
    st.warning(
        f"**Estado de validación (tal cual lo marca el propio dato del Rol 4):** "
        f"`absa_validation_status = {', '.join(status_vals) if len(status_vals) else 'sin datos'}`, "
        f"`eligible_final = {', '.join(map(str, elig_vals)) if len(elig_vals) else 'sin datos'}`. "
        f"Mientras sea `False`, el propio Rol 4 marca esta opinión como exploratoria — el Rol 3 ya "
        f"ha validado el modelo de sentimiento por su cuenta (ver el aviso de arriba de la página), "
        f"pero conviene confirmar con el equipo si el flag de esta tabla ya debería estar cerrado."
    )

with tab2:
    render_mock_badge("Mismo desglose recalculado con tus filtros de región/plataforma/mes (datos de prueba)")
    agg = df_f.groupby("aspecto_display")[["n_positivo", "n_neutro", "n_negativo"]].sum().reset_index()
    agg["total"] = agg[["n_positivo", "n_neutro", "n_negativo"]].sum(axis=1)
    agg = agg[agg["total"] > 0]
    for col, label in [("n_positivo", "pct_positivo"), ("n_neutro", "pct_neutro"), ("n_negativo", "pct_negativo")]:
        agg[label] = 100 * agg[col] / agg["total"]
    if agg.empty:
        st.info("No hay datos para la combinación de filtros elegida.")
    else:
        st.plotly_chart(diverging_stacked_bar(agg, "aspecto_display"), width='stretch')

st.divider()

# ---------------------------------------------------------------------------
# Fiabilidad del diccionario (Rol 2)
# ---------------------------------------------------------------------------
st.subheader("Fiabilidad del diccionario por aspecto (Rol 2)")
st.caption(
    "Precisión y recall frente a 200 reseñas anotadas a mano. La precisión/recall son cifras "
    "reales del informe del Rol 2 — no dependen de los filtros de arriba."
)

rel = get_aspect_reliability().sort_values("f1", ascending=False)


def badge(f1: float) -> str:
    if f1 >= 0.85:
        return "🟢 Alta"
    if f1 >= 0.5:
        return "🟠 Media — revisar con cautela"
    return "🔴 Baja — no usar para conclusiones fuertes"


rel_display = rel[["aspecto_display", "precision", "recall", "f1", "soporte"]].copy()
rel_display["fiabilidad"] = rel_display["f1"].map(badge)
rel_display.columns = ["Aspecto", "Precisión", "Recall", "F1", "Soporte (n)", "Fiabilidad"]

st.dataframe(
    rel_display,
    width='stretch',
    hide_index=True,
    column_config={
        "Precisión": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
        "Recall": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
        "F1": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
    },
)

st.warning(
    "**Equipamiento** (F1=0,195) y **Autenticidad** (F1=0,231) tienen precisión muy baja: el "
    "diccionario dispara en reseñas donde ese no es el tema real. **Masificación** tiene soporte "
    "casi nulo en la muestra de validación (n=2) — su cifra de fiabilidad no es concluyente, "
    "aunque el aspecto en sí es clave para el proyecto. Interpretar estos tres aspectos con más "
    "cautela que el resto."
)
