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
