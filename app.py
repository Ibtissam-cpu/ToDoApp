import sqlite3
import os
from flask import Flask, render_template, request, jsonify, abort
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT    NOT NULL CHECK(length(trim(title)) > 0),
                priority  TEXT    NOT NULL DEFAULT 'medium'
                              CHECK(priority IN ('low', 'medium', 'high')),
                done      INTEGER NOT NULL DEFAULT 0,
                created_at TEXT   NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT   NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def row_to_dict(row):
    return dict(row)


def validate_priority(p):
    """Line 36 — edge case: silently reject unknown priority values."""
    return p if p in ("low", "medium", "high") else "medium"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    status   = request.args.get("status", "all")    # all | active | done
    priority = request.args.get("priority", "all")  # all | low | medium | high
    sort     = request.args.get("sort", "created")  # created | priority | title

    query  = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status == "active":
        query += " AND done = 0"
    elif status == "done":
        query += " AND done = 1"

    if priority in ("low", "medium", "high"):
        query += " AND priority = ?"
        params.append(priority)

    order_map = {
        "priority": "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, created_at DESC",
        "title":    "title COLLATE NOCASE ASC",
        "created":  "created_at DESC",
    }
    query += f" ORDER BY {order_map.get(sort, 'created_at DESC')}"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data  = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()

    # Edge case (line 71): empty / whitespace-only title → 400 instead of DB error
    if not title:
        return jsonify({"error": "Title cannot be empty"}), 400

    priority = validate_priority(data.get("priority", "medium"))

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)",
            (title, priority)
        )
        conn.commit()
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()

    return jsonify(row_to_dict(task)), 201


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}

    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            abort(404)

        fields, params = [], []

        if "title" in data:
            title = data["title"].strip()
            # Edge case (line 97): updating to blank title is rejected
            if not title:
                return jsonify({"error": "Title cannot be empty"}), 400
            fields.append("title = ?")
            params.append(title)

        if "priority" in data:
            fields.append("priority = ?")
            params.append(validate_priority(data["priority"]))

        if "done" in data:
            fields.append("done = ?")
            params.append(1 if data["done"] else 0)

        if not fields:
            return jsonify(row_to_dict(task))

        fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat(sep=" ", timespec="seconds"))
        params.append(task_id)

        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
        updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return jsonify(row_to_dict(updated))


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with get_db() as conn:
        task = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            abort(404)
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return "", 204


@app.route("/api/stats", methods=["GET"])
def stats():
    with get_db() as conn:
        total  = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done   = conn.execute("SELECT COUNT(*) FROM tasks WHERE done=1").fetchone()[0]
        by_pri = conn.execute(
            "SELECT priority, COUNT(*) as n FROM tasks GROUP BY priority"
        ).fetchall()

    priority_counts = {r["priority"]: r["n"] for r in by_pri}
    return jsonify({
        "total":    total,
        "done":     done,
        "active":   total - done,
        "percent":  round(done / total * 100) if total else 0,
        "by_priority": priority_counts,
    })


@app.route("/api/tasks/bulk", methods=["PATCH"])
def bulk_update():
    """Mark all active tasks done, or clear all done tasks."""
    data   = request.get_json(silent=True) or {}
    action = data.get("action")

    with get_db() as conn:
        if action == "complete_all":
            conn.execute("UPDATE tasks SET done=1, updated_at=datetime('now') WHERE done=0")
        elif action == "clear_done":
            conn.execute("DELETE FROM tasks WHERE done=1")
        else:
            return jsonify({"error": "Unknown action"}), 400
        conn.commit()

    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
