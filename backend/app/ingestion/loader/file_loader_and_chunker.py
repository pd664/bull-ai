from pathlib import Path
from app.ingestion.loader.helpers import load_pdf, load_txt

def load_document_and_chunker(filename: str, file_bytes: bytes) -> list[dict]:
    """
    Entry point. Routes to the right loader based on file extension.
    Returns a list of page/section chunks.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return load_pdf(file_bytes)
    elif ext in (".txt", ".csv"):
        return load_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    