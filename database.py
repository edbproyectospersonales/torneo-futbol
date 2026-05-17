"""
database.py — Conexión y configuración de la base de datos SQLite.

Este archivo hace tres cosas:
1. Crea (o conecta) la base de datos SQLite
2. Define las tablas si no existen
3. Expone una función get_connection() para usarla desde cualquier parte de la app
"""

import sqlite3
import os

# Si existe la variable de entorno DB_PATH (seteada en docker-compose.yml),
# la usamos. Si no (desarrollo local sin Docker), usamos torneo.db aquí mismo.
DB_PATH = os.environ.get("DB_PATH", "torneo.db")


def get_connection():
    """
    Retorna una conexión activa a la base de datos SQLite.
    
    Usamos check_same_thread=False porque Streamlit corre en múltiples
    hilos y SQLite por defecto se queja de eso.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Esto hace que los resultados vengan como diccionarios (más cómodo)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    """
    Crea todas las tablas si todavía no existen.
    Esta función se llama al arrancar la app.
    
    Tablas:
    - equipos: los equipos del torneo
    - partidos: los partidos jugados (fecha, resultado, equipos)
    - goles: quién convirtió cada gol
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de equipos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    # Tabla de partidos
    # local_id y visitante_id referencian a equipos.id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_id INTEGER NOT NULL,
            visitante_id INTEGER NOT NULL,
            goles_local INTEGER NOT NULL DEFAULT 0,
            goles_visitante INTEGER NOT NULL DEFAULT 0,
            fecha TEXT NOT NULL,
            FOREIGN KEY (local_id) REFERENCES equipos(id),
            FOREIGN KEY (visitante_id) REFERENCES equipos(id)
        )
    """)

    # Tabla de goles individuales
    # partido_id referencia a partidos.id, equipo_id a equipos.id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jugador TEXT NOT NULL,
            equipo_id INTEGER NOT NULL,
            partido_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (equipo_id) REFERENCES equipos(id),
            FOREIGN KEY (partido_id) REFERENCES partidos(id)
        )
    """)

    conn.commit()
    conn.close()


def cargar_datos_demo():
    """
    Inserta datos de ejemplo para que la app no arranque vacía.
    Solo corre si no hay equipos cargados.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Si ya hay equipos, no hacemos nada
    cursor.execute("SELECT COUNT(*) FROM equipos")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Insertar equipos
    equipos = ["Los Pibes FC", "Villa Sur United", "Deportivo Cañuelas",
               "Racing de Barrio", "Atlético Merlo"]
    for nombre in equipos:
        cursor.execute("INSERT INTO equipos (nombre) VALUES (?)", (nombre,))

    conn.commit()

    # Insertar algunos partidos de ejemplo
    partidos_demo = [
        (1, 2, 3, 1, "2025-04-05"),
        (3, 4, 0, 2, "2025-04-05"),
        (5, 1, 1, 1, "2025-04-12"),
        (2, 3, 2, 2, "2025-04-12"),
        (4, 5, 3, 0, "2025-04-19"),
        (1, 3, 2, 0, "2025-04-26"),
        (2, 4, 1, 1, "2025-04-26"),
    ]
    for p in partidos_demo:
        cursor.execute("""
            INSERT INTO partidos (local_id, visitante_id, goles_local, goles_visitante, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, p)

    conn.commit()

    # Insertar goles de ejemplo
    goles_demo = [
        ("Martín García", 1, 1, 2),
        ("Lucas Pérez", 1, 1, 1),
        ("Diego Ruiz", 2, 1, 1),
        ("Sergio López", 4, 2, 2),
        ("Nicolás Torres", 4, 2, 2),  # (mismo partido, 2 goles)
        ("Martín García", 1, 3, 1),
        ("Pablo Sosa", 5, 3, 1),
        ("Diego Ruiz", 2, 4, 2),
        ("Carlos Vega", 3, 4, 2),
        ("Sergio López", 4, 5, 3),
        ("Martín García", 1, 6, 2),
        ("Lucas Pérez", 1, 6, 0),  # no convirtió en ese partido
        ("Diego Ruiz", 2, 7, 1),
        ("Nicolás Torres", 4, 7, 1),
    ]
    for g in goles_demo:
        # Solo insertamos si la cantidad es mayor a 0
        if g[3] > 0:
            cursor.execute("""
                INSERT INTO goles (jugador, equipo_id, partido_id, cantidad)
                VALUES (?, ?, ?, ?)
            """, g)

    conn.commit()
    conn.close()
