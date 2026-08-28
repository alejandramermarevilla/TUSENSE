"""
Paleta y utilidades visuales compartidas — TuriSense Dashboard.

Sigue la metodología de la skill dataviz: color asignado por el trabajo que
hace (categórico = identidad, secuencial = magnitud, divergente = polaridad),
orden categórico fijo (nunca ciclado), y colores de estado reservados para
fiabilidad/avisos.
"""

import plotly.graph_objects as go
import plotly.io as pio

# ---------------------------------------------------------------------------
# Paleta (paleta de referencia validada de la skill dataviz)
# ---------------------------------------------------------------------------

CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

SEQUENTIAL_BLUE = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
    "#184f95", "#104281", "#0d366b",
]

DIVERGING_POSITIVE = "#2a78d6"   # blue
DIVERGING_NEGATIVE = "#e34948"   # red
DIVERGING_NEUTRAL = "#c3c2b7"    # gray (baseline/axis, visible sobre superficie clara)

STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

CHROME = {
    "surface": "#fcfcfb",
    "page": "#f9f9f7",
    "text_primary": "#0b0b0b",
    "text_secondary": "#52514e",
    "muted": "#898781",
    "gridline": "#e1e0d9",
    "baseline": "#c3c2b7",
}

# Mapeos fijos de identidad — el color sigue a la entidad, nunca a su rango.
# Así un filtro que cambia cuántas plataformas se ven no repinta las que quedan.
PLATFORM_COLORS = {
    "Airbnb": CATEGORICAL[0],
    "Booking": CATEGORICAL[1],
    "Google Maps": CATEGORICAL[2],
    "Civitatis": CATEGORICAL[3],
    "Hostelworld": CATEGORICAL[4],
    "TheFork": CATEGORICAL[5],
}

CATEGORY_COLORS = {
    "Alojamiento": CATEGORICAL[0],
    "Hostelería": CATEGORICAL[1],
    "Ocio y naturaleza": CATEGORICAL[2],
    "Mercados": CATEGORICAL[3],
}

SENTIMENT_COLORS = {
    "Positivo": DIVERGING_POSITIVE,
    "Neutro": DIVERGING_NEUTRAL,
    "Negativo": DIVERGING_NEGATIVE,
}

ASPECT_ORDER = [
    "Trato/Anfitrión", "Autenticidad", "Ubicación", "Vistas", "Limpieza",
    "Desayuno/Restauración", "Aparcamiento", "Descanso/Ruido",
    "Equipamiento", "Precio", "Masificación",
]

# Nombres CANÓNICOS — idénticos a los del Rol 4 (fuente de verdad de los datos
# reales; ver data/real_data.py). Se usan también para los datos de prueba, para
# que un mismo filtro de región funcione igual en toda la app: 19 territorios,
# incluye Ceuta y Melilla.
CCAA_LIST = [
    "Andalucía", "Aragón", "Canarias", "Cantabria", "Castilla y León",
    "Castilla-La Mancha", "Cataluña", "Ceuta", "Comunidad Foral de Navarra",
    "Comunidad de Madrid", "Comunitat Valenciana", "Extremadura", "Galicia",
    "Illes Balears", "La Rioja", "Melilla", "País Vasco",
    "Principado de Asturias", "Región de Murcia",
]

PLATFORMS = list(PLATFORM_COLORS.keys())
CATEGORIES = list(CATEGORY_COLORS.keys())

# Identidad de color fija para las 8 CCAA de mayor peso turístico — techo de la
# escalera categórica (dataviz skill: 7-8 series = techo de tokens). Cualquier
# otra región seleccionada cae a gris (nunca se genera una 9ª tonalidad).
CCAA_COLORS = {
    "Andalucía": CATEGORICAL[0],
    "Cataluña": CATEGORICAL[1],
    "Comunidad de Madrid": CATEGORICAL[2],
    "Comunitat Valenciana": CATEGORICAL[3],
    "Illes Balears": CATEGORICAL[4],
    "Canarias": CATEGORICAL[5],
    "Galicia": CATEGORICAL[6],
    "País Vasco": CATEGORICAL[7],
}
CCAA_COLORS_DEFAULT = list(CCAA_COLORS.keys())


def ccaa_color(ccaa: str) -> str:
    return CCAA_COLORS.get(ccaa, CHROME["muted"])


def apply_plotly_template():
    """Registra y activa una plantilla plotly recesiva y coherente con la paleta."""
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor=CHROME["surface"],
        plot_bgcolor=CHROME["surface"],
        font=dict(color=CHROME["text_primary"], family="system-ui, -apple-system, 'Segoe UI', sans-serif", size=13),
        title=dict(font=dict(size=15, color=CHROME["text_primary"])),
        xaxis=dict(
            gridcolor=CHROME["gridline"], zerolinecolor=CHROME["baseline"],
            linecolor=CHROME["baseline"], tickfont=dict(color=CHROME["muted"]),
            title=dict(font=dict(color=CHROME["text_secondary"])),
        ),
        yaxis=dict(
            gridcolor=CHROME["gridline"], zerolinecolor=CHROME["baseline"],
            linecolor=CHROME["baseline"], tickfont=dict(color=CHROME["muted"]),
            title=dict(font=dict(color=CHROME["text_secondary"])),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=CHROME["text_secondary"])),
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(bgcolor=CHROME["surface"], font=dict(color=CHROME["text_primary"])),
    )
    pio.templates["turisense"] = template
    pio.templates.default = "turisense"


def reliability_badge(f1: float) -> str:
    """Etiqueta de fiabilidad (icono + texto, nunca solo color) a partir del F1
    del diccionario ABSA frente a la anotación manual (Rol 2)."""
    if f1 >= 0.85:
        return "🟢 Alta fiabilidad"
    if f1 >= 0.5:
        return "🟠 Fiabilidad media — revisar con cautela"
    return "🔴 Baja fiabilidad — no usar para conclusiones fuertes"
