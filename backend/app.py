import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("TASKFLOW_DB", os.path.join(BASE_DIR, "taskflow.db"))
JWT_SECRET = os.getenv("JWT_SECRET", "taskflow-local-secret-change-me")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "12"))
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]

STATUS_VALUES = {"todo", "in_progress", "completed"}
PRIORITY_VALUES = {"low", "medium", "high"}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'todo',
            priority TEXT NOT NULL DEFAULT 'medium',
            due_date TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CHECK (status IN ('todo', 'in_progress', 'completed')),
            CHECK (priority IN ('low', 'medium', 'high'))
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(user_id, status);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(user_id, due_date);
        """
    )
    db.commit()
    db.close()


def row_to_dict(row):
    return dict(row) if row else None


def make_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"],
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def get_auth_user():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, ("Authorization token required.", 401)
    token = header[7:].strip()
    if not token:
        return None, ("Authorization token required.", 401)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"id": int(payload["sub"]), "email": payload.get("email", ""), "name": payload.get("name", "")}, None
    except jwt.ExpiredSignatureError:
        return None, ("Session expired. Please log in again.", 401)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        return None, ("Invalid authorization token.", 401)


def require_auth(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user, error = get_auth_user()
        if error:
            return jsonify({"error": error[0]}), error[1]
        return fn(user, *args, **kwargs)
    return wrapped


def validate_task_payload(payload, partial=False):
    errors = {}
    if not partial or "title" in payload:
        title = str(payload.get("title") or "").strip()
        if not title:
            errors["title"] = "Title is required."
        elif len(title) > 160:
            errors["title"] = "Title must be 160 characters or fewer."
    if "description" in payload and len(str(payload.get("description") or "")) > 1200:
        errors["description"] = "Description must be 1200 characters or fewer."
    if "status" in payload and payload["status"] not in STATUS_VALUES:
        errors["status"] = "Invalid task status."
    if "priority" in payload and payload["priority"] not in PRIORITY_VALUES:
        errors["priority"] = "Invalid priority."
    if payload.get("due_date"):
        try:
            datetime.strptime(str(payload["due_date"]), "%Y-%m-%d")
        except ValueError:
            errors["due_date"] = "Due date must use YYYY-MM-DD."
    return errors


@app.get("/api/health")
def health():
    try:
        row = get_db().execute("SELECT 1 AS ok").fetchone()
        return jsonify({"status": "ok", "database": "connected" if row and row["ok"] == 1 else "error"})
    except sqlite3.Error as exc:
        return jsonify({"status": "error", "database": "error", "message": str(exc)}), 503


@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    errors = {}
    if not name or len(name) > 100:
        errors["name"] = "Enter a valid name."
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email."
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    if errors:
        return jsonify({"errors": errors}), 400

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
        user = {"id": cursor.lastrowid, "name": name, "email": email}
        return jsonify({"user": user, "token": make_token(user)}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with that email already exists."}), 409


@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    row = get_db().execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    user = {"id": row["id"], "name": row["name"], "email": row["email"]}
    return jsonify({"user": user, "token": make_token(user)})


@app.get("/api/auth/me")
@require_auth
def me(user):
    row = get_db().execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not row:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": row_to_dict(row)})


@app.get("/api/tasks")
@require_auth
def list_tasks(user):
    status = request.args.get("status")
    priority = request.args.get("priority")
    search = str(request.args.get("search", "")).strip()
    query = "SELECT id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE user_id = ?"
    params = [user["id"]]

    if status in STATUS_VALUES:
        query += " AND status = ?"
        params.append(status)
    if priority in PRIORITY_VALUES:
        query += " AND priority = ?"
        params.append(priority)
    if search:
        query += " AND (LOWER(title) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"
        pattern = f"%{search}%"
        params.extend([pattern, pattern])

    query += " ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC, updated_at DESC"
    rows = get_db().execute(query, params).fetchall()
    return jsonify({"tasks": [row_to_dict(row) for row in rows]})


@app.post("/api/tasks")
@require_auth
def create_task(user):
    payload = request.get_json(silent=True) or {}
    errors = validate_task_payload(payload)
    if errors:
        return jsonify({"errors": errors}), 400

    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    cursor = db.execute(
        """INSERT INTO tasks (user_id, title, description, status, priority, due_date, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user["id"],
            str(payload["title"]).strip(),
            str(payload.get("description", "")).strip(),
            payload.get("status", "todo"),
            payload.get("priority", "medium"),
            payload.get("due_date") or None,
            now,
            now,
        ),
    )
    db.commit()
    row = db.execute("SELECT id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify({"task": row_to_dict(row)}), 201


@app.get("/api/tasks/<int:task_id>")
@require_auth
def get_task(user, task_id):
    row = get_db().execute(
        "SELECT id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user["id"]),
    ).fetchone()
    if not row:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"task": row_to_dict(row)})


@app.patch("/api/tasks/<int:task_id>")
@require_auth
def update_task(user, task_id):
    payload = request.get_json(silent=True) or {}
    errors = validate_task_payload(payload, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    allowed = {"title", "description", "status", "priority", "due_date"}
    fields = []
    params = []
    for key in allowed:
        if key in payload:
            value = payload[key]
            if key in {"title", "description"}:
                value = str(value).strip()
            if key == "due_date":
                value = value or None
            fields.append(f"{key} = ?")
            params.append(value)

    if not fields:
        return jsonify({"error": "No changes supplied."}), 400

    fields.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.extend([task_id, user["id"]])

    db = get_db()
    cursor = db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ? AND user_id = ?", params)
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found."}), 404

    row = db.execute("SELECT id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify({"task": row_to_dict(row)})


@app.delete("/api/tasks/<int:task_id>")
@require_auth
def delete_task(user, task_id):
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"ok": True, "id": task_id})


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found."}), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)
