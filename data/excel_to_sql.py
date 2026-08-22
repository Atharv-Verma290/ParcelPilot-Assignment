from pathlib import Path
import sqlite3

import pandas as pd


EXCEL_PATH = Path("data/docs/ParcelPilot_Assessment_Data.xlsx")
DB_PATH = Path("data/parcel_pilot.db")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_column_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def to_bool(value):
    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()

    if value in {"1", "true", "yes"}:
        return True

    if value in {"0", "false", "no"}:
        return False

    raise ValueError(f"Invalid boolean value: {value}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    return df


# ---------------------------------------------------------------------------
# Sheet normalization
# ---------------------------------------------------------------------------

def normalize_accounts(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    df["premium_support"] = (
        df["premium_support"].map(to_bool)
    )

    string_columns = [
        "account_id",
        "account_name",
        "plan",
        "status",
        "csm",
        "contract_file",
        "notes",
    ]

    for column in string_columns:
        df[column] = df[column].astype("string")

    return df


def normalize_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    boolean_columns = [
        "carrier_fault",
        "customer_fault",
    ]

    for column in boolean_columns:
        df[column] = df[column].map(to_bool)

    datetime_columns = [
        "booked_at",
        "pickup_window_start",
        "pickup_window_end",
        "pickup_actual_at",
        "cancellation_requested_at",
    ]

    for column in datetime_columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    df["shipment_fee_inr"] = pd.to_numeric(
        df["shipment_fee_inr"],
        errors="coerce",
    )

    string_columns = [
        "order_id",
        "account_id",
        "carrier",
        "status",
        "notes",
    ]

    for column in string_columns:
        df[column] = df[column].astype("string")

    return df


def normalize_tickets(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    datetime_columns = [
        "created_at",
        "last_customer_message_at",
    ]

    for column in datetime_columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    string_columns = [
        "ticket_id",
        "account_id",
        "status",
        "subject",
        "description",
        "channel",
        "assigned_to",
        "historical_resolution",
    ]

    for column in string_columns:
        df[column] = df[column].astype("string")

    return df


# ---------------------------------------------------------------------------
# README metadata
# ---------------------------------------------------------------------------

def extract_readme_metadata(
    df: pd.DataFrame,
) -> dict[str, str]:

    metadata = {}

    for _, row in df.iterrows():

        if len(row) < 2:
            continue

        key = row.iloc[0]
        value = row.iloc[1]

        if pd.isna(key):
            continue

        key = str(key).strip()

        if pd.isna(value):
            value = ""

        metadata[key] = str(value).strip()

    return metadata


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_required_columns(
    df: pd.DataFrame,
    table_name: str,
    required_columns: set[str],
) -> None:

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"{table_name} is missing required columns: "
            f"{sorted(missing)}"
        )


def validate_data(
    accounts: pd.DataFrame,
    orders: pd.DataFrame,
    tickets: pd.DataFrame,
) -> None:

    validate_required_columns(
        accounts,
        "accounts",
        {
            "account_id",
            "account_name",
            "plan",
            "status",
            "premium_support",
        },
    )

    validate_required_columns(
        orders,
        "orders",
        {
            "order_id",
            "account_id",
            "status",
            "booked_at",
            "pickup_window_start",
            "pickup_window_end",
        },
    )

    validate_required_columns(
        tickets,
        "tickets",
        {
            "ticket_id",
            "account_id",
            "created_at",
            "status",
        },
    )

    # Primary key checks

    if accounts["account_id"].duplicated().any():
        raise ValueError(
            "Duplicate account_id values found."
        )

    if orders["order_id"].duplicated().any():
        raise ValueError(
            "Duplicate order_id values found."
        )

    if tickets["ticket_id"].duplicated().any():
        raise ValueError(
            "Duplicate ticket_id values found."
        )

    # Foreign key checks

    account_ids = set(
        accounts["account_id"].dropna()
    )

    invalid_order_accounts = (
        set(orders["account_id"].dropna())
        - account_ids
    )

    if invalid_order_accounts:
        raise ValueError(
            "Orders reference unknown accounts: "
            f"{invalid_order_accounts}"
        )

    invalid_ticket_accounts = (
        set(tickets["account_id"].dropna())
        - account_ids
    )

    if invalid_ticket_accounts:
        raise ValueError(
            "Tickets reference unknown accounts: "
            f"{invalid_ticket_accounts}"
        )


# ---------------------------------------------------------------------------
# SQLite schema
# ---------------------------------------------------------------------------

def create_database_schema(
    conn: sqlite3.Connection,
) -> None:

    # Make SQLite enforce foreign keys.
    conn.execute("PRAGMA foreign_keys = ON")

    # Accounts
    conn.execute(
        """
        CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY,
            account_name TEXT,
            plan TEXT,
            status TEXT,
            csm TEXT,
            contract_file TEXT,
            premium_support INTEGER,
            notes TEXT
        )
        """
    )

    # Orders
    conn.execute(
        """
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            carrier TEXT,
            status TEXT,
            booked_at TIMESTAMP,
            pickup_window_start TIMESTAMP,
            pickup_window_end TIMESTAMP,
            pickup_actual_at TIMESTAMP,
            shipment_fee_inr INTEGER,
            carrier_fault INTEGER,
            customer_fault INTEGER,
            cancellation_requested_at TIMESTAMP,
            notes TEXT,

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        )
        """
    )

    # Tickets
    conn.execute(
        """
        CREATE TABLE tickets (
            ticket_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            created_at TIMESTAMP,
            status TEXT,
            subject TEXT,
            description TEXT,
            channel TEXT,
            assigned_to TEXT,
            last_customer_message_at TIMESTAMP,
            historical_resolution TEXT,

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        )
        """
    )

    # Dataset metadata
    conn.execute(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )


# ---------------------------------------------------------------------------
# SQLite ingestion
# ---------------------------------------------------------------------------

def write_to_sqlite(
    db_path: Path,
    accounts: pd.DataFrame,
    orders: pd.DataFrame,
    tickets: pd.DataFrame,
    metadata: dict[str, str],
) -> None:

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove old database so the schema is recreated cleanly.
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:

        # Create our explicit relational schema.
        create_database_schema(conn)

        # Insert DataFrames into the already-created tables.
        accounts.to_sql(
            "accounts",
            conn,
            if_exists="append",
            index=False,
        )

        orders.to_sql(
            "orders",
            conn,
            if_exists="append",
            index=False,
        )

        tickets.to_sql(
            "tickets",
            conn,
            if_exists="append",
            index=False,
        )

        metadata_df = pd.DataFrame(
            [
                {
                    "key": key,
                    "value": value,
                }
                for key, value in metadata.items()
            ]
        )

        metadata_df.to_sql(
            "metadata",
            conn,
            if_exists="append",
            index=False,
        )

        conn.commit()


# ---------------------------------------------------------------------------
# Schema inspection
# ---------------------------------------------------------------------------

def get_database_schema(
    db_path: Path,
) -> str:

    schema = []

    with sqlite3.connect(db_path) as conn:

        conn.execute("PRAGMA foreign_keys = ON")

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """,
            conn,
        )

        for table_name in tables["name"]:

            columns = pd.read_sql_query(
                f'PRAGMA table_info("{table_name}")',
                conn,
            )

            schema.append(
                f"Table: {table_name}"
            )

            for _, column in columns.iterrows():

                primary_key = (
                    " PRIMARY KEY"
                    if column["pk"]
                    else ""
                )

                schema.append(
                    f"- {column['name']} "
                    f"({column['type']}{primary_key})"
                )

            foreign_keys = pd.read_sql_query(
                f'PRAGMA foreign_key_list("{table_name}")',
                conn,
            )

            for _, fk in foreign_keys.iterrows():

                schema.append(
                    f"  FK: {fk['from']} → "
                    f"{fk['table']}.{fk['to']}"
                )

            schema.append("")

    return "\n".join(schema)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def ingest_excel_to_sqlite(
    excel_path: Path,
    db_path: Path,
) -> None:

    print(f"Reading workbook: {excel_path}")

    sheets = pd.read_excel(
        excel_path,
        sheet_name=None,
    )

    print(
        "Sheets found:",
        list(sheets.keys()),
    )

    # README
    readme_df = sheets.get("README")

    if readme_df is None:
        raise ValueError(
            "README sheet not found."
        )

    metadata = extract_readme_metadata(
        readme_df
    )

    print("\nDataset metadata:")

    for key, value in metadata.items():
        print(f"  {key}: {value}")

    # Business data
    accounts = normalize_accounts(
        sheets["accounts"]
    )

    orders = normalize_orders(
        sheets["orders"]
    )

    tickets = normalize_tickets(
        sheets["tickets"]
    )

    # Validation
    validate_data(
        accounts,
        orders,
        tickets,
    )

    # Write database
    write_to_sqlite(
        db_path,
        accounts,
        orders,
        tickets,
        metadata,
    )

    print(
        f"\nSQLite database created at: {db_path}"
    )

    print("\nDatabase schema:")
    print(get_database_schema(db_path))


if __name__ == "__main__":
    ingest_excel_to_sqlite(
        EXCEL_PATH,
        DB_PATH,
    )