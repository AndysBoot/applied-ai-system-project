"""
SQLite-backed song catalog.

Lets the catalog grow beyond data/songs.csv without touching the scoring
pipeline in recommender.py -- load_songs_from_db() returns the exact same
List[Dict] shape as load_songs(), so recommend_songs()/score_song() don't
know or care where the rows came from.

On first use the DB is seeded from data/songs.csv. After that, songs.csv is
left alone; new songs are added straight to the DB (see scripts/manage_songs.py).
"""

import csv
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "songs.db"

SONG_COLUMNS = [
    "id", "title", "artist", "genre", "mood",
    "energy", "valence", "danceability", "acousticness",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT NOT NULL,
    mood TEXT NOT NULL,
    energy REAL NOT NULL,
    valence REAL NOT NULL,
    danceability REAL NOT NULL,
    acousticness REAL NOT NULL
)
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_from_csv(csv_path: Path) -> List[tuple]:
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        return [
            (
                int(row["id"]), row["title"], row["artist"], row["genre"], row["mood"],
                float(row["energy"]), float(row["valence"]),
                float(row["danceability"]), float(row["acousticness"]),
            )
            for row in reader
        ]


def init_db(db_path: Path = DB_PATH, seed_csv: Optional[Path] = None) -> None:
    """Create the songs table if needed, seeding it from seed_csv the first time it's empty."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        conn.execute(SCHEMA)
        count = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
        if count == 0 and seed_csv and seed_csv.exists():
            rows = _rows_from_csv(seed_csv)
            conn.executemany(
                f"INSERT INTO songs ({', '.join(SONG_COLUMNS)}) "
                f"VALUES ({', '.join('?' for _ in SONG_COLUMNS)})",
                rows,
            )
            conn.commit()
    finally:
        conn.close()


def load_songs_from_db(db_path: Path = DB_PATH) -> List[Dict]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(f"SELECT {', '.join(SONG_COLUMNS)} FROM songs ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def add_song(song: Dict, db_path: Path = DB_PATH) -> int:
    """Insert a new song, auto-assigning the next id if none is given. Returns the id used."""
    conn = get_connection(db_path)
    try:
        song_id = song.get("id")
        if song_id is None:
            row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM songs").fetchone()
            song_id = row[0]
        conn.execute(
            f"INSERT INTO songs ({', '.join(SONG_COLUMNS)}) "
            f"VALUES (:id, :title, :artist, :genre, :mood, :energy, :tempo_bpm, "
            f":valence, :danceability, :acousticness)",
            {**song, "id": song_id},
        )
        conn.commit()
        return song_id
    finally:
        conn.close()


def count_songs(db_path: Path = DB_PATH) -> int:
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    finally:
        conn.close()
