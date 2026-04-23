from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = "/data/ivao.db"

@app.route("/api/search")
def search():
    dep = request.args.get("dep", "").upper()
    arr = request.args.get("arr", "").upper()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT callsign, user_id, aircraft_id, departure, arrival, connected_at
        FROM pilot_sessions
        WHERE departure=? AND arrival=?
        ORDER BY connected_at DESC
        LIMIT 50
    """, (dep, arr))

    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "callsign": row[0],
            "vid": row[1],
            "aircraft": row[2],
            "dep": row[3],
            "arr": row[4],
            "time": row[5]
        })

    return jsonify(result)