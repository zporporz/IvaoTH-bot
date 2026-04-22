import sqlite3

DB_NAME = "ivao.db"


def get_conn():
    return sqlite3.connect(DB_NAME, timeout=30)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Better SQLite performance
    cur.execute("PRAGMA journal_mode=WAL;")

    # ---------------- PILOTS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pilot_sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        callsign TEXT,
        rating INTEGER,

        aircraft_id TEXT,
        departure TEXT,
        arrival TEXT,

        connected_at TEXT,
        departed_at TEXT,
        landed_at TEXT,
        disconnected_at TEXT,

        last_state TEXT,
        status TEXT
    )
    """)

    # ---------------- ATC ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS atc_sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        callsign TEXT,
        position TEXT,

        connected_at TEXT,
        disconnected_at TEXT,

        status TEXT
    )
    """)

    # ---------------- OBS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS observer_sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        callsign TEXT,

        connected_at TEXT,
        disconnected_at TEXT,

        status TEXT
    )
    """)

    # ---------------- INDEXES ----------------
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_pilot_callsign
    ON pilot_sessions(callsign)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_pilot_departure
    ON pilot_sessions(departure)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_pilot_arrival
    ON pilot_sessions(arrival)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_pilot_status
    ON pilot_sessions(status)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_atc_status
    ON atc_sessions(status)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_obs_status
    ON observer_sessions(status)
    """)

    conn.commit()
    conn.close()