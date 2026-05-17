"""
queries.py — Todas las consultas SQL de la app en un solo lugar.
"""

import sqlite3
import pandas as pd
from database import get_connection


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _numero_a_nombre_fecha(numero):
    """
    Convierte un número de jornada (1, 2, 3...) al label "Fecha 1", "Fecha 2", etc.
    Lo usamos para mostrar en la UI.
    """
    return f"Fecha {numero}"


def obtener_fechas_disponibles():
    """
    Devuelve lista de dicts: [{fecha: "2025-04-05", numero: 1, label: "Fecha 1 — 05/04/2025"}, ...]
    ordenadas cronológicamente.
    
    El número de jornada se calcula por orden de aparición (la fecha más antigua = Fecha 1).
    Así en la UI podemos mostrar "Fecha 1 — 05/04/2025" en lugar de solo la fecha cruda.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT fecha FROM partidos ORDER BY fecha ASC")
    fechas_raw = [row["fecha"] for row in cursor.fetchall()]
    conn.close()

    resultado = []
    for i, f in enumerate(fechas_raw, start=1):
        # Formateamos la fecha de YYYY-MM-DD a DD/MM/YYYY para mostrar
        partes = f.split("-")
        fecha_legible = f"{partes[2]}/{partes[1]}/{partes[0]}"
        resultado.append({
            "fecha": f,                                          # valor real para SQL
            "numero": i,                                         # número de jornada
            "label": f"Fecha {i} — {fecha_legible}",            # texto en el selectbox
        })

    return resultado


# ─────────────────────────────────────────────
# POSICIONES
# ─────────────────────────────────────────────

def obtener_tabla_posiciones(hasta_fecha=None):
    """
    Calcula la tabla de posiciones.
    hasta_fecha: string "YYYY-MM-DD" o None (= todo el torneo).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre FROM equipos ORDER BY nombre")
    equipos = cursor.fetchall()

    tabla = []
    for equipo in equipos:
        eid = equipo["id"]
        nombre = equipo["nombre"]

        filtro = "AND fecha <= ?" if hasta_fecha else ""
        params = (eid, hasta_fecha) if hasta_fecha else (eid,)

        cursor.execute(f"""
            SELECT goles_local AS gf, goles_visitante AS gc
            FROM partidos WHERE local_id = ? {filtro}
        """, params)
        como_local = cursor.fetchall()

        cursor.execute(f"""
            SELECT goles_visitante AS gf, goles_local AS gc
            FROM partidos WHERE visitante_id = ? {filtro}
        """, params)
        como_visitante = cursor.fetchall()

        todos = list(como_local) + list(como_visitante)
        if not todos:
            continue

        pj = len(todos)
        pg = sum(1 for p in todos if p["gf"] > p["gc"])
        pe = sum(1 for p in todos if p["gf"] == p["gc"])
        pp = sum(1 for p in todos if p["gf"] < p["gc"])
        gf = sum(p["gf"] for p in todos)
        gc = sum(p["gc"] for p in todos)
        dg = gf - gc
        pts = pg * 3 + pe

        tabla.append({
            "Equipo": nombre,
            "PJ": pj, "PG": pg, "PE": pe, "PP": pp,
            "GF": gf, "GC": gc, "DG": dg, "PTS": pts,
        })

    conn.close()
    tabla.sort(key=lambda x: (x["PTS"], x["DG"]), reverse=True)
    return tabla


