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

def _next_ticket_id(connection) -> str:
    row = connection.execute(
        """
        SELECT ticket_id
        FROM tickets
        WHERE ticket_id GLOB 'TICKET-[0-9]*'
        ORDER BY CAST(substr(ticket_id, 8) AS INTEGER) DESC
        LIMIT 1
        """
    ).fetchone()

    if not row:
        return "TICKET-001"

    next_number = int(str(row["ticket_id"]).split("-")[1]) + 1

    return f"TICKET-{next_number:03d}"

def create_ticket_in_database(
    account_id: str,
    subject: str,
    description: str,
    channel: str,
    status: str = "OPEN",
    assigned_to: Optional[str] = None,
) -> str:
    """
    Create a ticket in the database.
    """

    connection = get_connection()

    try:
        ticket_id = _next_ticket_id(connection)

        connection.execute(
            """
            INSERT INTO tickets (
                ticket_id,
                account_id,
                created_at,
                status,
                subject,
                description,
                channel,
                assigned_to,
                last_customer_message_at,
                historical_resolution
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                account_id,
                DATASET_REFERENCE_TIME,
                status,
                subject,
                description,
                channel,
                assigned_to,
                None,
                None,
            ),
        )

        connection.commit()

        return ticket_id

    finally:
        connection.close()

def update_ticket_in_database(
    ticket_id: str,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
) -> None:
    """
    Update an existing ticket in the database.
    """

    fields = []
    values = []

    updates = {
        "subject": subject,
        "description": description,
        "status": status,
        "assigned_to": assigned_to,
    }

    for column, value in updates.items():
        if value is not None:
            fields.append(f"{column} = ?")
            values.append(value)

    if not fields:
        raise ValueError("At least one field must be provided for update.")

    values.append(ticket_id)

    connection = get_connection()

    try:
        cursor = connection.execute(
            f"""
            UPDATE tickets
            SET {", ".join(fields)}
            WHERE ticket_id = ?
            """,
            tuple(values),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"No ticket found with ticket_id {ticket_id}."
            )

        connection.commit()

    finally:
        connection.close()

def delete_ticket_in_database(ticket_id: str) -> None:
    """
    Delete an existing ticket from the database.
    """

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"No ticket found with ticket_id {ticket_id}."
            )

        connection.commit()

    finally:
        connection.close()

    
def _next_order_id(connection) -> str:
    row = connection.execute(
        """
        SELECT order_id
        FROM orders
        WHERE order_id GLOB 'ORD-[0-9]*'
        ORDER BY CAST(substr(order_id, 7) AS INTEGER) DESC
        LIMIT 1
        """
    ).fetchone()

    if not row:
        return "ORD-001"

    next_number = int(str(row["order_id"]).split("-")[1]) + 1

    return f"ORD-{next_number:03d}"

def create_order_in_database(
    account_id: str,
    carrier: str,
    status: str,
    shipment_fee_inr: int,
    booked_at: Optional[str] = None,
    pickup_window_start: Optional[str] = None,
    pickup_window_end: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Create an order in the database.
    """

    connection = get_connection()

    try:
        order_id = _next_order_id(connection)

        connection.execute(
            """
            INSERT INTO orders (
                order_id,
                account_id,
                carrier,
                status,
                booked_at,
                pickup_window_start,
                pickup_window_end,
                pickup_actual_at,
                shipment_fee_inr,
                carrier_fault,
                customer_fault,
                cancellation_requested_at,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                account_id,
                carrier,
                status,
                booked_at,
                pickup_window_start,
                pickup_window_end,
                None,
                shipment_fee_inr,
                0,
                0,
                None,
                notes,
            ),
        )

        connection.commit()

        return order_id

    finally:
        connection.close()


def update_order_in_database(
    order_id: str,
    carrier: Optional[str] = None,
    status: Optional[str] = None,
    pickup_window_start: Optional[str] = None,
    pickup_window_end: Optional[str] = None,
    pickup_actual_at: Optional[str] = None,
    shipment_fee_inr: Optional[float] = None,
    carrier_fault: Optional[bool] = None,
    customer_fault: Optional[bool] = None,
    cancellation_requested_at: Optional[str] = None,
    notes: Optional[str] = None,
) -> None:
    """
    Update an existing order in the database.
    """

    fields = []
    values = []

    updates = {
        "carrier": carrier,
        "status": status,
        "pickup_window_start": pickup_window_start,
        "pickup_window_end": pickup_window_end,
        "pickup_actual_at": pickup_actual_at,
        "shipment_fee_inr": shipment_fee_inr,
        "carrier_fault": carrier_fault,
        "customer_fault": customer_fault,
        "cancellation_requested_at": cancellation_requested_at,
        "notes": notes,
    }

    for column, value in updates.items():
        if value is not None:
            fields.append(f"{column} = ?")
            values.append(value)

    if not fields:
        raise ValueError("At least one field must be provided for update.")

    values.append(order_id)

    connection = get_connection()

    try:
        cursor = connection.execute(
            f"""
            UPDATE orders
            SET {", ".join(fields)}
            WHERE order_id = ?
            """,
            tuple(values),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"No order found with order_id {order_id}."
            )

        connection.commit()

    finally:
        connection.close()

def delete_order_in_database(order_id: str) -> None:
    """
    Delete an existing order from the database.
    """

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM orders
            WHERE order_id = ?
            """,
            (order_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"No order found with order_id {order_id}."
            )

        connection.commit()

    finally:
        connection.close()

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


def update_task_in_database(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_team: Optional[str] = None,
    status: Optional[str] = None,
    ticket_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> None:
    fields = []
    values = []

    updates = {
        "title": title,
        "description": description,
        "priority": priority,
        "assigned_team": assigned_team,
        "status": status,
        "ticket_id": ticket_id,
        "order_id": order_id,
    }

    for column, value in updates.items():
        if value is not None:
            fields.append(f"{column} = ?")
            values.append(value)

    if not fields:
        raise ValueError("At least one field must be provided for update.")

    values.append(task_id)
    connection = get_connection()

    try:
        cursor = connection.execute(
            f"""
            UPDATE follow_up_tasks
            SET {", ".join(fields)}
            WHERE task_id = ?
            """,
            tuple(values),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"No follow-up task found with task_id {task_id}.")

        connection.commit()

    finally:
        connection.close()


def delete_task_in_database(task_id: int) -> None:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM follow_up_tasks
            WHERE task_id = ?
            """,
            (task_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"No follow-up task found with task_id {task_id}.")

        connection.commit()

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
