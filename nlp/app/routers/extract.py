from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from app.extractors.fir_extractor import FIRExtractor
from app.extractors.pattern_extractor import PatternExtractor
from app.extractors.ner_extractor import NERExtractor
from app.services.cdr_extractor import CDRExtractor

router = APIRouter(
    prefix="/extract",
    tags=["NLP Extraction"]
)


fir_extractor = FIRExtractor()
pattern_extractor = PatternExtractor()
ner_extractor = NERExtractor()
cdr_extractor = CDRExtractor()

class TextInput(BaseModel):
    text: str
    document_id: Optional[int] = None
    document_type: str = "general"


class BatchInput(BaseModel):
    documents: List[TextInput]


@router.post("/text")
def extract_from_text(input_data: TextInput):

    text = input_data.text

    ner_results = ner_extractor.extract_entities(text)

    pattern_results = pattern_extractor.extract_all(text)

    return {
        "document_id": input_data.document_id,
        "document_type": input_data.document_type,
        "named_entities": ner_results,
        "pattern_entities": pattern_results,
        "crime_keywords": ner_extractor.extract_crime_events(text),
        "ipc_sections": ner_extractor.extract_ipc_sections(text),
        "relationships": ner_extractor.extract_relationships(text)
    }


@router.post("/fir/{fir_id}")
def extract_from_fir(
    fir_id: int,
    text_input: TextInput
):

    return fir_extractor.extract_full_fir(
        text_input.text,
        fir_id
    )


@router.post("/phones")
def extract_phones(text_input: TextInput):

    phones = pattern_extractor.extract_phones(
        text_input.text
    )

    return {
        "phones": phones,
        "count": len(phones)
    }


@router.post("/batch")
def extract_batch(batch: BatchInput):

    results = []

    for document in batch.documents:

        result = extract_from_text(document)

        results.append(result)

    return {
        "processed": len(results),
        "results": results
    }
class CDRInput(BaseModel):
    records: List[dict]


@router.post("/cdr")
def analyze_cdr(input_data: CDRInput):

    return cdr_extractor.analyze_cdr(
        input_data.records
    )