def calcular_tabla_desde_partidos(partidos_extra):
    """
    Igual que obtener_tabla_posiciones() pero en memoria, sin tocar la DB.
    
    Recibe una lista de dicts con la estructura:
      {"local": "Equipo A", "visitante": "Equipo B", "goles_local": 2, "goles_visitante": 1}
    
    Combina los partidos reales de la DB con estos partidos simulados
    y devuelve una tabla calculada. Se usa para el simulador.
    """
    # Primero levantamos la tabla actual desde la DB
    base = obtener_tabla_posiciones()
    
    # Convertimos a dict {nombre: fila} para poder actualizar fácil
    tabla_dict = {e["Equipo"]: dict(e) for e in base}

    for p in partidos_extra:
        local     = p["local"]
        visitante = p["visitante"]
        gl        = p["goles_local"]
        gv        = p["goles_visitante"]

        # Si el equipo no estaba en la tabla todavía, lo inicializamos
        for nombre in [local, visitante]:
            if nombre not in tabla_dict:
                tabla_dict[nombre] = {
                    "Equipo": nombre,
                    "PJ": 0, "PG": 0, "PE": 0, "PP": 0,
                    "GF": 0, "GC": 0, "DG": 0, "PTS": 0,
                }

        # Actualizamos local
        e = tabla_dict[local]
        e["PJ"] += 1
        e["GF"] += gl
        e["GC"] += gv
        if gl > gv:   e["PG"] += 1; e["PTS"] += 3
        elif gl == gv: e["PE"] += 1; e["PTS"] += 1
        else:          e["PP"] += 1
        e["DG"] = e["GF"] - e["GC"]

        # Actualizamos visitante
        e = tabla_dict[visitante]
        e["PJ"] += 1
        e["GF"] += gv
        e["GC"] += gl
        if gv > gl:   e["PG"] += 1; e["PTS"] += 3
        elif gv == gl: e["PE"] += 1; e["PTS"] += 1
        else:          e["PP"] += 1
        e["DG"] = e["GF"] - e["GC"]

    tabla = list(tabla_dict.values())
    tabla.sort(key=lambda x: (x["PTS"], x["DG"]), reverse=True)
    return tabla


# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────

def obtener_resultados(hasta_fecha=None):
    """Lista de partidos jugados. Si hasta_fecha, filtra por fecha <= ese valor."""
    conn = get_connection()
    cursor = conn.cursor()

    filtro = "WHERE p.fecha <= ?" if hasta_fecha else ""
    params = (hasta_fecha,) if hasta_fecha else ()

    cursor.execute(f"""
        SELECT 
            e1.nombre AS local,
            p.goles_local,
            p.goles_visitante,
            e2.nombre AS visitante,
            p.fecha
        FROM partidos p
        JOIN equipos e1 ON p.local_id = e1.id
        JOIN equipos e2 ON p.visitante_id = e2.id
        {filtro}
        ORDER BY p.fecha DESC
    """, params)

    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


# ─────────────────────────────────────────────
# GOLEADORES
# ─────────────────────────────────────────────

def obtener_goleadores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.jugador AS Jugador, e.nombre AS Equipo, SUM(g.cantidad) AS Goles
        FROM goles g
        JOIN equipos e ON g.equipo_id = e.id
        GROUP BY g.jugador, g.equipo_id
        ORDER BY Goles DESC
    """)
    goleadores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return goleadores


# ─────────────────────────────────────────────
# EQUIPOS
# ─────────────────────────────────────────────

def obtener_equipos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM equipos ORDER BY nombre")
    equipos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return equipos


def agregar_equipo(nombre):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO equipos (nombre) VALUES (?)", (nombre,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


# ─────────────────────────────────────────────
# PARTIDOS (resultados reales)
# ─────────────────────────────────────────────

def guardar_partido(local_id, visitante_id, goles_local, goles_visitante, fecha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO partidos (local_id, visitante_id, goles_local, goles_visitante, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (local_id, visitante_id, goles_local, goles_visitante, fecha))
    conn.commit()
    pid = cursor.lastrowid
    conn.close()
    return pid


def guardar_goles(jugador, equipo_id, partido_id, cantidad):
    if cantidad <= 0:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO goles (jugador, equipo_id, partido_id, cantidad)
        VALUES (?, ?, ?, ?)
    """, (jugador, equipo_id, partido_id, cantidad))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# FIXTURE
# ─────────────────────────────────────────────

def obtener_proximos_partidos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e1.nombre AS local, e2.nombre AS visitante,
               f.fecha, f.horario, f.cancha
        FROM fixture f
        JOIN equipos e1 ON f.local_id = e1.id
        JOIN equipos e2 ON f.visitante_id = e2.id
        ORDER BY f.fecha ASC, f.horario ASC
    """)
    partidos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return partidos


def obtener_fixture_con_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id, e1.nombre AS local, e2.nombre AS visitante,
               f.fecha, f.horario, f.cancha
        FROM fixture f
        JOIN equipos e1 ON f.local_id = e1.id
        JOIN equipos e2 ON f.visitante_id = e2.id
        ORDER BY f.fecha ASC, f.horario ASC
    """)
    partidos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return partidos


