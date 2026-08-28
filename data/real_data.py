"""
Cargadores de los datos REALES entregados por el Rol 4 (Nicolás Díaz),
contrato `R4-F9-v1.0.0` — ver `data/raw/R4_CONTRATO_CONSUMO_ROL6.json`.

Reglas "no negociables" del contrato, aplicadas aquí o en las páginas que
consumen estos datos:

1. Mostrar unidad, fuente, soporte y flags junto al valor.        -> columnas conservadas tal cual
2. Plataforma como filtro obligatorio en cualquier vista de opinión. -> aplicado en las páginas
3. Ocultar o marcar las celdas de opinión con support_ge_30=false.   -> `mask_low_support()`
4. No presentar datos anuales como mensuales.                       -> CONTEXTO_ANUAL vive aparte, sin eje mensual
5. Pantallas, gráficos e interacción: los decide el Rol 6.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

RAW_DIR = Path(__file__).parent / "raw"

# CCAA canónicas — nombres EXACTOS del Rol 4 (fuente de verdad para datos reales).
# Sustituye a la lista aproximada que se usaba solo para los datos de prueba.
CCAA_LIST_REAL = [
    "Andalucía", "Aragón", "Canarias", "Cantabria", "Castilla y León",
    "Castilla-La Mancha", "Cataluña", "Ceuta", "Comunidad Foral de Navarra",
    "Comunidad de Madrid", "Comunitat Valenciana", "Extremadura", "Galicia",
    "Illes Balears", "La Rioja", "Melilla", "País Vasco",
    "Principado de Asturias", "Región de Murcia",
]

PLATFORMS_REAL = ["airbnb", "booking", "civitatis", "google_maps", "hostelworld", "thefork"]
PLATFORM_DISPLAY = {
    "airbnb": "Airbnb", "booking": "Booking", "civitatis": "Civitatis",
    "google_maps": "Google Maps", "hostelworld": "Hostelworld", "thefork": "TheFork",
}


@st.cache_data(show_spinner="Cargando catálogo de indicadores (Rol 4)...")
def load_catalogo() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "R4_CATALOGO_INDICADORES_DASHBOARD.csv")


@st.cache_data(show_spinner="Cargando datos oficiales (Rol 4 · CCAA x mes)...")
def load_oficial() -> pd.DataFrame:
    df = pd.read_parquet(RAW_DIR / "R4_DASHBOARD_OFICIAL_TIDY_CCAA_MES.parquet")
    df["period_dt"] = pd.to_datetime(df["period"] + "-01")
    return df


@st.cache_data(show_spinner="Cargando opinión global (Rol 4 · fuente x CCAA x mes)...")
def load_opinion_global() -> pd.DataFrame:
    df = pd.read_parquet(RAW_DIR / "R4_DASHBOARD_OPINION_GLOBAL_TIDY.parquet")
    df["period_dt"] = pd.to_datetime(df["period"] + "-01")
    df["plataforma"] = df["source"].map(PLATFORM_DISPLAY).fillna(df["source"])
    return df


@st.cache_data(show_spinner="Cargando opinión por aspecto (Rol 4 · fuente x CCAA x mes x aspecto)...")
def load_opinion_aspecto() -> pd.DataFrame:
    df = pd.read_parquet(RAW_DIR / "R4_DASHBOARD_OPINION_ASPECTO_TIDY.parquet")
    df["period_dt"] = pd.to_datetime(df["period"] + "-01")
    df["plataforma"] = df["source"].map(PLATFORM_DISPLAY).fillna(df["source"])
    return df


@st.cache_data(show_spinner="Cargando contexto estructural anual (Rol 4 · CCAA x año)...")
def load_contexto_anual() -> pd.DataFrame:
    return pd.read_parquet(RAW_DIR / "R4_DASHBOARD_CONTEXTO_ANUAL_CCAA.parquet")


def mask_low_support(df: pd.DataFrame, support_col: str = "support_ge_30") -> pd.DataFrame:
    """Regla no negociable #3: las celdas con soporte insuficiente (<30 reseñas)
    no deben mostrarse como si fueran una medición fiable. En vez de borrarlas
    (perderíamos el aviso), se marca `value` como NaN y se conserva el resto de
    columnas para que la interfaz pueda decir *por qué* falta el dato."""
    d = df.copy()
    d.loc[~d[support_col], "value"] = pd.NA
    return d


def pivot_opinion(df_long: pd.DataFrame, index_cols: list[str]) -> pd.DataFrame:
    """Las tablas de opinión vienen en formato largo (una fila por indicador).
    Para gráficos que necesitan positive/neutral/negative/balance como columnas
    separadas, se pivota sobre `indicator_id`."""
    wide = df_long.pivot_table(
        index=index_cols, columns="indicator_id", values="value", aggfunc="first"
    ).reset_index()
    # conservar columnas de soporte/flags (idénticas dentro de cada grupo index_cols)
    support_cols = ["n_reviews", "n_entities", "support_ge_20", "support_ge_30", "support_ge_50",
                     "absa_validation_status", "interpretation_status", "eligible_final"]
    support_cols = [c for c in support_cols if c in df_long.columns]
    support = df_long.groupby(index_cols)[support_cols].first().reset_index()
    return wide.merge(support, on=index_cols, how="left")
