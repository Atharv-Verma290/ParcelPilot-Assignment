import enum
import re
from typing import Dict, List
import pymupdf



def extract_pages_from_pdf(file_path: str) -> List[str]:
    """
    Extract sorted plain text from each page of a PDF.

    Args:
        file_path: Path to the PDF file.

    Returns:
        One string per page, in document order.
    """
    doc = pymupdf.open(file_path)

    pages = []

    for page in doc:
        text = page.get_text("text", sort=True)
        pages.append(text)
    
    doc.close()
    return pages

SECTION_PATTERN = re.compile(r"(?m)^(\d+\.\s+.+)$")

def split_into_sections(pages: List[str], document_metadata: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Split extracted PDF text into retrieval chunks.

    Numbered headings (`1. Title`) become section chunks. If none
    are found, each non-empty page is stored as its own chunk.

    Args:
        pages: Page texts from `extract_pages_from_pdf`.
        document_metadata: Metadata copied onto each chunk. Must
            include `source`.

    Returns:
        Chunks with `text` and `metadata` keys.
    """
    text = "\n".join(pages)
    matches = list(SECTION_PATTERN.finditer(text))

    # --------------------------------------------------
    # Strategy 1: Numbered sections
    # --------------------------------------------------
    if matches:
        return split_numbered_sections(text, document_metadata, matches)

    # --------------------------------------------------
    # Strategy 2: Fallback
    # --------------------------------------------------
    return split_into_pages(pages, document_metadata)


def split_numbered_sections(text: str, document_metadata: Dict[str, str], matches) -> List[Dict[str, str]]:
    """
    Build chunks from numbered section headings in full-document text.

    Each chunk includes the source document name and section title
    in both the body text and metadata.

    Args:
        text: Concatenated page text.
        document_metadata: Metadata copied onto each chunk.
        matches: Regex match objects for section headings.

    Returns:
        One chunk per numbered section.
    """
    chunks = []

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()

        if i + 1 < len(matches):
            end = matches[i+1].start()
        else:
            end = len(text)

        content = text[start: end].strip()
        chunk_text = (
            f"Document: {document_metadata['source']}\n"
            f"Section: {title}\n\n"
            f"{content}"
        )

        chunks.append({
            "text": chunk_text,
            "metadata": {
                **document_metadata,
                "section": title,
            }
        })

    return chunks


def split_into_pages(pages: List[str], document_metadata: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Build one chunk per non-empty PDF page.

    Used when the document has no numbered section headings.

    Args:
        pages: Page texts from `extract_pages_from_pdf`.
        document_metadata: Metadata copied onto each chunk.

    Returns:
        Chunks tagged with `section` and `page` metadata.
    """
    chunks = []

    for page_number, page_text in enumerate(pages, start=1):
        page_text = page_text.strip()
        
        if not page_text:
            continue

        chunk_text = (
            f"Document: {document_metadata['source']}\n"
            f"Section: Page {page_number}\n\n"
            f"{page_text}"
        )

        chunks.append({
            "text": chunk_text,
            "metadata": {
                **document_metadata,
                "section": f"Page {page_number}",
                "page": page_number,
            }
        })

    return chunks