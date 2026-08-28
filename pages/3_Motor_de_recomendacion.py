"""Motor de recomendación — demo del diseño básico (documento de diseño,
Fases 1–5): score_contenido + re-ranking por redistribución (volumen_relativo)."""

import plotly.graph_objects as go
import streamlit as st

from data.mock_data import generate_places, ASPECT_DISPLAY, CCAA_LIST, CATEGORIES
from utils.theme import apply_plotly_template, SEQUENTIAL_BLUE, CHROME

st.set_page_config(page_title="TuriSense · Motor de recomendación", layout="wide")
apply_plotly_template()

st.title("Motor de recomendación (demo)")
st.caption(
    "Implementa el diseño básico del documento «Motor de recomendación y redistribución de "
    "demanda»: score_contenido a partir de ABSA, re-ranking con volumen_relativo. Pieza nueva, "
    "todavía sin responsable de construcción asignado — este es un boceto funcional."
)

st.warning(
    "**Demo con datos de prueba.** `score_contenido` aquí se calcula sobre el catálogo sintético "
    "de ~260 lugares, no sobre las 4,14M reseñas reales. `volumen_relativo` sí sigue exactamente "
    "la definición que pidió el Rol 3: percentil de reseñas dentro de {categoría + territorio}. "
    "Falta decidir con el equipo si este formulario vive aquí de forma definitiva o en un "
    "notebook/demo aparte (punto abierto en el documento de diseño)."
)

ASPECT_KEYS = list(ASPECT_DISPLAY.keys())
ASPECT_LABELS = [ASPECT_DISPLAY[k] for k in ASPECT_KEYS]

df_places = generate_places()

st.subheader("1. Preferencias del viajero")

with st.form("preferencias"):
    st.markdown("**Importancia de cada aspecto** (0 = indiferente, 5 = muy importante)")
    cols = st.columns(4)
    pesos = {}
    for i, (key, label) in enumerate(zip(ASPECT_KEYS, ASPECT_LABELS)):
        with cols[i % 4]:
            pesos[key] = st.slider(label, 0, 5, 3, key=f"peso_{key}")

    c1, c2, c3 = st.columns(3)
    with c1:
        territorio = st.selectbox("Territorio (opcional)", ["Cualquiera"] + CCAA_LIST)
    with c2:
        categoria = st.selectbox("Tipo de experiencia (opcional)", ["Cualquiera"] + CATEGORIES)
    with c3:
        beta = st.slider(
            "Sensibilidad a la redistribución (β)", 0.0, 1.0, 0.4, 0.05,
            help="0 = solo importa el ajuste a tus preferencias. 1 = prioriza fuerte los lugares "
                 "menos masificados dentro de su categoría/territorio, aunque encajen algo peor.",
        )

    submitted = st.form_submit_button("Buscar recomendaciones", type="primary")

st.subheader("2. Recomendaciones")

if not submitted:
    st.caption("Ajusta tus preferencias arriba y pulsa «Buscar recomendaciones».")
else:
    df = df_places.copy()
    if territorio != "Cualquiera":
        df = df[df["ccaa"] == territorio]
    if categoria != "Cualquiera":
        df = df[df["categoria"] == categoria]

    # Fase 3 del diseño: filtrar antes lugares poco fiables (pocas reseñas o
    # sentimiento general bajo)
    df = df[(df["n_resenas"] >= 10) & (df["sentimiento_general"] >= 0.4)]

    if df.empty:
        st.info("No hay lugares de prueba que cumplan esos filtros. Prueba con otro territorio o categoría.")
    else:
        peso_total = sum(pesos.values())
        if peso_total == 0:
            st.info("Sube la importancia de al menos un aspecto para calcular recomendaciones.")
        else:
            score_contenido = sum(
                pesos[k] * df[f"sentimiento_{k}"] for k in ASPECT_KEYS
            ) / peso_total
            df["score_contenido"] = score_contenido
            df["score_final"] = df["score_contenido"] * (1 - beta * df["volumen_relativo"])

            top = df.sort_values("score_final", ascending=False).head(10)

            fig = go.Figure(go.Bar(
                x=top["score_final"][::-1], y=top["nombre"][::-1], orientation="h",
                marker_color=SEQUENTIAL_BLUE[7],
                hovertemplate="%{y}<br>score_final: %{x:.3f}<extra></extra>",
            ))
            fig.update_layout(
                xaxis=dict(title="score_final", range=[0, 1]), yaxis=dict(title=None),
                height=60 + 42 * len(top), margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig, width='stretch')

            # Explicabilidad (Fase 5 del diseño): qué aspectos coinciden más
            top_aspectos_usuario = sorted(pesos, key=pesos.get, reverse=True)[:3]
            top_aspectos_usuario = [a for a in top_aspectos_usuario if pesos[a] > 0]

            st.markdown("**Por qué se recomienda cada lugar**")
            for _, row in top.iterrows():
                aspectos_txt = ", ".join(
                    f"{ASPECT_DISPLAY[a]} ({row[f'sentimiento_{a}']:.0%} positivo)"
                    for a in top_aspectos_usuario
                )
                nota_redistribucion = (
                    f"recibe menos reseñas que el {row['volumen_relativo']:.0%} de lugares "
                    f"comparables en su categoría y territorio"
                    if row["volumen_relativo"] < 0.5
                    else
                    f"está entre los más reseñados de su categoría y territorio "
                    f"(percentil {row['volumen_relativo']:.0%})"
                )
                st.markdown(
                    f"- **{row['nombre']}** ({row['ccaa']}, {row['categoria']}) — coincide en "
                    f"{aspectos_txt}. En volumen, {nota_redistribucion}."
                )

            with st.expander("Ver tabla completa"):
                st.dataframe(
                    top[["nombre", "ccaa", "categoria", "n_resenas", "score_contenido", "volumen_relativo", "score_final"]],
                    width='stretch', hide_index=True,
                    column_config={
                        "score_contenido": st.column_config.NumberColumn(format="%.3f"),
                        "score_final": st.column_config.NumberColumn(format="%.3f"),
                        "volumen_relativo": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
                    },
                )

st.divider()
with st.expander("Cómo funciona (documento de diseño)"):
    st.markdown(
        "```\n"
        "score_contenido(lugar) = Σ [peso_usuario(aspecto) × sentimiento_positivo(lugar, aspecto)] "
        "/ Σ peso_usuario(aspecto)\n\n"
        "score_final(lugar) = score_contenido(lugar) × (1 − β × volumen_relativo(lugar))\n"
        "```\n"
        "`volumen_relativo(lugar)` penaliza los sitios más masificados dentro de su propia "
        "categoría y territorio, y prioriza los infrautilizados con un perfil de aspectos "
        "parecido — es la misma pieza que pidió el Rol 3 a la Persona 5, calculada aquí a nivel "
        "de lugar individual."
    )
