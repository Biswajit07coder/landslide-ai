import os
import sqlite3
from typing import Optional, Dict, List

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            device_token TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_location(location_name: str, latitude: float, longitude: float, device_token: str) -> Dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO locations (location_name, latitude, longitude, device_token) VALUES (?, ?, ?, ?)",
        (location_name, latitude, longitude, device_token),
    )
    conn.commit()
    loc_id = cur.lastrowid
    conn.close()
    return {"id": loc_id, "location_name": location_name, "latitude": latitude, "longitude": longitude, "device_token": device_token}


def get_location(location_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def list_locations() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM locations")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()
