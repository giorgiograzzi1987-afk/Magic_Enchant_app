from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "database" / "magic_enchant.db"
SCHEMA_PATH = BASE_DIR.parent / "database" / "database.sql"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    initialize = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if initialize:
        init_db(conn)
    else:
        ensure_character_columns(conn)
    return conn


def ensure_character_columns(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(character_profile)").fetchall()
    }
    if "name" not in columns:
        conn.execute("ALTER TABLE character_profile ADD COLUMN name TEXT")
    if "subclass" not in columns:
        conn.execute("ALTER TABLE character_profile ADD COLUMN subclass TEXT")


def init_db(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    ensure_character_columns(conn)
    conn.commit()


@app.route("/")
def index() -> Any:
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/character", methods=["GET", "POST"])
def character() -> Any:
    conn = get_db()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        class_name = data.get("class_name")
        subclass = data.get("subclass")
        level = data.get("level")
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = None
        if level is not None and (level < 1 or level > 20):
            return jsonify({"error": "level_out_of_range"}), 400
        conn.execute(
            """
            UPDATE character_profile
            SET name = ?, class_name = ?, subclass = ?, level = ?
            WHERE id = 1
            """,
            (name, class_name, subclass, level or 1),
        )
        conn.commit()

    row = conn.execute(
        "SELECT name, class_name, subclass, level FROM character_profile WHERE id = 1"
    ).fetchone()
    return jsonify(
        {
            "name": row["name"],
            "class_name": row["class_name"],
            "subclass": row["subclass"],
            "level": row["level"],
        }
    )


@app.route("/api/status", methods=["POST"])
def update_status() -> Any:
    data = request.get_json(silent=True) or {}
    spell_id = data.get("spell_id")
    if not spell_id:
        return jsonify({"error": "missing_spell_id"}), 400

    known = 1 if data.get("known") else 0
    prepared = 1 if data.get("prepared") else 0
    favorite = 1 if data.get("favorite") else 0

    conn = get_db()
    conn.execute(
        """
        INSERT INTO spell_status (spell_id, known, prepared, favorite, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(spell_id) DO UPDATE SET
            known = excluded.known,
            prepared = excluded.prepared,
            favorite = excluded.favorite,
            updated_at = datetime('now')
        """,
        (spell_id, known, prepared, favorite),
    )
    conn.commit()
    return jsonify({"ok": True})


def build_filters(params: Dict[str, Any]) -> Tuple[str, List[Any]]:
    clauses: List[str] = []
    values: List[Any] = []

    q = (params.get("q") or "").strip()
    if q:
        clauses.append("name LIKE ?")
        values.append(f"%{q}%")

    level = params.get("level")
    if level not in (None, ""):
        try:
            level_int = int(level)
            clauses.append("level = ?")
            values.append(level_int)
        except (TypeError, ValueError):
            pass

    class_name = (params.get("class") or "").strip().lower()
    if class_name:
        clauses.append("LOWER(classes) LIKE ?")
        values.append(f"%{class_name}%")

    school = (params.get("school") or "").strip().lower()
    if school:
        clauses.append("LOWER(school) LIKE ?")
        values.append(f"%{school}%")

    ritual = params.get("ritual")
    if ritual in ("true", "false"):
        clauses.append("ritual = ?")
        values.append(1 if ritual == "true" else 0)

    concentration = params.get("concentration")
    if concentration in ("true", "false"):
        clauses.append("concentration = ?")
        values.append(1 if concentration == "true" else 0)

    component = (params.get("component") or "").strip().upper()
    if component in ("V", "S", "M"):
        clauses.append("components LIKE ?")
        values.append(f"%{component}%")

    if not clauses:
        return "", []
    return " WHERE " + " AND ".join(clauses), values


@app.route("/api/spells")
def spells() -> Any:
    conn = get_db()
    where_sql, values = build_filters(request.args)

    sql = (
        "SELECT spells.*, "
        "COALESCE(spell_status.known, 0) AS known, "
        "COALESCE(spell_status.prepared, 0) AS prepared, "
        "COALESCE(spell_status.favorite, 0) AS favorite "
        "FROM spells "
        "LEFT JOIN spell_status ON spell_status.spell_id = spells.id "
        f"{where_sql} "
        "ORDER BY name ASC"
    )

    rows = conn.execute(sql, values).fetchall()
    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "name": row["name"],
                "level": row["level"],
                "school": row["school"],
                "ritual": bool(row["ritual"]),
                "concentration": bool(row["concentration"]),
                "casting_time": row["casting_time"],
                "range": row["range"],
                "components": row["components"],
                "material": row["material"],
                "duration": row["duration"],
                "classes": row["classes"],
                "description": row["description"],
                "higher_level": row["higher_level"],
                "url": row["url"],
                "known": bool(row["known"]),
                "prepared": bool(row["prepared"]),
                "favorite": bool(row["favorite"]),
            }
        )
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5178)
