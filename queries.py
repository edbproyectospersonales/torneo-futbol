"""
queries.py — Todas las consultas SQL de la app en un solo lugar.

Separar las queries del código de interfaz es una buena práctica:
- Más fácil de leer y mantener
- Si cambia la lógica SQL, solo tocás este archivo
- Las funciones retornan listas de diccionarios, listas como filas limpias
"""

import sqlite3
from database import get_connection


def obtener_tabla_posiciones():
    """
    Calcula la tabla de posiciones desde los partidos jugados.
    
    Por cada equipo cuenta:
    - PJ: partidos jugados
    - PG: partidos ganados (3 puntos)
    - PE: empatados (1 punto)
    - PP: perdidos (0 puntos)
    - GF: goles a favor
    - GC: goles en contra
    - DG: diferencia de gol (GF - GC)
    - PTS: puntos totales
    
    Retorna una lista de diccionarios, ordenada por puntos (desc) y DG (desc).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Primero traemos todos los equipos
    cursor.execute("SELECT id, nombre FROM equipos ORDER BY nombre")
    equipos = cursor.fetchall()

    tabla = []
    for equipo in equipos:
        eid = equipo["id"]
        nombre = equipo["nombre"]

        # Partidos como local
        cursor.execute("""
            SELECT goles_local AS gf, goles_visitante AS gc
            FROM partidos WHERE local_id = ?
        """, (eid,))
        como_local = cursor.fetchall()

        # Partidos como visitante
        cursor.execute("""
            SELECT goles_visitante AS gf, goles_local AS gc
            FROM partidos WHERE visitante_id = ?
        """, (eid,))
        como_visitante = cursor.fetchall()

        todos = list(como_local) + list(como_visitante)

        pj = len(todos)
        pg = sum(1 for p in todos if p["gf"] > p["gc"])
        pe = sum(1 for p in todos if p["gf"] == p["gc"])
        pp = sum(1 for p in todos if p["gf"] < p["gc"])
        gf = sum(p["gf"] for p in todos)
        gc = sum(p["gc"] for p in todos)
        dg = gf - gc
        pts = pg * 3 + pe * 1

        tabla.append({
            "Equipo": nombre,
            "PJ": pj,
            "PG": pg,
            "PE": pe,
            "PP": pp,
            "GF": gf,
            "GC": gc,
            "DG": dg,
            "PTS": pts,
        })

    conn.close()

    # Ordenar: primero por puntos, luego por diferencia de gol
    tabla.sort(key=lambda x: (x["PTS"], x["DG"]), reverse=True)
    return tabla


def obtener_resultados():
    """
    Devuelve la lista de partidos jugados con nombres de equipos y fecha.
    Ordenados del más reciente al más antiguo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e1.nombre AS local,
            p.goles_local,
            p.goles_visitante,
            e2.nombre AS visitante,
            p.fecha
        FROM partidos p
        JOIN equipos e1 ON p.local_id = e1.id
        JOIN equipos e2 ON p.visitante_id = e2.id
        ORDER BY p.fecha DESC
    """)

    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados


def obtener_goleadores():
    """
    Suma los goles de cada jugador y devuelve el ranking.
    Ordenado por cantidad de goles de mayor a menor.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            g.jugador AS Jugador,
            e.nombre AS Equipo,
            SUM(g.cantidad) AS Goles
        FROM goles g
        JOIN equipos e ON g.equipo_id = e.id
        GROUP BY g.jugador, g.equipo_id
        ORDER BY Goles DESC
    """)

    goleadores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return goleadores


def obtener_equipos():
    """
    Retorna todos los equipos como lista de dicts {id, nombre}.
    Útil para poblar selectores en el formulario admin.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM equipos ORDER BY nombre")
    equipos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return equipos


def guardar_partido(local_id, visitante_id, goles_local, goles_visitante, fecha):
    """
    Inserta un nuevo partido en la base de datos.
    Retorna el ID del partido recién creado (lo necesitamos para los goles).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO partidos (local_id, visitante_id, goles_local, goles_visitante, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (local_id, visitante_id, goles_local, goles_visitante, fecha))

    conn.commit()
    partido_id = cursor.lastrowid  # SQLite te da el ID del último insert
    conn.close()
    return partido_id


def guardar_goles(jugador, equipo_id, partido_id, cantidad):
    """
    Inserta los goles de un jugador para un partido específico.
    """
    if cantidad <= 0:
        return  # No guardamos si no convirtió goles

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO goles (jugador, equipo_id, partido_id, cantidad)
        VALUES (?, ?, ?, ?)
    """, (jugador, equipo_id, partido_id, cantidad))

    conn.commit()
    conn.close()


def agregar_equipo(nombre):
    """
    Agrega un nuevo equipo al torneo.
    Retorna True si se creó bien, False si ya existía (UNIQUE constraint).
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO equipos (nombre) VALUES (?)", (nombre,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # El equipo ya existe (nombre UNIQUE)
        conn.close()
        return False
