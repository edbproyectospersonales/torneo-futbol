"""
app.py — Punto de entrada principal de la aplicación.

Acá vive toda la interfaz: navegación, páginas y formularios.
Streamlit funciona de arriba a abajo: cada vez que el usuario
interactúa, el script se re-ejecuta completo. Es raro al principio
pero muy simple de entender.
"""

import streamlit as st
import pandas as pd
from datetime import date

# Importamos nuestros módulos locales
from database import inicializar_db, cargar_datos_demo
from queries import (
    obtener_tabla_posiciones,
    obtener_resultados,
    obtener_goleadores,
    obtener_equipos,
    guardar_partido,
    guardar_goles,
    agregar_equipo,
)

# ─────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL DE LA APP
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Torneo Local",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado para un look más limpio y moderno
# Streamlit tiene su estilo propio; esto lo refina sin romperlo
st.markdown("""
<style>
    /* Ocultar el menú de hamburguesa de Streamlit y footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tipografía general */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }

    /* Encabezados con color */
    h1, h2, h3 {
        color: #1a1a2e;
    }

    /* Tablas de pandas más limpias */
    .dataframe th {
        background-color: #16213e !important;
        color: white !important;
        font-weight: 600;
        text-align: center !important;
    }
    .dataframe td {
        text-align: center !important;
    }

    /* Barra lateral */
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Botón principal */
    .stButton > button {
        background-color: #16213e;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #0f3460;
        color: white;
    }

    /* Métricas: centramos el texto */
    [data-testid="metric-container"] {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INICIALIZACIÓN DE LA BASE DE DATOS
# ─────────────────────────────────────────────

# Esto corre cada vez que alguien abre la app.
# inicializar_db() crea las tablas solo si no existen → seguro correrlo siempre.
# cargar_datos_demo() solo inserta si la DB está vacía → también seguro.
inicializar_db()
cargar_datos_demo()

# ─────────────────────────────────────────────
# NAVEGACIÓN LATERAL
# ─────────────────────────────────────────────

st.sidebar.image(
    "https://img.icons8.com/emoji/96/soccer-ball-emoji.png",
    width=80,
)
st.sidebar.title("⚽ Torneo Local")
st.sidebar.markdown("---")

# Radio button para navegar entre secciones
pagina = st.sidebar.radio(
    "Navegación",
    options=["🏆 Posiciones", "📋 Resultados", "🥇 Goleadores", "🔧 Panel Admin"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Hecho con Streamlit + SQLite")

# ─────────────────────────────────────────────
# PÁGINA 1: TABLA DE POSICIONES
# ─────────────────────────────────────────────

if pagina == "🏆 Posiciones":
    st.title("🏆 Tabla de Posiciones")
    st.caption("Actualizada automáticamente con cada resultado cargado")

    tabla = obtener_tabla_posiciones()

    if not tabla:
        st.info("Todavía no hay partidos cargados.")
    else:
        df = pd.DataFrame(tabla)

        # Agregamos columna de posición al inicio
        df.insert(0, "Pos", range(1, len(df) + 1))

        # Mostramos la tabla con estilo
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        # Separador y referencia de columnas
        st.markdown("---")
        st.markdown(
            "**PJ** Jugados &nbsp;|&nbsp; "
            "**PG** Ganados &nbsp;|&nbsp; "
            "**PE** Empatados &nbsp;|&nbsp; "
            "**PP** Perdidos &nbsp;|&nbsp; "
            "**GF** Goles a favor &nbsp;|&nbsp; "
            "**GC** Goles en contra &nbsp;|&nbsp; "
            "**DG** Diferencia &nbsp;|&nbsp; "
            "**PTS** Puntos"
        )

        # Métricas rápidas al pie
        st.markdown("### 📊 Resumen del torneo")
        col1, col2, col3, col4 = st.columns(4)
        total_partidos = sum(e["PJ"] for e in tabla) // 2
        total_goles = sum(e["GF"] for e in tabla)
        lider = tabla[0]["Equipo"] if tabla else "—"
        col1.metric("Equipos", len(tabla))
        col2.metric("Partidos jugados", total_partidos)
        col3.metric("Goles totales", total_goles)
        col4.metric("Líder actual", lider)

# ─────────────────────────────────────────────
# PÁGINA 2: RESULTADOS
# ─────────────────────────────────────────────

elif pagina == "📋 Resultados":
    st.title("📋 Resultados")
    st.caption("Partidos jugados, del más reciente al más antiguo")

    resultados = obtener_resultados()

    if not resultados:
        st.info("No hay partidos cargados todavía.")
    else:
        # Mostramos cada partido como una "tarjeta" simple
        for r in resultados:
            with st.container():
                col_fecha, col_local, col_score, col_visita = st.columns([1.5, 3, 1.5, 3])

                col_fecha.markdown(
                    f"<div style='padding-top:8px; color:#888; font-size:0.85rem;'>{r['fecha']}</div>",
                    unsafe_allow_html=True
                )
                col_local.markdown(
                    f"<div style='padding-top:6px; font-weight:600; text-align:right;'>{r['local']}</div>",
                    unsafe_allow_html=True
                )
                col_score.markdown(
                    f"<div style='text-align:center; font-size:1.4rem; font-weight:800; "
                    f"background:#16213e; color:white; border-radius:8px; padding:2px 8px;'>"
                    f"{r['goles_local']} — {r['goles_visitante']}</div>",
                    unsafe_allow_html=True
                )
                col_visita.markdown(
                    f"<div style='padding-top:6px; font-weight:600;'>{r['visitante']}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("<hr style='margin:6px 0; border-color:#eee;'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PÁGINA 3: GOLEADORES
# ─────────────────────────────────────────────

elif pagina == "🥇 Goleadores":
    st.title("🥇 Tabla de Goleadores")
    st.caption("Ranking individual por cantidad de goles convertidos")

    goleadores = obtener_goleadores()

    if not goleadores:
        st.info("Todavía no hay goles registrados.")
    else:
        df = pd.DataFrame(goleadores)
        df.insert(0, "#", range(1, len(df) + 1))

        # Top 3 con destaque visual
        if len(goleadores) >= 1:
            st.markdown("### 🏅 Top Goleadores")
            cols = st.columns(min(3, len(goleadores)))
            medallas = ["🥇", "🥈", "🥉"]
            for i, col in enumerate(cols):
                g = goleadores[i]
                col.metric(
                    label=f"{medallas[i]} {g['Jugador']}",
                    value=f"{g['Goles']} goles",
                    delta=g["Equipo"],
                )

        st.markdown("---")
        st.markdown("### 📋 Tabla completa")
        st.dataframe(df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# PÁGINA 4: PANEL ADMIN
# ─────────────────────────────────────────────

elif pagina == "🔧 Panel Admin":
    st.title("🔧 Panel de Administración")
    st.caption("Cargá resultados y goles manualmente")

    # Aviso simple (sin autenticación por ahora)
    st.warning("⚠️ Este panel es público por ahora. En una versión futura podés agregar contraseña.")

    # ── SECCIÓN: Cargar resultado ──
    st.markdown("### ⚽ Cargar resultado de partido")

    equipos = obtener_equipos()

    if len(equipos) < 2:
        st.error("Necesitás al menos 2 equipos para cargar un partido. Agregá equipos primero.")
    else:
        nombres_equipos = {e["nombre"]: e["id"] for e in equipos}
        opciones = list(nombres_equipos.keys())

        with st.form("form_partido"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Local**")
                equipo_local = st.selectbox("Equipo local", opciones, key="local")
                goles_local = st.number_input("Goles local", min_value=0, max_value=20, value=0)

            with col2:
                st.markdown("**Visitante**")
                equipo_visitante = st.selectbox("Equipo visitante", opciones, key="visitante")
                goles_visitante = st.number_input("Goles visitante", min_value=0, max_value=20, value=0)

            fecha_partido = st.date_input("Fecha del partido", value=date.today())

            st.markdown("---")
            st.markdown("**Goleadores (opcional)**")
            st.caption("Podés agregar los goleadores de cada equipo. Dejá en 0 si no querés registrarlos.")

            col3, col4 = st.columns(2)
            with col3:
                goleador_local_nombre = st.text_input("Goleador del local (nombre)", placeholder="Ej: Martín García")
                goleador_local_goles = st.number_input("Goles convertidos (local)", min_value=0, max_value=20, value=0, key="gl_local")
            with col4:
                goleador_visita_nombre = st.text_input("Goleador del visitante (nombre)", placeholder="Ej: Diego Ruiz")
                goleador_visita_goles = st.number_input("Goles convertidos (visitante)", min_value=0, max_value=20, value=0, key="gl_visita")

            submitted = st.form_submit_button("💾 Guardar partido")

            if submitted:
                # Validación mínima
                if equipo_local == equipo_visitante:
                    st.error("El local y visitante no pueden ser el mismo equipo.")
                else:
                    local_id = nombres_equipos[equipo_local]
                    visitante_id = nombres_equipos[equipo_visitante]

                    # Guardamos el partido
                    partido_id = guardar_partido(
                        local_id, visitante_id,
                        goles_local, goles_visitante,
                        str(fecha_partido)
                    )

                    # Guardamos goles si se cargaron
                    if goleador_local_nombre and goleador_local_goles > 0:
                        guardar_goles(goleador_local_nombre, local_id, partido_id, goleador_local_goles)

                    if goleador_visita_nombre and goleador_visita_goles > 0:
                        guardar_goles(goleador_visita_nombre, visitante_id, partido_id, goleador_visita_goles)

                    st.success(f"✅ Partido guardado: {equipo_local} {goles_local} - {goles_visitante} {equipo_visitante}")
                    st.balloons()

    # ── SECCIÓN: Agregar equipo ──
    st.markdown("---")
    st.markdown("### 🆕 Agregar equipo nuevo")

    with st.form("form_equipo"):
        nombre_equipo = st.text_input("Nombre del equipo", placeholder="Ej: San Martín de Luján")
        submitted_equipo = st.form_submit_button("➕ Agregar equipo")

        if submitted_equipo:
            if not nombre_equipo.strip():
                st.error("El nombre no puede estar vacío.")
            else:
                ok = agregar_equipo(nombre_equipo.strip())
                if ok:
                    st.success(f"✅ Equipo '{nombre_equipo}' agregado correctamente.")
                else:
                    st.warning(f"⚠️ Ya existe un equipo con ese nombre.")

    # ── SECCIÓN: Lista de equipos actuales ──
    st.markdown("---")
    st.markdown("### 📋 Equipos registrados")
    equipos_actuales = obtener_equipos()
    if equipos_actuales:
        for e in equipos_actuales:
            st.markdown(f"- {e['nombre']}")
    else:
        st.info("No hay equipos cargados todavía.")
