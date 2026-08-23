from zoneinfo import ZoneInfo
from data.database import get_connection 
from datetime import datetime

CREATE_STAFF_TABLE = """
CREATE TABLE IF NOT EXISTS staff (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (role IN ('SUPPORT', 'OPERATIONS', 'ADMIN'))
);
"""

INITIAL_STAFF = [
    ("STAFF-001", "Alice", "SUPPORT"),
    ("STAFF-002", "Bob", "OPERATIONS"),
    ("STAFF-003", "Admin", "ADMIN"),
]

DATASET_REFERENCE_TIME = datetime(2026, 8, 16, 11, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))

def seed_staff():
    """
    Insert the initial staff roster if those user IDs are missing.

    Existing staff rows are left unchanged (`INSERT OR IGNORE`).
    Created-at timestamps use `DATASET_REFERENCE_TIME`.
    """
    connection = get_connection()

    try:
        connection.executemany(
            """
            INSERT OR IGNORE INTO staff (
                user_id,
                name,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    user_id,
                    name,
                    role,
                    DATASET_REFERENCE_TIME,
                )
                for user_id, name, role in INITIAL_STAFF
            ],
        )

        connection.commit()

    finally:
        connection.close()

def create_staff_table():
    """
    Drop and recreate the `staff` table.

    Any existing staff rows are removed. Call `seed_staff` afterward
    to reload the initial roster.
    """
    connection = get_connection()
    try:
        connection.execute("DROP TABLE IF EXISTS staff")
        connection.execute(CREATE_STAFF_TABLE)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()


if __name__ == "__main__":
    create_staff_table()
    print("staff table created successfully")
    seed_staff()
    print("staff seeded successfully")
