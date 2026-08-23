from data.create_staff_table import create_staff_table, seed_staff
from data.create_task_table import create_task_table
from data.excel_to_sql import DB_PATH, EXCEL_PATH, ingest_excel_to_sqlite
from data.ingest import ingest_documents


def initialize() -> None:
    """
    Rebuild SQLite tables, seed staff, and ingest documents.

    This replaces the operational database, follow-up tasks table,
    staff table, and Chroma document index from the source Excel
    and PDF files.
    """
    print("=== ParcelPilot initialization ===\n")

    print("1. Extracting Excel data into SQLite...")
    ingest_excel_to_sqlite(EXCEL_PATH, DB_PATH)

    print("\n2. Creating follow_up_tasks table...")
    create_task_table()
    print("follow_up_tasks table created.")

    print("\n3. Creating and seeding staff table...")
    create_staff_table()
    seed_staff()
    print("staff table created and seeded.")

    print("\n4. Parsing PDFs and embedding documents into ChromaDB...")
    ingest_documents()

    print("\n=== Initialization complete ===")


def main() -> None:
    """
    Entry point for one-time ParcelPilot data initialization.
    """
    initialize()


if __name__ == "__main__":
    main()
