from typing import Optional
import chromadb
from data.database import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo


DATASET_REFERENCE_TIME = datetime(2026, 8, 16, 11, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))


client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_collection(
    name="parcel_pilot_docs"
)

def search_docs(query: str, k: int = 3) -> list[dict]:
    results = collection.query(
        query_texts=[query],
        n_results=k
    )
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text": document,
            "metadata": metadata,
            "distance": distance 
        }
        for document, metadata, distance in zip(documents, metadatas, distances)
    ]


def create_task_in_database(
    title: str,
    description: str,
    priority: str,
    assigned_team: str,
    ticket_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> str:
    """
    Create a follow-up task in the database.
    
    """
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO follow_up_tasks (
                title,
                description,
                priority,
                assigned_team,
                status,
                ticket_id,
                order_id,
                created_at 
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                priority,
                assigned_team,
                "OPEN",
                ticket_id,
                order_id,
                DATASET_REFERENCE_TIME
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def _next_staff_user_id(connection) -> str:
    row = connection.execute(
        """
        SELECT user_id
        FROM staff
        WHERE user_id GLOB 'STAFF-[0-9]*'
        ORDER BY CAST(substr(user_id, 7) AS INTEGER) DESC
        LIMIT 1
        """
    ).fetchone()

    if not row:
        return "STAFF-001"

    next_number = int(str(row["user_id"]).split("-")[1]) + 1
    return f"STAFF-{next_number:03d}"


def create_staff_in_database(name: str, role: str) -> str:
    connection = get_connection()

    try:
        user_id = _next_staff_user_id(connection)
        connection.execute(
            """
            INSERT INTO staff (
                user_id,
                name,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                role,
                DATASET_REFERENCE_TIME,
            ),
        )
        connection.commit()
        return user_id

    finally:
        connection.close()


def update_staff_in_database(
    user_id: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
) -> None:
    if name is None and role is None:
        raise ValueError("At least one of name or role must be provided.")

    fields = []
    values = []

    if name is not None:
        fields.append("name = ?")
        values.append(name)

    if role is not None:
        fields.append("role = ?")
        values.append(role)

    values.append(user_id)
    connection = get_connection()

    try:
        cursor = connection.execute(
            f"""
            UPDATE staff
            SET {", ".join(fields)}
            WHERE user_id = ?
            """,
            tuple(values),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"No staff member found with user_id {user_id}.")

        connection.commit()

    finally:
        connection.close()


def delete_staff_in_database(user_id: str) -> None:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM staff
            WHERE user_id = ?
            """,
            (user_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"No staff member found with user_id {user_id}.")

        connection.commit()

    finally:
        connection.close()
