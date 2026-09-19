from pathlib import Path
import fitz


def extract_pages(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append({"page": page_no, "text": text})
    doc.close()
    return pages


def chunk_pages(pages: list[dict], chunk_size: int = 1200, overlap: int = 180) -> list[dict]:
    chunks = []
    counter = 0

    for p in pages:
        text = p["text"]
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "chunk_id": f"chunk-{counter}",
                    "page": p["page"],
                    "text": chunk_text,
                })
                counter += 1
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)

    return chunks
