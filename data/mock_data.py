"""
Datos para el prototipo del cuadro de mando TuriSense (Rol 6).

Dos tipos de datos conviven aquí, y se etiquetan como tal en cada pantalla:

1. CIFRAS REALES AGREGADAS — las tablas nacionales de los informes de los
   Roles 1, 2 y 3 (distribución de sentimiento por aspecto, precisión/recall
   del diccionario ABSA, recall de negativo de Cardiff). Estas NO son
   inventadas: son los números que ya entregaron los compañeros.

2. DATOS DE PRUEBA (mock) — todo lo que requiere granularidad que el
   dashboard todavía no tiene en producción: desglose por región/plataforma/
   mes, perfil de aspectos por lugar individual, y el Opportunity Score
   (pendiente de cerrar por la Persona 5). Se generan de forma determinista
   (semilla fija) a partir de las cifras reales nacionales, para que al
   agregar el mock vuelva a acercarse al número real reportado.

Cuando lleguen `reviews_aspectos_geo.parquet` y el índice real de la
Persona 5, solo hay que sustituir las funciones de esta sección — el resto
de la app (páginas, gráficos, filtros) no debería necesitar cambios porque
consume siempre las mismas columnas.
"""

import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 1. CIFRAS REALES AGREGADAS (Roles 1, 2, 3 — no inventadas)
# ---------------------------------------------------------------------------

ASPECT_DISPLAY = {
    "trato_anfitrion": "Trato/Anfitrión",
    "autenticidad": "Autenticidad",
    "ubicacion": "Ubicación",
    "vistas": "Vistas",
    "limpieza": "Limpieza",
    "desayuno_restauracion": "Desayuno/Restauración",
    "aparcamiento": "Aparcamiento",
    "descanso_ruido": "Descanso/Ruido",
    "equipamiento": "Equipamiento",
    "precio": "Precio",
    "masificacion": "Masificación",
}

# Rol 1 — Figura 1 / tabla 4.1 (v3, troceo corregido)
_ASPECT_NATIONAL_RAW = [
    # aspecto, n_pares, %positivo, %neutro, %negativo
    ("trato_anfitrion", 1_214_623, 94.9, 2.7, 2.4),
    ("autenticidad", 137_098, 94.5, 4.3, 1.2),
    ("ubicacion", 1_018_446, 93.3, 6.1, 0.6),
    ("vistas", 85_939, 91.1, 7.9, 1.1),
    ("limpieza", 362_697, 87.6, 8.8, 3.7),
    ("desayuno_restauracion", 145_103, 83.5, 12.0, 4.5),
    ("aparcamiento", 146_393, 80.8, 16.1, 3.1),
    ("descanso_ruido", 243_665, 79.9, 16.4, 3.7),
    ("equipamiento", 660_219, 79.6, 15.0, 5.4),
    ("precio", 82_705, 70.5, 22.5, 7.0),
    ("masificacion", 2_735, 59.1, 32.2, 8.7),
]

# Rol 2 — precisión/recall/F1 del diccionario vs. anotación manual (200 reseñas)
_ASPECT_RELIABILITY_RAW = [
    ("ubicacion", 0.926, 0.830, 0.876, 106),
    ("vistas", 1.000, 1.000, 1.000, 10),
    ("limpieza", 0.938, 0.769, 0.845, 39),
    ("precio", 0.788, 0.981, 0.874, 53),
    ("descanso_ruido", 0.692, 0.643, 0.667, 14),
    ("trato_anfitrion", 0.564, 0.907, 0.695, 225),
    ("equipamiento", 0.116, 0.610, 0.195, 41),
    ("desayuno_restauracion", 0.312, 0.714, 0.435, 7),
    ("aparcamiento", 0.889, 0.941, 0.914, 17),
    ("masificacion", 0.000, 0.000, 0.000, 2),
    ("autenticidad", 0.145, 0.562, 0.231, 16),
]

# Rol 1 — distribución por plataforma (n pares aspecto-sentimiento)
PLATFORM_VOLUME_REAL = {
    "Airbnb": 3_552_170,
    "Booking": 343_423,
    "Google Maps": 186_521,
    "TheFork": 8_878,
    "Civitatis": 8_584,
    "Hostelworld": 47,
}

# Rol 3 — validación de Cardiff frente a anotación humana (muestra Gold, 1.060 reseñas)
CARDIFF_VALIDATION = {
    "accuracy_global": 0.924,
    "recall_negativo": 0.256,
    "negativas_detectadas": 10,
    "negativas_totales_muestra": 39,
    "pct_negativo_corpus_completo": 0.0135,
    "kappa_sentimiento": 0.844,
    "kappa_aspectos_medio": 0.928,
}

CORPUS_TOTAL_RESENAS = 4_140_036
CORPUS_RESENAS_CON_ASPECTO = 1_996_719
CORPUS_PARES_ASPECTO_SENTIMIENTO = 4_099_623
COBERTURA_DICCIONARIO = CORPUS_RESENAS_CON_ASPECTO / CORPUS_TOTAL_RESENAS  # Rol 3, hallazgo 3


