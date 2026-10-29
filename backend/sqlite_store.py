import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "detections.db"


def initialize_database(db_path=None):
    path = db_path if db_path is not None else DB_PATH

    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL UNIQUE,
                animal TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                confidence REAL NOT NULL,
                image_path TEXT NOT NULL
            )
        """)


def save_detection(event_key, animal, timestamp, confidence, image_path, db_path=None):
    path = db_path if db_path is not None else DB_PATH
    initialize_database(path)

    with sqlite3.connect(path) as connection:
        result = connection.execute("""
            INSERT OR IGNORE INTO detections
            (event_key, animal, timestamp, confidence, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (event_key, animal, timestamp, confidence, image_path))

        return result.rowcount == 1

def detection_exists(event_key, db_path=None):
    path = db_path if db_path is not None else DB_PATH
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        result = connection.execute(
            "SELECT 1 FROM detections WHERE event_key = ? LIMIT 1",
            (event_key,)
        )
        return result.fetchone() is not None
