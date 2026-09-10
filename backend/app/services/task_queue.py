from celery import Celery
from ..config import settings
from ..database import SessionLocal
from ..models.call_record import CallRecord
from ..models.transaction import Transaction
from .data_normalizer import DataNormalizer
import pandas as pd
import io

celery_app = Celery("tasks", broker=settings.REDIS_URL)

@celery_app.task
def process_cdr_bulk(file_content_bytes, case_id):
    db = SessionLocal()
    try:
        df = pd.read_csv(io.BytesIO(file_content_bytes))
        records_to_add = []
        
        for _, row in df.iterrows():
            record = CallRecord(
                caller_number=DataNormalizer.normalize_phone(row['caller_number']),
                receiver_number=DataNormalizer.normalize_phone(row['receiver_number']),
                call_duration=int(row.get('duration', 0)),
                call_timestamp=pd.to_datetime(row['timestamp']),
                case_id=case_id
            )
            records_to_add.append(record)
            
            # Batch insert every 500 records
            if len(records_to_add) >= 500:
                db.bulk_save_objects(records_to_add)
                db.commit()
                records_to_add = []
        
        db.bulk_save_objects(records_to_add)
        db.commit()
    finally:
        db.close()