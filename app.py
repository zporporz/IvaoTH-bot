from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = "/data/ivao.db"

@app.route("/api/search")
def search():

    dep = request.args.get("dep", "").upper().strip()
    arr = request.args.get("arr", "").upper().strip()
    from_time = request.args.get("from", "").strip()
    to_time = request.args.get("to", "").strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sql = """
        SELECT callsign, user_id, aircraft_id,
               departure, arrival, connected_at
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

    sql += " ORDER BY connected_at DESC LIMIT 100"

    cur.execute(sql, params)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)