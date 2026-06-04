def build_llm_context(chunks: list[dict]) -> tuple[list, list]:
    """
    Convert chunks into two things:
    - text_context: a single string of all text + tables for the text prompt
    - image_chunks: list of chunks that have image_b64 (for vision calls)
 
    The LLM extraction call uses text_context as the main input.
    Image chunks are passed separately if the model supports vision.
    """
    text_parts = []
    image_chunks = []
 
    for chunk in chunks:
        if not chunk["has_content"]:
            continue
 
        if chunk["image_b64"]:
            # Image-only page — collect for vision
            image_chunks.append(chunk)
            continue
 
        page_text = f"[Page {chunk['page']}]\n"
 
        if chunk["text"]:
            page_text += chunk["text"] + "\n"
 
        if chunk["tables"]:
            page_text += "\n[Tables on this page]\n" + chunk["tables"] + "\n"
 
        text_parts.append(page_text.strip())
 
    text_context = "\n\n---\n\n".join(text_parts)
    return text_context, image_chunks