def get_aspect_national_stats() -> pd.DataFrame:
    df = pd.DataFrame(
        _ASPECT_NATIONAL_RAW,
        columns=["aspecto", "n_pares", "pct_positivo", "pct_neutro", "pct_negativo"],
    )
    df["aspecto_display"] = df["aspecto"].map(ASPECT_DISPLAY)
    return df


def get_aspect_reliability() -> pd.DataFrame:
    df = pd.DataFrame(
        _ASPECT_RELIABILITY_RAW,
        columns=["aspecto", "precision", "recall", "f1", "soporte"],
    )
    df["aspecto_display"] = df["aspecto"].map(ASPECT_DISPLAY)
    return df


# ---------------------------------------------------------------------------
# 2. DATOS DE PRUEBA (mock, deterministas) — desglose granular
# ---------------------------------------------------------------------------

# Nombres canónicos — idénticos a los del Rol 4 (ver data/real_data.py), para
# que un mismo filtro de región funcione en las pantallas con datos reales y
# en las que todavía usan datos de prueba.
CCAA_LIST = [
    "Andalucía", "Aragón", "Canarias", "Cantabria", "Castilla y León",
    "Castilla-La Mancha", "Cataluña", "Ceuta", "Comunidad Foral de Navarra",
    "Comunidad de Madrid", "Comunitat Valenciana", "Extremadura", "Galicia",
    "Illes Balears", "La Rioja", "Melilla", "País Vasco",
    "Principado de Asturias", "Región de Murcia",
]

# Peso turístico aproximado por CCAA (orden de magnitud plausible, no oficial)
_CCAA_WEIGHTS_RAW = {
    "Andalucía": 17, "Cataluña": 16, "Comunidad de Madrid": 12,
    "Comunitat Valenciana": 11, "Illes Balears": 10, "Canarias": 11,
    "Galicia": 4, "País Vasco": 3, "Castilla y León": 3,
    "Castilla-La Mancha": 2, "Aragón": 2, "Región de Murcia": 2,
    "Extremadura": 1, "Principado de Asturias": 2, "Cantabria": 1.5,
    "Comunidad Foral de Navarra": 1.5, "La Rioja": 0.5,
    "Ceuta": 0.1, "Melilla": 0.1,
}

# CCAA con más presión de masificación en el imaginario turístico — se usa
# solo para que el mock cuente una historia plausible en "masificación";
# el resto de aspectos no llevan este ajuste.
_MASIFICACION_PRESSURE = {
    "Illes Balears": 1.9, "Cataluña": 1.6, "Canarias": 1.5,
    "Andalucía": 1.3, "Comunitat Valenciana": 1.2, "Comunidad de Madrid": 1.1,
}

CATEGORIES = ["Alojamiento", "Hostelería", "Ocio y naturaleza", "Mercados"]
_CATEGORY_WEIGHTS = {"Alojamiento": 0.82, "Hostelería": 0.10, "Ocio y naturaleza": 0.06, "Mercados": 0.02}

N_MONTHS = 24
MONTHS = pd.date_range(end="2026-07-01", periods=N_MONTHS, freq="MS")


def _normalized(weights_dict):
    s = sum(weights_dict.values())
    return {k: v / s for k, v in weights_dict.items()}


def _month_weights():
    w = {}
    for m in MONTHS:
        if m.month in (6, 7, 8, 9):
            w[m] = 1.4
        elif m.month in (4, 5, 10):
            w[m] = 1.1
        else:
            w[m] = 0.8
    return _normalized(w)


