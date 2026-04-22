import sqlite3

DB_NAME = "ivao.db"


def get_conn():
    return sqlite3.connect(DB_NAME, timeout=30)


def process_data(data):
    conn = get_conn()
    cur = conn.cursor()

    try:
        pilots = data["clients"]["pilots"]
        atcs = data["clients"]["atcs"]
        observers = data["clients"]["observers"]

        online_pilot_ids = set()
        online_atc_ids = set()
        online_obs_ids = set()

        # ---------------- PILOTS ----------------
        for p in pilots:
            sid = p["id"]
            online_pilot_ids.add(sid)

            fp = p.get("flightPlan") or {}
            track = p.get("lastTrack") or {}

            state = track.get("state")

            cur.execute("""
                SELECT session_id, departed_at, landed_at
                FROM pilot_sessions
                WHERE session_id=?
            """, (sid,))
            row = cur.fetchone()

            if row is None:
                # New session
                cur.execute("""
                INSERT INTO pilot_sessions (
                    session_id, user_id, callsign, rating,
                    aircraft_id, departure, arrival,
                    connected_at, last_state, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sid,
                    p.get("userId"),
                    p.get("callsign"),
                    p.get("rating"),
                    fp.get("aircraftId"),
                    fp.get("departureId"),
                    fp.get("arrivalId"),
                    p.get("createdAt"),
                    state,
                    "online"
                ))

            else:
                departed_at = row[1]
                landed_at = row[2]

                # Detect departure
                if departed_at is None and state in [
                    "Departing", "Climbing", "En Route", "Approach", "Landed"
                ]:
                    cur.execute("""
                    UPDATE pilot_sessions
                    SET departed_at=CURRENT_TIMESTAMP
                    WHERE session_id=?
                    """, (sid,))

                # Detect landing
                if landed_at is None and state == "Landed":
                    cur.execute("""
                    UPDATE pilot_sessions
                    SET landed_at=CURRENT_TIMESTAMP
                    WHERE session_id=?
                    """, (sid,))

                # Always refresh online state
                cur.execute("""
                UPDATE pilot_sessions
                SET last_state=?, status='online'
                WHERE session_id=?
                """, (state, sid))

        # Mark offline pilots
        cur.execute("""
            SELECT session_id
            FROM pilot_sessions
            WHERE status='online'
        """)

        for row in cur.fetchall():
            sid = row[0]

            if sid not in online_pilot_ids:
                cur.execute("""
                UPDATE pilot_sessions
                SET disconnected_at=CURRENT_TIMESTAMP,
                    status='offline'
                WHERE session_id=?
                AND disconnected_at IS NULL
                """, (sid,))

        # ---------------- ATC ----------------
        for a in atcs:
            sid = a["id"]
            online_atc_ids.add(sid)

            pos = (a.get("atcSession") or {}).get("position")

            cur.execute("""
                SELECT session_id
                FROM atc_sessions
                WHERE session_id=?
            """, (sid,))
            row = cur.fetchone()

            if row is None:
                cur.execute("""
                INSERT INTO atc_sessions (
                    session_id, user_id, callsign, position,
                    connected_at, status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sid,
                    a.get("userId"),
                    a.get("callsign"),
                    pos,
                    a.get("createdAt"),
                    "online"
                ))
            else:
                cur.execute("""
                UPDATE atc_sessions
                SET status='online'
                WHERE session_id=?
                """, (sid,))

        # Mark offline ATC
        cur.execute("""
            SELECT session_id
            FROM atc_sessions
            WHERE status='online'
        """)

        for row in cur.fetchall():
            sid = row[0]

            if sid not in online_atc_ids:
                cur.execute("""
                UPDATE atc_sessions
                SET disconnected_at=CURRENT_TIMESTAMP,
                    status='offline'
                WHERE session_id=?
                AND disconnected_at IS NULL
                """, (sid,))

        # ---------------- OBS ----------------
        for o in observers:
            sid = o["id"]
            online_obs_ids.add(sid)

            cur.execute("""
                SELECT session_id
                FROM observer_sessions
                WHERE session_id=?
            """, (sid,))
            row = cur.fetchone()

            if row is None:
                cur.execute("""
                INSERT INTO observer_sessions (
                    session_id, user_id, callsign,
                    connected_at, status
                )
                VALUES (?, ?, ?, ?, ?)
                """, (
                    sid,
                    o.get("userId"),
                    o.get("callsign"),
                    o.get("createdAt"),
                    "online"
                ))
            else:
                cur.execute("""
                UPDATE observer_sessions
                SET status='online'
                WHERE session_id=?
                """, (sid,))

        # Mark offline OBS
        cur.execute("""
            SELECT session_id
            FROM observer_sessions
            WHERE status='online'
        """)

        for row in cur.fetchall():
            sid = row[0]

            if sid not in online_obs_ids:
                cur.execute("""
                UPDATE observer_sessions
                SET disconnected_at=CURRENT_TIMESTAMP,
                    status='offline'
                WHERE session_id=?
                AND disconnected_at IS NULL
                """, (sid,))

        conn.commit()

    finally:
        conn.close()