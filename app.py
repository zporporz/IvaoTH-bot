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
        SELECT session_id, callsign, user_id, aircraft_id,
                departure, arrival, connected_at, status
        FROM pilot_sessions
        WHERE 1=1
    """

    params = []

    # dep filter
    if dep:
        sql += " AND departure=?"
        params.append(dep)

    # arr filter
    if arr:
        sql += " AND arrival=?"
        params.append(arr)

    # time filter
    if from_time:
        sql += " AND connected_at >= ?"
        params.append(from_time)

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
            "status": row[7]           
        })

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)