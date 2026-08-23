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
    """
    Look up a staff member by name.

    The match is case-insensitive.

    Args:
        name: Staff display name, for example `"Alice"`.

    Returns:
        A dict with `user_id`, `name`, and `role`, or `None` if no
        matching staff row exists.
    """
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
    """
    Return all staff rows ordered by name.

    Returns:
        A list of dicts with `user_id`, `name`, and `role`.
    """
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