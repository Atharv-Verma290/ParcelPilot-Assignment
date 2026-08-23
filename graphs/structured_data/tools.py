import json

from langchain.tools import ToolRuntime, tool

from auth.authorization import require_permission, Permission
from data.database import execute_query, get_connection
from .states import StructuredDataState

def get_required_permission(sql: str) -> set[Permission]:
    normalized_sql = sql.lower() 

    permissions = set() 
    if "staff" in normalized_sql:
        permissions.add(Permission.READ_STAFF)

    if any(table in normalized_sql for table in ["accounts", "orders", "tickets", "follow_up_tasks"]):
        permissions.add(Permission.READ_OPERATIONAL_DATA)

    return permissions


@tool
def execute_sql(sql: str, runtime: ToolRuntime) -> str:
    """
    Execute a read-only SQL query against the ParcelPilot
    structured data database.

    Use this tool for information from:
    - accounts
    - orders
    - tickets
    - follow_up_tasks
    - staff
    - metadata

    Queries that touch staff require READ_STAFF.
    Queries that touch accounts, orders, tickets, or
    follow_up_tasks require READ_OPERATIONAL_DATA.

    The SQL query must be read-only (SELECT or WITH ... SELECT).
    """
    role = runtime.state.get("role") 

    sql = sql.strip()
    normalized_sql = sql.lower() 

    if not (normalized_sql.startswith("select") or normalized_sql.startswith("with")):
        raise ValueError("Only SELECT or WITH ... SELECT queries are allowed.")

    required_permissions = get_required_permission(sql)

    for permission in required_permissions:
        try:
            require_permission(role, permission)
        except PermissionError as error:
            return f"Access denied: {error}"
        
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


@tool 
def query_staff_data(sql: str, runtime: ToolRuntime) -> str:
    """sdfsdfs"""

