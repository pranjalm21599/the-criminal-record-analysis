from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.file_parser import FileParser
from ..models.fir import FIR
from ..mongo import raw_docs_collection
import uuid

router = APIRouter(prefix="/upload", tags=["Data Ingestion"])

@router.post("/fir")
async def upload_fir(
    case_id: int = Form(...),
    fir_number: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    
    # 1. Parse Text
    raw_text = ""
    if file.filename.endswith(".pdf"):
        raw_text = FileParser.parse_pdf(content)
    else:
        raw_text = content.decode("utf-8")

    # 2. Store in MongoDB (Raw Storage for NLP/AI teammates)
    mongo_entry = {
        "fir_number": fir_number,
        "filename": file.filename,
        "content": raw_text,
        "uuid": str(uuid.uuid4())
    }
    await raw_docs_collection.insert_one(mongo_entry)

    # 3. Store Structured Record in Postgres
    new_fir = FIR(
        fir_number=fir_number,
        case_id=case_id,
        raw_text=raw_text,
        source_file=file.filename,
        # Other fields would be extracted by NLP service (Member 2)
        # Here we just initialize the record
    )
    db.add(new_fir)
    db.commit()
    db.refresh(new_fir)

    return {"message": "FIR Uploaded and Queued for Analysis", "fir_id": new_fir.id}