import json

from langchain.tools import tool

from data.database import execute_query, get_connection
from .schema import StructuredDataState


@tool
def execute_sql(sql: str) -> str:
    """
    Execute a read-only SQL query against the ParcelPilot
    structured data database.

    Use this tool when information is needed from accounts,
    orders, tickets, or other structured ParcelPilot data.

    The SQL query must be read-only.
    """

    sql = sql.strip()

    normalized_sql = sql.lower() 
    if not normalized_sql.startswith("select") or normalized_sql.startswith("with"):
        raise ValueError("Only SELECT or WITH ... SELECT queries are allowed.")

    connection = get_connection()

    try:
        rows = execute_query(connection, sql)
    except Exception as error:
        return f"SQL error: {error}"
    finally:
        connection.close()

    if not rows:
        return "No rows returned."

    return json.dumps(rows, default=str)

