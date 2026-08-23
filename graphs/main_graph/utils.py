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
    """
    Retrieve the nearest documentation chunks from Chroma.

    Args:
        query: Natural-language search text.
        k: Maximum number of chunks to return.

    Returns:
        Chunks with `text`, `metadata`, and `distance`.
    """
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
    """
    Allocate the next sequential `TICKET-NNN` identifier.

    Args:
        connection: Open SQLite connection.

    Returns:
        The next unused ticket ID, starting at `TICKET-001`.
    """
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
    Insert a new ticket and return its generated ID.

    `created_at` is set to `DATASET_REFERENCE_TIME`. Customer-message
    and historical-resolution fields start empty.

    Args:
        account_id: Account the ticket belongs to.
        subject: Short ticket subject.
        description: Ticket body.
        channel: Intake channel, such as email.
        status: Initial status. Defaults to `"OPEN"`.
        assigned_to: Optional assignee.

    Returns:
        The new `ticket_id`.
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
    Patch non-null fields on an existing ticket.

    Args:
        ticket_id: Ticket to update.
        subject: Replacement subject, if provided.
        description: Replacement description, if provided.
        status: Replacement status, if provided.
        assigned_to: Replacement assignee, if provided.

    Raises:
        ValueError: If no fields are provided or the ticket is missing.
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
    Delete a ticket by ID.

    Args:
        ticket_id: Ticket to remove.

    Raises:
        ValueError: If no ticket matches `ticket_id`.
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
    """
    Allocate the next sequential `ORD-NNN` identifier.

    Args:
        connection: Open SQLite connection.

    Returns:
        The next unused order ID, starting at `ORD-001`.
    """
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
    Insert a new order and return its generated ID.

    Pickup-actual, fault flags, and cancellation time start unset.

    Args:
        account_id: Account placing the order.
        carrier: Carrier name.
        status: Initial order status.
        shipment_fee_inr: Shipment fee in INR.
        booked_at: Optional booking timestamp.
        pickup_window_start: Optional pickup window start.
        pickup_window_end: Optional pickup window end.
        notes: Optional free-text notes.

    Returns:
        The new `order_id`.
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
    Patch non-null fields on an existing order.

    Args:
        order_id: Order to update.
        carrier: Replacement carrier, if provided.
        status: Replacement status, if provided.
        pickup_window_start: Replacement window start, if provided.
        pickup_window_end: Replacement window end, if provided.
        pickup_actual_at: Actual pickup time, if provided.
        shipment_fee_inr: Replacement fee, if provided.
        carrier_fault: Carrier-fault flag, if provided.
        customer_fault: Customer-fault flag, if provided.
        cancellation_requested_at: Cancellation time, if provided.
        notes: Replacement notes, if provided.

    Raises:
        ValueError: If no fields are provided or the order is missing.
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
    Delete an order by ID.

    Args:
        order_id: Order to remove.

    Raises:
        ValueError: If no order matches `order_id`.
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
    Insert a follow-up task with status `OPEN`.

    `created_at` is set to `DATASET_REFERENCE_TIME`.

    Args:
        title: Task title.
        description: Task details.
        priority: One of LOW, MEDIUM, HIGH, URGENT.
        assigned_team: Team responsible for the task.
        ticket_id: Optional related ticket.
        order_id: Optional related order.

    Returns:
        The new integer `task_id`.
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
    """
    Patch non-null fields on an existing follow-up task.

    Args:
        task_id: Task to update.
        title: Replacement title, if provided.
        description: Replacement description, if provided.
        priority: Replacement priority, if provided.
        assigned_team: Replacement team, if provided.
        status: Replacement status, if provided.
        ticket_id: Replacement related ticket, if provided.
        order_id: Replacement related order, if provided.

    Raises:
        ValueError: If no fields are provided or the task is missing.
    """
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
    """
    Delete a follow-up task by ID.

    Args:
        task_id: Task to remove.

    Raises:
        ValueError: If no task matches `task_id`.
    """
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
    """
    Allocate the next sequential `STAFF-NNN` identifier.

    Args:
        connection: Open SQLite connection.

    Returns:
        The next unused staff ID, starting at `STAFF-001`.
    """
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
    """
    Insert a staff member and return the generated user ID.

    `created_at` is set to `DATASET_REFERENCE_TIME`.

    Args:
        name: Display name.
        role: One of SUPPORT, OPERATIONS, ADMIN.

    Returns:
        The new `user_id`.
    """
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
    """
    Patch name and/or role on an existing staff row.

    Args:
        user_id: Staff member to update.
        name: Replacement name, if provided.
        role: Replacement role, if provided.

    Raises:
        ValueError: If neither field is provided or the staff row is
            missing.
    """
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
    """
    Delete a staff member by user ID.

    Args:
        user_id: Staff member to remove.

    Raises:
        ValueError: If no staff row matches `user_id`.
    """
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