@st.cache_data(show_spinner="Generando datos de prueba (ABSA por región/plataforma/mes)...")
def generate_absa_breakdown(seed: int = 42) -> pd.DataFrame:
    """Desglose sintético de pares aspecto-sentimiento por CCAA × plataforma ×
    mes, calibrado para que la suma nacional se aproxime a la tabla real del
    Rol 1 (ver `get_aspect_national_stats`). DATOS DE PRUEBA."""
    rng = np.random.default_rng(seed)

    region_w = _normalized(_CCAA_WEIGHTS_RAW)
    platform_w = _normalized(PLATFORM_VOLUME_REAL)
    month_w = _month_weights()

    regions = list(region_w.keys())
    platforms = list(platform_w.keys())
    months = list(month_w.keys())

    cell_index = pd.MultiIndex.from_product(
        [regions, platforms, months], names=["ccaa", "plataforma", "mes"]
    )
    base_probs = np.array([
        region_w[r] * platform_w[p] * month_w[m] for r, p, m in cell_index
    ])
    base_probs = base_probs / base_probs.sum()

    national = get_aspect_national_stats()
    rows = []
    for _, arow in national.iterrows():
        aspecto = arow["aspecto"]
        n_total = int(arow["n_pares"])

        # Reparto del volumen total del aspecto entre las celdas región×plataforma×mes
        counts = rng.multinomial(n_total, base_probs)

        # Sentimiento nacional del aspecto, con jitter por región (± hasta 4 puntos)
        base_pos, base_neu, base_neg = arow["pct_positivo"], arow["pct_neutro"], arow["pct_negativo"]

        for (r, p, m), n_cell in zip(cell_index, counts):
            if n_cell == 0:
                continue
            jitter = rng.normal(0, 2.0, size=3)
            pos = base_pos + jitter[0]
            neu = base_neu + jitter[1]
            neg = base_neg + jitter[2]

            if aspecto == "masificacion":
                pressure = _MASIFICACION_PRESSURE.get(r, 1.0)
                shift = (pressure - 1.0) * 12  # más presión -> más negativo, menos positivo
                neg += shift
                pos -= shift

            probs3 = np.clip([pos, neu, neg], 0.5, None)
            probs3 = probs3 / probs3.sum()
            n_pos, n_neu, n_neg = rng.multinomial(int(n_cell), probs3)

            rows.append((aspecto, r, p, m, int(n_pos), int(n_neu), int(n_neg)))

    df = pd.DataFrame(
        rows, columns=["aspecto", "ccaa", "plataforma", "mes", "n_positivo", "n_neutro", "n_negativo"]
    )
    df["aspecto_display"] = df["aspecto"].map(ASPECT_DISPLAY)
    df["n_total"] = df["n_positivo"] + df["n_neutro"] + df["n_negativo"]
    return df


@st.cache_data(show_spinner="Generando perfiles de lugar de prueba...")
def generate_places(seed: int = 7, n_places: int = 260) -> pd.DataFrame:
    """Perfil sintético por lugar (entity_id): sentimiento por aspecto (11
    dimensiones), nº de reseñas y categoría/territorio. Sustituye, de forma
    ilustrativa, a la agregación real por `entity_id` de reviews_master.parquet
    que el Rol 3 ya ha entregado (pendiente de conectar). DATOS DE PRUEBA."""
    rng = np.random.default_rng(seed)
    region_w = _normalized(_CCAA_WEIGHTS_RAW)
    regions = rng.choice(list(region_w.keys()), size=n_places, p=list(region_w.values()))
    categorias = rng.choice(CATEGORIES, size=n_places, p=list(_CATEGORY_WEIGHTS.values()))

    # nº de reseñas: log-normal, para que haya cola larga (pocos lugares muy reseñados)
    n_resenas = np.clip(rng.lognormal(mean=3.2, sigma=1.1, size=n_places), 3, 4000).astype(int)

    national = get_aspect_national_stats().set_index("aspecto")
    aspectos = list(ASPECT_DISPLAY.keys())

    data = {
        "entity_id": [f"lugar_{i:04d}" for i in range(n_places)],
        "nombre": [f"Alojamiento {r} · Ref. {i:04d}" for i, r in enumerate(regions)],
        "ccaa": regions,
        "categoria": categorias,
        "n_resenas": n_resenas,
    }
    df = pd.DataFrame(data)

    for aspecto in aspectos:
        base = national.loc[aspecto, "pct_positivo"] / 100.0
        noise = rng.normal(0, 0.08, size=n_places)
        col = np.clip(base + noise, 0.02, 0.99)
        if aspecto == "masificacion":
            pressure = df["ccaa"].map(_MASIFICACION_PRESSURE).fillna(1.0).to_numpy()
            col = np.clip(col - (pressure - 1.0) * 0.18, 0.02, 0.99)
        df[f"sentimiento_{aspecto}"] = col

    df["sentimiento_general"] = df[[f"sentimiento_{a}" for a in aspectos]].mean(axis=1)

    # volumen_relativo: percentil de n_resenas DENTRO de {categoría, territorio} —
    # exactamente la granularidad que pide el motor de recomendación (nota Rol 3 -> Persona 5)
    df["volumen_relativo"] = (
        df.groupby(["categoria", "ccaa"])["n_resenas"].rank(pct=True)
    )
    return df


@st.cache_data(show_spinner=False)
def opportunity_score_placeholder(df_places: pd.DataFrame) -> pd.DataFrame:
    """Marcador de posición del Opportunity Score (Persona 5, apartado 5.1 —
    todavía sin cerrar). Combina sentimiento general con infrautilización, de
    forma puramente ilustrativa: sentimiento alto + poco reseñado = 'oportunidad';
    volumen alto + masificación negativa = 'riesgo'. NO es la fórmula final."""
    df = df_places.copy()
    df["opportunity_score_mock"] = (
        df["sentimiento_general"] * (1 - 0.5 * df["volumen_relativo"])
    ).round(3)
    df["riesgo_masificacion_mock"] = (
        (df["volumen_relativo"] > 0.7) & (df["sentimiento_masificacion"] < 0.65)
    )
    return df
