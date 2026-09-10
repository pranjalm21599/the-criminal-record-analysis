import pandas as pd
import json
from PyPDF2 import PdfReader
import io
from fastapi import HTTPException

class FileParser:
    @staticmethod
    def parse_pdf(file_content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF Parsing Error: {str(e)}")

    @staticmethod
    def parse_csv(file_content: bytes):
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            return df.to_dict(orient="records")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV Parsing Error: {str(e)}")

    @staticmethod
    def parse_excel(file_content: bytes):
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            return df.to_dict(orient="records")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel Parsing Error: {str(e)}")

    @staticmethod
    def parse_json(file_content: bytes):
        try:
            return json.loads(file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"JSON Parsing Error: {str(e)}")
        