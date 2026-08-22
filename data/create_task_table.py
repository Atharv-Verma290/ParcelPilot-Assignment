from data.database import get_connection

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS follow_up_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    assigned_team TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    ticket_id TEXT,
    order_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    CHECK (status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'))
);
"""

def create_task_table():
    connection = get_connection()
    try:
        connection.execute("DROP TABLE IF EXISTS follow_up_tasks")
        connection.execute(CREATE_TASKS_TABLE)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close() 


if __name__ == "__main__":
    create_task_table()
    print("follow_up_tasks table created successfully")
