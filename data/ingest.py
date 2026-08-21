from pathlib import Path
from pdf_parser import extract_pages_from_pdf, split_into_sections
from vector_store import add_chunks

docs_dir = Path("data/docs")

for pdf_path in docs_dir.glob("*.pdf"):
    print("\n")
    print("=" * 80)
    print(pdf_path.name)
    print("=" * 80)

    pages = extract_pages_from_pdf(str(pdf_path))

    sections = split_into_sections(
        pages,
        {
            "source": pdf_path.name,
        }
    )

    add_chunks(sections)

    for section in sections:
        print(section["metadata"])
        print(section["text"][:300])
        print()