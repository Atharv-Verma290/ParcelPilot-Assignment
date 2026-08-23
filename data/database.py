from pathlib import Path
import sqlite3
from typing import Any, List


DB_PATH = Path("data/parcel_pilot.db")


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection to the ParcelPilot database.

    Rows are returned as `sqlite3.Row` objects, and foreign-key
    enforcement is enabled.

    Returns:
        An open connection to `data/parcel_pilot.db`.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute_query(
    connection: sqlite3.Connection,
    sql: str,
) -> List[dict[str, Any]]:
    """
    Run a SQL statement and return all result rows as dicts.

    Args:
        connection: Open SQLite connection.
        sql: SQL to execute.

    Returns:
        A list of row dictionaries. Empty if the statement has no
        result set.
    """
    cursor = connection.execute(sql)

    return [
        dict(row)
        for row in cursor.fetchall()
    ]
