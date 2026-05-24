"""
app.py — Interfaz principal del Torneo Local.
"""

import streamlit as st
import pandas as pd
from datetime import date
from collections import defaultdict

from database import inicializar_db, cargar_datos_demo
from queries import (
    obtener_tabla_posiciones,
    obtener_resultados,
    obtener_goleadores,
    obtener_equipos,
    obtener_fechas_disponibles,
    obtener_proximos_partidos,
    obtener_fixture_con_ids,
    obtener_matriz_resultados,
    calcular_tabla_desde_partidos,
    guardar_partido,
    guardar_goles,
    guardar_fixture,
    eliminar_fixture,
    agregar_equipo,
)

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Torneo Local",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: #1a1a2e; }
    .dataframe th {
        background-color: #16213e !important;
        color: white !important;
        font-weight: 600;
        text-align: center !important;
    }
    .dataframe td { text-align: center !important; }
    .stButton > button {
        background-color: #16213e;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover { background-color: #0f3460; color: white; }
    [data-testid="metric-container"] { text-align: center; }
    .fixture-card {
        background: #f8f9fa;
        border-left: 4px solid #16213e;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .fixture-vs { font-size: 1.1rem; font-weight: 700; color: #1a1a2e; }
    .fixture-meta { font-size: 0.85rem; color: #666; margin-top: 4px; }
    /* Simulador: tabla con fondo levemente distinto para diferenciarlo */
    .sim-banner {
        background: #fff8e1;
        border-left: 4px solid #f0a500;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 16px;
        font-size: 0.95rem;
        color: #7a5c00;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────────

inicializar_db()
cargar_datos_demo()

# ─────────────────────────────────────────────
# CONTRASEÑA ADMIN
# ─────────────────────────────────────────────
# Guardamos si el admin está autenticado en session_state.
# session_state persiste mientras el navegador está abierto
# pero se resetea al cerrar o refrescar → seguro y simple.
#
# Cambiá ADMIN_PASSWORD por la que quieras. En el futuro
# esto se puede mover a un archivo .env o st.secrets.

ADMIN_PASSWORD = "torneo2025"

if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False


def verificar_password():
    """Muestra el formulario de login y actualiza el estado."""
    st.title("🔒 Panel de Administración")
    st.caption("Ingresá la contraseña para acceder")

    with st.form("form_login"):
        pwd = st.text_input("Contraseña", type="password", placeholder="••••••••")
        if st.form_submit_button("Entrar"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")


# ─────────────────────────────────────────────
# NAVEGACIÓN
# ─────────────────────────────────────────────

st.sidebar.image("https://img.icons8.com/emoji/96/soccer-ball-emoji.png", width=80)
st.sidebar.title("⚽ Torneo Local")
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegación",
    options=[
        "🏆 Posiciones",
        "📋 Resultados",
        "📅 Próxima Fecha",
        "🔮 Simulador",
        "🥇 Goleadores",
        "🔧 Panel Admin",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Hecho con Streamlit + SQLite")

# ─────────────────────────────────────────────
# HELPER: formatear fecha YYYY-MM-DD → DD/MM/YYYY
# ─────────────────────────────────────────────

def fmt(fecha_iso):
    """'2025-04-05' → '05/04/2025'"""
    p = fecha_iso.split("-")
    return f"{p[2]}/{p[1]}/{p[0]}"


# ─────────────────────────────────────────────
# PÁGINA 1 — POSICIONES
# ─────────────────────────────────────────────

if pagina == "🏆 Posiciones":
    st.title("🏆 Tabla de Posiciones")

    fechas_info = obtener_fechas_disponibles()

    if not fechas_info:
        st.info("Todavía no hay partidos cargados.")
    else:
        # Las opciones del selector muestran "Fecha N — DD/MM/YYYY"
        opciones_label = ["📊 Todas las fechas"] + [f["label"] for f in fechas_info]
        # Mapeamos label → valor real de fecha ISO para pasarle al SQL
        label_a_fecha  = {f["label"]: f["fecha"] for f in fechas_info}

        col_sel, col_info = st.columns([2, 3])
        with col_sel:
            seleccion = st.selectbox(
                "Ver tabla hasta:",
                options=opciones_label,
                index=len(opciones_label) - 1,   # Default: última fecha
                help="Seleccioná una jornada para ver la tabla en ese momento"
            )

        if seleccion == "📊 Todas las fechas":
            hasta = None
            with col_info:
                st.caption(" ")
                st.info("Mostrando el torneo completo")
        else:
            hasta = label_a_fecha[seleccion]
            with col_info:
                st.caption(" ")
                st.success(f"📅 Tabla acumulada hasta el **{seleccion}**")

        tabla = obtener_tabla_posiciones(hasta_fecha=hasta)

        if not tabla:
            st.warning("No hay partidos para esa fecha.")
        else:
            df = pd.DataFrame(tabla)
            df.insert(0, "Pos", range(1, len(df) + 1))

            # Alineamos todo a la izquierda — headers y celdas consistentes
            st.dataframe(
                df.style.set_properties(**{"text-align": "left"})
                  .set_table_styles([{
                      "selector": "th",
                      "props": [("text-align", "left")]
                  }]),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("---")
            st.markdown(
                "**PJ** Jugados &nbsp;|&nbsp; **PG** Ganados &nbsp;|&nbsp; "
                "**PE** Empatados &nbsp;|&nbsp; **PP** Perdidos &nbsp;|&nbsp; "
                "**GF** Goles a favor &nbsp;|&nbsp; **GC** Goles en contra &nbsp;|&nbsp; "
                "**DG** Diferencia &nbsp;|&nbsp; **PTS** Puntos"
            )

            st.markdown("### 📊 Resumen")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Equipos", len(tabla))
            c2.metric("Partidos jugados", sum(e["PJ"] for e in tabla) // 2)
            c3.metric("Goles totales",    sum(e["GF"] for e in tabla))
            c4.metric("Líder", tabla[0]["Equipo"])

            # ── Matriz de resultados ───────────────────────────────────
            st.markdown("---")
            st.markdown("### 🔲 Matriz de resultados")
            st.caption("Resultado del partido entre cada par de equipos · **—** pendiente")

            df_matriz, nombres = obtener_matriz_resultados()

            if df_matriz.empty:
                st.info("No hay partidos jugados todavía.")
            else:
                import base64
                from pathlib import Path
                from queries import _siglas

                ESCUDOS_DIR = Path("assets/escudos")

                def escudo_html(nombre_equipo, size=20):
                    """
                    Busca el archivo de escudo en assets/escudos/<nombre_equipo>.png/jpg
                    Lo convierte a base64 para embeber directo en el HTML.
                    Si no existe el archivo, muestra las siglas como fallback.
                    """
                    for ext in [".png", ".jpg", ".jpeg"]:
                        path = ESCUDOS_DIR / f"{nombre_equipo}{ext}"
                        if path.exists():
                            data = base64.b64encode(path.read_bytes()).decode()
                            mime = "image/png" if ext == ".png" else "image/jpeg"
                            return (
                                f'<img src="data:{mime};base64,{data}" '
                                f'width="{size}" height="{size}" '
                                f'style="object-fit:contain;vertical-align:middle;" '
                                f'title="{nombre_equipo}">'
                            )
                    # Sin escudo: fallback a siglas
                    return f'<span style="font-size:0.7rem;color:#888;">{_siglas(nombre_equipo)}</span>'

                # Reconstruimos partidos_por_par para el HTML
                from database import get_connection as _gc
                _conn = _gc()
                _cur  = _conn.cursor()
                _cur.execute("""
                    SELECT e1.nombre AS local, e2.nombre AS visitante,
                           p.goles_local, p.goles_visitante
                    FROM partidos p
                    JOIN equipos e1 ON p.local_id = e1.id
                    JOIN equipos e2 ON p.visitante_id = e2.id
                """)
                partidos_por_par = {}
                for p in _cur.fetchall():
                    clave = frozenset([p["local"], p["visitante"]])
                    partidos_por_par[clave] = dict(p)
                _conn.close()

                def celda_html(equipo_fila, equipo_col):
                    """Genera el <td> de cada celda con escudos y marcador."""
                    if equipo_fila == equipo_col:
                        return '<td style="background:#2a2a3e;padding:4px 8px;"></td>'

                    clave = frozenset([equipo_fila, equipo_col])
                    p = partidos_por_par.get(clave)

                    if not p:
                        return '<td style="text-align:center;color:#bbb;padding:4px 8px;">—</td>'

                    gl    = p["goles_local"]
                    gv    = p["goles_visitante"]
                    local = p["local"]
                    vis   = p["visitante"]

                    if gl > gv:
                        # Ganador primero, perdedor después
                        contenido = f'{escudo_html(local)} <b>{gl}-{gv}</b> {escudo_html(vis)}'
                    elif gv > gl:
                        contenido = f'{escudo_html(vis)} <b>{gv}-{gl}</b> {escudo_html(local)}'
                    else:
                        # Empate: sin negrita, ambos escudos
                        contenido = f'{escudo_html(local)} {gl}-{gv} {escudo_html(vis)}'

                    return (
                        f'<td style="text-align:center;white-space:nowrap;'
                        f'padding:4px 8px;">{contenido}</td>'
                    )

                # Header de columnas: escudo + siglas
                th_cols = "".join(
                    f'<th style="text-align:center;padding:6px 4px;min-width:75px;">'
                    f'{escudo_html(n, size=22)}<br>'
                    f'<span style="font-size:0.65rem;color:#555;">{_siglas(n)}</span>'
                    f'</th>'
                    for n in nombres
                )

                # Filas: escudo + nombre completo + celdas
                filas_html = []
                for equipo_fila in nombres:
                    td_nombre = (
                        f'<td style="white-space:nowrap;padding:4px 12px 4px 6px;'
                        f'font-size:0.82rem;font-weight:600;border-right:2px solid #e0e0e0;">'
                        f'{escudo_html(equipo_fila, size=18)} {equipo_fila}</td>'
                    )
                    celdas = "".join(celda_html(equipo_fila, n) for n in nombres)
                    filas_html.append(f"<tr>{td_nombre}{celdas}</tr>")

                tabla_html = f"""
                <div style="overflow-x:auto;margin-top:8px;">
                  <table style="border-collapse:collapse;font-size:0.83rem;width:100%;">
                    <thead>
                      <tr>
                        <th style="border-right:2px solid #e0e0e0;"></th>
                        {th_cols}
                      </tr>
                    </thead>
                    <tbody>{"".join(filas_html)}</tbody>
                  </table>
                </div>
                """
                st.markdown(tabla_html, unsafe_allow_html=True)

                st.caption(
                    "En cada celda: el escudo del **ganador** aparece primero · "
                    "en empates ambos escudos al mismo nivel"
                )


# ─────────────────────────────────────────────
# PÁGINA 2 — RESULTADOS
# ─────────────────────────────────────────────

elif pagina == "📋 Resultados":
    st.title("📋 Resultados")

    fechas_info = obtener_fechas_disponibles()

    if not fechas_info:
        st.info("No hay partidos cargados todavía.")
    else:
        opciones_label = ["📋 Todas las fechas"] + [f["label"] for f in fechas_info]
        label_a_fecha  = {f["label"]: f["fecha"] for f in fechas_info}

        seleccion = st.selectbox(
            "Mostrar partidos hasta:",
            options=opciones_label,
            index=len(opciones_label) - 1,
        )

        hasta = None if seleccion == "📋 Todas las fechas" else label_a_fecha[seleccion]
        resultados = obtener_resultados(hasta_fecha=hasta)

        if not resultados:
            st.warning("No hay partidos para esa selección.")
        else:
            # Agrupamos por fecha ISO para poder mostrar el label "Fecha N"
            # Construimos un mapa fecha_iso → label
            iso_a_label = {f["fecha"]: f["label"] for f in fechas_info}

            por_fecha = defaultdict(list)
            for r in resultados:
                por_fecha[r["fecha"]].append(r)

            # Iteramos en orden cronológico inverso (más reciente primero)
            for fecha_iso in sorted(por_fecha.keys(), reverse=True):
                label = iso_a_label.get(fecha_iso, fmt(fecha_iso))
                st.markdown(f"#### 📅 {label} — {fmt(fecha_iso)}")

                for r in por_fecha[fecha_iso]:
                    col_local, col_score, col_visita = st.columns([3, 1.5, 3])
                    col_local.markdown(
                        f"<div style='padding-top:6px;font-weight:600;text-align:right;'>{r['local']}</div>",
                        unsafe_allow_html=True)
                    col_score.markdown(
                        f"<div style='text-align:center;font-size:1.4rem;font-weight:800;"
                        f"background:#16213e;color:white;border-radius:8px;padding:2px 8px;'>"
                        f"{r['goles_local']} — {r['goles_visitante']}</div>",
                        unsafe_allow_html=True)
                    col_visita.markdown(
                        f"<div style='padding-top:6px;font-weight:600;'>{r['visitante']}</div>",
                        unsafe_allow_html=True)

                st.markdown("<hr style='margin:8px 0;border-color:#ddd;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PÁGINA 3 — PRÓXIMA FECHA
# ─────────────────────────────────────────────

elif pagina == "📅 Próxima Fecha":
    st.title("📅 Próxima Fecha")
    st.caption("Partidos programados, cancha y horario")

    proximos = obtener_proximos_partidos()

    if not proximos:
        st.info("No hay partidos programados todavía. Podés cargarlos desde el Panel Admin.")
    else:
        por_fecha = defaultdict(list)
        for p in proximos:
            por_fecha[p["fecha"]].append(p)

        # Calculamos el número de jornada siguiente basado en cuántas ya hubo
        fechas_jugadas = obtener_fechas_disponibles()
        siguiente_num  = len(fechas_jugadas) + 1

        for i, fecha_iso in enumerate(sorted(por_fecha.keys())):
            num_label = f"Fecha {siguiente_num + i} — {fmt(fecha_iso)}"
            st.markdown(f"### 📅 {num_label}")

            for p in por_fecha[fecha_iso]:
                st.markdown(f"""
                <div class="fixture-card">
                    <div class="fixture-vs">
                        {p['local']} <span style="color:#e94560;">vs</span> {p['visitante']}
                    </div>
                    <div class="fixture-meta">
                        🕐 {p['horario']} &nbsp;|&nbsp; 🏟️ {p['cancha']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("")


# ─────────────────────────────────────────────
# PÁGINA 4 — SIMULADOR
# ─────────────────────────────────────────────

elif pagina == "🔮 Simulador":
    st.title("🔮 Simulador de Fecha")
    st.caption("Probá resultados hipotéticos y mirá cómo quedaría la tabla. No se guarda nada.")

    # ── Explicación del session_state ──────────────────────────────────
    # st.session_state es un diccionario que Streamlit mantiene en memoria
    # mientras el navegador está abierto. Al refrescar (F5) se borra solo.
    # Perfecto para datos temporales que no queremos persistir en la DB.
    # ───────────────────────────────────────────────────────────────────

    if "sim_partidos" not in st.session_state:
        st.session_state.sim_partidos = []   # Lista de partidos simulados

    equipos = obtener_equipos()

    if len(equipos) < 2:
        st.error("Necesitás al menos 2 equipos cargados para usar el simulador.")
    else:
        nombres = [e["nombre"] for e in equipos]

        # ── Formulario para agregar un partido simulado ────────────────
        st.markdown("### Agregar resultado hipotético")

        with st.form("form_sim"):
            col1, col2 = st.columns(2)
            with col1:
                sim_local    = st.selectbox("Local",    nombres, key="sim_l")
                sim_gl       = st.number_input("Goles local", min_value=0, max_value=20, value=1, key="sim_gl")
            with col2:
                sim_visitante = st.selectbox("Visitante", nombres, key="sim_v")
                sim_gv        = st.number_input("Goles visitante", min_value=0, max_value=20, value=0, key="sim_gv")

            if st.form_submit_button("➕ Agregar partido simulado"):
                if sim_local == sim_visitante:
                    st.error("Local y visitante no pueden ser el mismo equipo.")
                else:
                    st.session_state.sim_partidos.append({
                        "local":         sim_local,
                        "visitante":     sim_visitante,
                        "goles_local":   sim_gl,
                        "goles_visitante": sim_gv,
                    })
                    st.rerun()

        # ── Partidos simulados cargados ────────────────────────────────
        if st.session_state.sim_partidos:
            st.markdown("### Partidos en simulación")

            st.markdown(
                '<div class="sim-banner">⚠️ Resultados hipotéticos — no están guardados en la base de datos</div>',
                unsafe_allow_html=True
            )

            for i, p in enumerate(st.session_state.sim_partidos):
                col_info, col_del = st.columns([5, 1])
                col_info.markdown(
                    f"**{p['local']}** {p['goles_local']} — {p['goles_visitante']} **{p['visitante']}**"
                )
                if col_del.button("✕", key=f"sim_del_{i}", help="Quitar"):
                    st.session_state.sim_partidos.pop(i)
                    st.rerun()

            # Botón para limpiar todo
            if st.button("🗑️ Limpiar simulación"):
                st.session_state.sim_partidos = []
                st.rerun()

            # ── Tabla proyectada ───────────────────────────────────────
            st.markdown("---")
            st.markdown("### 📊 Tabla proyectada")
            st.caption("Posiciones si estos resultados se confirmaran")

            tabla_sim = calcular_tabla_desde_partidos(st.session_state.sim_partidos)
            df_sim = pd.DataFrame(tabla_sim)
            df_sim.insert(0, "Pos", range(1, len(df_sim) + 1))
            st.dataframe(df_sim, use_container_width=True, hide_index=True)

            # Comparación rápida: ¿quién sube / quién baja?
            tabla_real = obtener_tabla_posiciones()
            pos_real = {e["Equipo"]: i+1 for i, e in enumerate(tabla_real)}
            pos_sim  = {e["Equipo"]: i+1 for i, e in enumerate(tabla_sim)}

            st.markdown("### 📈 Cambios de posición")
            cambios = []
            for equipo, pos_nueva in pos_sim.items():
                pos_anterior = pos_real.get(equipo, pos_nueva)
                delta = pos_anterior - pos_nueva   # positivo = subió
                if delta > 0:
                    icono = f"🟢 +{delta}"
                elif delta < 0:
                    icono = f"🔴 {delta}"
                else:
                    icono = "⚪ ="
                cambios.append({"Equipo": equipo, "Pos. actual": pos_anterior,
                                 "Pos. proyectada": pos_nueva, "Cambio": icono})

            df_cambios = pd.DataFrame(cambios)
            st.dataframe(df_cambios, use_container_width=True, hide_index=True)

        else:
            st.info("Agregá partidos hipotéticos arriba para ver cómo quedaría la tabla.")


# ─────────────────────────────────────────────
# PÁGINA 5 — GOLEADORES
# ─────────────────────────────────────────────

elif pagina == "🥇 Goleadores":
    st.title("🥇 Tabla de Goleadores")
    st.caption("Ranking individual por cantidad de goles convertidos")

    goleadores = obtener_goleadores()

    if not goleadores:
        st.info("Todavía no hay goles registrados.")
    else:
        st.markdown("### 🏅 Top Goleadores")
        cols = st.columns(min(3, len(goleadores)))
        medallas = ["🥇", "🥈", "🥉"]
        for i, col in enumerate(cols):
            g = goleadores[i]
            col.metric(label=f"{medallas[i]} {g['Jugador']}",
                       value=f"{g['Goles']} goles", delta=g["Equipo"])

        st.markdown("---")
        df = pd.DataFrame(goleadores)
        df.insert(0, "#", range(1, len(df) + 1))
        st.dataframe(df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# PÁGINA 6 — PANEL ADMIN (con password)
# ─────────────────────────────────────────────

elif pagina == "🔧 Panel Admin":

    # Si no está autenticado, mostramos el login y cortamos acá
    if not st.session_state.admin_autenticado:
        verificar_password()
        st.stop()   # Nada de lo de abajo se ejecuta si no pasó el login

    # ── A partir de acá: usuario autenticado ──────────────────────────

    col_title, col_logout = st.columns([5, 1])
    col_title.title("🔧 Panel de Administración")
    # Botón de cerrar sesión: simplemente resetea el flag en session_state
    if col_logout.button("🚪 Salir"):
        st.session_state.admin_autenticado = False
        st.rerun()

    st.caption("Cargá resultados, fixture y equipos")

    tab_resultado, tab_fixture, tab_equipos = st.tabs([
        "⚽ Cargar resultado", "📅 Cargar fixture", "🆕 Equipos"
    ])

    # ── TAB 1: Resultado ───────────────────────────────────────────────
    with tab_resultado:
        st.markdown("### Resultado de partido jugado")
        equipos = obtener_equipos()

        if len(equipos) < 2:
            st.error("Necesitás al menos 2 equipos. Agregálos en la pestaña Equipos.")
        else:
            ne = {e["nombre"]: e["id"] for e in equipos}
            ops = list(ne.keys())

            with st.form("form_partido"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Local**")
                    eq_local  = st.selectbox("Equipo local",    ops, key="local")
                    gl        = st.number_input("Goles", min_value=0, max_value=20, value=0, key="gl_l")
                with c2:
                    st.markdown("**Visitante**")
                    eq_visita = st.selectbox("Equipo visitante", ops, key="visitante")
                    gv        = st.number_input("Goles", min_value=0, max_value=20, value=0, key="gl_v")

                fecha_p = st.date_input("Fecha del partido", value=date.today())

                st.markdown("---")
                st.markdown("**Goleadores** *(opcional)*")
                c3, c4 = st.columns(2)
                with c3:
                    gol_ln = st.text_input("Goleador local",    placeholder="Ej: Martín García")
                    gol_lc = st.number_input("Goles convertidos", min_value=0, max_value=20, value=0, key="glc_l")
                with c4:
                    gol_vn = st.text_input("Goleador visitante", placeholder="Ej: Diego Ruiz")
                    gol_vc = st.number_input("Goles convertidos", min_value=0, max_value=20, value=0, key="glc_v")

                if st.form_submit_button("💾 Guardar partido"):
                    if eq_local == eq_visita:
                        st.error("Local y visitante no pueden ser el mismo equipo.")
                    else:
                        lid = ne[eq_local]
                        vid = ne[eq_visita]
                        pid = guardar_partido(lid, vid, gl, gv, str(fecha_p))
                        if gol_ln and gol_lc > 0: guardar_goles(gol_ln, lid, pid, gol_lc)
                        if gol_vn and gol_vc > 0: guardar_goles(gol_vn, vid, pid, gol_vc)
                        st.success(f"✅ {eq_local} {gl} - {gv} {eq_visita} guardado.")
                        st.balloons()

    # ── TAB 2: Fixture ─────────────────────────────────────────────────
    with tab_fixture:
        st.markdown("### Programar próximo partido")
        equipos = obtener_equipos()

        if len(equipos) < 2:
            st.error("Necesitás al menos 2 equipos.")
        else:
            ne = {e["nombre"]: e["id"] for e in equipos}
            ops = list(ne.keys())

            with st.form("form_fixture"):
                c1, c2 = st.columns(2)
                with c1:
                    fx_local  = st.selectbox("Local",    ops, key="fx_l")
                with c2:
                    fx_visita = st.selectbox("Visitante", ops, key="fx_v")

                c3, c4, c5 = st.columns(3)
                with c3: fx_fecha   = st.date_input("Fecha", value=date.today())
                with c4: fx_horario = st.text_input("Horario", placeholder="16:00")
                with c5: fx_cancha  = st.text_input("Cancha",  placeholder="Cancha Municipal")

                if st.form_submit_button("📅 Agregar al fixture"):
                    if fx_local == fx_visita:
                        st.error("Local y visitante no pueden ser el mismo.")
                    elif not fx_horario.strip():
                        st.error("El horario es obligatorio.")
                    elif not fx_cancha.strip():
                        st.error("La cancha es obligatoria.")
                    else:
                        guardar_fixture(ne[fx_local], ne[fx_visita],
                                        str(fx_fecha), fx_horario.strip(), fx_cancha.strip())
                        st.success(f"✅ {fx_local} vs {fx_visita} — {fx_fecha} {fx_horario}")

            st.markdown("---")
            st.markdown("#### Fixture cargado")
            fixture_actual = obtener_fixture_con_ids()

            if not fixture_actual:
                st.info("No hay partidos en el fixture todavía.")
            else:
                for p in fixture_actual:
                    ci, cb = st.columns([5, 1])
                    ci.markdown(
                        f"📅 **{fmt(p['fecha'])}** — {p['local']} vs {p['visitante']} "
                        f"| 🕐 {p['horario']} | 🏟️ {p['cancha']}"
                    )
                    if cb.button("🗑️", key=f"del_fix_{p['id']}", help="Eliminar"):
                        eliminar_fixture(p["id"])
                        st.success("Partido eliminado.")
                        st.rerun()

    # ── TAB 3: Equipos ─────────────────────────────────────────────────
    with tab_equipos:
        st.markdown("### Agregar equipo nuevo")

        with st.form("form_equipo"):
            nombre_eq = st.text_input("Nombre del equipo", placeholder="Ej: San Martín de Luján")
            if st.form_submit_button("➕ Agregar equipo"):
                if not nombre_eq.strip():
                    st.error("El nombre no puede estar vacío.")
                else:
                    ok = agregar_equipo(nombre_eq.strip())
                    if ok:
                        st.success(f"✅ '{nombre_eq}' agregado.")
                    else:
                        st.warning("⚠️ Ya existe un equipo con ese nombre.")

        st.markdown("---")
        st.markdown("#### Equipos registrados")
        for e in obtener_equipos():
            st.markdown(f"- {e['nombre']}")
