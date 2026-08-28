"""Componentes compartidos entre páginas: filtros de sidebar y avisos."""

import pandas as pd
import streamlit as st

from data.mock_data import (
    CARDIFF_VALIDATION, COBERTURA_DICCIONARIO, CCAA_LIST, CATEGORIES,
)
from utils.theme import PLATFORMS, ASPECT_ORDER


def sidebar_filters(df_absa: pd.DataFrame) -> dict:
    """Filtros globales (región, plataforma, aspecto, fecha). Se guardan en
    session_state con claves fijas para que persistan al cambiar de página."""
    st.sidebar.markdown("### Filtros")

    ccaas = st.sidebar.multiselect(
        "Región (CCAA)", options=CCAA_LIST, default=st.session_state.get("f_ccaa", []),
        key="f_ccaa", placeholder="Todas las regiones",
    )
    plataformas = st.sidebar.multiselect(
        "Plataforma", options=PLATFORMS, default=st.session_state.get("f_plataforma", []),
        key="f_plataforma", placeholder="Todas las plataformas",
    )
    aspectos = st.sidebar.multiselect(
        "Aspecto", options=ASPECT_ORDER, default=st.session_state.get("f_aspecto", []),
        key="f_aspecto", placeholder="Todos los aspectos",
    )

    min_date, max_date = df_absa["mes"].min(), df_absa["mes"].max()
    fecha_ini, fecha_fin = st.sidebar.select_slider(
        "Rango de fechas",
        options=list(pd.date_range(min_date, max_date, freq="MS")),
        value=(min_date, max_date),
        format_func=lambda d: d.strftime("%b %Y"),
        key="f_fechas",
    )

    st.sidebar.caption(
        "Los filtros de región/plataforma/mes se aplican sobre datos de prueba "
        "(ver aviso arriba). El aspecto filtra también las cifras nacionales reales."
    )

    return {
        "ccaas": ccaas or CCAA_LIST,
        "plataformas": plataformas or PLATFORMS,
        "aspectos": aspectos or ASPECT_ORDER,
        "fecha_ini": fecha_ini,
        "fecha_fin": fecha_fin,
    }


def apply_filters(df_absa: pd.DataFrame, filters: dict) -> pd.DataFrame:
    mask = (
        df_absa["ccaa"].isin(filters["ccaas"])
        & df_absa["plataforma"].isin(filters["plataformas"])
        & df_absa["aspecto_display"].isin(filters["aspectos"])
        & df_absa["mes"].between(filters["fecha_ini"], filters["fecha_fin"])
    )
    return df_absa[mask]


def render_top_caveats():
    """Avisos que deben verse en cualquier pantalla del dashboard, no solo en
    la memoria: el punto ciego de Cardiff con las negativas, y la cobertura
    real del diccionario ABSA (Rol 3, hallazgos 2 y 3)."""
    with st.expander(
        "⚠️ Antes de interpretar estos datos — 2 avisos importantes del equipo de validación (Rol 3)",
        expanded=False,
    ):
        st.warning(
            f"**El modelo de sentimiento (Cardiff) casi no detecta negatividad real.** "
            f"Frente a la anotación humana, el recall de reseñas negativas es solo del "
            f"{CARDIFF_VALIDATION['recall_negativo']:.1%} "
            f"({CARDIFF_VALIDATION['negativas_detectadas']} de "
            f"{CARDIFF_VALIDATION['negativas_totales_muestra']} negativas reales detectadas). "
            f"El {CARDIFF_VALIDATION['pct_negativo_corpus_completo']:.2%} de negativas que sale "
            f"del corpus completo hay que leerlo con esta limitación por delante — "
            f"probablemente hay más insatisfacción real de la que muestran estas cifras."
        )
        st.info(
            f"**El diccionario ABSA no cubre toda reseña.** Detecta al menos un aspecto en el "
            f"{COBERTURA_DICCIONARIO:.1%} de las 4.140.036 reseñas del corpus — el resto no "
            f"menciona ningún aspecto reconocible por el diccionario (Rol 3, hallazgo de "
            f"trazabilidad). Además, la fiabilidad del diccionario varía mucho por aspecto: "
            f"ver el detalle de precisión/recall en la pestaña ABSA por aspecto antes de sacar "
            f"conclusiones sobre Equipamiento o Autenticidad."
        )


def render_mock_badge(text: str = "Datos de prueba — pendiente de conectar datos reales"):
    st.caption(f"🧪 {text}")
