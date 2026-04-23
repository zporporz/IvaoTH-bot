from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = "/data/ivao.db"


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "IVAO TH Search API"
    })


@app.route("/api/search")
def search():

    dep = request.args.get("dep", "").upper().strip()
    arr = request.args.get("arr", "").upper().strip()
    from_time = request.args.get("from", "").strip()
    to_time = request.args.get("to", "").strip()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    sql = """
        SELECT
            session_id,
            callsign,
            user_id,
            aircraft_id,
            departure,
            arrival,
            connected_at,
            landed_at,
            status,
            last_state
        FROM pilot_sessions
        WHERE 1=1
    """

    params = []

    # departure filter
    if dep:
        sql += " AND departure=?"
        params.append(dep)

    # arrival filter
    if arr:
        sql += " AND arrival=?"
        params.append(arr)

    # from time
    if from_time:
        sql += " AND connected_at >= ?"
        params.append(from_time)

    # to time
    if to_time:
        sql += " AND connected_at <= ?"
        params.append(to_time)

    sql += " ORDER BY connected_at DESC LIMIT 300"

    cur.execute(sql, params)
    rows = cur.fetchall()

    conn.close()

    result = []

    for row in rows:
        result.append({
            "track_id": row[0],
            "callsign": row[1],
            "vid": row[2],
            "aircraft": row[3],
            "dep": row[4],
            "arr": row[5],
            "time": row[6],
            "landed_at": row[7],
            "status": row[8],
            "last_state": row[9]
        })

    return jsonify(result)

@app.route("/api/dashboard")
def dashboard():

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()

    # pilots online
    cur.execute("""
        SELECT COUNT(*)
        FROM pilot_sessions
        WHERE status='online'
    """)
    pilots_online = cur.fetchone()[0]

    # atc online
    cur.execute("""
        SELECT COUNT(*)
        FROM atc_sessions
        WHERE status='online'
    """)
    atc_online = cur.fetchone()[0]

    # observers online
    cur.execute("""
        SELECT COUNT(*)
        FROM observer_sessions
        WHERE status='online'
    """)
    observers_online = cur.fetchone()[0]

    # landed flights
    cur.execute("""
        SELECT COUNT(*)
        FROM pilot_sessions
        WHERE landed_at IS NOT NULL
    """)
    landed = cur.fetchone()[0]

    # missing flights
    cur.execute("""
        SELECT COUNT(*)
        FROM pilot_sessions
        WHERE status='offline'
        AND landed_at IS NULL
    """)
    missing = cur.fetchone()[0]

    # top departures
    cur.execute("""
        SELECT departure, COUNT(*)
        FROM pilot_sessions
        WHERE departure IS NOT NULL
        GROUP BY departure
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    top_departures = []
    for row in cur.fetchall():
        top_departures.append({
            "icao": row[0],
            "count": row[1]
        })

    conn.close()

    return jsonify({
        "pilots_online": pilots_online,
        "atc_online": atc_online,
        "observers_online": observers_online,
        "landed": landed,
        "missing": missing,
        "top_departures": top_departures
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)