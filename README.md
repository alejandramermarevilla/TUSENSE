# TuriSense — Cuadro de mando (Rol 6)

Prototipo funcional del dashboard. Ya conecta los **datos reales** entregados
por el Rol 3 (validación de sentimiento) y el Rol 4 (datos oficiales de
turismo + opinión real por región), y usa **datos de prueba** solo donde
todavía no ha llegado nada real (el índice de la Persona 5 y el motor de
recomendación).

## Cómo ejecutarlo

```bash
# 1. (Recomendado) crea un entorno virtual
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate

# 2. Instala las dependencias
pip install -r requirements.txt

# 3. Arranca la app
streamlit run app.py
```

Se abrirá automáticamente en `http://localhost:8501`. Streamlit detecta los
archivos de la carpeta `pages/` y monta la navegación lateral solo.

## Estructura

```
app.py                          # Vista general (KPIs, tendencia, plataformas, regiones)
pages/
  1_ABSA_por_aspecto.py         # Sentimiento por aspecto (Rol 1/2) + opinión REAL por región (Rol 4)
  2_Por_region.py               # Por región y por tipo de establecimiento + Opportunity Score (mock)
  3_Motor_de_recomendacion.py   # Demo del motor de recomendación (formulario + ranking explicable)
  4_Datos_oficiales.py          # 11 indicadores oficiales REALES (Rol 4) + contexto estructural anual
data/
  mock_data.py                  # Cifras reales agregadas (Rol 1/2/3) + generadores de datos de prueba
  real_data.py                  # Cargadores de los parquet/csv/json reales del Rol 4
  raw/                          # Los 5 ficheros que entregó el Rol 4 (contrato de consumo incluido)
utils/
  theme.py                      # Paleta, plantilla plotly y CCAA canónicas (metodología dataviz skill)
  charts.py                     # Gráfico de bar divergente reutilizado entre páginas
  components.py                 # Filtros de sidebar y avisos compartidos entre páginas
```

## Qué es real y qué es de prueba

- **Real** (no inventado):
  - Cifras nacionales agregadas de sentimiento por aspecto (Rol 1), precisión/recall
    del diccionario (Rol 2), validación de Cardiff y volumen por plataforma (Rol 3)
    — constantes en `data/mock_data.py`, sección 1.
  - Opinión por fuente×CCAA×mes(×aspecto) y los 11 indicadores oficiales
    CCAA×mes + contexto estructural anual (Rol 4) — `data/real_data.py` y
    `data/raw/*.parquet`. Ver pestaña *Datos reales del Rol 4* en ABSA por
    aspecto, y la página **Datos oficiales**.
- **De prueba** (mock, determinista con semilla fija): el desglose ABSA por
  región/plataforma/mes en la Vista general y en la pestaña "Con tus filtros",
  el catálogo de ~260 "lugares" con perfil de aspectos, y el Opportunity
  Score — todo marcado en pantalla con el aviso 🧪.

## El contrato de consumo del Rol 4 (`data/raw/R4_CONTRATO_CONSUMO_ROL6.json`)

Reglas aplicadas en las páginas que consumen datos reales:

1. Unidad, fuente, soporte y flags se muestran junto al valor (tabla expandible
   en ABSA por aspecto; columnas dedicadas en Datos oficiales).
2. La plataforma es un **selectbox obligatorio** (nunca "todas") en la pestaña
   de opinión real — no se combinan fuentes sin método explícito.
3. Las regiones con soporte insuficiente (`support_ge_30 = false`, menos de 30
   reseñas en el rango elegido) se ocultan del gráfico y se listan aparte.
4. El contexto estructural anual vive en su propia sección, con su propio
   selector de año — nunca se dibuja en el eje mensual.
5. Pantallas, gráficos e interacción: decisión del Rol 6.

**Aviso pendiente de aclarar con el equipo**: en las tablas de opinión del
Rol 4, `eligible_final = False` y `absa_validation_status =
"pendiente_validacion_roles_2_3"` en el 100% de las filas — el propio dato se
marca como exploratorio, aunque el Rol 3 ya cerró su validación por su cuenta.
La app muestra este estado leyéndolo directamente del parquet (no hardcodeado),
así que en cuanto el Rol 4 actualice el flag, el aviso deja de aparecer solo.

## Próximos pasos

- Sustituir el desglose ABSA de prueba (Vista general, pestaña "Con tus
  filtros") por `reviews_aspectos_geo.parquet` del Rol 3 (4.099.623 filas,
  nivel de reseña individual).
- Sustituir `opportunity_score_placeholder()` por el índice real de la
  Persona 5 en cuanto lo cierre a nivel de lugar individual.
- Cruzar Datos oficiales (Rol 4) con la opinión por aspecto — hoy son dos
  páginas separadas; el propio Rol 4 lo señala como el objetivo final
  ("¿coincide una caída de sentimiento con una anomalía real?").
- Conectar el motor de recomendación real cuando el equipo asigne quién lo
  construye (documento de diseño, "Qué falta decidir").
