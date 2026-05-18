"""
database.py — Conexión y configuración de la base de datos SQLite.
"""

import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "torneo.db")
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    """
    Crea todas las tablas si no existen todavía.
    Seguro correrlo en cada arranque: CREATE TABLE IF NOT EXISTS no rompe nada.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

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

    # Nueva tabla: fixture (próximos partidos programados)
    # A diferencia de 'partidos', acá no hay resultado todavía.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fixture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_id INTEGER NOT NULL,
            visitante_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            horario TEXT NOT NULL DEFAULT '00:00',
            cancha TEXT NOT NULL DEFAULT 'A confirmar',
            FOREIGN KEY (local_id) REFERENCES equipos(id),
            FOREIGN KEY (visitante_id) REFERENCES equipos(id)
        )
    """)

    conn.commit()
    conn.close()


def cargar_datos_demo():
    """Inserta datos de ejemplo solo si la DB está vacía."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM equipos")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    equipos = ["Juventud de San Miguel", "Moron", "San Telmo",
               "Los Andes", "San Miguel",
               "All Boys", "Racing de Cordoba",
               "Club Ciudad de Bolivar", "Colon",
               "Godoy Cruz"
               ]
               
    for nombre in equipos:
        cursor.execute("INSERT INTO equipos (nombre) VALUES (?)", (nombre,))
    conn.commit()

    # Partidos distribuidos en fechas distintas para que el slider tenga sentido
    partidos_demo = [
        (1, 2,  4, 1,  "2025-04-11"), #fecha1
        (5, 6,  0, 5,  "2025-04-11"), #fecha1
        (3, 4,  0, 2,  "2025-04-11"), #fecha1
        (7, 8,  6, 2,  "2025-04-11"), #fecha1
        (9, 10, 2, 3,  "2025-04-11"), #fecha1
        (1, 4,  2, 2,  "2025-04-18"), #fecha2
        (2, 6,  0, 2,  "2025-04-18"), #fecha2
        (3, 8,  1, 2,  "2025-04-18"), #fecha2
        (5, 10, 4, 0,  "2025-04-18"), #fecha2
        (7, 9,  0, 3,  "2025-04-18"), #fecha2
        (1, 6,  1, 0,  "2025-04-25"), #fecha3
        (4, 8,  2, 1,  "2025-04-25"), #fecha3
        (2, 10, 1, 4,  "2025-04-25"), #fecha3
        (3, 9,  2, 2,  "2025-04-25"), #fecha3
        (5, 7,  1, 5,  "2025-04-25"), #fecha3
        (1, 8,  1, 1,  "2025-05-02"), #fecha4
        (6, 10, 1, 4,  "2025-05-02"), #fecha4
        (4, 9,  4, 1,  "2025-05-02"), #fecha4
        (2, 7,  2, 1,  "2025-05-02"), #fecha4
        (3, 5,  1, 1,  "2025-05-02"), #fecha4
        (1, 10, 1, 0,  "2025-05-09"), #fecha5
        (8, 9,  0, 4,  "2025-05-09"), #fecha5
        (6, 7,  1, 1,  "2025-05-09"), #fecha5
        (4, 5,  2, 0,  "2025-05-09"), #fecha5
        (2, 3,  0, 0,  "2025-05-09"), #fecha5
        (1,  7,  4, 1, "2025-05-16"), #fecha6
        (9,  5,  0, 2, "2025-05-16"), #fecha6
        (10, 3, 0, 1,  "2025-05-16"), #fecha6
        (8,  2, 0, 3,  "2025-05-16"), #fecha6
        (6,  4,  2, 0, "2025-05-16")  #fecha6



    ]
    for p in partidos_demo:
        cursor.execute("""
            INSERT INTO partidos (local_id, visitante_id, goles_local, goles_visitante, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, p)
    conn.commit()

    goles_demo = [
    ("FASCELLA JOAQUIN", 10, 1, 7),
    ("PEREYRA JULIAN", 7, 1, 6),
    ("PEREIRA GABRIEL", 9, 1, 5),
    ("TORRES LUCA", 7, 1, 4),
    ("HERRERA EZEQUIEL", 5, 1, 4),
    ("CACERES ENZO", 4, 1, 4),
    ("CORREA RAMIRO", 9, 1, 4),
    ("BELLANTONIO EZEQUIEL", 6, 1, 3),
    ("ALTURRIA NICOLAS", 1, 1, 3),
    ("RODRIGUEZ TOMAS", 4, 1, 3),
    ("DIAZ DIEGO", 1, 1, 2),
    ("BONAVITA ROBERTO", 10, 1, 2),
    ("RUIZ MATIAS", 6, 1, 2),
    ("RAMOS PABLO", 4, 1, 2),
    ("ROMERO IVAN", 2, 1, 2),
    ("QUINTANA MATIAS", 1, 1, 2),
    ("CORVALAN DIEGO", 4, 1, 2),
    ("BENAVENTE GONZALO", 2, 1, 1),
    ("LAZARTE FRANCO", 4, 1, 1),
    ("BAIGORRIA ESTEBAN", 6, 1, 1),
    ("NIEVA ALEJANDRO", 7, 1, 1),
    ("MIRANDA LAUTARO", 7, 1, 1),
    ("BUSTAMANTE MAURO", 9, 1, 1),
    ("GARCIA ABEL", 1, 1, 1),
    ("RODRIGUEZ PABLO", 6, 1, 1),
    ("APEZATO FAVIO", 3, 1, 1),
    ("GOMEZ ALEXIS", 8, 1, 1),
    ("LOPEZ LUCAS", 8, 1, 1),
    ("MARTINEZ LEANDRO", 5, 1, 1),
    ("CASAS AMARU", 10, 1, 1),
    ("LEIVA FRANCO", 10, 1, 1),
    ("TOLOZA LEANDRO", 2, 1, 1),
    ("BENAVENTE NICOLAS", 5, 1, 1),
    ("ARRUGARENA DANIEL", 7, 1, 1),
    ("GUEVARA ENZO", 6, 1, 1),
    ("CAROL TOMAS", 8, 1, 1),
    ("ARIAS MATIAS", 3, 1, 1),
    ("GONZALEZ MATIAS", 9, 1, 1),
    ("BERRA FEDERICO", 6, 1, 1),
    ]
    for g in goles_demo:
        if g[3] > 0:
            cursor.execute(
                "INSERT INTO goles (jugador, equipo_id, partido_id, cantidad) VALUES (?, ?, ?, ?)", g
            )
    conn.commit()

    # Fixture demo: próxima fecha
    fixture_demo = [
    ]
    for f in fixture_demo:
        cursor.execute("""
            INSERT INTO fixture (local_id, visitante_id, fecha, horario, cancha)
            VALUES (?, ?, ?, ?, ?)
        """, f)
    conn.commit()
    conn.close()
