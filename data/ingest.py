from pathlib import Path

from data.pdf_parser import extract_pages_from_pdf, split_into_sections
from data.vector_store import add_chunks, reset_collection


DOCS_DIR = Path("data/docs")


def ingest_documents(docs_dir: Path = DOCS_DIR) -> None:
    """
    Parse PDFs in `docs_dir`, split them into sections, and store
    the chunks in Chroma.

    The collection is reset first so ingestion always starts from
    a clean index.

    Args:
        docs_dir: Directory containing PDF files. Defaults to
            `data/docs`.
    """
    reset_collection()

    pdf_paths = sorted(docs_dir.glob("*.pdf"))

    if not pdf_paths:
        print(f"No PDF files found in {docs_dir}")
        return

    for pdf_path in pdf_paths:
        print("\n")
        print("=" * 80)
        print(pdf_path.name)
        print("=" * 80)

        pages = extract_pages_from_pdf(str(pdf_path))

        sections = split_into_sections(
            pages,
            {
                "source": pdf_path.name,
            },
        )

        add_chunks(sections)

        for section in sections:
            print(section["metadata"])
            print(section["text"][:300])
            print()

    print(f"\nIngested {len(pdf_paths)} PDF(s) into ChromaDB.")


if __name__ == "__main__":
    ingest_documents()
