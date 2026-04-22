import sqlite3

DB_NAME = "ivao.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


# ---------------- AIRPORT STATS ----------------
def get_airport_stats(icao):
    conn = get_conn()
    cur = conn.cursor()

    icao = icao.upper()

    # departures จริง
    cur.execute("""
    SELECT COUNT(*)
    FROM pilot_sessions
    WHERE departure = ?
    AND departed_at IS NOT NULL
    AND DATE(departed_at)=DATE('now')
    """, (icao,))
    dep_count = cur.fetchone()[0]

    # arrivals จริง
    cur.execute("""
    SELECT COUNT(*)
    FROM pilot_sessions
    WHERE arrival = ?
    AND landed_at IS NOT NULL
    AND DATE(landed_at)=DATE('now')
    """, (icao,))
    arr_count = cur.fetchone()[0]

    # missing inbound
    cur.execute("""
    SELECT COUNT(*)
    FROM pilot_sessions
    WHERE arrival = ?
    AND landed_at IS NULL
    AND status='offline'
    """, (icao,))
    missing = cur.fetchone()[0]

    conn.close()

    return (
        f"📍 {icao} Today\n"
        f"🛫 Departures: {dep_count}\n"
        f"🛬 Arrivals: {arr_count}\n"
        f"⚠️ Missing: {missing}"
    )
def get_airport_activity(icao):
    conn = get_conn()
    cur = conn.cursor()

    icao = icao.upper()

    cur.execute("""
    SELECT COUNT(*)
    FROM pilot_sessions
    WHERE (departure=? OR arrival=?)
    AND DATE(connected_at)=DATE('now')
    """, (icao, icao))

    total = cur.fetchone()[0]
    conn.close()

    return f"📡 {icao} Sessions Today: {total}"

# ---------------- PILOT HISTORY ----------------
def get_pilot_history(callsign):
    conn = get_conn()
    cur = conn.cursor()

    callsign = callsign.upper()

    cur.execute("""
    SELECT callsign, departure, arrival, departed_at, landed_at, status
    FROM pilot_sessions
    WHERE callsign = ?
    ORDER BY connected_at DESC
    LIMIT 5
    """, (callsign,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"No history for {callsign}"

    result = [f"✈️ History {callsign}"]

    for row in rows:
        dep = row[1] or "----"
        arr = row[2] or "----"
        dep_time = row[3] or "-"
        land_time = row[4] or "-"
        status = row[5]

        result.append(f"{dep} → {arr} | DEP {dep_time} | LAND {land_time} | {status}")

    return "\n".join(result)


# ---------------- MISSING FLIGHTS ----------------
def get_missing_flights():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT callsign, departure, arrival
    FROM pilot_sessions
    WHERE landed_at IS NULL
    AND status = 'offline'
    ORDER BY connected_at DESC
    LIMIT 20
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "✅ No missing flights"

    result = ["⚠️ Missing Flights"]

    for row in rows:
        result.append(f"{row[0]} {row[1]} → {row[2]}")

    return "\n".join(result)

# ---------------- ATC ONLINE ----------------
def get_atc_online(keyword=None):
    conn = get_conn()
    cur = conn.cursor()

    if keyword:
        keyword = keyword.upper() + "%"

        cur.execute("""
        SELECT callsign, position, connected_at
        FROM atc_sessions
        WHERE status='online'
        AND callsign LIKE ?
        ORDER BY callsign
        """, (keyword,))
    else:
        cur.execute("""
        SELECT callsign, position, connected_at
        FROM atc_sessions
        WHERE status='online'
        ORDER BY callsign
        """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No ATC online"

    result = ["🎧 ATC Online"]

    for row in rows:
        result.append(f"{row[0]} ({row[1]}) since {row[2]}")

    return "\n".join(result)


# ---------------- ATC TODAY ----------------
def get_atc_today():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT callsign, position
    FROM atc_sessions
    WHERE DATE(connected_at)=DATE('now')
    ORDER BY connected_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No ATC today"

    result = ["🎧 ATC Today"]

    for row in rows[:20]:
        result.append(f"{row[0]} ({row[1]})")

    return "\n".join(result)


# ---------------- OBS ONLINE ----------------
def get_obs_online():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT callsign
    FROM observer_sessions
    WHERE status='online'
    ORDER BY callsign
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No observers online"

    result = ["👀 Observers Online"]

    for row in rows:
        result.append(row[0])

    return "\n".join(result)


# ---------------- OBS TODAY ----------------
def get_obs_today():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT callsign
    FROM observer_sessions
    WHERE DATE(connected_at)=DATE('now')
    ORDER BY connected_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No observers today"

    result = ["👀 Observers Today"]

    for row in rows[:20]:
        result.append(row[0])

    return "\n".join(result)    