def guardar_fixture(local_id, visitante_id, fecha, horario, cancha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fixture (local_id, visitante_id, fecha, horario, cancha)
        VALUES (?, ?, ?, ?, ?)
    """, (local_id, visitante_id, fecha, horario, cancha))
    conn.commit()
    conn.close()


def eliminar_fixture(fixture_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fixture WHERE id = ?", (fixture_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# MATRIZ DE RESULTADOS
# ─────────────────────────────────────────────

def obtener_matriz_resultados():
    """
    Construye la matriz de doble entrada: quién jugó contra quién y el resultado.

    Retorna un DataFrame donde:
    - Las filas son el equipo LOCAL
    - Las columnas son el equipo VISITANTE
    - Cada celda muestra "GL - GV" si el partido se jugó, o "—" si no

    La diagonal (equipo contra sí mismo) se marca con "·" para que
    visualmente quede claro que esa celda no tiene sentido.

    Ejemplo:
                    Villa Sur   Deportivo   Racing
    Los Pibes FC      3 - 1       2 - 0      —
    Villa Sur           ·          —        1 - 1
    Deportivo           —          ·         —
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Traemos todos los equipos ordenados alfabéticamente
    cursor.execute("SELECT id, nombre FROM equipos ORDER BY nombre")
    equipos = cursor.fetchall()

    # Traemos todos los partidos jugados con nombres de equipos
    cursor.execute("""
        SELECT e1.nombre AS local, e2.nombre AS visitante,
               p.goles_local, p.goles_visitante
        FROM partidos p
        JOIN equipos e1 ON p.local_id  = e1.id
        JOIN equipos e2 ON p.visitante_id = e2.id
    """)
    partidos = cursor.fetchall()
    conn.close()

    nombres = [e["nombre"] for e in equipos]

def _siglas(nombre):
    """
    Genera las siglas de un equipo a partir de su nombre.
    Toma la primera letra de cada palabra significativa (ignora artículos).
    Ej: "Los Pibes FC" → "LPF", "Villa Sur United" → "VSU"
    """
    ignorar = {"de", "del", "la", "el", "los", "las", "y", "e"}
    palabras = [p for p in nombre.split() if p.lower() not in ignorar]
    return "".join(p[0].upper() for p in palabras[:4])


def obtener_matriz_resultados():
    """
    Matriz de doble entrada: fila = rival, columna = cualquier equipo.
    
    Cada celda muestra el resultado del partido entre esos dos equipos.
    El formato es siempre desde un punto de vista neutral:
      "3-1 ✔ LPF ganó"   → hubo ganador
      "1-1 = Empate"      → empate
      "—"                 → partido no jugado todavía
      "·"                 → diagonal (mismo equipo)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre FROM equipos ORDER BY nombre")
    equipos = cursor.fetchall()

    cursor.execute("""
        SELECT e1.nombre AS local, e2.nombre AS visitante,
               p.goles_local, p.goles_visitante
        FROM partidos p
        JOIN equipos e1 ON p.local_id  = e1.id
        JOIN equipos e2 ON p.visitante_id = e2.id
    """)
    partidos = cursor.fetchall()
    conn.close()

    nombres = [e["nombre"] for e in equipos]

    # Dict por par: frozenset({A, B}) → partido
    partidos_por_par = {}
    for p in partidos:
        clave = frozenset([p["local"], p["visitante"]])
        partidos_por_par[clave] = dict(p)

    filas = []
    for equipo_fila in nombres:
        fila = {"Equipo": equipo_fila}
        for equipo_col in nombres:
            if equipo_fila == equipo_col:
                fila[equipo_col] = "·"
                continue

            clave = frozenset([equipo_fila, equipo_col])
            p = partidos_por_par.get(clave)

            if not p:
                fila[equipo_col] = "—"
            else:
                gl = p["goles_local"]
                gv = p["goles_visitante"]
                local    = p["local"]
                visitante = p["visitante"]

                if gl > gv:
                    fila[equipo_col] = f"{gl}-{gv}"
                elif gv > gl:
                    fila[equipo_col] = f"{gv}-{gl}"
                else:
                    fila[equipo_col] = f"{gl}-{gv}"

        filas.append(fila)

    df = pd.DataFrame(filas).set_index("Equipo")
    return df, nombres
