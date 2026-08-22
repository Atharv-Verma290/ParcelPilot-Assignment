from pathlib import Path
import sqlite3
from typing import Any, List


DB_PATH = Path("data/parcel_pilot.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute_query(
    connection: sqlite3.Connection,
    sql: str,
) -> List[dict[str, Any]]:
    cursor = connection.execute(sql)

    return [
        dict(row)
        for row in cursor.fetchall()
    ]
