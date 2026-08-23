from typing import Any
from data.database import get_connection

USERS = {
    "alice": {
        "user_id": "STAFF-001",
        "name": "Alice",
        "role": "SUPPORT",
    },

    "bob": {
        "user_id": "STAFF-002",
        "name": "Bob",
        "role": "OPERATIONS",
    },

    "admin": {
        "user_id": "STAFF-003",
        "name": "Admin",
        "role": "ADMIN",
    },
}

def get_staff_by_name(name: str) -> dict[str, Any] | None:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT user_id, name, role
            FROM staff
            WHERE LOWER(name) = LOWER(?)
            """,
            (name,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def get_all_staff() -> list[dict[str, Any]]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT user_id, name, role
            FROM staff
            ORDER BY name
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()