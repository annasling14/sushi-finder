import sqlite3
from datetime import datetime, timezone

DB_PATH = "sushi.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS restaurants (
    place_id    TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    address     TEXT,
    price_level INTEGER,
    maps_url    TEXT
);

CREATE TABLE IF NOT EXISTS searches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    location    TEXT NOT NULL,
    searched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    search_id      INTEGER NOT NULL REFERENCES searches(id),
    place_id       TEXT    NOT NULL REFERENCES restaurants(place_id),
    rank           INTEGER NOT NULL,
    rating         REAL,
    review_count   INTEGER,
    adjusted_score REAL,
    PRIMARY KEY (search_id, place_id)
);
"""

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()

def save_results(location, results):
    searched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO searches (location, searched_at) VALUES (?, ?)",
                (location, searched_at),
            )
            search_id = cursor.lastrowid

            for rank, r in enumerate(results, start=1):
                conn.execute(
                    """
                    INSERT INTO restaurants (place_id, name, address, price_level, maps_url)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(place_id) DO UPDATE SET
                        name = excluded.name,
                        address = excluded.address,
                        price_level = excluded.price_level,
                        maps_url = excluded.maps_url
                    """,
                    (r["place_id"], r["name"], r["address"], r["price"], r["maps_url"]),
                )
                conn.execute(
                    """
                    INSERT INTO snapshots
                        (search_id, place_id, rank, rating, review_count, adjusted_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (search_id, r["place_id"], rank, r["rating"], r["reviews"], r["score"]),
                )
    finally:
        conn.close()