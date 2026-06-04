import base64
import io
from pathlib import Path

import pdfplumber
import fitz

def table_to_markdown(table: list[list]) -> str:
    """Convert a pdfplumber table (list of lists) to a markdown table string."""
    if not table:
        return ""
 
    # Clean None cells
    cleaned = []
    for row in table:
        cleaned.append([str(cell).strip() if cell is not None else "" for cell in row])
 
    if not cleaned:
        return ""
 
    header = cleaned[0]
    rows = cleaned[1:]
 
    md = "| " + " | ".join(header) + " |\n"
    md += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in rows:
        # Pad row if shorter than header
        padded = row + [""] * (len(header) - len(row))
        md += "| " + " | ".join(padded[:len(header)]) + " |\n"
 
    return md

def page_to_base64_image(fitz_doc, page_index: int) -> str:
    """Render a PDF page as a PNG and return base64 string."""
    page = fitz_doc[page_index]
    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for readability
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    return base64.b64encode(img_bytes).decode("utf-8")

def load_pdf(file_bytes: bytes) -> list[dict]:
    print("11......")
    """
    Load a PDF and return a list of page chunks.
 
    Each chunk is a dict:
    {
        "page": int,
        "text": str,          # extracted text (may be empty)
        "tables": str,        # tables as markdown (may be empty)
        "image_b64": str | None,  # set only for image-only pages
        "has_content": bool
    }
    """
    chunks = []
    print("a......")
    pdf_stream = io.BytesIO(file_bytes)
    fitz_doc = fitz.open(stream=file_bytes, filetype="pdf")
    print("b.........")
    with pdfplumber.open(pdf_stream) as pdf:
        for i, page in enumerate(pdf.pages):
            raw_text = page.extract_text() or ""
            text = raw_text.strip()
 
            # Extract and convert tables to markdown
            tables_md = ""
            try:
                tables = page.extract_tables()
                if tables:
                    table_parts = []
                    for table in tables:
                        md = table_to_markdown(table)
                        if md:
                            table_parts.append(md)
                    tables_md = "\n\n".join(table_parts)
            except Exception:
                pass
 
            # Decide if this is an image-only page
            # Criteria: has images embedded but very little extractable text
            page_images = page.images
            is_image_only = len(page_images) > 0 and len(text) < 80 and not tables_md
 
            image_b64 = None
            if is_image_only:
                try:
                    image_b64 = page_to_base64_image(fitz_doc, i)
                except Exception:
                    pass
 
            has_content = bool(text) or bool(tables_md) or image_b64 is not None
 
            chunks.append({
                "page": i + 1,
                "text": text,
                "tables": tables_md,
                "image_b64": image_b64,
                "has_content": has_content,
            })
 
    fitz_doc.close()
    return chunks

def load_txt(file_bytes: bytes) -> list[dict]:
    """
    Load a plain text or CSV file.
 
    Splits on double newlines (paragraph/section boundaries).
    Returns a list of chunks, each with just a "text" field.
    """
    content = file_bytes.decode("utf-8", errors="replace").strip()
 
    raw_sections = [s.strip() for s in content.split("\n\n") if s.strip()]
 
    merged = []
    buffer = ""
    for section in raw_sections:
        buffer = (buffer + "\n\n" + section).strip() if buffer else section
        if len(buffer) > 300:
            merged.append(buffer)
            buffer = ""
    if buffer:
        merged.append(buffer)
 
    return [
        {"page": i + 1, "text": chunk, "tables": "", "image_b64": None, "has_content": True}
        for i, chunk in enumerate(merged)
    ]
 
 
