from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from pathlib import Path 
from app.ingestion.loader.file_loader_and_chunker import load_document_and_chunker
from app.ingestion.clean_text import clean_text
from app.llm.build_context import build_llm_context
from app.llm.extractor import extract_fields
from app.generator.pdf_generator import generate_pdf

router = APIRouter()

Upload_Dir = Path("uploads")
Upload_Dir.mkdir(
    exist_ok=True
)

@router.post('/generate-report')
async def upload_file(company_name: str = Form(...), file: UploadFile = File(...)):
    try: 
        print(1)
        file_bytes = await file.read()  
        print(2)
        file_path = Upload_Dir / file.filename
        with open(file_path, 'wb') as buffer:
            buffer.write(file_bytes)  
        print(3)
        chunks = load_document_and_chunker(file.filename, file_bytes)

        text_context, _ = build_llm_context(chunks)
        print(4)
        data = extract_fields(company_name, text_context)
        print("extracted fields ", data)
        pdf_bytes = generate_pdf(data)
        print(6)
        filename = f"{company_name.replace(' ', '_')}_report.pdf"
        print(7)
        return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="{filename}"'
                    )
                },
            )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}",
        )